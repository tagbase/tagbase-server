# coding: utf-8

"""Compose smoke: drop eTUFF into staging_data and observe tag via nginx API."""

import os
import shutil
import time
from pathlib import Path

import httpx
import pytest

from tagbase_server.test.helpers import ETUFF_FIXTURE

pytestmark = pytest.mark.stack

API = "/tagbase/api/v0.14.0"
REPO_ROOT = Path(__file__).resolve().parents[4]
STAGING = REPO_ROOT / "staging_data"


def _base():
    return os.getenv("TAGBASE_STACK_BASE", "https://localhost:443").rstrip("/")


def _auth():
    return (
        os.getenv("TAGBASE_STACK_USER", "testuser"),
        os.getenv("TAGBASE_STACK_PASS", "testpass"),
    )


def _stack_ready():
    try:
        with httpx.Client(verify=False, timeout=2.0) as client:
            r = client.get(_base() + f"{API}/tags", auth=_auth())
        return r.status_code == 200
    except Exception:
        return False


@pytest.fixture(scope="module", autouse=True)
def require_full_stack():
    if not _stack_ready():
        pytest.skip(
            "full stack not ready; "
            "docker compose -f docker-compose.test.yml --profile stack up -d --build"
        )


def test_staging_drop_ingests_etuff_visible_via_api():
    STAGING.mkdir(exist_ok=True)
    # clear prior drops from this suite
    for stale in STAGING.glob("stack-smoke-*.txt"):
        stale.unlink()

    with httpx.Client(verify=False, timeout=30.0) as client:
        client.delete(_base() + f"{API}/tags", auth=_auth())

    dest = STAGING / "stack-smoke-etuff.txt"
    shutil.copyfile(ETUFF_FIXTURE, dest)

    deadline = time.time() + 90
    last = None
    while time.time() < deadline:
        with httpx.Client(verify=False, timeout=30.0) as client:
            last = client.get(_base() + f"{API}/tags", auth=_auth())
        if last.status_code == 200 and last.json().get("count", 0) >= 1:
            break
        time.sleep(2)
    assert last is not None
    assert last.status_code == 200
    assert last.json()["count"] >= 1
