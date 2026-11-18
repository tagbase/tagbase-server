# coding: utf-8

import json
import logging
import threading
import time
from datetime import datetime, timezone
from email.message import Message
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request

import psycopg2
import pytest

from tagbase_server.archives import PreparedIngest
from tagbase_server.ingest_jobs import (
    _CLAIM_SQL,
    _FETCH_SQL,
    DEFAULT_RETENTION_DAYS,
    MISSING_FILE_ERROR,
    RESTART_ERROR,
    LokiQueryError,
    public_job,
    query_job_lines,
    retention_days,
    select_job_lines,
    stale_failures,
)
from tagbase_server.ingest_log import HEARTBEAT_TEXT, current_job_id, heartbeat_while
from tagbase_server.ingest_worker import logger as worker_logger
from tagbase_server.ingest_worker import (
    process_available,
    process_next,
    run_job,
    summary_line,
)
from tagbase_server.models.ingest_job import IngestJob
from tagbase_server.models.ingest_job_log_line import IngestJobLogLine
from tagbase_server.utils import processing_utils as pu
from tagbase_server.utils.processing_utils import _migrate_proc_observations

JOB_A = "11111111-1111-1111-1111-111111111111"
JOB_B = "22222222-2222-2222-2222-222222222222"


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
        path,
        version=None,
        notes=None,
        count_request=True,
        submission_name=None,
        stats=None,
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


def _loki_payload():
    return {
        "status": "success",
        "data": {
            "resultType": "streams",
            "result": [
                {
                    "stream": {"service_name": "tagbase_server"},
                    "values": [
                        [
                            "200",
                            (
                                "Built Pandas DF from 3 records. "
                                f"Time elapsed: 1 second(s) job_id={JOB_A}"
                            ),
                            {"job_id": JOB_A},
                        ],
                        [
                            "100",
                            f"Processing etuff file: a.txt job_id={JOB_A}",
                            {"job_id": JOB_A},
                        ],
                        [
                            "300",
                            f"Processing etuff file: b.txt job_id={JOB_B}",
                            {"job_id": JOB_B},
                        ],
                        ["400", "gunicorn access line", {}],
                    ],
                }
            ],
        },
    }


class _LokiResponse:
    def __init__(self, payload=None, raw=None):
        self._raw = raw if raw is not None else json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, size=-1):
        if size is None or size < 0:
            size = len(self._raw)
        chunk, self._raw = self._raw[:size], self._raw[size:]
        return chunk


def _job_row(**extra):
    row = {
        "id": JOB_A,
        "status": "running",
        "files_done": 0,
        "error": None,
        "files_total": 1,
    }
    row.update(extra)
    return row


def test_public_job_returns_only_this_jobs_lines(monkeypatch):
    seen = []

    def fake_open(req, timeout=2):
        assert isinstance(req, Request)
        seen.append(req.full_url)
        return _LokiResponse(_loki_payload())

    monkeypatch.setattr("tagbase_server.ingest_jobs.urlopen", fake_open)
    job = public_job(
        {
            "id": JOB_A,
            "status": "running",
            "files_done": 0,
            "error": None,
            "files_total": 1,
        }
    )

    assert job["log_available"] is True
    assert [line["text"] for line in job["lines"]] == [
        f"Processing etuff file: a.txt job_id={JOB_A}",
        "Built Pandas DF from 3 records. Time elapsed: 1 second(s) " f"job_id={JOB_A}",
    ]
    assert all(JOB_B not in line["text"] for line in job["lines"])
    assert job["lines"][0]["time"] == "1970-01-01T00:00:00.000+00:00"
    assert JOB_A in seen[0]
    assert JOB_B not in seen[0]


def test_line_time_is_utc_to_the_millisecond():
    payload = {
        "data": {
            "result": [
                {
                    "values": [
                        [
                            "1794158668105532416",
                            f"Processing etuff file: a.txt job_id={JOB_A}",
                            {"job_id": JOB_A},
                        ]
                    ]
                }
            ]
        }
    }

    (line,) = select_job_lines(payload, JOB_A)
    assert line["time"] == "2026-11-08T17:24:28.105+00:00"


def test_public_job_reports_log_unavailable_when_loki_fails():
    def fail(_job_id, _since):
        raise LokiQueryError("down")

    job = public_job(
        {
            "id": JOB_A,
            "status": "running",
            "files_done": 0,
            "error": None,
            "files_total": 1,
        },
        line_source=fail,
    )

    assert job["log_available"] is False
    assert job["lines"] == []
    assert job["status"] == "running"


def test_query_job_lines_rejects_a_non_uuid():
    with pytest.raises(LokiQueryError):
        query_job_lines("job-1")


