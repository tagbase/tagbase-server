"""One ingest process. It runs a single upload at a time."""

from __future__ import annotations

import logging
import os
import time
from typing import Any

from tagbase_server.archives import PreparedIngest, materialize
from tagbase_server.ingest_jobs import (
    STAGE_READING,
    claim_next_job,
    finish_job,
    recover_stale_jobs,
    set_progress,
    set_stage,
)
from tagbase_server.ingest_log import current_job_id, install_job_tagging
from tagbase_server.utils.processing_utils import process_etuff_file

logger = logging.getLogger(__name__)
install_job_tagging()

_POLL_SECONDS = 3


def run_job(job: dict) -> dict[str, Any]:
    """Ingest every member and return the job summary.

    The first error fails the job and stops the queue.
    """
    job_id = str(job["id"])
    token = current_job_id.set(job_id)
    try:
        return _run_job(job, job_id)
    finally:
        current_job_id.reset(token)


def summary_stats(files: int, outcomes: list[dict], seconds: float) -> dict[str, Any]:
    """Totals for a finished job. The job row keeps them for the upload page."""
    counts = {"ingested": 0, "metadata_only": 0, "duplicate": 0}
    skipped = 0
    for stats in outcomes:
        outcome = stats.get("outcome")
        if outcome in counts:
            counts[outcome] += 1
        skipped += int(stats.get("skipped_lines") or 0)
    return {
        "files": files,
        "loaded": counts["ingested"],
        "metadata_only": counts["metadata_only"],
        "duplicates": counts["duplicate"],
        "skipped_lines": skipped,
        "seconds": round(seconds, 2),
    }


def _format_summary(stats: dict[str, Any]) -> str:
    return (
        f"ingest.summary files={stats['files']} loaded={stats['loaded']} "
        f"metadata_only={stats['metadata_only']} duplicates={stats['duplicates']} "
        f"skipped_lines={stats['skipped_lines']} seconds={stats['seconds']}"
    )


def summary_line(files: int, outcomes: list[dict], seconds: float) -> str:
    """The job's last log line, which the Grafana job-log panel shows."""
    return _format_summary(summary_stats(files, outcomes, seconds))


def _run_job(job: dict, job_id: str) -> dict[str, Any]:
    started = time.perf_counter()
    logical = job.get("filename") or os.path.basename(job["source_path"])
    prepared = materialize(job["source_path"], logical)
    job["_workspace"] = prepared.workspace
    members = prepared.files
    if not members:
        raise RuntimeError("archive contained no eTUFF files")
    set_progress(job_id, files_total=len(members), files_done=0)
    outcomes: list[dict] = []
    for done, (member, name) in enumerate(
        zip(members, prepared.submission_names(), strict=True), start=1
    ):
        if len(members) > 1:
            logger.info(
                "ingest.file index=%s total=%s member=%s",
                done,
                len(members),
                name,
            )
        set_stage(job_id, STAGE_READING, member=name)
        stats: dict = {}
        process_etuff_file(
            member,
            version=job.get("version"),
            notes=job.get("notes"),
            count_request=False,
            submission_name=name,
            stats=stats,
        )
        outcomes.append(stats)
        set_progress(job_id, files_total=len(members), files_done=done)
    summary = summary_stats(len(members), outcomes, time.perf_counter() - started)
    logger.info("%s", _format_summary(summary))
    return summary


def _discard_job_files(job: dict) -> None:
    workspace = job.get("_workspace")
    if workspace:
        try:
            PreparedIngest(files=[], workspace=workspace).cleanup()
        except OSError:
            logger.exception(
                "Failed to delete extracted workspace for job %s", job.get("id")
            )
    source = job.get("source_path")
    if not source:
        return
    try:
        if os.path.isfile(source):
            os.remove(source)
    except OSError:
        logger.exception("Failed to delete staged upload %s", source)


def process_next() -> bool:
    """Claim and run the oldest queued job. Return False when the queue is empty."""
    job = claim_next_job()
    if job is None:
        return False
    job_id = str(job["id"])
    token = current_job_id.set(job_id)
    try:
        summary = run_job(job)
    except Exception as exc:
        logger.exception("Ingest job %s failed", job_id)
        finish_job(job_id, status="failed", error=str(exc))
    else:
        finish_job(job_id, status="succeeded", error=None, summary=summary)
    finally:
        _discard_job_files(job)
        current_job_id.reset(token)
    return True


def process_available() -> int:
    """Run every job that is already queued. Used by tests in this process."""
    recover_stale_jobs()
    ran = 0
    while process_next():
        ran += 1
    return ran


def main() -> None:
    from tagbase_server.profiling import setup_profiling
    from tagbase_server.telemetry import setup_telemetry

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    setup_telemetry(flask_app=None)
    setup_profiling("ingest_worker")
    logger.info("Ingest worker starting")
    recover_stale_jobs()
    while True:
        if not process_next():
            time.sleep(_POLL_SECONDS)


if __name__ == "__main__":
    main()
