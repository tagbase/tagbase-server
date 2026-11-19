// Browser checks for the upload page against a running https://localhost stack.
// Driven by test_upload_page_sanity.py, which starts headless Chrome with a
// DevTools port and passes that port as argv[2]. Ingest POST and GET are
// answered here, so the check never writes a submission; any other write is
// refused.
//
// Env: UPLOAD_SANITY_URL, UPLOAD_SANITY_USER, UPLOAD_SANITY_PASS.

const port = process.argv[2];
const pageUrl = process.env.UPLOAD_SANITY_URL;
const user = process.env.UPLOAD_SANITY_USER;
const pass = process.env.UPLOAD_SANITY_PASS;
const pageOrigin = new URL(pageUrl).origin;
const STORAGE_KEY = "tagbase-ingest-jobs";
const MISSING_ID = "00000000-0000-4000-8000-0000000000ff";
const FLAKY_ID = "00000000-0000-4000-8000-0000000000fe";
const SUMMARY_ID = "00000000-0000-4000-8000-0000000000fd";
const QUEUED_ID = "00000000-0000-4000-8000-0000000000fc";
const TIMEOUT_ID = "00000000-0000-4000-8000-0000000000fb";
const READ_ONLY_POSTS = [
  "/grafana/ofrep/v1/evaluate/flags",
  "/grafana/api/ds/query",
];

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const results = [];
let fatal = null;
let cdp;
let jobPhase = "running";
let missingMode = "show";
let flakyMode = "ok";
let queueAhead = 2;
let postsInFlight = 0;
let postsOverlapped = false;
const posts = [];
const uploadIds = [];
const pageLogs = [];
const getsInFlight = new Map();
const getCounts = new Map();
let getsOverlapped = false;
const strayWrites = [];
const offOriginAuth = [];
const jobIds = new Map();

const deadline = setTimeout(() => {
  console.log("FAIL  sanity check timed out");
  process.exit(1);
}, 240000);
deadline.unref();

function report(ok, name, detail) {
  const suffix = !ok && detail ? `: ${detail}` : "";
  console.log(`${ok ? "PASS" : "FAIL"}  ${name}${suffix}`);
  results.push(ok);
}

function header(request, name) {
  const headers = request.headers || {};
  const key = Object.keys(headers).find(
    (item) => item.toLowerCase() === name.toLowerCase(),
  );
  return key ? String(headers[key]) : "";
}

function jobIdFromUrl(url) {
  const parsed = new URL(url);
  const filename = parsed.searchParams.get("filename") || "file";
  if (!jobIds.has(filename)) {
    const n = (jobIds.size + 1).toString(16).padStart(12, "0");
    jobIds.set(filename, `00000000-0000-4000-8000-${n}`);
  }
  return jobIds.get(filename);
}

class Cdp {
  constructor(ws) {
    this.ws = ws;
    this.next = 0;
    this.pending = new Map();
    this.eventWaiters = [];
    ws.addEventListener("message", (event) => {
      const message = JSON.parse(event.data);
      if (message.id && this.pending.has(message.id)) {
        const waiter = this.pending.get(message.id);
        this.pending.delete(message.id);
        if (message.error)
          waiter.reject(new Error(JSON.stringify(message.error)));
        else waiter.resolve(message.result);
        return;
      }
      if (message.method === "Fetch.requestPaused") {
        onPaused(message).catch((error) => {
          fatal = error;
        });
        return;
      }
      if (
        message.method === "Runtime.exceptionThrown" ||
        message.method === "Runtime.consoleAPICalled"
      ) {
        pageLogs.push(message);
        return;
      }
      if (message.method === "Fetch.authRequired") {
        this.send("Fetch.continueWithAuth", {
          requestId: message.params.requestId,
          authChallengeResponse: {
            response: "ProvideCredentials",
            username: user,
            password: pass,
          },
        }).catch((error) => {
          fatal = error;
        });
        return;
      }
      const index = this.eventWaiters.findIndex((waiter) =>
        waiter.match(message),
      );
      if (index >= 0) {
        const waiter = this.eventWaiters.splice(index, 1)[0];
        clearTimeout(waiter.timer);
        waiter.resolve(message);
      }
    });
  }

