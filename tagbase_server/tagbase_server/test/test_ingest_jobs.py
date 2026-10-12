# coding: utf-8

from unittest.mock import patch

import pytest

from tagbase_server.archives import PreparedIngest
from tagbase_server.ingest_jobs import (
    _CLAIM_SQL,
    DEFAULT_RETENTION_DAYS,
    MISSING_FILE_ERROR,
    RESTART_ERROR,
    retention_days,
    stale_failures,
)
from tagbase_server.ingest_worker import process_available, process_next, run_job


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

    def _ingest(
        path, version=None, notes=None, count_request=True, submission_name=None
    ):
        seen.append((path, count_request, submission_name))
        if submission_name == "b.txt":
            raise RuntimeError("bad member")

    prepared = PreparedIngest(
        files=["/tmp/staged-a", "/tmp/staged-b", "/tmp/staged-c"],
        workspace=None,
        names=["a.txt", "b.txt", "c.txt"],
    )
    with (
        patch("tagbase_server.ingest_worker.materialize", return_value=prepared),
        patch("tagbase_server.ingest_worker.process_etuff_file", side_effect=_ingest),
        patch("tagbase_server.ingest_worker.set_progress") as progress,
        patch("tagbase_server.ingest_worker.finish_job") as finish,
    ):
        with pytest.raises(RuntimeError, match="bad member"):
            run_job(job)

    assert [path for path, _counted, _name in seen] == [
        "/tmp/staged-a",
        "/tmp/staged-b",
    ]
    assert [name for _path, _counted, name in seen] == ["a.txt", "b.txt"]
    assert all(counted is False for _path, counted, _name in seen)
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


def test_claim_orders_by_created_at_then_updated_at():
    assert "ORDER BY created_at, updated_at" in _CLAIM_SQL
    assert "FOR UPDATE SKIP LOCKED" in _CLAIM_SQL


def test_retention_defaults_to_thirty_days(monkeypatch):
    monkeypatch.delenv("INGEST_JOB_RETENTION_DAYS", raising=False)
    assert DEFAULT_RETENTION_DAYS == 30
    assert retention_days() == 30


def test_process_available_runs_two_queued_jobs():
    jobs = iter(
        [
            {"id": "job-a", "source_path": "/tmp/a.txt", "filename": "a.txt"},
            {"id": "job-b", "source_path": "/tmp/b.txt", "filename": "b.txt"},
        ]
    )

    def claim():
        return next(jobs, None)

    with (
        patch("tagbase_server.ingest_worker.recover_stale_jobs"),
        patch("tagbase_server.ingest_worker.claim_next_job", side_effect=claim),
        patch("tagbase_server.ingest_worker.run_job"),
        patch("tagbase_server.ingest_worker.finish_job") as finish,
    ):
        assert process_available() == 2

    assert [call.kwargs["status"] for call in finish.call_args_list] == [
        "succeeded",
        "succeeded",
    ]


def test_process_next_deletes_the_staged_file_after_success(tmp_path):
    source = tmp_path / "one.txt"
    source.write_text("etuff", encoding="utf-8")
    job = {"id": "job-3", "source_path": str(source), "filename": "one.txt"}
    claims = iter([job])
    with (
        patch(
            "tagbase_server.ingest_worker.claim_next_job",
            side_effect=lambda: next(claims, None),
        ),
        patch("tagbase_server.ingest_worker.run_job"),
        patch("tagbase_server.ingest_worker.finish_job") as finish,
    ):
        assert process_next() is True
    finish.assert_called_once_with("job-3", status="succeeded", error=None)
    assert not source.exists()
