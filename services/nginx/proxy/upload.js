const form = document.querySelector("#upload-form");
const status = document.querySelector("#status");
const jobsEl = document.querySelector("#jobs");
const abortButton = document.querySelector("#abort");
const versionInput = document.querySelector("#version");
const notesInput = document.querySelector("#notes");

const STORAGE_KEY = "tagbase-ingest-jobs";
const POLL_MS = 3000;
// Extra polls after a job finishes, waiting for its last log lines.
const SETTLE_POLLS = 5;
const MAX_STORED_JOBS = 50;
const JOB_ID =
  /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;
const BUSY_MESSAGE = "An upload is already in progress.";
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

const JOB_ID_TAG = / job_id=[0-9a-fA-F-]{36}/;
const HEARTBEAT = "Writing measurements, still running";
const TOTAL_TIME =
  /Data file (.+) successfully ingested into Tagbase DB\. Total time: (\d+(?:\.\d+)?) second\(s\)/;

const FILE_LINE = /ingest\.file index=(\d+) total=(\d+) member=(.+)$/;
const SUMMARY_LINE =
  /ingest\.summary files=(\d+) loaded=(\d+) metadata_only=(\d+) duplicates=(\d+) skipped_lines=(\d+) seconds=(\d+(?:\.\d+)?)/;
const DUPLICATE_LINE =
  /Data file '(.+)' with SHA256 hash '[0-9a-fA-F]+' identified as exact duplicate/;
const HASH = /\b[0-9a-fA-F]{64}\b/g;
const HIDDEN_LINES = [
  "ingest.timings ",
  "Computed hash",
  "Content Hash",
  "MD Hash",
  "File Hash",
  "Executing sp_execute_data_migration",
];

function rawText(entry) {
  const text = String(entry);
  if (!text.trim().startsWith("{")) return text;
  try {
    const parsed = JSON.parse(text);
    if (parsed && typeof parsed.body === "string") return parsed.body;
  } catch {
    return text;
  }
  return text;
}

function logSentence(entry) {
  return rawText(entry).replace(JOB_ID_TAG, "");
}

function baseName(path) {
  const parts = String(path).split(/[\\/]/);
  return parts[parts.length - 1] || String(path);
}

function plural(count, word) {
  return `${count} ${word}${count === 1 ? "" : "s"}`;
}

