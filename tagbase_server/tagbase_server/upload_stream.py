"""Stream ingest uploads before Connexion buffers the request body.

Synchronous POST /ingest is rejected above 100 MiB. POST /ingest/jobs is
written to a staging file in chunks, with a 2 GiB cap, and the application
then sees a short substitute body.
"""

from __future__ import annotations

import contextvars
import json
import os
import tempfile
from collections.abc import Callable

from tagbase_server.problem import TYPE_HTTP, current_trace_id
from tagbase_server.utils.io_utils import TEMP_DIR

SYNC_MAX_BYTES = 100 * 1024 * 1024
JOB_MAX_BYTES = 2 * 1024 * 1024 * 1024
_STAGED_BODY = b"staged"
_CHUNK = 1024 * 1024

staged_upload: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "staged_upload",
    default=None,
)
_heartbeat: Callable[[], None] | None = None


def register_upload_heartbeat(callback: Callable[[], None] | None) -> None:
    """Keep the Gunicorn worker alive while a chunked upload is in progress."""
    global _heartbeat
    _heartbeat = callback


def sync_max_bytes() -> int:
    return int(os.environ.get("TAGBASE_SYNC_MAX_BYTES", SYNC_MAX_BYTES))


def job_max_bytes() -> int:
    return int(os.environ.get("TAGBASE_JOB_MAX_BYTES", JOB_MAX_BYTES))


def upload_route(path: str) -> str | None:
    trimmed = path.rstrip("/") or "/"
    if trimmed.endswith("/ingest/jobs"):
        return "jobs"
    if trimmed.endswith("/ingest"):
        return "sync"
    return None


class UploadGuardMiddleware:
    """ASGI middleware installed outside Connexion."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http" or scope.get("method") != "POST":
            await self.app(scope, receive, send)
            return
        route = upload_route(scope.get("path", ""))
        if route == "jobs":
            await self._stream_job(scope, receive, send)
            return
        if route == "sync":
            await self._guard_sync(scope, receive, send)
            return
        await self.app(scope, receive, send)

    async def _guard_sync(self, scope, receive, send):
        length = _content_length(scope)
        limit = sync_max_bytes()
        if length == 0:
            await _send_problem(send, 400, "Bad Request", "Request body is empty.")
            return
        if length is not None and length > limit:
            await _send_problem(
                send,
                413,
                "Payload Too Large",
                "Synchronous ingest accepts at most 100 MiB. Use POST /ingest/jobs.",
            )
            return
        if length is not None:
            await self.app(scope, receive, send)
            return
        try:
            body = await _read_bounded(receive, limit)
        except _TooLarge:
            await _send_problem(
                send,
                413,
                "Payload Too Large",
                "Synchronous ingest accepts at most 100 MiB. Use POST /ingest/jobs.",
            )
            return
        except _ClientGone:
            return
        if not body:
            await _send_problem(send, 400, "Bad Request", "Request body is empty.")
            return
        await self.app(
            _with_content_length(scope, len(body)),
            _replay(body),
            send,
        )

    async def _stream_job(self, scope, receive, send):
        length = _content_length(scope)
        limit = job_max_bytes()
        if length == 0:
            await _send_problem(send, 400, "Bad Request", "Request body is empty.")
            return
        if length is not None and length > limit:
            await _send_problem(
                send,
                413,
                "Payload Too Large",
                "Ingest jobs accept at most 2 GiB.",
            )
            return
        handle = tempfile.NamedTemporaryFile(
            dir=TEMP_DIR,
            prefix="tagbase-upload-",
            delete=False,
        )
        path = handle.name
        try:
            total = await _write_bounded(receive, handle, limit)
        except _TooLarge:
            handle.close()
            _remove(path)
            await _send_problem(
                send,
                413,
                "Payload Too Large",
                "Ingest jobs accept at most 2 GiB.",
            )
            return
        except _ClientGone:
            handle.close()
            _remove(path)
            return
        except Exception:
            handle.close()
            _remove(path)
            raise
        handle.close()
        if total == 0:
            _remove(path)
            await _send_problem(send, 400, "Bad Request", "Request body is empty.")
            return
        token = staged_upload.set(path)
        try:
            await self.app(
                _with_content_length(scope, len(_STAGED_BODY)),
                _replay(_STAGED_BODY),
                send,
            )
        finally:
            staged_upload.reset(token)


def _content_length(scope) -> int | None:
    for key, value in scope.get("headers", []):
        if key.lower() == b"content-length":
            try:
                return int(value)
            except ValueError:
                return None
    return None


def _with_content_length(scope, size: int):
    headers = [
        (key, value)
        for key, value in scope.get("headers", [])
        if key.lower() != b"content-length"
    ]
    headers.append((b"content-length", str(size).encode("ascii")))
    updated = dict(scope)
    updated["headers"] = headers
    return updated


def _replay(body: bytes):
    sent = False

    async def receive():
        nonlocal sent
        if sent:
            return {"type": "http.request", "body": b"", "more_body": False}
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    return receive


async def _read_bounded(receive, limit: int) -> bytes:
    chunks = []
    total = 0
    while True:
        message = await receive()
        if message["type"] == "http.disconnect":
            raise _ClientGone()
        if message["type"] != "http.request":
            continue
        piece = message.get("body") or b""
        if piece:
            total += len(piece)
            if total > limit:
                raise _TooLarge()
            chunks.append(piece)
            _beat()
        if not message.get("more_body", False):
            return b"".join(chunks)


async def _write_bounded(receive, handle, limit: int) -> int:
    total = 0
    while True:
        message = await receive()
        if message["type"] == "http.disconnect":
            raise _ClientGone()
        if message["type"] != "http.request":
            continue
        piece = message.get("body") or b""
        if piece:
            total += len(piece)
            if total > limit:
                raise _TooLarge()
            handle.write(piece)
            _beat()
        if not message.get("more_body", False):
            return total


def _beat() -> None:
    if _heartbeat is not None:
        _heartbeat()


def _remove(path: str) -> None:
    try:
        os.remove(path)
    except OSError:
        pass


async def _send_problem(send, status: int, title: str, detail: str) -> None:
    payload = json.dumps(
        {
            "type": TYPE_HTTP,
            "title": title,
            "status": status,
            "detail": detail,
            "trace_id": current_trace_id(),
        }
    ).encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"application/problem+json"),
                (b"content-length", str(len(payload)).encode("ascii")),
            ],
        }
    )
    await send({"type": "http.response.body", "body": payload})


class _TooLarge(Exception):
    pass


class _ClientGone(Exception):
    pass