  send(method, params = {}) {
    const id = ++this.next;
    this.ws.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
    });
  }

  waitFor(match, timeoutMs) {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        const index = this.eventWaiters.findIndex(
          (waiter) => waiter.timer === timer,
        );
        if (index >= 0) this.eventWaiters.splice(index, 1);
        reject(new Error(`timed out waiting for ${timeoutMs}ms`));
      }, timeoutMs);
      this.eventWaiters.push({ match, resolve, timer });
    });
  }
}

const PHRASES = {
  200: "OK",
  202: "Accepted",
  204: "No Content",
  404: "Not Found",
  405: "Method Not Allowed",
  500: "Internal Server Error",
};

async function fulfill(
  requestId,
  status,
  body,
  contentType = "application/json",
) {
  const payload = typeof body === "string" ? body : JSON.stringify(body);
  await cdp.send("Fetch.fulfillRequest", {
    requestId,
    responseCode: status,
    responsePhrase: PHRASES[status] || "OK",
    responseHeaders: [
      { name: "Content-Type", value: contentType },
      { name: "Cache-Control", value: "no-store" },
    ],
    body: Buffer.from(payload).toString("base64"),
  });
}

async function passThrough(requestId, request, parsed) {
  if (parsed.origin !== pageOrigin) {
    if (header(request, "authorization")) offOriginAuth.push(request.url);
    await cdp.send("Fetch.continueRequest", { requestId });
    return;
  }
  // The page and its assets sit behind basic auth. Headless Chrome fails
  // the navigation on a 401, so attach the credentials, same origin only.
  const headers = Object.entries(request.headers || {}).map(
    ([name, value]) => ({
      name,
      value: String(value),
    }),
  );
  headers.push({
    name: "Authorization",
    value: `Basic ${Buffer.from(`${user}:${pass}`).toString("base64")}`,
  });
  await cdp.send("Fetch.continueRequest", { requestId, headers });
}

async function onPaused(message) {
  const { requestId, request } = message.params;
  const method = request.method;
  const url = request.url;
  let parsed;
  try {
    parsed = new URL(url);
  } catch (error) {
    await fulfill(requestId, 500, { error: "bad url" });
    throw error;
  }
  const collection = parsed.pathname.endsWith("/ingest/jobs");
  const oneJob = /\/ingest\/jobs\/[^/]+$/.test(parsed.pathname);
  if (!collection && !oneJob) {
    // The embedded Grafana panel POSTs these reads (feature flags, a Loki
    // query). They are not writes, so they pass with the page's credentials.
    const grafanaRead =
      method === "POST" &&
      parsed.origin === pageOrigin &&
      READ_ONLY_POSTS.includes(parsed.pathname);
    if (method !== "GET" && method !== "HEAD" && !grafanaRead) {
      strayWrites.push(`${method} ${url}`);
      await fulfill(requestId, 405, { error: "sanity check refuses writes" });
      return;
    }
    await passThrough(requestId, request, parsed);
    return;
  }
  if (method === "OPTIONS") {
    await fulfill(requestId, 204, "");
    return;
  }
  if (method === "POST" && collection) {
    if (postsInFlight > 0) postsOverlapped = true;
    postsInFlight += 1;
    posts.push({
      filename: parsed.searchParams.get("filename") || "",
      contentType: header(request, "content-type"),
    });
    await sleep(250);
    postsInFlight -= 1;
    const id = jobIdFromUrl(url);
    uploadIds.push(id);
    await fulfill(requestId, 202, { id, status: "queued" });
    return;
  }
  if (method === "GET" && oneJob) {
    const id = decodeURIComponent(parsed.pathname.split("/").pop());
    getCounts.set(id, (getCounts.get(id) || 0) + 1);
    const inFlight = (getsInFlight.get(id) || 0) + 1;
    getsInFlight.set(id, inFlight);
    if (inFlight > 1) getsOverlapped = true;
    try {
      await sleep(150);
      await answerJob(requestId, id);
    } finally {
      getsInFlight.set(id, getsInFlight.get(id) - 1);
    }
    return;
  }
  strayWrites.push(`${method} ${url}`);
  await fulfill(requestId, 405, { error: "unexpected ingest request" });
}

