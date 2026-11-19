const form = document.querySelector("#upload-form");
const status = document.querySelector("#status");
const jobsEl = document.querySelector("#jobs");
const abortButton = document.querySelector("#abort");
const versionInput = document.querySelector("#version");
const notesInput = document.querySelector("#notes");

const STORAGE_KEY = "tagbase-ingest-jobs";
const POLL_MS = 3000;
// A status check that gets no answer within this time counts as failed.
const REQUEST_TIMEOUT_MS = 10000;
const MAX_STORED_JOBS = 50;
// The Grafana panel that shows one job's log lines. Only opened on demand.
const LOG_DASHBOARD = "tagbase-job-log";
const LOG_SLUG = "ingest-job-log";
// The log window starts this long before the job was accepted.
const LOG_MARGIN_MS = 60 * 1000;
const JOB_ID =
  /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;
const BUSY_MESSAGE = "An upload is already in progress.";
const SKIPPED_LABEL = "Skipped: already ingested";
let activeXhr = null;
let pollTimer = null;
let polling = null;
let clockTimer = null;
let batchActive = false;
let batchLockTimer = null;
const snapshots = new Map();
const cards = new Map();
const failures = [];

function showStatus(type, message) {
  status.className = `alert alert-${type} mt-4`;
  status.textContent = message;
}

function hideStatus() {
  status.className = "alert d-none mt-4";
  status.textContent = "";
}

function loadJobs() {
  let stored;
  try {
    stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
  } catch {
    return [];
  }
  if (!Array.isArray(stored)) return [];
  return stored
    .filter(
      (item) => item && typeof item.id === "string" && JOB_ID.test(item.id),
    )
    .slice(-MAX_STORED_JOBS);
}

function saveJobs(jobs) {
  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify(jobs.slice(-MAX_STORED_JOBS)),
  );
}

function rememberJob(job) {
  const jobs = loadJobs().filter((item) => item.id !== job.id);
  jobs.push({
    id: job.id,
    filename: job.filename,
    acceptedAt: job.acceptedAt || Date.now(),
  });
  saveJobs(jobs);
}

function forgetJob(id) {
  saveJobs(loadJobs().filter((item) => item.id !== id));
}

function formatDuration(seconds) {
  const total = Math.max(0, Math.round(Number(seconds) || 0));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const secs = total % 60;
  if (hours) return `${hours}h ${minutes}m ${secs}s`;
  if (minutes) return `${minutes}m ${secs}s`;
  return `${secs}s`;
}

function uploadSeconds(job) {
  const end = job.finishedAt || Date.now();
  return Math.max(0, (end - job.acceptedAt) / 1000);
}

function baseName(path) {
  const parts = String(path).split(/[\\/]/);
  return parts[parts.length - 1] || String(path);
}

// A break is allowed after "_", "-" and "." so a long name wraps between
// words, never inside one. A <wbr> adds no text, so textContent is the name.
function nameParts(name) {
  const pieces = name.split(/(?<=[_.-])/);
  const nodes = [];
  pieces.forEach((piece, i) => {
    nodes.push(document.createTextNode(piece));
    if (i < pieces.length - 1) nodes.push(document.createElement("wbr"));
  });
  return nodes;
}

function plural(count, word) {
  return `${count} ${word}${count === 1 ? "" : "s"}`;
}

// The job row carries the totals. Snake_case keys come from the API.
function summaryFrom(body) {
  const raw = body.summary;
  if (!raw || typeof raw !== "object") return null;
  return {
    files: Number(raw.files) || 0,
    loaded: Number(raw.loaded) || 0,
    metadataOnly: Number(raw.metadata_only) || 0,
    duplicates: Number(raw.duplicates) || 0,
    skippedLines: Number(raw.skipped_lines) || 0,
    seconds: Number(raw.seconds) || 0,
  };
}

function summaryText(summary) {
  const parts = [`${summary.loaded} loaded`];
  if (summary.metadataOnly) {
    parts.push(`${summary.metadataOnly} metadata updated`);
  }
  if (summary.duplicates) parts.push(`${summary.duplicates} already ingested`);
  if (summary.skippedLines) {
    parts.push(`${plural(summary.skippedLines, "line")} skipped`);
  }
  parts.push(formatDuration(summary.seconds));
  return `${plural(summary.files, "file")}: ${parts.join(", ")}`;
}

function fallbackSummary(body) {
  const total = Number(body.files_total || 0);
  if (!total) return "";
  return `${body.files_done || 0} of ${plural(total, "file")} processed`;
}

