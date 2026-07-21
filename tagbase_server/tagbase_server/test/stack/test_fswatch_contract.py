# coding: utf-8

"""Contract tests for fswatch post.sh against a mock ingest HTTP server.

Uses a fake ``fswatch`` on PATH so tests do not depend on host FSEvents/inotify
(which agent sandboxes often block). The fake emits paths for files already in
the watch dir, covering continuous multi-file ingest + dedupe in post.sh.
"""

import os
import shutil
import signal
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

pytestmark = pytest.mark.stack

POST_SH = Path(__file__).resolve().parents[4] / "services" / "fswatch" / "post.sh"
_CONTRACT_ROOT = (
    Path(__file__).resolve().parents[4] / "staging_data" / ".contract_tests"
)

_FAKE_FSWATCH = r"""#!/usr/bin/env sh
# Emit paths for existing ingestible files, then poll for new ones.
# Args match: fswatch "$PATH_TO_CHECK" --event ...
dir=""
for a in "$@"; do
  case "$a" in
    -*) ;;
    *)
      dir=$a
      break
      ;;
  esac
done
[ -n "$dir" ] || exit 1
seen_file="${TMPDIR:-/tmp}/fake-fswatch-seen-$$"
: >"$seen_file"
emit_new() {
  for f in "$dir"*; do
    [ -f "$f" ] || continue
    base=${f##*/}
    case "$base" in
      .*|*.crdownload|*.part|*.tmp|*.download) continue ;;
    esac
    if grep -Fxq "$f" "$seen_file" 2>/dev/null; then
      continue
    fi
    echo "$f"
    echo "$f" >>"$seen_file"
  done
}
# Initial delay so post.sh can finish scan_existing, then poll.
sleep 0.3
while true; do
  emit_new
  sleep 0.2
done
"""


class _IngestHandler(BaseHTTPRequestHandler):
    requests = []

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b""
        parsed = urlparse(self.path)
        self.requests.append(
            {
                "path": parsed.path,
                "query": parse_qs(parsed.query),
                "body": body,
            }
        )
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"code":"200","message":"ok","elapsed":"0"}')

    def log_message(self, format, *args):  # noqa: A003
        return