def test_run_job_logs_file_counter_for_a_zip(caplog):
    caplog.set_level(logging.INFO, logger="tagbase_server.ingest_worker")
    job = {
        "id": "job-1",
        "source_path": "/tmp/archive.zip",
        "version": None,
        "notes": None,
    }
    prepared = PreparedIngest(
        files=["/tmp/staged-a", "/tmp/staged-b"],
        workspace=None,
        names=["a.txt", "b.txt"],
    )
    with (
        patch("tagbase_server.ingest_worker.materialize", return_value=prepared),
        patch("tagbase_server.ingest_worker.process_etuff_file"),
        patch("tagbase_server.ingest_worker.set_progress"),
    ):
        run_job(job)

    assert "ingest.file index=1 total=2 member=a.txt" in caplog.text
    assert "ingest.file index=2 total=2 member=b.txt" in caplog.text
    assert "job_id=job-1" in caplog.text


def test_run_job_omits_file_counter_for_one_file(caplog):
    caplog.set_level(logging.INFO, logger="tagbase_server.ingest_worker")
    job = {
        "id": "job-1",
        "source_path": "/tmp/one.txt",
        "filename": "one.txt",
        "version": None,
        "notes": None,
    }
    prepared = PreparedIngest(
        files=["/tmp/staged-a"],
        workspace=None,
        names=["one.txt"],
    )
    with (
        patch("tagbase_server.ingest_worker.materialize", return_value=prepared),
        patch("tagbase_server.ingest_worker.process_etuff_file"),
        patch("tagbase_server.ingest_worker.set_progress"),
    ):
        run_job(job)

    assert "ingest.file" not in caplog.text


def test_query_reads_the_most_recent_lines_since_the_job_was_created(monkeypatch):
    seen = []

    def fake_open(req, timeout=2):
        seen.append(req.full_url)
        return _LokiResponse(_loki_payload())

    monkeypatch.setattr("tagbase_server.ingest_jobs.urlopen", fake_open)
    created = datetime(2026, 11, 8, 17, 0, tzinfo=timezone.utc)
    public_job(_job_row(created_at=created))

    params = parse_qs(urlparse(seen[0]).query)
    assert params["direction"] == ["backward"]
    assert params["limit"] == ["500"]
    assert params["start"] == [str(int(created.timestamp()) - 60)]
    assert params["query"] == [f'{{service_name="tagbase_server"}} |= "job_id={JOB_A}"']


def test_select_keeps_the_most_recent_500_oldest_first():
    values = [[str(n), f"line {n} job_id={JOB_A}"] for n in range(600, 0, -1)]
    payload = {"data": {"result": [{"values": values}]}}

    lines = select_job_lines(payload, JOB_A)

    assert len(lines) == 500
    assert lines[0]["text"] == f"line 101 job_id={JOB_A}"
    assert lines[-1]["text"] == f"line 600 job_id={JOB_A}"


def _http_error(*_args, **_kwargs):
    raise HTTPError("http://loki", 500, "boom", Message(), None)


def _timeout(*_args, **_kwargs):
    raise TimeoutError("timed out")


@pytest.mark.parametrize(
    "opener",
    [
        _http_error,
        _timeout,
        lambda *_a, **_k: _LokiResponse(raw=b"not json"),
        lambda *_a, **_k: _LokiResponse(raw=b"\xff\xfe\xfa"),
        lambda *_a, **_k: _LokiResponse(raw=b"[1, 2]"),
        lambda *_a, **_k: _LokiResponse({"status": "error"}),
        lambda *_a, **_k: _LokiResponse(
            {
                "status": "success",
                "data": {"result": [{"values": [["soon", f"x job_id={JOB_A}"]]}]},
            }
        ),
    ],
    ids=[
        "non-200",
        "timeout",
        "bad-json",
        "bad-bytes",
        "not-an-object",
        "loki-error",
        "bad-timestamp",
    ],
)
def test_any_loki_failure_reports_log_unavailable(monkeypatch, opener):
    monkeypatch.setattr("tagbase_server.ingest_jobs.urlopen", opener)

    job = public_job(_job_row())

    assert job["log_available"] is False
    assert job["lines"] == []


def test_loki_read_stops_at_its_time_budget(monkeypatch):
    monkeypatch.setattr("tagbase_server.ingest_jobs._LOKI_TIMEOUT_SECONDS", -1)
    monkeypatch.setattr(
        "tagbase_server.ingest_jobs.urlopen",
        lambda *_a, **_k: _LokiResponse(_loki_payload()),
    )

    with pytest.raises(LokiQueryError, match="time budget"):
        query_job_lines(JOB_A)