function finishedStatus(status) {
  return status === "succeeded" || status === "failed";
}

// A succeeded job where every member was a duplicate loaded nothing.
function allDuplicates(summary) {
  return (
    Boolean(summary) &&
    summary.files > 0 &&
    summary.duplicates === summary.files
  );
}

function queueLabel(body) {
  const ahead = body.queue_position;
  if (!Number.isInteger(ahead) || ahead < 0) return "queued";
  return ahead === 0 ? "Queued, next" : `Queued, ${ahead} ahead`;
}

function labelFor(body) {
  if (body.status === "succeeded") {
    return allDuplicates(summaryFrom(body)) ? SKIPPED_LABEL : "Successful";
  }
  if (body.status === "failed") return "Failed";
  if (body.status === "queued") return queueLabel(body);
  return body.stage || "Starting";
}

function logParams(job, body) {
  const created = Date.parse(body.created_at || "");
  const from = Number.isNaN(created) ? job.acceptedAt : created;
  // The job-log dashboard refreshes every 15 seconds. The page says so
  // next to Log, and this URL does not add a second interval.
  return new URLSearchParams({
    orgId: "1",
    "var-job_id": job.id,
    from: String(from - LOG_MARGIN_MS),
    to: "now",
    theme: "dark",
  });
}

function logFrameSrc(job, body) {
  const params = logParams(job, body);
  // hideLogo removes the "Powered by Grafana" control. Its menu opens
  // Explore inside this frame, and the frame has no way back to the log.
  params.set("hideLogo", "true");
  return `/grafana/d-solo/${LOG_DASHBOARD}/${LOG_SLUG}?panelId=1&${params}`;
}

function logPageHref(job, body) {
  return `/grafana/d/${LOG_DASHBOARD}/${LOG_SLUG}?${logParams(job, body)}`;
}

function addText(parent, tag, className, text) {
  const el = document.createElement(tag);
  if (className) el.className = className;
  el.textContent = text;
  parent.append(el);
  return el;
}

function jobCard(job) {
  let card = cards.get(job.id);
  if (card) return card;
  card = document.createElement("article");
  card.className = "job-card";
  card.dataset.jobId = job.id;
  addText(card, "div", "job-title", job.filename);

  const ticker = document.createElement("div");
  ticker.className = "job-ticker";
  const pulse = document.createElement("span");
  pulse.className = "job-pulse";
  pulse.setAttribute("aria-hidden", "true");
  ticker.append(pulse);
  addText(ticker, "span", "job-stage", "queued");
  const count = document.createElement("div");
  count.className = "job-count";
  count.hidden = true;
  const countLine = document.createElement("div");
  countLine.className = "job-count-line";
  addText(countLine, "span", "job-count-kicker", "File");
  addText(countLine, "span", "job-count-current", "");
  addText(countLine, "span", "job-count-of", "of");
  addText(countLine, "span", "job-count-total", "");
  count.append(countLine);
  addText(count, "div", "job-member", "");
  ticker.append(count);
  addText(ticker, "span", "job-elapsed", formatDuration(uploadSeconds(job)));
  card.append(ticker);

  const summary = addText(card, "div", "job-summary small mt-1", "");
  summary.hidden = true;
  const warning = addText(card, "div", "job-warning small mt-1", "");
  warning.hidden = true;

  const error = document.createElement("div");
  error.className = "job-error text-danger small mt-1";
  error.hidden = true;
  card.append(error);

  const logButton = document.createElement("button");
  logButton.type = "button";
  logButton.className = "job-log-toggle";
  logButton.textContent = "Log";
  logButton.setAttribute("aria-expanded", "false");
  const panel = document.createElement("div");
  panel.className = "job-log-panel";
  panel.id = `job-log-${job.id}`;
  panel.hidden = true;
  logButton.setAttribute("aria-controls", panel.id);
  const logActions = document.createElement("div");
  logActions.className = "job-log-actions";
  const refreshNote = document.createElement("span");
  refreshNote.className = "job-log-refresh small text-body-secondary";
  refreshNote.textContent = "Refreshes every 15 seconds";
  logActions.append(logButton, refreshNote);
  const openLink = document.createElement("a");
  openLink.className = "job-log-open small";
  openLink.target = "_blank";
  openLink.rel = "noopener";
  openLink.textContent = "Open in Grafana";
  const back = document.createElement("button");
  back.type = "button";
  back.className = "job-log-back";
  back.textContent = "Back to log";
  back.hidden = true;
  back.addEventListener("click", () => {
    const frame = panel.querySelector("iframe");
    const current = snapshots.get(job.id);
    if (!frame || !current) return;
    frame.src = logFrameSrc(current, current.body || {});
    back.hidden = true;
  });
  panel.append(back, openLink);
  logButton.addEventListener("click", () => {
    setLogOpen(job.id, logButton.getAttribute("aria-expanded") !== "true");
  });
  card.append(logActions, panel);
  jobsEl.prepend(card);
  cards.set(job.id, card);
  return card;
}

