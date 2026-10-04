# coding: utf-8

from unittest.mock import patch

import pytest

from tagbase_server.ingest_jobs import MISSING_FILE_ERROR, RESTART_ERROR, stale_failures
from tagbase_server.ingest_worker import process_next, run_job


def test_stale_failures_marks_running_and_missing_queued_files():
    jobs = [
        {"id": "running-1", "status": "running", "source_path": "/tmp/a.zip"},
        {"id": "queued-gone", "status": "queued", "source_path": "/tmp/missing.zip"},
        {"id": "queued-kept", "status": "queued", "source_path": "/tmp/kept.zip"},
        {"id": "done", "status": "succeeded", "source_path": "/tmp/done.zip"},
    ]

    failed = stale_failures(jobs, lambda path: path == "/tmp/kept.zip")

    assert failed == [
        ("running-1", RESTART_ERROR),
        ("queued-gone", MISSING_FILE_ERROR),
    ]


def test_run_job_stops_on_the_first_member_error():
    job = {
        "id": "job-1",
        "source_path": "/tmp/archive.zip",
        "version": "1",
        "notes": None,
    }
    seen = []

    def _ingest(path, version=None, notes=None, count_request=True):
        seen.append((path, count_request))
        if path.endswith("b.txt"):
            raise RuntimeError("bad member")

    with (
        patch(
            "tagbase_server.ingest_worker.members_for",
            return_value=["/tmp/a.txt", "/tmp/b.txt", "/tmp/c.txt"],
        ),
        patch("tagbase_server.ingest_worker.process_etuff_file", side_effect=_ingest),
        patch("tagbase_server.ingest_worker.set_progress") as progress,
        patch("tagbase_server.ingest_worker.finish_job") as finish,
    ):
        with pytest.raises(RuntimeError, match="bad member"):
            run_job(job)

    assert [path for path, _counted in seen] == ["/tmp/a.txt", "/tmp/b.txt"]
    assert all(counted is False for _path, counted in seen)
    finish.assert_not_called()
    assert progress.call_args_list[-1].kwargs["files_done"] == 1


def test_process_next_fails_the_job_and_keeps_the_queue_moving():
    job = {"id": "job-2", "source_path": "/tmp/one.txt", "version": None, "notes": None}
    with (
        patch("tagbase_server.ingest_worker.claim_next_job", return_value=job),
        patch(
            "tagbase_server.ingest_worker.run_job",
            side_effect=RuntimeError("stopped"),
        ),
        patch("tagbase_server.ingest_worker.finish_job") as finish,
    ):
        assert process_next() is True

    finish.assert_called_once_with("job-2", status="failed", error="stopped")
