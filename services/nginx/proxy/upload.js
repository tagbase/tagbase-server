const form = document.querySelector("#upload-form");
const dropZone = document.querySelector("#drop-zone");
const fileInput = document.querySelector("#file");
const fileName = document.querySelector("#file-name");
const status = document.querySelector("#status");
const submit = document.querySelector("#submit");
const abortButton = document.querySelector("#abort");
const stopMonitor = document.querySelector("#stop-monitor");
const progressWrap = document.querySelector("#progress-wrap");
const progress = document.querySelector("#progress");

const STORAGE_KEY = "tagbase-ingest-jobs";
const POLL_MS = 3000;
let activeXhr = null;
let pollTimer = null;

function showStatus(type, message) {
  status.className = `alert alert-${type} mt-4`;
  status.textContent = message;
}

function updateFileListDisplay() {
  const files = Array.from(fileInput.files);
  if (files.length === 0) {
    fileName.textContent = "";
  } else if (files.length === 1) {
    fileName.textContent = files[0].name;
  } else {
    fileName.textContent =
      `${files.length} files selected:\n` + files.map((f) => f.name).join(", ");
  }
}

function setFiles(files) {
  if (!files || !files.length) return;
  const transfer = new DataTransfer();
  for (const file of files) {
    transfer.items.add(file);
  }
  fileInput.files = transfer.files;
  updateFileListDisplay();
}

["dragenter", "dragover"].forEach((name) =>
  dropZone.addEventListener(name, (event) => {
    event.preventDefault();
    dropZone.classList.add("is-dragging");
  }),
);
["dragleave", "drop"].forEach((name) =>
  dropZone.addEventListener(name, (event) => {
    event.preventDefault();
    dropZone.classList.remove("is-dragging");
  }),
);
dropZone.addEventListener("drop", (event) =>
  setFiles(event.dataTransfer.files),
);
fileInput.addEventListener("change", updateFileListDisplay);

function loadJobs() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
  } catch {
    return [];
  }
}

function saveJobs(jobs) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(jobs));
  stopMonitor.classList.toggle("d-none", jobs.length === 0);
}

function rememberJob(job) {
  const jobs = loadJobs().filter((item) => item.id !== job.id);
  jobs.push(job);
  saveJobs(jobs);
}

function forgetJob(id) {
  saveJobs(loadJobs().filter((item) => item.id !== id));
}

function postFile(file, params) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    activeXhr = xhr;
    xhr.open("POST", `/tagbase/api/v0/ingest/jobs?${params}`);
    xhr.setRequestHeader(
      "Content-Type",
      file.type || "application/octet-stream",
    );
    xhr.setRequestHeader("Accept", "application/json");
    xhr.upload.onprogress = (event) => {
      if (!event.lengthComputable) return;
      const pct = Math.round((event.loaded / event.total) * 100);
      progress.style.width = `${pct}%`;
      progress.textContent = `${pct}%`;
    };
    xhr.onload = () => {
      activeXhr = null;
      if (xhr.status === 202) {
        resolve(JSON.parse(xhr.responseText));
        return;
      }
      reject(new Error(`${xhr.status}\n${xhr.responseText}`));
    };
    xhr.onerror = () => {
      activeXhr = null;
      reject(new Error("upload failed"));
    };
    xhr.onabort = () => {
      activeXhr = null;
      reject(new Error("upload aborted"));
    };
    progressWrap.classList.remove("d-none");
    abortButton.classList.remove("d-none");
    xhr.send(file);
  });
}

async function pollOnce() {
  const jobs = loadJobs();
  if (!jobs.length) {
    stopMonitor.classList.add("d-none");
    return;
  }
  const lines = [];
  for (const job of jobs) {
    try {
      const response = await fetch(`/tagbase/api/v0/ingest/jobs/${job.id}`, {
        headers: { Accept: "application/json" },
      });
      const body = await response.json();
      if (body.status === "succeeded") {
        forgetJob(job.id);
        lines.push(`✓ ${job.filename}: succeeded`);
      } else if (body.status === "failed") {
        forgetJob(job.id);
        lines.push(`✗ ${job.filename}: ${body.error || "failed"}`);
      } else {
        lines.push(`… ${job.filename}: ${body.status}`);
      }
    } catch (error) {
      lines.push(`… ${job.filename}: ${error.message}`);
    }
  }
  const remaining = loadJobs();
  showStatus(
    remaining.length ? "info" : "success",
    lines.join("\n") || "No jobs are being monitored.",
  );
}

function ensurePolling() {
  if (pollTimer) return;
  pollTimer = window.setInterval(pollOnce, POLL_MS);
  pollOnce();
}

abortButton.addEventListener("click", () => {
  if (activeXhr) activeXhr.abort();
});

stopMonitor.addEventListener("click", () => {
  saveJobs([]);
  showStatus("info", "Stopped monitoring. The server job keeps running.");
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const files = Array.from(fileInput.files);
  if (!files.length) return;
  const version = document.querySelector("#version").value.trim();
  const notes = document.querySelector("#notes").value.trim();
  submit.disabled = true;
  const results = [];
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    const params = new URLSearchParams({ filename: file.name });
    if (version) params.set("version", version);
    if (notes) params.set("notes", notes);
    showStatus(
      "info",
      `Uploading file ${i + 1} of ${files.length}: ${file.name}…`,
    );
    try {
      const accepted = await postFile(file, params);
      rememberJob({ id: accepted.id, filename: file.name });
      results.push(`queued ${file.name} (${accepted.id})`);
    } catch (error) {
      results.push(`✗ ${file.name}: ${error.message}`);
    } finally {
      abortButton.classList.add("d-none");
      progressWrap.classList.add("d-none");
      progress.style.width = "0%";
    }
  }
  showStatus("info", results.join("\n"));
  submit.disabled = false;
  form.reset();
  fileName.textContent = "";
  ensurePolling();
});

if (loadJobs().length) ensurePolling();
