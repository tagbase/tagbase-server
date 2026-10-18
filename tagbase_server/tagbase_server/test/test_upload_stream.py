# coding: utf-8

import asyncio
import os

from tagbase_server.api_prefix import API_PREFIX
from tagbase_server.test.conftest import create_test_app
from tagbase_server.upload_stream import (
    JOB_MAX_BYTES,
    SYNC_MAX_BYTES,
    UploadGuardMiddleware,
    staged_upload,
)


def test_default_upload_caps():
    assert SYNC_MAX_BYTES == 100 * 1024 * 1024
    assert JOB_MAX_BYTES == 2 * 1024 * 1024 * 1024


def test_sync_post_above_cap_is_413(monkeypatch):
    monkeypatch.setenv("TAGBASE_SYNC_MAX_BYTES", "4")
    app = create_test_app()
    with app.test_client() as client:
        response = client.post(
            f"{API_PREFIX}/ingest",
            params={"filename": "a.txt"},
            headers={"Content-Type": "text/plain", "Accept": "application/json"},
            data=b"12345",
        )
    assert response.status_code == 413
    assert response.headers["content-type"].startswith("application/problem+json")


def _run(middleware, body, limit_env="8"):
    captured = {}

    async def app(scope, receive, send):
        message = await receive()
        captured["body"] = message.get("body")
        captured["staged"] = staged_upload.get()
        if captured["staged"]:
            with open(captured["staged"], "rb") as handle:
                captured["file"] = handle.read()
        await send(
            {
                "type": "http.response.start",
                "status": 202,
                "headers": [(b"content-type", b"application/json")],
            }
        )
        await send({"type": "http.response.body", "body": b'{"status":"queued"}'})

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/tagbase/api/v0/ingest/jobs",
        "headers": [(b"content-length", str(len(body)).encode("ascii"))],
    }

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    sent = []

    async def send(message):
        sent.append(message)

    asyncio.run(UploadGuardMiddleware(app)(scope, receive, send))
    return captured, sent


def test_job_upload_streams_without_buffering_the_body(monkeypatch, tmp_path):
    monkeypatch.setenv("TAGBASE_JOB_MAX_BYTES", "8")
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    captured, sent = _run(None, b"12345678")
    assert captured["body"] == b"staged"
    assert captured["file"] == b"12345678"
    assert sent[0]["status"] == 202
    os.remove(captured["staged"])


def test_job_upload_one_byte_over_is_413(monkeypatch):
    monkeypatch.setenv("TAGBASE_JOB_MAX_BYTES", "8")
    captured, sent = _run(None, b"123456789")
    assert captured == {}
    assert sent[0]["status"] == 413
