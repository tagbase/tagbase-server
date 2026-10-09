"""One ingest process. It runs a single zip at a time."""

from __future__ import annotations

import logging
import time

from tagbase_server.ingest_jobs import (
    claim_next_job,
    finish_job,
    recover_stale_jobs,
    set_progress,
)
from tagbase_server.utils.io_utils import unpack_compressed_binary
from tagbase_server.utils.processing_utils import process_etuff_file

logger = logging.getLogger(__name__)

_POLL_SECONDS = 1


def members_for(source_path: str) -> list[str]:
    if source_path.endswith(".txt"):
        return [source_path]
    unpacked = unpack_compressed_binary(source_path)
    return list(unpacked or [])


def run_job(job: dict) -> None:
    """Ingest every member. The first error fails the job and stops the queue."""
    job_id = str(job["id"])
    members = members_for(job["source_path"])
    if not members:
        raise RuntimeError("archive contained no eTUFF files")
    set_progress(job_id, files_total=len(members), files_done=0)
    for done, member in enumerate(members, start=1):
        process_etuff_file(
            member,
            version=job.get("version"),
            notes=job.get("notes"),
            count_request=False,
        )
        set_progress(job_id, files_total=len(members), files_done=done)
    finish_job(job_id, status="succeeded", error=None)


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
    return True


def process_available() -> int:
    """Run every job that is already queued. Used by tests in this process."""
    recover_stale_jobs()
    ran = 0
    while process_next():
        ran += 1
    return ran


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    logger.info("Ingest worker starting")
    recover_stale_jobs()
    while True:
        if not process_next():
            time.sleep(_POLL_SECONDS)


if __name__ == "__main__":
    main()
