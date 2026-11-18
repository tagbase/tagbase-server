"""Queued ingest jobs.

A request stores the upload and inserts one row. The ingest process claims
the oldest queued row and updates it until the job is terminal.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from psycopg2.extras import RealDictCursor

from tagbase_server.utils.db_utils import connect

logger = logging.getLogger(__name__)

RESTART_ERROR = "restarted before ingest finished"
MISSING_FILE_ERROR = "upload file missing after restart"
DEFAULT_RETENTION_DAYS = 30
_LINE_CAP = 500
_TEXT_MAX = 10000
# Loki may stamp a line slightly before the job row's created_at.
_START_MARGIN_SECONDS = 60
# Total budget for the Loki read. urlopen's timeout applies per socket
# operation, so the body is read in chunks against this deadline.
_LOKI_TIMEOUT_SECONDS = 2
_READ_CHUNK = 64 * 1024
_JOB_ID = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

_CLAIM_SQL = """
UPDATE ingest_job
SET status = 'running', updated_at = now()
WHERE id = (
    SELECT id
    FROM ingest_job
    WHERE status = 'queued'
    ORDER BY created_at, updated_at
    FOR UPDATE SKIP LOCKED
    LIMIT 1
)
RETURNING *
"""

# Jobs ahead of a queued one, in _CLAIM_SQL order. NULL unless queued.
_FETCH_SQL = """
SELECT j.*,
    CASE WHEN j.status = 'queued' THEN (
        SELECT count(*)
        FROM ingest_job q
        WHERE q.status = 'running'
            OR (
                q.status = 'queued'
                AND (q.created_at, q.updated_at) < (j.created_at, j.updated_at)
            )
    ) END AS queue_position
FROM ingest_job j
WHERE j.id = %s
"""


class IngestJobError(Exception):
    """The job table could not be read or written."""


class LokiQueryError(Exception):
    """Loki could not be queried for this job."""


def stale_failures(jobs: list[dict[str, Any]], path_exists) -> list[tuple[str, str]]:
    """Jobs a restart must fail.

    A running job was interrupted. A queued job whose upload is gone cannot
    run. A queued job whose file is still present stays queued.
    """
    failed: list[tuple[str, str]] = []
    for job in jobs:
        status = job["status"]
        job_id = str(job["id"])
        if status == "running":
            failed.append((job_id, RESTART_ERROR))
        elif status == "queued" and not path_exists(job["source_path"]):
            failed.append((job_id, MISSING_FILE_ERROR))
    return failed


def loki_url() -> str:
    """Base URL of the Loki that holds the worker's log lines."""
    return os.environ.get("LOKI_URL", "http://loki:3100").rstrip("/")


def _line_time(timestamp_ns: int) -> str:
    """Loki stores nanoseconds since the epoch. Return UTC to the millisecond."""
    when = datetime.fromtimestamp(timestamp_ns / 1_000_000_000, tz=timezone.utc)
    return when.isoformat(timespec="milliseconds")


def select_job_lines(payload: dict[str, Any], job_id: str) -> list[dict[str, str]]:
    """Keep this job's most recent lines, oldest first, with Loki's time."""
    rows: list[tuple[int, str]] = []
    result = payload.get("data", {}).get("result", [])
    for stream in result:
        for value in stream.get("values", []):
            if len(value) < 2:
                continue
            meta = value[2] if len(value) > 2 and isinstance(value[2], dict) else {}
            tagged = meta.get("job_id")
            line = str(value[1])
            if tagged not in (None, "") and tagged != job_id:
                continue
            if tagged != job_id and f"job_id={job_id}" not in line:
                continue
            text = line.strip()
            if not text:
                continue
            rows.append((int(value[0]), text[:_TEXT_MAX]))
    rows.sort(key=lambda item: item[0])
    seen: set[tuple[int, str]] = set()
    lines: list[dict[str, str]] = []
    for item in rows:
        if item in seen:
            continue
        seen.add(item)
        lines.append({"time": _line_time(item[0]), "text": item[1]})
    return lines[-_LINE_CAP:]