// The Grafana frame exists only while the log is open. Closing it removes the
// frame, so a closed log costs nothing on the page.
function setLogOpen(jobId, open) {
  const card = cards.get(jobId);
  const snapshot = snapshots.get(jobId);
  if (!card || !snapshot) return;
  const panel = card.querySelector(".job-log-panel");
  const logButton = card.querySelector(".job-log-toggle");
  panel.hidden = !open;
  logButton.classList.toggle("is-open", open);
  logButton.setAttribute("aria-expanded", open ? "true" : "false");
  const frame = panel.querySelector("iframe");
  if (!open) {
    if (frame) frame.remove();
    return;
  }
  if (frame) return;
  const embed = document.createElement("iframe");
  embed.className = "job-log-frame";
  embed.title = `Log for ${snapshot.filename}`;
  embed.addEventListener("load", () => {
    const back = panel.querySelector(".job-log-back");
    if (!back) return;
    let leftLog = false;
    try {
      const doc = embed.contentDocument;
      leftLog = !embed.contentWindow.location.pathname.includes("/d-solo/");
      // The panel menu opens Explore in this frame. Grafana also paints
      // the job_id text because the query filters on it; that mark is
      // not something the reader asked to see.
      if (!leftLog && doc && !doc.getElementById("tagbase-log-frame-style")) {
        const style = doc.createElement("style");
        style.id = "tagbase-log-frame-style";
        style.textContent = [
          '[data-testid="panel-menu-button"],button[aria-label^="Menu for panel"]{display:none !important}',
          "mark{background:transparent !important;background-color:transparent !important;color:inherit !important}",
        ].join("");
        doc.head.append(style);
      }
    } catch {
      leftLog = false;
    }
    back.hidden = !leftLog;
  });
  embed.src = logFrameSrc(snapshot, snapshot.body || {});
  panel.insertBefore(embed, panel.firstChild);
}

function dropCard(id) {
  const card = cards.get(id);
  if (card) card.remove();
  cards.delete(id);
}

function syncCount(card, body) {
  const countEl = card.querySelector(".job-count");
  const total = Number(body.files_total || 0);
  // A one-member upload still shows "File 1 of 1". The log no longer carries
  // that line, so hiding the chip left the card with no file position.
  if (total < 1 || body.status === "queued") {
    countEl.hidden = true;
    countEl.dataset.index = "";
    return;
  }
  countEl.hidden = false;
  const done = Number(body.files_done || 0);
  const index = body.status === "succeeded" ? total : Math.min(done + 1, total);
  const member = finishedStatus(body.status) ? "" : body.current_member || "";
  countEl.querySelector(".job-count-current").textContent = String(index);
  countEl.querySelector(".job-count-total").textContent = String(total);
  const memberEl = countEl.querySelector(".job-member");
  const name = member ? baseName(member) : "";
  if (memberEl.textContent !== name) {
    memberEl.replaceChildren(...nameParts(name));
  }
  if (member) memberEl.title = member;
  else memberEl.removeAttribute("title");
  if (countEl.dataset.index !== String(index)) {
    countEl.dataset.index = String(index);
    countEl.classList.remove("is-advance");
    void countEl.offsetWidth;
    countEl.classList.add("is-advance");
  }
}

function syncSummary(card, body) {
  const summaryEl = card.querySelector(".job-summary");
  const warningEl = card.querySelector(".job-warning");
  const finished = finishedStatus(body.status);
  const summary = finished ? summaryFrom(body) : null;
  let text = "";
  if (summary) text = summaryText(summary);
  else if (finished) text = fallbackSummary(body);
  summaryEl.hidden = !text;
  summaryEl.textContent = text;
  const skippedLines = summary ? summary.skippedLines : 0;
  warningEl.hidden = skippedLines === 0;
  warningEl.textContent = skippedLines
    ? `${plural(skippedLines, "line")} had no date and time and ${skippedLines === 1 ? "was" : "were"} skipped.`
    : "";
}

