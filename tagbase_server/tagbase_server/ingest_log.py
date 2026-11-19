"""Tag worker log lines with the current ingest job id.

The Grafana job-log panel finds a job's lines in Loki by the ``job_id=<uuid>``
text in each line, so the id must be part of the message, not only a record
attribute.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from collections.abc import Callable
from contextvars import ContextVar

current_job_id: ContextVar[str | None] = ContextVar("ingest_job_id", default=None)

HEARTBEAT_SECONDS = 15.0
HEARTBEAT_TEXT = "Writing measurements, still running"

logger = logging.getLogger(__name__)

_install_lock = threading.Lock()
_installed = False


def tag_record(record: logging.LogRecord) -> logging.LogRecord:
    """Append the current job id to the record's message."""
    job_id = current_job_id.get()
    if not job_id:
        return record
    record.job_id = job_id
    try:
        message = record.getMessage()
    except Exception:
        # A bad format string must not fail the ingest that logged it.
        message = f"{record.msg} {record.args!r}"
    token = f"job_id={job_id}"
    if token not in message:
        message = f"{message} {token}"
    record.msg = message
    record.args = None
    return record


def install_job_tagging() -> None:
    """Tag every record this process creates. Calling it again does nothing."""
    global _installed
    with _install_lock:
        if _installed:
            return
        previous = logging.getLogRecordFactory()

        def factory(*args, **kwargs) -> logging.LogRecord:
            return tag_record(previous(*args, **kwargs))

        logging.setLogRecordFactory(factory)
        _installed = True


def heartbeat_seconds() -> float:
    raw = os.environ.get("INGEST_HEARTBEAT_SECONDS", "")
    try:
        value = float(raw) if raw.strip() else HEARTBEAT_SECONDS
    except ValueError:
        return HEARTBEAT_SECONDS
    return value if value > 0 else HEARTBEAT_SECONDS


def heartbeat_while(
    stop: threading.Event,
    started: float,
    job_id: str,
    interval: float | None = None,
    on_beat: Callable[[], None] | None = None,
) -> None:
    """Log a still-running line every interval until stop is set.

    ``started`` is a ``time.perf_counter()`` reading. A new thread starts with
    an empty context, so the job id is set here. ``on_beat`` runs after each
    line, for example to refresh the job row's stage.
    """
    every = heartbeat_seconds() if interval is None else interval
    token = current_job_id.set(job_id)
    try:
        while not stop.wait(every):
            elapsed = int(time.perf_counter() - started)
            logger.info("%s elapsed=%ss", HEARTBEAT_TEXT, elapsed)
            if on_beat is not None:
                on_beat()
    finally:
        current_job_id.reset(token)