const isoAgo = (seconds) => new Date(Date.now() - seconds * 1000).toISOString();

// Job bodies follow the row-backed contract: stage, current_member, summary,
// created_at, and updated_at come from the ingest_job row.
function runningBody() {
  return {
    status: "running",
    stage: "Writing measurements",
    current_member: "deep/dir/dup.txt",
    files_done: 1,
    files_total: 3,
    created_at: isoAgo(20),
    updated_at: isoAgo(2),
  };
}

function succeededBody() {
  return {
    status: "succeeded",
    files_done: 3,
    files_total: 3,
    created_at: isoAgo(30),
    updated_at: isoAgo(0),
    summary: {
      files: 3,
      loaded: 1,
      metadata_only: 0,
      duplicates: 2,
      skipped_lines: 0,
      seconds: 4.5,
    },
  };
}

function summaryBody() {
  return {
    status: "succeeded",
    files_done: 2,
    files_total: 2,
    created_at: isoAgo(10),
    updated_at: isoAgo(0),
    summary: {
      files: 2,
      loaded: 0,
      metadata_only: 0,
      duplicates: 2,
      skipped_lines: 3,
      seconds: 4.5,
    },
  };
}

async function answerJob(requestId, id) {
  // Never answered: the page's own timeout must report it.
  if (id === TIMEOUT_ID) return;
  if (id === MISSING_ID) {
    if (missingMode === "show") {
      await fulfill(requestId, 200, {
        status: "running",
        stage: "Starting",
        files_done: 0,
        files_total: 0,
        created_at: isoAgo(5),
        updated_at: isoAgo(5),
      });
    } else {
      await fulfill(requestId, 404, {});
    }
    return;
  }
  if (id === SUMMARY_ID) {
    await fulfill(requestId, 200, summaryBody());
    return;
  }
  if (id === QUEUED_ID) {
    await fulfill(requestId, 200, {
      status: "queued",
      files_done: 0,
      files_total: 0,
      queue_position: queueAhead,
      created_at: isoAgo(1),
      updated_at: isoAgo(1),
    });
    return;
  }
  if (id === FLAKY_ID) {
    if (flakyMode === "ok") {
      await fulfill(requestId, 200, {
        status: "running",
        stage: "Reading the file",
        current_member: "flaky.txt",
        files_done: 0,
        files_total: 1,
        created_at: isoAgo(3),
        updated_at: isoAgo(1),
      });
    } else {
      await fulfill(
        requestId,
        500,
        {
          type: "urn:tagbase:problem:http-error",
          title: "Internal Server Error",
          status: 500,
          detail: "sanity server error",
        },
        "application/problem+json",
      );
    }
    return;
  }
  await fulfill(
    requestId,
    200,
    jobPhase === "succeeded" ? succeededBody() : runningBody(),
  );
}

async function evaluate(expression, awaitPromise = false) {
  if (fatal) throw fatal;
  const result = await cdp.send("Runtime.evaluate", {
    expression,
    awaitPromise,
    returnByValue: true,
  });
  if (result.exceptionDetails) {
    const details = result.exceptionDetails;
    const described =
      details.exception && details.exception.description
        ? details.exception.description
        : details.text;
    throw new Error(described || "page evaluate failed");
  }
  return result.result ? result.result.value : undefined;
}

async function waitUntil(expression, timeoutMs, label) {
  const start = Date.now();
  let last = null;
  while (Date.now() - start < timeoutMs) {
    if (fatal) throw fatal;
    last = await evaluate(expression);
    if (last) return last;
    await sleep(100);
  }
  throw new Error(`${label} timed out: ${JSON.stringify(last)}`);
}