function syncError(card, job, body) {
  const error = card.querySelector(".job-error");
  if (body.status === "failed" && body.error) {
    error.hidden = false;
    error.textContent = body.error;
  } else if (job.pollError) {
    error.hidden = false;
    error.textContent = `Status check failed: ${job.pollError}`;
  } else {
    error.hidden = true;
    error.textContent = "";
  }
}

function syncJob(job) {
  const card = jobCard(job);
  const body = job.body || {};
  const succeeded = body.status === "succeeded";
  const failed = body.status === "failed";
  const finished = finishedStatus(body.status);
  const running = body.status === "queued" || body.status === "running";
  const pulse = card.querySelector(".job-pulse");
  pulse.hidden = !running && !finished;
  pulse.classList.toggle("is-done", succeeded);
  pulse.classList.toggle("is-failed", failed);
  const stageEl = card.querySelector(".job-stage");
  const label = labelFor(body);
  const skipped = succeeded && label === SKIPPED_LABEL;
  stageEl.textContent = label;
  stageEl.classList.toggle("is-done", succeeded && !skipped);
  stageEl.classList.toggle("is-skipped", skipped);
  stageEl.classList.toggle("is-failed", failed);
  syncCount(card, body);
  card.querySelector(".job-elapsed").textContent = formatDuration(
    uploadSeconds(job),
  );
  syncSummary(card, body);
  syncError(card, job, body);
  card.querySelector(".job-log-open").href = logPageHref(job, body);
}

function tickClocks() {
  for (const job of snapshots.values()) {
    const card = cards.get(job.id);
    if (!card) continue;
    const body = job.body || {};
    if (finishedStatus(body.status)) continue;
    card.querySelector(".job-elapsed").textContent = formatDuration(
      uploadSeconds(job),
    );
  }
}

async function fetchJob(id) {
  const response = await fetch(`/tagbase/api/v0/ingest/jobs/${id}`, {
    headers: { Accept: "application/json, application/problem+json" },
    signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
  });
  if (response.status === 404) return { gone: true };
  let body = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  if (!response.ok) {
    const detail = body && (body.detail || body.title);
    throw new Error(detail || `HTTP ${response.status}`);
  }
  if (!body || typeof body !== "object" || typeof body.status !== "string") {
    throw new Error("unreadable job status");
  }
  return { body };
}

function reasonText(reason) {
  if (reason && reason.name === "TimeoutError") {
    return "no response from the server";
  }
  return reason && reason.message ? reason.message : "network error";
}

function applyPoll(jobId, outcome) {
  const current = snapshots.get(jobId);
  if (!current) return;
  if (outcome.status === "rejected") {
    // Keep the last good body; a failed check is not a job state.
    snapshots.set(jobId, { ...current, pollError: reasonText(outcome.reason) });
    return;
  }
  if (outcome.value.gone) {
    snapshots.delete(jobId);
    forgetJob(jobId);
    dropCard(jobId);
    return;
  }
  const { body } = outcome.value;
  const finished = finishedStatus(body.status);
  snapshots.set(jobId, {
    ...current,
    body,
    pollError: "",
    finishedAt: finished ? current.finishedAt || Date.now() : undefined,
  });
  // The job row is complete once finished, so it needs no further polls.
  if (finished) forgetJob(jobId);
}

async function pollJobs() {
  const jobs = loadJobs();
  for (const job of jobs) {
    if (!snapshots.has(job.id)) {
      snapshots.set(job.id, {
        id: job.id,
        filename: job.filename,
        acceptedAt: job.acceptedAt || Date.now(),
        body: { status: "queued" },
      });
    }
  }
  const outcomes = await Promise.allSettled(
    jobs.map((job) => fetchJob(job.id)),
  );
  jobs.forEach((job, i) => applyPoll(job.id, outcomes[i]));
  // Redraw only the jobs polled this round. A finished job is redrawn once
  // here, then left alone.
  for (const job of jobs) {
    const current = snapshots.get(job.id);
    if (current) syncJob(current);
  }
}

// One poll at a time: a caller during a poll shares the one in flight.
function pollOnce() {
  if (!polling) {
    polling = pollJobs().finally(() => {
      polling = null;
    });
  }
  return polling;
}

function stopTimers() {
  if (pollTimer) window.clearTimeout(pollTimer);
  pollTimer = null;
  if (clockTimer) window.clearInterval(clockTimer);
  clockTimer = null;
}

