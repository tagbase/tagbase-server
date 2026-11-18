#!/usr/bin/env bash
# Check the upload page against a running https://localhost stack.
# Ingest POST and GET are answered inside headless Chrome, and any other
# write is refused, so the check never writes submissions.
#
# Usage: scripts/upload-page-sanity.sh
# Needs Chrome or Chromium (set CHROME_BIN to override) and Node 22+.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

UPLOAD_SANITY_URL="${UPLOAD_SANITY_URL:-https://localhost/upload.html}"
export UPLOAD_SANITY_URL
export UPLOAD_SANITY_USER="${UPLOAD_SANITY_USER:-tagbase}"
export UPLOAD_SANITY_PASS="${UPLOAD_SANITY_PASS:-tagbase}"

find_chrome() {
	if [[ -n "${CHROME_BIN:-}" ]]; then
		printf '%s' "$CHROME_BIN"
		return
	fi
	local mac="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
	if [[ -x "$mac" ]]; then
		printf '%s' "$mac"
		return
	fi
	local name
	for name in google-chrome google-chrome-stable chromium chromium-browser; do
		if command -v "$name" >/dev/null 2>&1; then
			command -v "$name"
			return
		fi
	done
}

CHROME_BIN="$(find_chrome)"
if [[ -z "$CHROME_BIN" || ! -x "$CHROME_BIN" ]]; then
	echo "FAIL  Chrome or Chromium not found; set CHROME_BIN" >&2
	exit 1
fi

tmpdir="$(mktemp -d "${TMPDIR:-/tmp}/upload-page-sanity.XXXXXX")"
chrome_pid=""

cleanup() {
	if [[ -n "$chrome_pid" ]]; then
		kill "$chrome_pid" >/dev/null 2>&1 || true
		wait "$chrome_pid" >/dev/null 2>&1 || true
	fi
	rm -rf "$tmpdir"
}
trap cleanup EXIT

"$CHROME_BIN" \
	--headless=new \
	--disable-gpu \
	--ignore-certificate-errors \
	--no-first-run \
	--no-default-browser-check \
	--user-data-dir="$tmpdir/profile" \
	--remote-debugging-port=0 \
	--remote-allow-origins=http://127.0.0.1 \
	--window-size=1280,900 \
	about:blank \
	>"$tmpdir/chrome.log" 2>&1 &
chrome_pid="$!"

port=""
attempts=0
while [[ "$attempts" -lt 50 ]]; do
	attempts=$((attempts + 1))
	if [[ -s "$tmpdir/profile/DevToolsActivePort" ]]; then
		port="$(head -n 1 "$tmpdir/profile/DevToolsActivePort")"
		break
	fi
	if ! kill -0 "$chrome_pid" >/dev/null 2>&1; then
		echo "FAIL  Chrome exited before DevTools was ready" >&2
		cat "$tmpdir/chrome.log" >&2 || true
		exit 1
	fi
	sleep 0.2
done

if [[ -z "$port" ]]; then
	echo "FAIL  Chrome DevTools port was not ready" >&2
	cat "$tmpdir/chrome.log" >&2 || true
	exit 1
fi

cat >"$tmpdir/sanity.mjs" <<'END_JS'
const port = process.argv[2];
const pageUrl = process.env.UPLOAD_SANITY_URL;
const user = process.env.UPLOAD_SANITY_USER;
const pass = process.env.UPLOAD_SANITY_PASS;
const pageOrigin = new URL(pageUrl).origin;
const MISSING_ID = "00000000-0000-4000-8000-0000000000ff";
const FLAKY_ID = "00000000-0000-4000-8000-0000000000fe";
const SUMMARY_ID = "00000000-0000-4000-8000-0000000000fd";
const QUEUED_ID = "00000000-0000-4000-8000-0000000000fc";
const STUB_HASH = "ab".repeat(32);

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const results = [];
let fatal = null;
let jobPhase = "running";
let missingMode = "show";
let flakyMode = "ok";
let queueAhead = 2;
let postsInFlight = 0;
let postsOverlapped = false;
const posts = [];
const pageLogs = [];
const getsInFlight = new Map();
let getsOverlapped = false;
const strayWrites = [];
const offOriginAuth = [];
const jobIds = new Map();