function parseSummary(lines) {
  for (let i = lines.length - 1; i >= 0; i -= 1) {
    const match = lines[i].text.match(SUMMARY_LINE);
    if (!match) continue;
    return {
      files: Number(match[1]),
      loaded: Number(match[2]),
      metadataOnly: Number(match[3]),
      duplicates: Number(match[4]),
      skippedLines: Number(match[5]),
      seconds: Number(match[6]),
    };
  }
  return null;
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

// The default log view: hashes, timings JSON and key=value lines are
// rewritten or left out. Technical details shows the raw lines.
function readableText(text) {
  if (HIDDEN_LINES.some((prefix) => text.includes(prefix))) return null;
  const file = text.match(FILE_LINE);
  if (file) {
    return `Started file ${file[1]} of ${file[2]}: ${baseName(file[3])}`;
  }
  const summary = parseSummary([{ text }]);
  if (summary) return `Finished. ${summaryText(summary)}`;
  const duplicate = text.match(DUPLICATE_LINE);
  if (duplicate) {
    return `${baseName(duplicate[1])} was already ingested, so it was skipped.`;
  }
  return text.replace(HASH, "…");
}

function rewriteDurations(line) {
  return line
    .replace(
      /(in|Time elapsed|Elapsed time|Total time): (\d+(?:\.\d+)?) second\(s\)/g,
      (_, label, amount) => `${label}: ${formatDuration(amount)}`,
    )
    .replace(
      / elapsed=(\d+)s\b/,
      (_, amount) => ` (${formatDuration(amount)})`,
    );
}

function isHeartbeat(line) {
  return line.text.includes(HEARTBEAT);
}

function latestHeartbeat(lines) {
  for (let i = lines.length - 1; i >= 0; i -= 1) {
    if (isHeartbeat(lines[i])) return lines[i];
  }
  return null;
}

// Heartbeats repeat every few seconds; the log keeps only the newest one.
function logLinesOf(lines) {
  const latest = latestHeartbeat(lines);
  return lines.filter((line) => !isHeartbeat(line) || line === latest);
}

function linesFrom(body) {
  const entries = Array.isArray(body.lines) ? body.lines : [];
  return entries
    .map((entry) => {
      const isObject = entry && typeof entry === "object";
      const source = isObject ? entry.text || "" : entry;
      return {
        time: isObject ? entry.time || "" : "",
        text: logSentence(source),
        raw: rawText(source),
      };
    })
    .filter((line) => line.text.length > 0);
}

function clockOf(iso) {
  const when = new Date(iso);
  if (!iso || Number.isNaN(when.getTime())) return "";
  return when.toLocaleTimeString("en-GB", { hour12: false });
}

function withClock(line, text) {
  const clock = clockOf(line.time);
  return clock ? `${clock}  ${text}` : text;
}

function displayLines(lines, technical) {
  if (technical) return lines.map((line) => withClock(line, line.raw));
  const shown = [];
  for (const line of logLinesOf(lines)) {
    const text = readableText(line.text);
    if (text) shown.push(withClock(line, rewriteDurations(text)));
  }
  return shown;
}

function sameFile(left, right) {
  if (left === right) return true;
  return left.endsWith(`/${right}`) || right.endsWith(`/${left}`);
}

function workerTotalSeconds(lines, member) {
  for (let i = lines.length - 1; i >= 0; i -= 1) {
    const match = lines[i].match(TOTAL_TIME);
    if (!match) continue;
    if (member && !sameFile(match[1], member)) continue;
    return Number(match[2]);
  }
  return null;
}

const SKIPPED_LABEL = "Skipped: already ingested";

function isDuplicateLine(line) {
  return (
    line.includes("No ingestion performed") || line.includes("exact duplicate")
  );
}

function stageFor(line) {
  if (isDuplicateLine(line)) return SKIPPED_LABEL;
  if (
    line.includes("Writing measurements") ||
    line.includes("Copying memory buffer") ||
    line.includes("Successful migration")
  ) {
    return "Writing measurements";
  }
  if (line.includes("to the COPY buffer")) return "Loading rows";
  if (line.includes("Built raw") || line.includes("Successful INSERT")) {
    return "Preparing rows";
  }
  if (
    line.includes("Processing etuff file") ||
    line.includes("Computed hash") ||
    line.includes("Computed metadata hash")
  ) {
    return "Reading the file";
  }
  return "";
}

// A succeeded job where every member was a duplicate loaded nothing.
function allDuplicates(body, lines) {
  const summary = parseSummary(lines);
  if (summary) return summary.files > 0 && summary.duplicates === summary.files;
  const file = latestFile(lines);
  if (Number(body.files_total || (file ? file.total : 1)) > 1) return false;
  return lines.some((line) => isDuplicateLine(line.text));
}

function queueLabel(body) {
  const ahead = body.queue_position;
  if (!Number.isInteger(ahead) || ahead < 0) return "queued";
  return ahead === 0 ? "Queued, next" : `Queued, ${ahead} ahead`;
}

function labelFor(body, lines) {
  if (body.status === "succeeded") {
    return allDuplicates(body, lines) ? SKIPPED_LABEL : "Successful";
  }
  if (body.status === "failed") return "Failed";
  if (body.status === "queued") return queueLabel(body);
  return latestStage(lines.map((line) => line.text)) || body.status;
}

function latestStage(lines) {
  for (let i = lines.length - 1; i >= 0; i -= 1) {
    const stage = stageFor(lines[i]);
    if (stage) return stage;
  }
  return "";
}

function latestFile(lines) {
  let found = null;
  for (const line of lines) {
    const match = line.text.match(FILE_LINE);
    if (!match) continue;
    const at = Date.parse(line.time);
    found = {
      index: Number(match[1]),
      total: Number(match[2]),
      member: match[3],
      started: Number.isNaN(at) ? null : at,
    };
  }
  return found;
}

function lastLineTime(lines) {
  for (let i = lines.length - 1; i >= 0; i -= 1) {
    const at = Date.parse(lines[i].time);
    if (!Number.isNaN(at)) return at;
  }
  return null;
}

// The file a finished job ended on, from the job row rather than the log.
// Loki can lag the status, so the last ingest.file line may not be there yet.
function finalIndex(body) {
  const total = Number(body.files_total || 0);
  if (body.status === "succeeded") return total;
  if (body.status === "failed") {
    return Math.min(Number(body.files_done || 0) + 1, total);
  }
  return 0;
}

function logCaughtUp(body) {
  if (Number(body.files_total || 0) <= 1) return true;
  const file = latestFile(linesFrom(body));
  return Boolean(file) && file.index >= finalIndex(body);
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
  addText(count, "div", "job-file-time", "");
  ticker.append(count);
  addText(ticker, "span", "job-elapsed", formatDuration(uploadSeconds(job)));
  card.append(ticker);

  const hint = addText(
    card,
    "div",
    "job-hint small text-body-secondary mt-1",
    "",
  );
  hint.hidden = true;

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
  const technical = document.createElement("button");
  technical.type = "button";
  technical.className = "job-log-mode";
  technical.textContent = "Technical details";
  technical.setAttribute("aria-pressed", "false");
  technical.addEventListener("click", () => {
    const on = technical.getAttribute("aria-pressed") !== "true";
    technical.setAttribute("aria-pressed", on ? "true" : "false");
    const current = snapshots.get(job.id);
    if (current) syncJob(current);
  });
  const pre = document.createElement("pre");
  pre.dataset.mode = "empty";
  pre.dataset.count = "0";
  pre.textContent = "No log lines yet.";
  panel.append(technical, pre);
  logButton.addEventListener("click", () => {
    const open = logButton.getAttribute("aria-expanded") !== "true";
    panel.hidden = !open;
    logButton.classList.toggle("is-open", open);
    logButton.setAttribute("aria-expanded", open ? "true" : "false");
  });
  card.append(logButton, panel);
  jobsEl.prepend(card);
  cards.set(job.id, card);
  return card;
}

function dropCard(id) {
  const card = cards.get(id);
  if (card) card.remove();
  cards.delete(id);
}

const renderedLogs = new WeakMap();

function syncLog(pre, sentences, unavailable, jobId) {
  if (pre.dataset.jobId !== jobId) {
    pre.dataset.jobId = jobId;
    pre.dataset.mode = "";
    pre.dataset.count = "0";
    pre.textContent = "";
    renderedLogs.delete(pre);
  }
  const nearBottom = pre.scrollHeight - pre.scrollTop - pre.clientHeight < 8;
  if (unavailable) {
    if (pre.dataset.mode !== "unavailable") {
      pre.textContent = "The log is unavailable.";
      pre.dataset.mode = "unavailable";
      pre.dataset.count = "0";
      renderedLogs.delete(pre);
    }
    return;
  }
  if (!sentences.length) {
    if (pre.dataset.mode !== "empty") {
      pre.textContent = "No log lines yet.";
      pre.dataset.mode = "empty";
      pre.dataset.count = "0";
      renderedLogs.delete(pre);
    }
    return;
  }
  const shown = renderedLogs.get(pre) || [];
  const extendsShown =
    pre.dataset.mode === "lines" &&
    shown.length <= sentences.length &&
    shown.every((line, i) => line === sentences[i]);
  if (!extendsShown) {
    pre.textContent = sentences.join("\n");
  } else if (sentences.length > shown.length) {
    const extra = sentences.slice(shown.length).join("\n");
    const prefix = shown.length === 0 ? "" : "\n";
    pre.append(document.createTextNode(prefix + extra));
  }
  pre.dataset.mode = "lines";
  pre.dataset.count = String(sentences.length);
  renderedLogs.set(pre, sentences.slice());
  if (nearBottom) pre.scrollTop = pre.scrollHeight;
}

function collapseLog(card) {
  const panel = card.querySelector(".job-log-panel");
  const logButton = card.querySelector(".job-log-toggle");
  panel.hidden = true;
  logButton.classList.remove("is-open");
  logButton.setAttribute("aria-expanded", "false");
}

function finishedStatus(status) {
  return status === "succeeded" || status === "failed";
}

function syncJob(job) {
  const card = jobCard(job);
  const body = job.body || {};
  const lines = linesFrom(body);
  const sentences = lines.map((line) => line.text);
  const succeeded = body.status === "succeeded";
  const failed = body.status === "failed";
  const running = body.status === "queued" || body.status === "running";
  const pulse = card.querySelector(".job-pulse");
  pulse.hidden = !running && !succeeded && !failed;
  pulse.classList.toggle("is-done", succeeded);
  pulse.classList.toggle("is-failed", failed);
  const stageEl = card.querySelector(".job-stage");
  const label = labelFor(body, lines);
  const skipped = succeeded && label === SKIPPED_LABEL;
  stageEl.textContent = label;
  stageEl.classList.toggle("is-done", succeeded && !skipped);
  stageEl.classList.toggle("is-skipped", skipped);
  stageEl.classList.toggle("is-failed", failed);
  const finished = finishedStatus(body.status);
  const becameFinished = finished && card.dataset.finished !== "1";
  if (becameFinished) collapseLog(card);
  const file = latestFile(lines);
  const countEl = card.querySelector(".job-count");
  const indexLocked = countEl.dataset.indexLocked === "1";
  const total = Number(body.files_total || (file ? file.total : 0));
  if (total > 1 && (file || finished)) {
    countEl.hidden = false;
    if (!indexLocked) {
      delete card.dataset.uploadLocked;
      const index = Math.max(file ? file.index : 0, finalIndex(body));
      const member = file && file.index === index ? file.member : "";
      countEl.querySelector(".job-count-current").textContent = String(index);
      countEl.querySelector(".job-count-total").textContent = String(total);
      const memberEl = countEl.querySelector(".job-member");
      memberEl.textContent = member ? baseName(member) : "";
      if (member) memberEl.title = member;
      else memberEl.removeAttribute("title");
      if (countEl.dataset.index !== String(index)) {
        countEl.dataset.index = String(index);
        countEl.classList.remove("is-advance");
        void countEl.offsetWidth;
        countEl.classList.add("is-advance");
      }
      if (countEl.dataset.member !== member) {
        countEl.dataset.member = member;
        delete countEl.dataset.lockedSeconds;
        if (member) {
          card.dataset.fileStarted = String(file.started || Date.now());
        } else {
          delete card.dataset.fileStarted;
        }
      }
      const worker = member ? workerTotalSeconds(sentences, member) : null;
      if (worker != null) countEl.dataset.lockedSeconds = String(worker);
      if (
        finished &&
        member &&
        typeof countEl.dataset.lockedSeconds === "undefined"
      ) {
        const started = Number(card.dataset.fileStarted);
        const end = lastLineTime(lines) || job.finishedAt || Date.now();
        countEl.dataset.lockedSeconds = String(
          Math.max(0, (end - started) / 1000),
        );
      }
      if (finished && (job.settled || (member && worker != null))) {
        countEl.dataset.indexLocked = "1";
      }
    }
    let fileTime = "";
    if (countEl.dataset.lockedSeconds) {
      fileTime = formatDuration(Number(countEl.dataset.lockedSeconds));
    } else if (card.dataset.fileStarted && !finished) {
      fileTime = formatDuration(
        (Date.now() - Number(card.dataset.fileStarted)) / 1000,
      );
    }
    countEl.querySelector(".job-file-time").textContent = fileTime;
  } else if (!indexLocked) {
    countEl.hidden = true;
    countEl.dataset.index = "";
    delete countEl.dataset.member;
    delete countEl.dataset.lockedSeconds;
    delete countEl.dataset.indexLocked;
    countEl.classList.remove("is-advance");
    const worker = workerTotalSeconds(sentences, "");
    if (worker != null) card.dataset.uploadLocked = String(worker);
    else delete card.dataset.uploadLocked;
  }
  if (finished && !card.dataset.uploadLocked) {
    card.dataset.uploadLocked = String(uploadSeconds(job));
  }
  if (finished) card.dataset.finished = "1";
  const uploadClock = card.dataset.uploadLocked
    ? Number(card.dataset.uploadLocked)
    : uploadSeconds(job);
  card.querySelector(".job-elapsed").textContent = formatDuration(uploadClock);
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
  const hint = card.querySelector(".job-hint");
  const beat = running ? latestHeartbeat(lines) : null;
  hint.hidden = !beat;
  hint.textContent = beat ? rewriteDurations(beat.text) : "";
  syncSummary(card, body, lines, finished);
  const technical =
    card.querySelector(".job-log-mode").getAttribute("aria-pressed") === "true";
  syncLog(
    card.querySelector(".job-log-panel pre"),
    displayLines(lines, technical),
    body.log_available === false,
    `${job.id}:${technical ? "technical" : "readable"}`,
  );
}

function fallbackSummary(body) {
  const total = Number(body.files_total || 0);
  if (!total) return "";
  return `${body.files_done || 0} of ${plural(total, "file")} processed`;
}

function syncSummary(card, body, lines, finished) {
  const summaryEl = card.querySelector(".job-summary");
  const warningEl = card.querySelector(".job-warning");
  const summary = finished ? parseSummary(lines) : null;
  const text = summary
    ? summaryText(summary)
    : finished
      ? fallbackSummary(body)
      : "";
  summaryEl.hidden = !text;
  summaryEl.textContent = text;
  const skippedLines = summary ? summary.skippedLines : 0;
  warningEl.hidden = skippedLines === 0;
  warningEl.textContent = skippedLines
    ? `${plural(skippedLines, "line")} had no date and time and ${skippedLines === 1 ? "was" : "were"} skipped.`
    : "";
}

function tickClocks() {
  for (const job of snapshots.values()) {
    const card = cards.get(job.id);
    if (!card) continue;
    if (finishedStatus((job.body || {}).status)) continue;
    if (!card.dataset.uploadLocked) {
      card.querySelector(".job-elapsed").textContent = formatDuration(
        uploadSeconds(job),
      );
    }
    const count = card.querySelector(".job-count");
    if (!count || count.hidden || count.dataset.lockedSeconds) continue;
    const started = Number(card.dataset.fileStarted || "0");
    if (!started) continue;
    count.querySelector(".job-file-time").textContent = formatDuration(
      (Date.now() - started) / 1000,
    );
  }
}

async function fetchJob(id) {
  const response = await fetch(`/tagbase/api/v0/ingest/jobs/${id}`, {
    headers: { Accept: "application/json, application/problem+json" },
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

function applyPoll(job, outcome) {
  const current = snapshots.get(job.id);
  if (!current) return;
  if (outcome.status === "rejected") {
    // Keep the last good body; a failed check is not a job state.
    const reason = outcome.reason;
    snapshots.set(job.id, {
      ...current,
      pollError: reason && reason.message ? reason.message : "network error",
    });
    return;
  }
  if (outcome.value.gone) {
    snapshots.delete(job.id);
    forgetJob(job.id);
    dropCard(job.id);
    return;
  }
  const { body } = outcome.value;
  const finished = finishedStatus(body.status);
  const settlePolls = finished ? (current.settlePolls || 0) + 1 : 0;
  const settled = finished && (logCaughtUp(body) || settlePolls > SETTLE_POLLS);
  snapshots.set(job.id, {
    ...current,
    body,
    pollError: "",
    finishedAt: finished ? current.finishedAt || Date.now() : undefined,
    settlePolls,
    settled,
  });
  if (settled) forgetJob(job.id);
}

async function pollJobs() {
  const jobs = loadJobs();
  for (const job of jobs) {
    if (!snapshots.has(job.id)) {
      snapshots.set(job.id, {
        id: job.id,
        filename: job.filename,
        acceptedAt: job.acceptedAt || Date.now(),
        body: { status: "queued", lines: [], log_available: true },
      });
    }
  }
  const outcomes = await Promise.allSettled(
    jobs.map((job) => fetchJob(job.id)),
  );
  jobs.forEach((job, i) => applyPoll(job, outcomes[i]));
  for (const job of snapshots.values()) syncJob(job);
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