def test_heartbeat_logs_job_tagged_lines_until_stopped(caplog):
    caplog.set_level(logging.INFO, logger="tagbase_server.ingest_log")
    stop = threading.Event()
    thread = threading.Thread(
        target=heartbeat_while,
        args=(stop, time.perf_counter(), JOB_A, 0.01),
    )
    thread.start()
    time.sleep(0.1)
    stop.set()
    thread.join(timeout=1)

    beats = [r.getMessage() for r in caplog.records if HEARTBEAT_TEXT in r.getMessage()]
    assert len(beats) >= 2
    assert all("elapsed=" in beat and f"job_id={JOB_A}" in beat for beat in beats)
    assert not thread.is_alive()
    assert current_job_id.get() is None


def _heartbeats_alive():
    return [t for t in threading.enumerate() if t.name == "ingest-heartbeat"]


@pytest.mark.parametrize("call_fails", [False, True], ids=["call-ok", "call-raises"])
def test_heartbeat_runs_during_the_call_and_stops_after_it(
    monkeypatch, caplog, call_fails
):
    monkeypatch.setenv("INGEST_HEARTBEAT_SECONDS", "0.01")
    caplog.set_level(logging.INFO, logger="tagbase_server.ingest_log")
    cur = MagicMock()

    def blocked_call(sql, _params=None):
        if sql.startswith("CALL"):
            time.sleep(0.1)
            if call_fails:
                raise psycopg2.DatabaseError("call failed")

    cur.execute.side_effect = blocked_call
    conn = MagicMock(notices=[])
    token = current_job_id.set(JOB_A)
    try:
        result = _migrate_proc_observations(cur, conn, MagicMock(), 7, False)
    finally:
        current_job_id.reset(token)

    assert (result is False) is call_fails
    assert HEARTBEAT_TEXT in caplog.text
    assert f"job_id={JOB_A}" in caplog.text
    time.sleep(0.05)
    assert _heartbeats_alive() == []


def test_tagging_covers_every_module_logger(caplog):
    caplog.set_level(logging.INFO, logger="tagbase_server.archives")
    token = current_job_id.set(JOB_A)
    try:
        logging.getLogger("tagbase_server.archives").info("Extracting archive")
    finally:
        current_job_id.reset(token)

    assert f"Extracting archive job_id={JOB_A}" in caplog.text


def test_failed_job_line_is_tagged(caplog):
    caplog.set_level(logging.ERROR, logger="tagbase_server.ingest_worker")
    job = {"id": JOB_A, "source_path": "/tmp/one.txt", "filename": "one.txt"}
    with (
        patch("tagbase_server.ingest_worker.claim_next_job", return_value=job),
        patch("tagbase_server.ingest_worker.run_job", side_effect=RuntimeError("x")),
        patch("tagbase_server.ingest_worker.finish_job"),
    ):
        process_next()

    assert f"Ingest job {JOB_A} failed job_id={JOB_A}" in caplog.text
    assert current_job_id.get() is None


def test_a_bad_format_string_does_not_raise_into_ingest(caplog):
    caplog.set_level(logging.INFO, logger="tagbase_server.ingest_worker")
    token = current_job_id.set(JOB_A)
    try:
        worker_logger.info("rows %s of %s", 1)
    finally:
        current_job_id.reset(token)

    assert f"job_id={JOB_A}" in caplog.text


def test_job_lines_cap_at_500_in_the_model():
    line = IngestJobLogLine()
    line.time = datetime(2026, 11, 8, tzinfo=timezone.utc)
    line.text = "Traceback (most recent call last):\n  File x"
    job = IngestJob()
    job.lines = [line] * 500
    with pytest.raises(ValueError, match="500"):
        job.lines = [line] * 501


def test_job_filter_leaves_lines_alone_without_a_job(caplog):
    caplog.set_level(logging.INFO, logger="tagbase_server.ingest_worker")
    worker_logger.info("Processing etuff file: a.txt")
    assert "job_id=" not in caplog.text


def _mock_connection(mock_connect):
    conn = MagicMock()
    mock_connect.return_value = conn
    conn.__enter__.return_value = conn
    conn.cursor.return_value.__enter__.return_value = MagicMock()
    return conn


@patch("tagbase_server.utils.processing_utils.detect_duplicate_file", return_value=True)
@patch(
    "tagbase_server.utils.processing_utils._compute_submission_hashes",
    return_value=("c", "m", "f"),
)
@patch(
    "tagbase_server.utils.processing_utils.get_dataset_properties",
    return_value=("i", "s", "p", "pl", 1, ["line"], [":a = 1"], 0),
)
@patch("tagbase_server.utils.processing_utils.connect")
def test_a_duplicate_file_reports_the_duplicate_outcome(mock_connect, *_mocks):
    _mock_connection(mock_connect)
    stats = {}

    assert pu.process_etuff_file("f.txt", count_request=False, stats=stats) == 1

    assert stats == {"outcome": "duplicate", "skipped_lines": 0}


def _build_with_skips(*args):
    args[-1]["skipped_lines"] = 2
    return [[timezone.utc, 1, "1", 3, 2]], 1


