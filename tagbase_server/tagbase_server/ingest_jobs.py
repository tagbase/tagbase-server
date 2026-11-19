"""Queued ingest jobs.

A request stores the upload and inserts one row. The ingest process claims
the oldest queued row and updates it until the job is terminal. The row holds
what the upload page shows: the stage, the current member, and the summary.
Log lines stay in Loki and are read through Grafana.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Any

from psycopg2.extras import Json, RealDictCursor

from tagbase_server.utils.db_utils import connect

RESTART_ERROR = "restarted before ingest finished"
MISSING_FILE_ERROR = "upload file missing after restart"
DEFAULT_RETENTION_DAYS = 30
STAGE_READING = "Reading the file"
STAGE_WRITING = "Writing measurements"

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


def _iso(value: Any) -> str:
    """Datetimes leave the API as UTC ISO 8601 to the millisecond."""
    if isinstance(value, datetime):
        return value.isoformat(timespec="milliseconds")
    return str(value)


def public_job(row: dict[str, Any]) -> dict[str, Any]:
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
    if row.get("stage"):
        job["stage"] = row["stage"]
    if row.get("current_member"):
        job["current_member"] = row["current_member"]
    if row.get("summary") is not None:
        job["summary"] = row["summary"]
    if row.get("created_at") is not None:
        job["created_at"] = _iso(row["created_at"])
    if row.get("updated_at") is not None:
        job["updated_at"] = _iso(row["updated_at"])
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


def set_stage(job_id: str, stage: str, member: str | None = None) -> None:
    """Record what a running job is doing. A member name replaces the current one.

    Only running rows change, so a late heartbeat cannot rewrite a finished job.
    """
    with _connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE ingest_job
                SET stage = %s,
                    current_member = COALESCE(%s, current_member),
                    updated_at = now()
                WHERE id = %s AND status = 'running'
                """,
                (stage, member, job_id),
            )
        conn.commit()


def finish_job(
    job_id: str,
    *,
    status: str,
    error: str | None,
    summary: dict[str, Any] | None = None,
) -> None:
    with _connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE ingest_job
                SET status = %s, error = %s, summary = %s,
                    stage = NULL, current_member = NULL, updated_at = now()
                WHERE id = %s
                """,
                (status, error, Json(summary) if summary is not None else None, job_id),
            )
        conn.commit()


def _connection():
    conn = connect()
    if not hasattr(conn, "cursor"):
        raise IngestJobError("database unavailable")
    conn.autocommit = False
    return conn
