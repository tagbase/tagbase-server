"""Queued ingest jobs.

A request stores the upload and inserts one row. The ingest process claims
the oldest queued row and updates it until the job is terminal.
"""

from __future__ import annotations

import os
import uuid
from typing import Any

from psycopg2.extras import RealDictCursor

from tagbase_server.utils.db_utils import connect

RESTART_ERROR = "restarted before ingest finished"
MISSING_FILE_ERROR = "upload file missing after restart"

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS ingest_job (
    id uuid PRIMARY KEY,
    status text NOT NULL
        CHECK (status IN ('queued', 'running', 'succeeded', 'failed')),
    source_path text NOT NULL,
    filename text,
    version text,
    notes text,
    error text,
    files_total integer,
    files_done integer NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
)
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
        _ensure_table(conn)
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
        _ensure_table(conn)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM ingest_job WHERE id = %s", (job_id,))
            row = cur.fetchone()
        conn.commit()
    if row is None:
        return None
    return public_job(dict(row))


def recover_stale_jobs() -> None:
    with _connection() as conn:
        _ensure_table(conn)
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
        _ensure_table(conn)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                UPDATE ingest_job
                SET status = 'running', updated_at = now()
                WHERE id = (
                    SELECT id
                    FROM ingest_job
                    WHERE status = 'queued'
                    ORDER BY created_at
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                )
                RETURNING *
                """)
            row = cur.fetchone()
        conn.commit()
    if row is None:
        return None
    return dict(row)


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


def _ensure_table(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(_CREATE_TABLE)