@patch(
    "tagbase_server.utils.processing_utils._migrate_proc_observations", return_value=0.1
)
@patch("tagbase_server.utils.processing_utils._dataframe_to_buffer")
@patch(
    "tagbase_server.utils.processing_utils._build_proc_observations",
    side_effect=_build_with_skips,
)
@patch("tagbase_server.utils.processing_utils.insert_metadata")
@patch(
    "tagbase_server.utils.processing_utils.is_only_metadata_change", return_value=False
)
@patch("tagbase_server.utils.processing_utils.process_global_attributes_metadata")
@patch("tagbase_server.utils.processing_utils.insert_new_submission", return_value=3)
@patch("tagbase_server.utils.processing_utils.get_submission_id", return_value=None)
@patch("tagbase_server.utils.processing_utils.get_tag_id", return_value=2)
@patch("tagbase_server.utils.processing_utils.get_dataset_id", return_value=1)
@patch(
    "tagbase_server.utils.processing_utils.detect_duplicate_file", return_value=False
)
@patch(
    "tagbase_server.utils.processing_utils._compute_submission_hashes",
    return_value=("c", "m", "f"),
)
@patch(
    "tagbase_server.utils.processing_utils.get_dataset_properties",
    return_value=("i", "s", "p", "pl", 1, ["line"], [":a = 1"], 0),
)
@patch("tagbase_server.utils.processing_utils.connect")
def test_an_ingested_file_reports_its_skipped_lines(mock_connect, *_mocks):
    _mock_connection(mock_connect)
    stats = {}

    assert pu.process_etuff_file("f.txt", count_request=False, stats=stats) is None

    assert stats == {"outcome": "ingested", "skipped_lines": 2}


def test_build_rows_counts_lines_without_a_datetime():
    lines = [
        '"2020-01-01 00:00:00",1,5.0,depth\n',
        ",1,6.0,depth\n",
        ",1,7.0,depth\n",
    ]
    timings = {}
    with patch(
        "tagbase_server.utils.processing_utils._resolve_variable_id", return_value=1
    ):
        rows, count = pu._build_proc_observations(
            MagicMock(), MagicMock(), lines, "f.txt", 3, 2, timings
        )

    assert count == 1
    assert timings["skipped_lines"] == 2


def test_run_job_logs_a_job_tagged_summary_last(caplog):
    caplog.set_level(logging.INFO, logger="tagbase_server.ingest_worker")
    job = {"id": JOB_A, "source_path": "/tmp/archive.zip", "filename": "archive.zip"}
    outcomes = iter(
        [
            {"outcome": "ingested", "skipped_lines": 2},
            {"outcome": "duplicate", "skipped_lines": 0},
        ]
    )

    def _ingest(*_args, stats=None, **_kwargs):
        stats.update(next(outcomes))

    prepared = PreparedIngest(
        files=["/tmp/staged-a", "/tmp/staged-b"],
        workspace=None,
        names=["a.txt", "b.txt"],
    )
    with (
        patch("tagbase_server.ingest_worker.materialize", return_value=prepared),
        patch("tagbase_server.ingest_worker.process_etuff_file", side_effect=_ingest),
        patch("tagbase_server.ingest_worker.set_progress"),
    ):
        run_job(job)

    last = caplog.records[-1].getMessage()
    assert last.startswith(
        "ingest.summary files=2 loaded=1 metadata_only=0 duplicates=1 "
        "skipped_lines=2 seconds="
    )
    assert last.endswith(f"job_id={JOB_A}")


def test_summary_counts_nothing_for_unknown_outcomes():
    assert summary_line(1, [{}], 0.123) == (
        "ingest.summary files=1 loaded=0 metadata_only=0 duplicates=0 "
        "skipped_lines=0 seconds=0.12"
    )


def _no_lines(*_args):
    return []


def test_queue_position_is_only_reported_while_queued():
    queued = public_job(
        _job_row(status="queued", queue_position=3), line_source=_no_lines
    )
    running = public_job(
        _job_row(status="running", queue_position=None), line_source=_no_lines
    )
    stale = public_job(
        _job_row(status="succeeded", queue_position=2), line_source=_no_lines
    )

    assert queued["queue_position"] == 3
    assert "queue_position" not in running
    assert "queue_position" not in stale


def test_queue_position_counts_the_running_job_and_earlier_queued_jobs():
    assert "q.status = 'running'" in _FETCH_SQL
    assert "(q.created_at, q.updated_at) < (j.created_at, j.updated_at)" in _FETCH_SQL


def test_model_rejects_a_negative_queue_position():
    job = IngestJob()
    job.queue_position = 0
    with pytest.raises(ValueError, match="greater than or equal to `0`"):
        job.queue_position = -1