@pytest.fixture
def mock_ingest_server():
    _IngestHandler.requests = []
    server = HTTPServer(("127.0.0.1", 0), _IngestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    yield f"http://{host}:{port}/tagbase/api/v0.14.0", _IngestHandler
    server.shutdown()


def _workspace_tmpdir(name):
    root = _CONTRACT_ROOT / name
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _install_fake_fswatch(work):
    bin_dir = work / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "fswatch"
    fake.write_text(_FAKE_FSWATCH, encoding="utf-8")
    fake.chmod(0o755)
    return bin_dir


def _run_fswatch(env, log_path):
    log_f = open(log_path, "w", encoding="utf-8")
    proc = subprocess.Popen(
        ["sh", str(POST_SH)],
        env=env,
        stdout=log_f,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    proc._log_f = log_f  # noqa: SLF001 — closed in _stop_fswatch
    return proc


def _stop_fswatch(proc, timeout=5):
    log_f = getattr(proc, "_log_f", None)
    try:
        if proc.poll() is None:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass
    finally:
        if log_f is not None:
            try:
                log_f.close()
            except Exception:
                pass


def _clean_env(base_env, staging, dedupe_path, ingest_base, bin_dir):
    """Build a child env without HTTP proxies; prefer fake fswatch on PATH."""
    env = base_env.copy()
    for key in list(env):
        if key.lower() in {
            "http_proxy",
            "https_proxy",
            "all_proxy",
            "socks_proxy",
            "socks5_proxy",
        }:
            env.pop(key, None)
    env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
    env["PATH_TO_CHECK"] = str(staging) + os.sep
    env["TAGBASE_INGEST_BASE"] = ingest_base
    env["DEDUPE_STATE"] = str(dedupe_path)
    env["no_proxy"] = "*"
    env["NO_PROXY"] = "*"
    return env


def _read_log(log_path):
    try:
        return Path(log_path).read_text(encoding="utf-8")
    except OSError:
        return ""


def test_fswatch_posts_basename_and_body_after_size_stable(mock_ingest_server):
    if not POST_SH.is_file():
        pytest.skip("post.sh not found")

    ingest_base, handler = mock_ingest_server
    work = _workspace_tmpdir("single")
    staging = work / "staging_data"
    staging.mkdir()
    bin_dir = _install_fake_fswatch(work)
    log_path = work / "fswatch.log"
    env = _clean_env(os.environ, staging, work / "dedupe", ingest_base, bin_dir)

    # File present before watch starts — covered by scan_existing + fake emit.
    target = staging / "drop-etuff.txt"
    target.write_bytes(b"partial-complete")

    proc = _run_fswatch(env, log_path)
    try:
        deadline = time.time() + 25
        while time.time() < deadline and not handler.requests:
            time.sleep(0.25)
        if not handler.requests:
            pytest.fail(
                f"fswatch did not POST to ingest. post.sh output:\n{_read_log(log_path)}"
            )
        req = handler.requests[0]
        assert req["path"].endswith("/ingest")
        assert req["query"]["filename"] == ["drop-etuff.txt"]
        assert req["query"]["type"] == ["etuff"]
        assert req["body"] == b"partial-complete"
    finally:
        _stop_fswatch(proc)
        shutil.rmtree(work, ignore_errors=True)


def test_fswatch_skips_browser_temp_crdownload(mock_ingest_server):
    if not POST_SH.is_file():
        pytest.skip("post.sh not found")

    ingest_base, handler = mock_ingest_server
    work = _workspace_tmpdir("crdownload")
    staging = work / "staging_data"
    staging.mkdir()
    bin_dir = _install_fake_fswatch(work)
    log_path = work / "fswatch.log"
    env = _clean_env(os.environ, staging, work / "dedupe", ingest_base, bin_dir)

    proc = _run_fswatch(env, log_path)
    try:
        time.sleep(0.5)
        temp = staging / "Unconfirmed 821370.crdownload"
        temp.write_bytes(b"partial-download")
        time.sleep(1.5)
        assert handler.requests == []
    finally:
        _stop_fswatch(proc)
        shutil.rmtree(work, ignore_errors=True)


def test_fswatch_ingests_multiple_files_dropped_quickly(mock_ingest_server):
    """Continuous watch must POST every sibling file, not only the first."""
    if not POST_SH.is_file():
        pytest.skip("post.sh not found")

    ingest_base, handler = mock_ingest_server
    work = _workspace_tmpdir("multi")
    staging = work / "staging_data"
    staging.mkdir()
    bin_dir = _install_fake_fswatch(work)
    log_path = work / "fswatch.log"
    env = _clean_env(os.environ, staging, work / "dedupe", ingest_base, bin_dir)

    names = ["multi-a.txt", "multi-b.txt", "multi-c.txt"]
    bodies = {n: f"body-{n}".encode() for n in names}

    proc = _run_fswatch(env, log_path)
    try:
        time.sleep(0.5)
        for name in names:
            (staging / name).write_bytes(bodies[name])
            time.sleep(0.15)
        deadline = time.time() + 40
        while time.time() < deadline:
            got = {(r["query"].get("filename") or [None])[0] for r in handler.requests}
            if got >= set(names):
                break
            time.sleep(0.25)
        else:
            got = [(r["query"].get("filename") or [None])[0] for r in handler.requests]
            pytest.fail(
                f"expected POSTs for {names}, got {got}. "
                f"post.sh output:\n{_read_log(log_path)}"
            )
        by_name = {
            (r["query"].get("filename") or [None])[0]: r["body"]
            for r in handler.requests
        }
        for name in names:
            assert by_name[name] == bodies[name]
    finally:
        _stop_fswatch(proc)
        shutil.rmtree(work, ignore_errors=True)