def _read_before(response, deadline: float) -> bytes:
    chunks: list[bytes] = []
    while True:
        if time.monotonic() > deadline:
            raise TimeoutError("loki read exceeded its time budget")
        chunk = response.read(_READ_CHUNK)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def query_job_lines(job_id: str, since: datetime | None = None) -> list[dict[str, str]]:
    """Read this job's most recent lines from Loki, oldest first.

    ``since`` is the job's creation time. Without it the window is the job
    retention period.
    """
    if not _JOB_ID.fullmatch(job_id):
        raise LokiQueryError("invalid job id")
    query = '{service_name="tagbase_server"} |= "job_id=%s"' % job_id
    end = time.time()
    if since is None:
        start = end - DEFAULT_RETENTION_DAYS * 24 * 60 * 60
    else:
        start = since.timestamp() - _START_MARGIN_SECONDS
    params = urlencode(
        {
            "query": query,
            "start": str(int(start)),
            "end": str(int(end) + 1),
            "limit": str(_LINE_CAP),
            "direction": "backward",
        }
    )
    request = Request(f"{loki_url()}/loki/api/v1/query_range?{params}")
    deadline = time.monotonic() + _LOKI_TIMEOUT_SECONDS
    try:
        with urlopen(request, timeout=_LOKI_TIMEOUT_SECONDS) as response:
            raw = _read_before(response, deadline)
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict) or payload.get("status") != "success":
            raise LokiQueryError("loki query failed")
        return select_job_lines(payload, job_id)
    except LokiQueryError:
        raise
    except Exception as exc:
        raise LokiQueryError(str(exc) or type(exc).__name__) from exc


def public_job(
    row: dict[str, Any],
    *,
    line_source: Callable[[str, datetime | None], list[dict[str, str]]] | None = None,
) -> dict[str, Any]:
    job: dict[str, Any] = {
        "id": str(row["id"]),
        "status": row["status"],
        "files_done": row["files_done"],
    }
    if row["error"] is not None:
        job["error"] = row["error"]
    if row["files_total"] is not None:
        job["files_total"] = row["files_total"]
    if row["status"] == "queued" and row.get("queue_position") is not None:
        job["queue_position"] = int(row["queue_position"])
    source = query_job_lines if line_source is None else line_source
    try:
        job["lines"] = source(str(row["id"]), row.get("created_at"))
        job["log_available"] = True
    except LokiQueryError:
        logger.warning("Ingest job %s log is unavailable", row["id"])
        job["lines"] = []
        job["log_available"] = False
    return job


def enqueue_job(
    *,
    source_path: str,
    filename: str | None,
    version: str | None,
    notes: str | None,
) -> str:
    job_id = str(uuid.uuid4())
    with _connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ingest_job (id, status, source_path, filename, version, notes)
                VALUES (%s, 'queued', %s, %s, %s, %s)
                """,
                (job_id, source_path, filename, version, notes),
            )
        conn.commit()
    return job_id


def fetch_job(job_id: str) -> dict[str, Any] | None:
    with _connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(_FETCH_SQL, (job_id,))
            row = cur.fetchone()
        conn.commit()
    if row is None:
        return None
    return public_job(dict(row))


def recover_stale_jobs() -> None:
    with _connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, status, source_path
                FROM ingest_job
                WHERE status IN ('queued', 'running')
                """)
            rows = [dict(row) for row in cur.fetchall()]
            for job_id, error in stale_failures(rows, os.path.isfile):
                cur.execute(
                    """
                    UPDATE ingest_job
                    SET status = 'failed', error = %s, updated_at = now()
                    WHERE id = %s AND status IN ('queued', 'running')
                    """,
                    (error, job_id),
                )
        conn.commit()


def claim_next_job() -> dict[str, Any] | None:
    with _connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(_CLAIM_SQL)
            row = cur.fetchone()
        conn.commit()
    if row is None:
        return None
    return dict(row)


def retention_days() -> int:
    return int(os.environ.get("INGEST_JOB_RETENTION_DAYS", DEFAULT_RETENTION_DAYS))


def purge_expired_jobs(days: int | None = None) -> int:
    """Delete terminal jobs older than the retention window."""
    window = DEFAULT_RETENTION_DAYS if days is None else days
    with _connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM ingest_job
                WHERE status IN ('succeeded', 'failed')
                  AND updated_at < now() - (%s * interval '1 day')
                """,
                (window,),
            )
            deleted = cur.rowcount
        conn.commit()
    return deleted


def set_progress(job_id: str, *, files_total: int, files_done: int) -> None:
    with _connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE ingest_job
                SET files_total = %s, files_done = %s, updated_at = now()
                WHERE id = %s
                """,
                (files_total, files_done, job_id),
            )
        conn.commit()


def finish_job(job_id: str, *, status: str, error: str | None) -> None:
    with _connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE ingest_job
                SET status = %s, error = %s, updated_at = now()
                WHERE id = %s
                """,
                (status, error, job_id),
            )
        conn.commit()


def _connection():
    conn = connect()
    if not hasattr(conn, "cursor"):
        raise IngestJobError("database unavailable")
    conn.autocommit = False
    return conn
