# coding: utf-8

"""Contract tests for fswatch post.sh against a mock ingest HTTP server."""

import os
import shutil
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

pytestmark = pytest.mark.stack

POST_SH = Path(__file__).resolve().parents[4] / "services" / "fswatch" / "post.sh"


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


def _run_fswatch(env):
    return subprocess.Popen(
        ["sh", str(POST_SH)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def test_fswatch_posts_basename_and_body_after_size_stable(
    mock_ingest_server, tmp_path
):
    if shutil.which("fswatch") is None:
        pytest.skip("fswatch binary not installed on host")
    if not POST_SH.is_file():
        pytest.skip("post.sh not found")

    ingest_base, handler = mock_ingest_server
    staging = tmp_path / "staging_data"
    staging.mkdir()
    env = os.environ.copy()
    env["PATH_TO_CHECK"] = str(staging) + os.sep
    env["TAGBASE_INGEST_BASE"] = ingest_base

    proc = _run_fswatch(env)
    try:
        # let fswatch attach before creating the file
        time.sleep(1.0)
        # Atomic move into the watched dir (stable size before Created/MovedTo).
        staging_tmp = tmp_path / "drop-etuff.txt.part"
        target = staging / "drop-etuff.txt"
        staging_tmp.write_bytes(b"partial-complete")
        os.replace(staging_tmp, target)
        deadline = time.time() + 25
        while time.time() < deadline and not handler.requests:
            time.sleep(0.25)
        if not handler.requests:
            out = ""
            proc.terminate()
            try:
                out, _ = proc.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
                out, _ = proc.communicate(timeout=2)
            pytest.fail(f"fswatch did not POST to ingest. post.sh output:\n{out}")
        req = handler.requests[0]
        assert req["path"].endswith("/ingest")
        assert req["query"]["filename"] == ["drop-etuff.txt"]
        assert req["query"]["type"] == ["etuff"]
        assert req["body"] == b"partial-complete"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_fswatch_skips_browser_temp_crdownload(mock_ingest_server, tmp_path):
    if shutil.which("fswatch") is None:
        pytest.skip("fswatch binary not installed on host")
    if not POST_SH.is_file():
        pytest.skip("post.sh not found")

    ingest_base, handler = mock_ingest_server
    staging = tmp_path / "staging_data"
    staging.mkdir()
    env = os.environ.copy()
    env["PATH_TO_CHECK"] = str(staging) + os.sep
    env["TAGBASE_INGEST_BASE"] = ingest_base

    proc = _run_fswatch(env)
    try:
        time.sleep(1.0)
        temp = staging / "Unconfirmed 821370.crdownload"
        temp.write_bytes(b"partial-download")
        # Allow watcher loop to see and skip the temp file.
        time.sleep(2.0)
        assert handler.requests == []
    finally:
        proc.kill()
        try:
            proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            pass