function schedulePoll() {
  if (pollTimer) return;
  pollTimer = window.setTimeout(async () => {
    try {
      await pollOnce();
    } finally {
      pollTimer = null;
      if (loadJobs().length) schedulePoll();
      else stopTimers();
    }
  }, POLL_MS);
}

function ensurePolling() {
  if (!loadJobs().length) return;
  if (!clockTimer) {
    clockTimer = window.setInterval(tickClocks, 1000);
  }
  if (pollTimer) return;
  pollOnce().finally(() => {
    if (loadJobs().length) schedulePoll();
    else stopTimers();
  });
}

function responseId(response) {
  let id = "";
  if (response && typeof response === "object") {
    id = response.id;
  } else if (typeof response === "string") {
    try {
      const parsed = JSON.parse(response);
      id = parsed && parsed.id;
    } catch {
      return "";
    }
  }
  return typeof id === "string" && JOB_ID.test(id) ? id : "";
}

function scheduleBatchLock() {
  if (batchActive || batchLockTimer) return;
  batchLockTimer = window.setTimeout(() => {
    batchLockTimer = null;
    const busy =
      dropzone.getAddedFiles().length +
      dropzone.getQueuedFiles().length +
      dropzone.getUploadingFiles().length;
    if (busy > 0) batchActive = true;
  }, 0);
}

function finishBatch() {
  if (!batchActive) return;
  if (batchLockTimer) {
    window.clearTimeout(batchLockTimer);
    batchLockTimer = null;
  }
  batchActive = false;
  activeXhr = null;
  abortButton.classList.add("d-none");
  versionInput.value = "";
  notesInput.value = "";
  dropzone.removeAllFiles(true);
  if (failures.length) showStatus("danger", failures.join("\n"));
  else hideStatus();
  failures.length = 0;
  ensurePolling();
}

const dropzone = new window.Dropzone("#drop-zone", {
  url(files) {
    const file = files[0];
    const params = new URLSearchParams({ filename: file.name });
    if (file.tagbaseVersion) params.set("version", file.tagbaseVersion);
    if (file.tagbaseNotes) params.set("notes", file.tagbaseNotes);
    return `/tagbase/api/v0/ingest/jobs?${params.toString()}`;
  },
  method: "POST",
  parallelUploads: 1,
  uploadMultiple: false,
  autoProcessQueue: true,
  binaryBody: true,
  maxFilesize: null,
  acceptedFiles: ".txt,.zip,.tar.gz,.tgz",
  createImageThumbnails: false,
  previewTemplate: [
    '<div class="dz-preview dz-file-preview">',
    '<div class="dz-details">',
    '<div class="dz-filename"><span data-dz-name></span></div>',
    '<div class="dz-size"><span data-dz-size></span></div>',
    "</div>",
    '<div class="dz-progress"><span class="dz-upload" data-dz-uploadprogress></span></div>',
    '<div class="dz-error-message"><span data-dz-errormessage></span></div>',
    "</div>",
  ].join(""),
  accept(file, done) {
    if (batchActive) {
      showStatus("warning", BUSY_MESSAGE);
      done(BUSY_MESSAGE);
      return;
    }
    file.tagbaseVersion = versionInput.value.trim();
    file.tagbaseNotes = notesInput.value.trim();
    scheduleBatchLock();
    done();
  },
});

dropzone.on("sending", (file, xhr) => {
  activeXhr = xhr;
  abortButton.classList.remove("d-none");
  if (!file.type) {
    xhr.setRequestHeader("Content-Type", "application/octet-stream");
  }
});

dropzone.on("success", (file, response) => {
  const id = responseId(response);
  if (!id) return;
  rememberJob({ id, filename: file.name });
  ensurePolling();
});

dropzone.on("error", (file, message) => {
  const text = typeof message === "string" ? message : "upload failed";
  if (text === BUSY_MESSAGE) return;
  failures.push(`✗ ${file.name}: ${text}`);
});

dropzone.on("canceled", (file) => {
  failures.push(`✗ ${file.name}: upload aborted`);
});

dropzone.on("queuecomplete", finishBatch);

form.addEventListener("submit", (event) => {
  event.preventDefault();
});

abortButton.addEventListener("click", () => {
  const uploading = dropzone.getUploadingFiles();
  if (uploading[0]) dropzone.cancelUpload(uploading[0]);
  else if (activeXhr) activeXhr.abort();
});

if (loadJobs().length) ensurePolling();
