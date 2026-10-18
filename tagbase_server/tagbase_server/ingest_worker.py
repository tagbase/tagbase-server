"""One ingest process. It runs a single upload at a time."""

from __future__ import annotations

import logging
import os
import time

from tagbase_server.archives import PreparedIngest, materialize
from tagbase_server.ingest_jobs import (
    claim_next_job,
    finish_job,
    recover_stale_jobs,
    set_progress,
)
from tagbase_server.utils.processing_utils import process_etuff_file

logger = logging.getLogger(__name__)

_POLL_SECONDS = 3


def run_job(job: dict) -> None:
    """Ingest every member. The first error fails the job and stops the queue."""
    job_id = str(job["id"])
    logical = job.get("filename") or os.path.basename(job["source_path"])
    prepared = materialize(job["source_path"], logical)
    job["_workspace"] = prepared.workspace
    members = prepared.files
    if not members:
        raise RuntimeError("archive contained no eTUFF files")
    set_progress(job_id, files_total=len(members), files_done=0)
    for done, (member, name) in enumerate(
        zip(members, prepared.submission_names(), strict=True), start=1
    ):
        process_etuff_file(
            member,
            version=job.get("version"),
            notes=job.get("notes"),
            count_request=False,
            submission_name=name,
        )
        set_progress(job_id, files_total=len(members), files_done=done)


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
    try:
        run_job(job)
    except Exception as exc:
        logger.exception("Ingest job %s failed", job_id)
        finish_job(job_id, status="failed", error=str(exc))
    else:
        finish_job(job_id, status="succeeded", error=None)
    finally:
        _discard_job_files(job)
    return True


def process_available() -> int:
    """Run every job that is already queued. Used by tests in this process."""
    recover_stale_jobs()
    ran = 0
    while process_next():
        ran += 1
    return ran


def main() -> None:
    from tagbase_server.telemetry import setup_telemetry

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    setup_telemetry(flask_app=None)
    logger.info("Ingest worker starting")
    recover_stale_jobs()
    while True:
        if not process_next():
            time.sleep(_POLL_SECONDS)


if __name__ == "__main__":
    main()