const deadline = setTimeout(() => {
  console.log("FAIL  sanity check timed out");
  process.exit(1);
}, 180000);
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
        if (message.error) waiter.reject(new Error(JSON.stringify(message.error)));
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
      const index = this.eventWaiters.findIndex((waiter) => waiter.match(message));
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
        const index = this.eventWaiters.findIndex((waiter) => waiter.timer === timer);
        if (index >= 0) this.eventWaiters.splice(index, 1);
        reject(new Error(`timed out waiting for ${timeoutMs}ms`));
      }, timeoutMs);
      this.eventWaiters.push({ match, resolve, timer });
    });
  }
}

let cdp;

const PHRASES = {
  200: "OK",
  202: "Accepted",
  204: "No Content",
  404: "Not Found",
  405: "Method Not Allowed",
  500: "Internal Server Error",
};

async function fulfill(requestId, status, body, contentType = "application/json") {
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

function logLines(...texts) {
  const now = new Date().toISOString();
  return texts.map((text) => ({ time: now, text }));
}

function runningBody() {
  return {
    status: "running",
    log_available: true,
    lines: logLines(
      "ingest.file index=2 total=3 member=dup.txt",
      "Writing measurements, still running elapsed=15s",
      "Writing measurements, still running elapsed=30s",
    ),
  };
}

function succeededBody() {
  return {
    status: "succeeded",
    log_available: true,
    lines: logLines(
      "ingest.file index=2 total=3 member=dup.txt",
      "No ingestion performed. exact duplicate",
    ),
  };
}

async function passThrough(requestId, request, parsed) {
  if (parsed.origin !== pageOrigin) {
    if (header(request, "authorization")) offOriginAuth.push(request.url);
    await cdp.send("Fetch.continueRequest", { requestId });
    return;
  }
  // The page and its assets sit behind basic auth. Headless Chrome fails
  // the navigation on a 401, so attach the credentials, same origin only.
  const headers = Object.entries(request.headers || {}).map(([name, value]) => ({
    name,
    value: String(value),
  }));
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
    if (method !== "GET" && method !== "HEAD") {
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
    await fulfill(requestId, 202, {
      id: jobIdFromUrl(url),
      status: "queued",
    });
    return;
  }
  if (method === "GET" && oneJob) {
    const id = decodeURIComponent(parsed.pathname.split("/").pop());
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

async function answerJob(requestId, id) {
  if (id === MISSING_ID) {
    if (missingMode === "show") {
      await fulfill(requestId, 200, {
        status: "running",
        log_available: true,
        lines: [],
      });
    } else {
      await fulfill(requestId, 404, {});
    }
    return;
  }
  if (id === SUMMARY_ID) {
    await fulfill(requestId, 200, {
      status: "succeeded",
      files_done: 2,
      files_total: 2,
      log_available: true,
      lines: logLines(
        "ingest.file index=1 total=2 member=deep/dir/a.txt",
        `Data file 'deep/dir/a.txt' with SHA256 hash '${STUB_HASH}' identified as exact duplicate. No ingestion performed.`,
        "ingest.file index=2 total=2 member=deep/dir/b.txt",
        `Data file 'deep/dir/b.txt' with SHA256 hash '${STUB_HASH}' identified as exact duplicate. No ingestion performed.`,
        "ingest.summary files=2 loaded=0 metadata_only=0 duplicates=2 skipped_lines=3 seconds=4.5",
      ),
    });
    return;
  }
  if (id === QUEUED_ID) {
    await fulfill(requestId, 200, {
      status: "queued",
      files_done: 0,
      queue_position: queueAhead,
      log_available: true,
      lines: [],
    });
    return;
  }
  if (id === FLAKY_ID) {
    if (flakyMode === "ok") {
      await fulfill(requestId, 200, {
        status: "running",
        log_available: true,
        lines: logLines("Processing etuff file: flaky.txt"),
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
  await fulfill(requestId, 200, jobPhase === "succeeded" ? succeededBody() : runningBody());
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

const CARD = `(() => {
  const card = document.querySelector("#jobs .job-card");
  if (!card) return null;
  const count = card.querySelector(".job-count");
  const panel = card.querySelector(".job-log-panel");
  const button = card.querySelector(".job-log-toggle");
  return {
    stage: card.querySelector(".job-stage").textContent,
    elapsed: card.querySelector(".job-elapsed").textContent,
    chipHidden: count.hidden,
    index: count.querySelector(".job-count-current").textContent,
    total: count.querySelector(".job-count-total").textContent,
    member: count.querySelector(".job-member").textContent,
    fileTime: count.querySelector(".job-file-time").textContent,
    panelHidden: panel.hidden,
    expanded: button.getAttribute("aria-expanded"),
    controls: button.getAttribute("aria-controls"),
    panelId: panel.id,
    log: panel.querySelector("pre").textContent,
    hint: card.querySelector(".job-hint").textContent,
    hintHidden: card.querySelector(".job-hint").hidden,
  };
})()`;

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
  const list = await fetch(`http://127.0.0.1:${port}/json/list`).then((response) =>
    response.json(),
  );
  const page = list.find((target) => target.type === "page");
  if (!page) throw new Error("Chrome has no page target");
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    ws.addEventListener("open", resolve, { once: true });
    ws.addEventListener("error", () => reject(new Error("DevTools socket failed")), {
      once: true,
    });
  });
  cdp = new Cdp(ws);
  await cdp.send("Network.enable");
  await cdp.send("Page.enable");
  await cdp.send("Runtime.enable");
  await cdp.send("Fetch.enable", {
    handleAuthRequests: true,
    patterns: [{ urlPattern: "*", requestStage: "Request" }],
  });
  const loaded = cdp.waitFor((message) => message.method === "Page.loadEventFired", 20000);
  // Credentials are answered through Fetch.authRequired, not put in the URL:
  // a URL with user:pass makes the page's fetch() calls fail.
  await cdp.send("Page.navigate", { url: pageUrl });
  await loaded;
  const probe = await evaluate(`(() => ({
    href: location.href,
    title: document.title,
    ready: document.readyState,
    dropzone: typeof window.Dropzone,
    zone: !!document.querySelector("#drop-zone"),
    scripts: [...document.scripts].map((script) => script.src),
    resources: performance.getEntriesByType("resource").map((entry) => ({
      name: entry.name,
      duration: Math.round(entry.duration),
      size: entry.transferSize,
      decoded: entry.decodedBodySize,
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
    ["sanity-a.txt", "sanity-b.txt", "sanity-c.txt"].every((name) => unique.has(name));
  report(
    separate,
    "three files, three jobs, one at a time",
    `posts=${JSON.stringify(posts)} overlap=${postsOverlapped} added=${JSON.stringify(added)}`,
  );

  await waitUntil(
    `(() => {
      const card = document.querySelector("#jobs .job-card");
      if (!card) return null;
      const count = card.querySelector(".job-count");
      if (count.hidden) return null;
      if (count.querySelector(".job-count-current").textContent !== "2") return null;
      return true;
    })()`,
    10000,
    "running file chip",
  );
  const runningBefore = await evaluate(CARD);
  await sleep(1200);
  const runningAfter = await evaluate(CARD);
  const beats = runningAfter ? runningAfter.log.split("still running").length - 1 : -1;
  report(
    runningAfter &&
      runningAfter.hintHidden === false &&
      runningAfter.hint.includes("still running") &&
      beats === 1 &&
      runningAfter.log.includes("30s") &&
      runningAfter.controls === runningAfter.panelId &&
      runningAfter.panelId.length > 0,
    "heartbeat shows as a hint and once in the log",
    `hint=${runningAfter && runningAfter.hint} beats=${beats} controls=${runningAfter && runningAfter.controls} panel=${runningAfter && runningAfter.panelId}`,
  );
  const clockWasMoving =
    runningBefore &&
    runningAfter &&
    runningBefore.fileTime !== runningAfter.fileTime &&
    runningBefore.elapsed !== runningAfter.elapsed;
  await evaluate(`(() => {
    document.querySelector("#jobs .job-card .job-log-toggle").click();
    return true;
  })()`);
  const openedWhileRunning = await evaluate(`(() => {
    const panel = document.querySelector("#jobs .job-card .job-log-panel");
    return panel.hidden === false;
  })()`);
  jobPhase = "succeeded";
  await evaluate(
    `(async () => {
      await pollOnce();
      await pollOnce();
      return true;
    })()`,
    true,
  );
  const held = await evaluate(CARD);
  const collapsed =
    openedWhileRunning === true &&
    held &&
    held.stage === "Successful" &&
    held.panelHidden === true &&
    held.expanded === "false" &&
    held.chipHidden === false &&
    held.index === "2" &&
    held.total === "3" &&
    held.member === "dup.txt" &&
    held.elapsed.length > 0 &&
    held.fileTime.length > 0;
  await sleep(1200);
  const tickOne = await evaluate(CARD);
  await sleep(1200);
  const tickTwo = await evaluate(CARD);
  const still =
    collapsed &&
    clockWasMoving &&
    tickOne &&
    tickTwo &&
    tickOne.elapsed === held.elapsed &&
    tickTwo.elapsed === held.elapsed &&
    tickOne.fileTime === held.fileTime &&
    tickTwo.fileTime === held.fileTime &&
    tickOne.index === held.index &&
    tickTwo.index === held.index &&
    tickOne.member === held.member &&
    tickTwo.member === held.member;
  const later = await evaluate(`(() => {
    const card = document.querySelector("#jobs .job-card");
    syncJob({
      id: card.dataset.jobId,
      filename: card.querySelector(".job-title").textContent,
      acceptedAt: Date.now() - 20000,
      finishedAt: Date.now() - 2000,
      body: {
        status: "succeeded",
        log_available: true,
        lines: [{ time: new Date().toISOString(), text: "ingest.file index=9 total=3 member=other.txt" }],
      },
    });
    const count = card.querySelector(".job-count");
    const panel = card.querySelector(".job-log-panel");
    return {
      index: count.querySelector(".job-count-current").textContent,
      member: count.querySelector(".job-member").textContent,
      fileTime: count.querySelector(".job-file-time").textContent,
      elapsed: card.querySelector(".job-elapsed").textContent,
      panelHidden: panel.hidden,
    };
  })()`);
  const laterHeld =
    later &&
    later.index === "2" &&
    later.member === "dup.txt" &&
    later.fileTime === held.fileTime &&
    later.elapsed === held.elapsed &&
    later.panelHidden === true;
  report(
    still && laterHeld,
    "succeeded card holds Successful, duration, and file chip",
    clockWasMoving
      ? `stage=${held && held.stage} elapsed=${held && held.elapsed}->${tickTwo && tickTwo.elapsed} file=${held && held.fileTime}->${tickTwo && tickTwo.fileTime} later=${JSON.stringify(later)}`
      : "file chip or total did not advance while the job was running",
  );

  const openClick = await clickSelector("#jobs .job-card .job-log-toggle");
  const opened = await evaluate(CARD);
  await evaluate(`(() => {
    const pre = document.querySelector("#jobs .job-card .job-log-panel pre");
    pre.dataset.gotClick = "no";
    pre.addEventListener("click", () => {
      pre.dataset.gotClick = "yes";
    });
    return true;
  })()`);
  const panelClick = await clickSelector("#jobs .job-card .job-log-panel pre");
  const afterPanel = await evaluate(`(() => {
    const pre = document.querySelector("#jobs .job-card .job-log-panel pre");
    const panel = document.querySelector("#jobs .job-card .job-log-panel");
    return {
      gotClick: pre.dataset.gotClick,
      hidden: panel.hidden,
      log: pre.textContent,
    };
  })()`);
  const closeClick = await clickSelector("#jobs .job-card .job-log-toggle");
  const closed = await evaluate(CARD);
  const toggled =
    collapsed &&
    openClick.ok &&
    opened &&
    opened.panelHidden === false &&
    opened.expanded === "true" &&
    opened.log.includes("other.txt") &&
    panelClick.ok &&
    afterPanel &&
    afterPanel.gotClick === "yes" &&
    afterPanel.hidden === false &&
    closeClick.ok &&
    closed &&
    closed.panelHidden === true &&
    closed.expanded === "false";
  report(
    toggled,
    "log opens on click and closes on the next click",
    `open=${JSON.stringify(openClick)} close=${JSON.stringify(closeClick)} panel=${JSON.stringify(panelClick)} after=${JSON.stringify(afterPanel)} startedOpen=${openedWhileRunning} collapsed=${held && held.panelHidden}`,
  );

  const appeared = await evaluate(
    `(async () => {
      localStorage.setItem(
        "tagbase-ingest-jobs",
        JSON.stringify([
          { id: "${MISSING_ID}", filename: "gone.txt", acceptedAt: Date.now() },
        ]),
      );
      await pollOnce();
      await pollOnce();
      return !!document.querySelector('[data-job-id="${MISSING_ID}"]');
    })()`,
    true,
  );
  missingMode = "drop";
  const leftBehind = await evaluate(
    `(async () => {
      await pollOnce();
      await pollOnce();
      return !!document.querySelector('[data-job-id="${MISSING_ID}"]');
    })()`,
    true,
  );
  report(
    appeared === true && leftBehind === false,
    "404 job id does not leave a card",
    `appeared=${appeared} left=${leftBehind}`,
  );

  const FLAKY_CARD = `(() => {
    const card = document.querySelector('[data-job-id="${FLAKY_ID}"]');
    if (!card) return null;
    const error = card.querySelector(".job-error");
    return {
      stage: card.querySelector(".job-stage").textContent,
      log: card.querySelector(".job-log-panel pre").textContent,
      errorHidden: error.hidden,
      error: error.textContent,
    };
  })()`;
  const flakyBefore = await evaluate(
    `(async () => {
      localStorage.setItem(
        "tagbase-ingest-jobs",
        JSON.stringify([
          { id: "${FLAKY_ID}", filename: "flaky.txt", acceptedAt: Date.now() },
        ]),
      );
      await pollOnce();
      await pollOnce();
      return ${FLAKY_CARD};
    })()`,
    true,
  );
  flakyMode = "error";
  const flakyAfter = await evaluate(
    `(async () => {
      await pollOnce();
      await pollOnce();
      return ${FLAKY_CARD};
    })()`,
    true,
  );
  report(
    flakyBefore &&
      flakyAfter &&
      flakyAfter.stage === flakyBefore.stage &&
      flakyAfter.log.includes("flaky.txt") &&
      flakyAfter.errorHidden === false &&
      flakyAfter.error.includes("sanity server error"),
    "5xx keeps the last good card and shows the error",
    `before=${JSON.stringify(flakyBefore)} after=${JSON.stringify(flakyAfter)}`,
  );

  const SUMMARY_CARD = `(() => {
    const card = document.querySelector('[data-job-id="${SUMMARY_ID}"]');
    if (!card) return null;
    const member = card.querySelector(".job-member");
    return {
      stage: card.querySelector(".job-stage").textContent,
      member: member.textContent,
      memberTitle: member.title,
      summary: card.querySelector(".job-summary").textContent,
      summaryHidden: card.querySelector(".job-summary").hidden,
      warning: card.querySelector(".job-warning").textContent,
      warningHidden: card.querySelector(".job-warning").hidden,
      pressed: card.querySelector(".job-log-mode").getAttribute("aria-pressed"),
      log: card.querySelector(".job-log-panel pre").textContent,
    };
  })()`;
  const readable = await evaluate(
    `(async () => {
      localStorage.setItem(
        "tagbase-ingest-jobs",
        JSON.stringify([
          { id: "${SUMMARY_ID}", filename: "dups.zip", acceptedAt: Date.now() },
        ]),
      );
      await pollOnce();
      await pollOnce();
      return ${SUMMARY_CARD};
    })()`,
    true,
  );
  report(
    readable &&
      readable.stage === "Skipped: already ingested" &&
      readable.member === "b.txt" &&
      readable.memberTitle === "deep/dir/b.txt" &&
      readable.summaryHidden === false &&
      readable.summary === "2 files: 0 loaded, 2 already ingested, 3 lines skipped, 5s" &&
      readable.warningHidden === false &&
      readable.warning.startsWith("3 lines had no date and time"),
    "duplicates show as skipped, with base names, a summary, and a skipped-lines warning",
    JSON.stringify(readable),
  );

  const technical = await evaluate(
    `(() => {
      const button = document.querySelector('[data-job-id="${SUMMARY_ID}"] .job-log-mode');
      button.click();
      const on = ${SUMMARY_CARD};
      button.click();
      return { on, off: ${SUMMARY_CARD} };
    })()`,
  );
  const plainLog = readable ? readable.log : "";
  report(
    readable &&
      technical &&
      !plainLog.includes(STUB_HASH) &&
      !plainLog.includes("ingest.summary") &&
      plainLog.includes("a.txt was already ingested, so it was skipped.") &&
      plainLog.includes("Finished. 2 files") &&
      technical.on.pressed === "true" &&
      technical.on.log.includes(STUB_HASH) &&
      technical.on.log.includes("ingest.summary files=2") &&
      technical.off.pressed === "false" &&
      technical.off.log === plainLog,
    "Technical details toggles between readable and raw log lines",
    `readable=${JSON.stringify(plainLog)} technical=${JSON.stringify(technical)}`,
  );

  const QUEUED_STAGE = `document.querySelector('[data-job-id="${QUEUED_ID}"] .job-stage').textContent`;
  const queuedBehind = await evaluate(
    `(async () => {
      localStorage.setItem(
        "tagbase-ingest-jobs",
        JSON.stringify([
          { id: "${QUEUED_ID}", filename: "waiting.txt", acceptedAt: Date.now() },
        ]),
      );
      await pollOnce();
      await pollOnce();
      return ${QUEUED_STAGE};
    })()`,
    true,
  );
  queueAhead = 0;
  const queuedNext = await evaluate(
    `(async () => {
      await pollOnce();
      await pollOnce();
      return ${QUEUED_STAGE};
    })()`,
    true,
  );
  report(
    queuedBehind === "Queued, 2 ahead" && queuedNext === "Queued, next",
    "queued jobs show how many are ahead",
    `behind=${queuedBehind} next=${queuedNext}`,
  );

  await evaluate(
    `(async () => {
      await Promise.all([pollOnce(), pollOnce(), pollOnce()]);
      return true;
    })()`,
    true,
  );
  report(!getsOverlapped, "job polls never overlap", "two GETs for one job were in flight at once");

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
  console.log(`FAIL  sanity check aborted: ${error && error.message ? error.message : error}`);
  process.exit(1);
});
END_JS

node --check "$tmpdir/sanity.mjs"
node "$tmpdir/sanity.mjs" "$port"