// Reads one job card by id. Returns a plain object the checks compare.
function cardState(id) {
  return `(() => {
    const card = document.querySelector('[data-job-id="${id}"]');
    if (!card) return null;
    const count = card.querySelector(".job-count");
    const panel = card.querySelector(".job-log-panel");
    const button = card.querySelector(".job-log-toggle");
    const frame = panel.querySelector("iframe");
    const member = count.querySelector(".job-member");
    const summary = card.querySelector(".job-summary");
    const warning = card.querySelector(".job-warning");
    const error = card.querySelector(".job-error");
    return {
      stage: card.querySelector(".job-stage").textContent,
      elapsed: card.querySelector(".job-elapsed").textContent,
      chipHidden: count.hidden,
      index: count.querySelector(".job-count-current").textContent,
      total: count.querySelector(".job-count-total").textContent,
      member: member.textContent,
      memberTitle: member.title,
      summary: summary.textContent,
      summaryHidden: summary.hidden,
      warning: warning.textContent,
      warningHidden: warning.hidden,
      error: error.textContent,
      errorHidden: error.hidden,
      panelHidden: panel.hidden,
      expanded: button.getAttribute("aria-expanded"),
      frameSrc: frame ? frame.getAttribute("src") : null,
      openHref: panel.querySelector(".job-log-open").getAttribute("href"),
      technicalButtons: card.querySelectorAll(".job-log-mode").length,
    };
  })()`;
}

function setJobs(jobs) {
  return `localStorage.setItem(${JSON.stringify(STORAGE_KEY)}, JSON.stringify(${JSON.stringify(jobs)}))`;
}

async function clickSelector(selector) {
  const point = await evaluate(`(() => {
    const el = document.querySelector(${JSON.stringify(selector)});
    if (!el) return null;
    el.scrollIntoView({ behavior: "instant", block: "center", inline: "center" });
    const rect = el.getBoundingClientRect();
    const x = rect.left + rect.width / 2;
    const y = rect.top + rect.height / 2;
    const top = document.elementFromPoint(x, y);
    return {
      x,
      y,
      hit: !!top && (top === el || el.contains(top)),
      top: top ? String(top.className || top.tagName) : "",
    };
  })()`);
  if (!point) return { ok: false, detail: `missing ${selector}` };
  if (!point.hit) return { ok: false, detail: `covered by ${point.top}` };
  await cdp.send("Input.dispatchMouseEvent", {
    type: "mouseMoved",
    x: point.x,
    y: point.y,
  });
  await cdp.send("Input.dispatchMouseEvent", {
    type: "mousePressed",
    x: point.x,
    y: point.y,
    button: "left",
    clickCount: 1,
  });
  await cdp.send("Input.dispatchMouseEvent", {
    type: "mouseReleased",
    x: point.x,
    y: point.y,
    button: "left",
    clickCount: 1,
  });
  return { ok: true };
}

