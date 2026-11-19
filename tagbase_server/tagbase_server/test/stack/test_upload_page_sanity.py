# coding: utf-8

"""Upload page browser check against the running compose stack.

Starts headless Chrome and runs upload_page_sanity.mjs, which drives the page
over the DevTools protocol. Ingest POST and GET are answered in the browser,
so no submission is written. Other writes are refused.

Requires: docker compose -f docker-compose.test.yml --profile stack up -d
Also needs Chrome or Chromium (CHROME_BIN overrides discovery) and Node 22+.
The log panel's iframe loads Grafana when the observability profile is up;
the checks do not depend on it.
Env (defaults match docker-compose.test.yml, as in test_nginx_auth.py):
  UPLOAD_SANITY_URL=https://localhost/upload.html
  UPLOAD_SANITY_USER=testuser
  UPLOAD_SANITY_PASS=testpass
"""

import os
import shutil
import subprocess
import time
from pathlib import Path

import httpx
import pytest

pytestmark = pytest.mark.stack

SCRIPT = Path(__file__).with_name("upload_page_sanity.mjs")
CHROME_FLAGS = [
    "--headless=new",
    "--disable-gpu",
    "--ignore-certificate-errors",
    "--no-first-run",
    "--no-default-browser-check",
    "--remote-debugging-port=0",
    "--remote-allow-origins=http://127.0.0.1",
    "--window-size=1280,900",
]


def _page_url():
    return os.getenv("UPLOAD_SANITY_URL", "https://localhost/upload.html")


def _auth():
    return (
        os.getenv("UPLOAD_SANITY_USER", "testuser"),
        os.getenv("UPLOAD_SANITY_PASS", "testpass"),
    )


def _stack_up():
    try:
        with httpx.Client(verify=False, timeout=2.0) as client:
            client.get(_page_url(), auth=_auth())
        return True
    except Exception:
        return False


def _find_chrome():
    configured = os.getenv("CHROME_BIN")
    if configured:
        return configured
    mac = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if os.access(mac, os.X_OK):
        return mac
    for name in (
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
    ):
        found = shutil.which(name)
        if found:
            return found
    return None


def _start_chrome(chrome, profile, log_path):
    with open(log_path, "w", encoding="utf-8") as log:
        proc = subprocess.Popen(
            [chrome, *CHROME_FLAGS, f"--user-data-dir={profile}", "about:blank"],
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    port_file = profile / "DevToolsActivePort"
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if port_file.exists() and port_file.stat().st_size > 0:
            return proc, port_file.read_text(encoding="utf-8").splitlines()[0]
        if proc.poll() is not None:
            raise AssertionError(
                f"Chrome exited before DevTools was ready:\n{log_path.read_text()}"
            )
        time.sleep(0.2)
    proc.kill()
    raise AssertionError(f"Chrome DevTools port was not ready:\n{log_path.read_text()}")


@pytest.mark.skipif(
    not _stack_up(), reason="compose stack not running on the upload page URL"
)
def test_upload_page_sanity(tmp_path):
    chrome = _find_chrome()
    if not chrome or not os.access(chrome, os.X_OK):
        pytest.skip("Chrome or Chromium not found; set CHROME_BIN")
    node = shutil.which("node")
    if not node:
        pytest.skip("node not found; the browser check needs Node 22+")

    profile = tmp_path / "profile"
    proc, port = _start_chrome(chrome, profile, tmp_path / "chrome.log")
    env = {
        **os.environ,
        "UPLOAD_SANITY_URL": _page_url(),
        "UPLOAD_SANITY_USER": _auth()[0],
        "UPLOAD_SANITY_PASS": _auth()[1],
    }
    try:
        result = subprocess.run(
            [node, str(SCRIPT), port],
            env=env,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
    finally:
        proc.kill()
        proc.wait(timeout=10)

    print(result.stdout)
    assert result.returncode == 0, result.stdout + result.stderr