async function main() {
  const list = await fetch(`http://127.0.0.1:${port}/json/list`).then(
    (response) => response.json(),
  );
  const page = list.find((target) => target.type === "page");
  if (!page) throw new Error("Chrome has no page target");
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    ws.addEventListener("open", resolve, { once: true });
    ws.addEventListener(
      "error",
      () => reject(new Error("DevTools socket failed")),
      {
        once: true,
      },
    );
  });
  cdp = new Cdp(ws);
  await cdp.send("Network.enable");
  await cdp.send("Page.enable");
  await cdp.send("Runtime.enable");
  await cdp.send("Fetch.enable", {
    handleAuthRequests: true,
    patterns: [{ urlPattern: "*", requestStage: "Request" }],
  });
  const loaded = cdp.waitFor(
    (message) => message.method === "Page.loadEventFired",
    20000,
  );
  // Credentials are answered through Fetch.authRequired, not put in the URL:
  // a URL with user:pass makes the page's fetch() calls fail.
  await cdp.send("Page.navigate", { url: pageUrl });
  await loaded;
  const probe = await evaluate(`(() => ({
    dropzone: typeof window.Dropzone,
    resources: performance.getEntriesByType("resource").map((entry) => ({
      name: entry.name,
      status: entry.responseStatus,
    })),
  }))()`);
  if (probe.dropzone !== "function") {
    throw new Error(
      `Dropzone missing: ${JSON.stringify(probe)} logs=${JSON.stringify(pageLogs).slice(0, 1500)}`,
    );
  }
  await waitUntil(
    `(() => {
      const zone = document.querySelector("#drop-zone");
      return !!(window.Dropzone && zone && zone.dropzone);
    })()`,
    20000,
    "Dropzone",
  );

  const dropzoneAssets = probe.resources.filter((entry) =>
    /dropzone/i.test(entry.name),
  );
  report(
    dropzoneAssets.length > 0 &&
      dropzoneAssets.every(
        (entry) => entry.name.startsWith(pageOrigin) && entry.status === 200,
      ),
    "Dropzone is served from this origin, not a CDN",
    JSON.stringify(dropzoneAssets),
  );

  const buttons = await evaluate(`(() => {
    const zone = document.querySelector("#drop-zone.dropzone");
    const labels = [...document.querySelectorAll("button")].map((button) =>
      button.textContent.replace(/\\s+/g, " ").trim(),
    );
    return {
      dropzone: !!zone,
      uploadButtons: labels.filter((label) => /^upload$/i.test(label)),
    };
  })()`);
  report(
    buttons.dropzone && buttons.uploadButtons.length === 0,
    "no Upload button; Dropzone is present",
    buttons.dropzone ? "found an Upload button" : "Dropzone is missing",
  );

  const added = await evaluate(`(() => {
    const zone = document.querySelector("#drop-zone").dropzone;
    const names = ["sanity-a.txt", "sanity-b.txt", "sanity-c.txt"];
    for (const name of names) {
      zone.addFile(new File(["tagbase sanity\\n"], name, { type: "" }));
    }
    return zone.files.map((file) => ({ name: file.name, status: file.status }));
  })()`);
  const postDeadline = Date.now() + 15000;
  while (posts.length < 3 && Date.now() < postDeadline) {
    if (fatal) throw fatal;
    await sleep(50);
  }
  const names = posts.map((post) => post.filename);
  const unique = new Set(names);
  const raw = posts.every(
    (post) =>
      post.contentType.toLowerCase().includes("application/octet-stream") &&
      !post.contentType.toLowerCase().includes("multipart"),
  );
  const separate =
    posts.length === 3 &&
    unique.size === 3 &&
    !postsOverlapped &&
    raw &&
    ["sanity-a.txt", "sanity-b.txt", "sanity-c.txt"].every((name) =>
      unique.has(name),
    );
  report(
    separate,
    "three files, three jobs, one at a time",
    `posts=${JSON.stringify(posts)} overlap=${postsOverlapped} added=${JSON.stringify(added)}`,
  );

  const sanityId = uploadIds[0];
  const sanityIds = uploadIds.slice(0, 3);

  await waitUntil(
    `(() => {
      const card = document.querySelector('[data-job-id="${sanityId}"]');
      if (!card) return null;
      const count = card.querySelector(".job-count");
      if (count.hidden) return null;
      if (count.querySelector(".job-count-current").textContent !== "2") return null;
      return true;
    })()`,
    10000,
    "running file chip",
  );
  const running = await evaluate(cardState(sanityId));
  report(
    running &&
      running.stage === "Writing measurements" &&
      running.member === "dup.txt" &&
      running.memberTitle === "deep/dir/dup.txt" &&
      running.index === "2" &&
      running.total === "3" &&
      running.panelHidden === true &&
      running.expanded === "false" &&
      running.frameSrc === null,
    "running card shows the row's stage and file; log stays closed",
    JSON.stringify(running),
  );

  await sleep(2000);
  const later = await evaluate(cardState(sanityId));
  report(
    running && later && later.elapsed !== running.elapsed,
    "elapsed clock keeps moving while the job runs",
    `${running && running.elapsed} -> ${later && later.elapsed}`,
  );

  const openClick = await clickSelector(
    `[data-job-id="${sanityId}"] .job-log-toggle`,
  );
  const opened = await evaluate(cardState(sanityId));
  report(
    openClick.ok &&
      opened &&
      opened.panelHidden === false &&
      opened.expanded === "true" &&
      typeof opened.frameSrc === "string" &&
      opened.frameSrc.startsWith(
        "/grafana/d-solo/tagbase-job-log/ingest-job-log?",
      ) &&
      opened.frameSrc.includes(`var-job_id=${sanityId}`) &&
      opened.openHref.startsWith(
        "/grafana/d/tagbase-job-log/ingest-job-log?",
      ) &&
      opened.openHref.includes(`var-job_id=${sanityId}`),
    "Log click mounts a Grafana frame for this job only",
    `click=${JSON.stringify(openClick)} state=${JSON.stringify(opened)}`,
  );

  jobPhase = "succeeded";
  await evaluate(
    `(async () => {
      await pollOnce();
      await pollOnce();
      return true;
    })()`,
    true,
  );
  const held = await evaluate(cardState(sanityId));
  const settled =
    held &&
    held.stage === "Successful" &&
    held.chipHidden === false &&
    held.index === "3" &&
    held.total === "3" &&
    held.member === "" &&
    held.summary === "3 files: 1 loaded, 2 already ingested, 5s" &&
    held.summaryHidden === false &&
    held.errorHidden === true;
  report(
    settled,
    "finished card shows Successful, the summary from the row, and the file total",
    JSON.stringify(held),
  );

  let dropped = false;
  try {
    await waitUntil(
      `JSON.parse(localStorage.getItem("${STORAGE_KEY}") || "[]").length === 0 || null`,
      10000,
      "finished jobs leave storage",
    );
    dropped = true;
  } catch {
    dropped = false;
  }
  report(dropped, "finished jobs are dropped from localStorage");

  const countsBefore = sanityIds.map((id) => getCounts.get(id) || 0);
  await sleep(1200);
  const tickOne = await evaluate(cardState(sanityId));
  await sleep(3500);
  const tickTwo = await evaluate(cardState(sanityId));
  const countsAfter = sanityIds.map((id) => getCounts.get(id) || 0);
  report(
    held &&
      tickOne &&
      tickTwo &&
      tickOne.elapsed === held.elapsed &&
      tickTwo.elapsed === held.elapsed &&
      JSON.stringify(countsBefore) === JSON.stringify(countsAfter),
    "finished jobs are not polled again and their card stays still",
    `elapsed=${held && held.elapsed}->${tickTwo && tickTwo.elapsed} polls=${JSON.stringify(countsBefore)}->${JSON.stringify(countsAfter)}`,
  );

  const closeClick = await clickSelector(
    `[data-job-id="${sanityId}"] .job-log-toggle`,
  );
  const closed = await evaluate(cardState(sanityId));
  report(
    closeClick.ok &&
      closed &&
      closed.panelHidden === true &&
      closed.expanded === "false" &&
      closed.frameSrc === null,
    "Log click again closes the panel and removes the frame",
    `click=${JSON.stringify(closeClick)} state=${JSON.stringify(closed)}`,
  );

  await evaluate(
    `(async () => {
      ${setJobs([{ id: MISSING_ID, filename: "gone.txt", acceptedAt: Date.now() }])};
      await pollOnce();
      await pollOnce();
      return true;
    })()`,
    true,
  );
  const appeared = await evaluate(
    `!!document.querySelector('[data-job-id="${MISSING_ID}"]')`,
  );
  missingMode = "drop";
  await evaluate(
    `(async () => {
      await pollOnce();
      await pollOnce();
      return true;
    })()`,
    true,
  );
  const removed = await evaluate(
    `!document.querySelector('[data-job-id="${MISSING_ID}"]')`,
  );
  report(
    appeared === true && removed === true,
    "404 job id does not leave a card",
    `appeared=${appeared} removed=${removed}`,
  );

  await evaluate(
    `(async () => {
      ${setJobs([{ id: FLAKY_ID, filename: "flaky.txt", acceptedAt: Date.now() }])};
      await pollOnce();
      await pollOnce();
      return true;
    })()`,
    true,
  );
  const flakyBefore = await evaluate(cardState(FLAKY_ID));
  flakyMode = "error";
  await evaluate(
    `(async () => {
      await pollOnce();
      await pollOnce();
      return true;
    })()`,
    true,
  );
  const flakyAfter = await evaluate(cardState(FLAKY_ID));
  report(
    flakyBefore &&
      flakyAfter &&
      flakyBefore.stage === "Reading the file" &&
      flakyAfter.stage === flakyBefore.stage &&
      flakyAfter.errorHidden === false &&
      flakyAfter.error === "Status check failed: sanity server error",
    "server error keeps the last good card and shows the error",
    `before=${JSON.stringify(flakyBefore)} after=${JSON.stringify(flakyAfter)}`,
  );

  // A status request that gets no answer must fail after the page's timeout.
  await evaluate(
    `(() => {
      ${setJobs([{ id: TIMEOUT_ID, filename: "slow.txt", acceptedAt: Date.now() }])};
      pollOnce();
      return true;
    })()`,
  );
  let timedOut = false;
  try {
    await waitUntil(
      `(() => {
        const card = document.querySelector('[data-job-id="${TIMEOUT_ID}"]');
        if (!card) return null;
        const error = card.querySelector(".job-error");
        return !error.hidden && error.textContent === "Status check failed: no response from the server" ? true : null;
      })()`,
      30000,
      "timeout error",
    );
    timedOut = true;
  } catch {
    timedOut = false;
  }
  await evaluate(`(() => { ${setJobs([])}; return true; })()`);
  report(timedOut, "a status check with no answer shows a timeout error");

  await evaluate(
    `(async () => {
      ${setJobs([{ id: QUEUED_ID, filename: "waiting.txt", acceptedAt: Date.now() }])};
      await pollOnce();
      await pollOnce();
      return true;
    })()`,
    true,
  );
  const queuedBehind = await evaluate(cardState(QUEUED_ID));
  queueAhead = 0;
  await evaluate(
    `(async () => {
      await pollOnce();
      await pollOnce();
      return true;
    })()`,
    true,
  );
  const queuedNext = await evaluate(cardState(QUEUED_ID));
  report(
    queuedBehind &&
      queuedNext &&
      queuedBehind.stage === "Queued, 2 ahead" &&
      queuedNext.stage === "Queued, next",
    "queued jobs show how many are ahead",
    `behind=${queuedBehind && queuedBehind.stage} next=${queuedNext && queuedNext.stage}`,
  );

  await evaluate(
    `(async () => {
      ${setJobs([{ id: SUMMARY_ID, filename: "dups.zip", acceptedAt: Date.now() }])};
      await pollOnce();
      await pollOnce();
      return true;
    })()`,
    true,
  );
  const readable = await evaluate(cardState(SUMMARY_ID));
  report(
    readable &&
      readable.stage === "Skipped: already ingested" &&
      readable.summaryHidden === false &&
      readable.summary ===
        "2 files: 0 loaded, 2 already ingested, 3 lines skipped, 5s" &&
      readable.warningHidden === false &&
      readable.warning.startsWith("3 lines had no date and time") &&
      readable.technicalButtons === 0,
    "duplicates show as skipped with a summary and a skipped-lines warning",
    JSON.stringify(readable),
  );

  await evaluate(
    `(async () => {
      await Promise.all([pollOnce(), pollOnce(), pollOnce()]);
      return true;
    })()`,
    true,
  );
  report(
    !getsOverlapped,
    "job polls never overlap",
    "two GETs for one job were in flight at once",
  );

  report(
    strayWrites.length === 0 && offOriginAuth.length === 0,
    "no writes reach the server; credentials stay on the page origin",
    `writes=${JSON.stringify(strayWrites)} offOriginAuth=${JSON.stringify(offOriginAuth)}`,
  );

  if (!results.every(Boolean)) process.exit(1);
  // The CDP socket and Chrome keep the event loop alive; exit explicitly.
  process.exit(0);
}

main().catch((error) => {
  console.log(
    `FAIL  sanity check aborted: ${error && error.message ? error.message : error}`,
  );
  process.exit(1);
});
