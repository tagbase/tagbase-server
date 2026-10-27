# coding: utf-8

import os
import tempfile
from datetime import timezone
from io import StringIO
from unittest import mock

import pytest

from tagbase_server.__main__ import configure_cors, parse_cors_origins
from tagbase_server.controllers import ingest_controller
from tagbase_server.controllers.ingest_controller import _resolve_ingest_file_type
from tagbase_server.models.base_model_ import Model
from tagbase_server.models.tag_put200 import TagPut200
from tagbase_server.utils import io_utils
from tagbase_server.utils import processing_utils as pu


def test_parse_cors_origins_empty_and_list():
    assert parse_cors_origins("") == []
    assert parse_cors_origins("https://a.example, https://b.example") == [
        "https://a.example",
        "https://b.example",
    ]


def test_configure_cors_skips_when_unset(monkeypatch):
    monkeypatch.delenv("TAGBASE_CORS_ORIGINS", raising=False)
    calls = []

    def fake_cors(*args, **kwargs):
        calls.append((args, kwargs))

    configure_cors(object(), cors_factory=fake_cors)
    assert calls == []


def test_configure_cors_applies_allowlist(monkeypatch):
    monkeypatch.setenv("TAGBASE_CORS_ORIGINS", "https://a.example")
    calls = []

    def fake_cors(*args, **kwargs):
        calls.append((args, kwargs))

    flask_app = object()
    configure_cors(flask_app, cors_factory=fake_cors)
    assert len(calls) == 1
    assert calls[0][0][0] is flask_app
    assert calls[0][1]["resources"]["/*"]["origins"] == ["https://a.example"]


def test_io_utils_uses_tempfile_dir_not_literal_tmp():
    assert io_utils.TEMP_DIR == tempfile.gettempdir()
    source = open(io_utils.__file__, encoding="utf-8").read()
    assert "/tmp/" not in source


def test_url_scheme_prefix_matches_file_and_https():
    assert (
        io_utils._URL_SCHEME_PREFIX.search("file:///data/a.txt").group(0) == "file://"
    )
    assert (
        io_utils._URL_SCHEME_PREFIX.search("https://example.com/a.txt").group(0)
        == "https://example.com"
    )


def test_process_post_input_data_writes_under_temp_dir():
    body = b"hello-etuff"
    path = io_utils.process_post_input_data("sonar-post.txt", body)
    try:
        assert path.startswith(tempfile.gettempdir())
        assert os.path.basename(path) == "sonar-post.txt"
        with open(path, "rb") as handle:
            assert handle.read() == body
    finally:
        if os.path.exists(path):
            os.remove(path)


def test_process_get_input_data_local_file(tmp_path):
    local = tmp_path / "local.txt"
    local.write_text("x", encoding="utf-8")
    result = io_utils.process_get_input_data(f"file://{local}")
    assert result == str(local)


@mock.patch("tagbase_server.utils.io_utils.urlopen")
def test_process_get_input_data_downloads_remote(mock_urlopen, tmp_path):
    mock_urlopen.return_value.read.side_effect = [b"chunk", b""]
    path = io_utils.process_get_input_data("https://example.com/remote.txt")
    try:
        assert path.startswith(tempfile.gettempdir())
        with open(path, "rb") as handle:
            assert handle.read() == b"chunk"
    finally:
        if os.path.exists(path):
            os.remove(path)


def test_resolve_ingest_file_type_defaults_and_rejects():
    assert _resolve_ingest_file_type(None) == "etuff"
    assert _resolve_ingest_file_type("etuff") == "etuff"
    from tagbase_server.problem import TagbaseClientError

    with pytest.raises(TagbaseClientError, match="Unsupported ingest file type"):
        _resolve_ingest_file_type("csv")


@mock.patch("tagbase_server.controllers.ingest_controller.record_ingest_request")
@mock.patch("tagbase_server.controllers.ingest_controller._run_ingest_queue")
@mock.patch("tagbase_server.controllers.ingest_controller.materialize")
@mock.patch("tagbase_server.controllers.ingest_controller.process_get_input_data")
def test_ingest_get_happy_path(mock_get, mock_materialize, mock_queue, mock_record):
    from tagbase_server.archives import PreparedIngest

    mock_get.return_value = "/data/file.txt"
    mock_materialize.return_value = PreparedIngest(
        files=["/data/file.txt"], workspace=None
    )
    result, status, headers = ingest_controller.ingest_get(
        "file:///data/file.txt", type="etuff"
    )
    assert status == 200
    assert headers["Content-Type"] == "application/json"
    assert result.code == "200"
    assert len(result.trace_id) == 32
    mock_queue.assert_called_once()
    mock_record.assert_called_once()
    assert mock_record.call_args.args[0] == "success"


@mock.patch("tagbase_server.controllers.ingest_controller.record_ingest_request")
@mock.patch("tagbase_server.controllers.ingest_controller._run_ingest_queue")
@mock.patch("tagbase_server.controllers.ingest_controller.materialize")
@mock.patch("tagbase_server.controllers.ingest_controller.process_post_input_data")
def test_ingest_post_archive_path(mock_post, mock_materialize, mock_queue, mock_record):
    from tagbase_server.archives import PreparedIngest

    mock_post.return_value = "/tmp/bundle.zip"
    mock_materialize.return_value = PreparedIngest(
        files=["/tmp/inner.txt"], workspace=None
    )
    result, status, headers = ingest_controller.ingest_post(
        "bundle.zip", b"x", type=None
    )
    assert status == 200
    assert headers["Content-Type"] == "application/json"
    assert result.code == "200"
    mock_queue.assert_called_once()
    mock_record.assert_called_once()


def test_processing_utils_has_no_pytz():
    source = open(pu.__file__, encoding="utf-8").read()
    assert "pytz" not in source
    assert "timezone.utc" in source
    assert timezone.utc is not None


def test_resolve_variable_id_cache_and_lookup():
    cur = mock.Mock()
    conn = mock.Mock()
    lookup = {"temp": 9}
    assert pu._resolve_variable_id(cur, conn, "temp", [], lookup) == 9

    cur.fetchone.return_value = (42,)
    lookup = {}
    assert (
        pu._resolve_variable_id(cur, conn, "lat", ["", "", "", "lat", "deg"], lookup)
        == 42
    )
    assert lookup["lat"] == 42


def test_resolve_variable_id_insert_and_exception():
    cur = mock.Mock()
    conn = mock.Mock()
    # lookup miss, INSERT raises, then fallback SELECT
    cur.fetchone.side_effect = [None, (7,)]
    cur.execute.side_effect = [None, Exception("dup"), None]
    lookup = {}
    assert (
        pu._resolve_variable_id(cur, conn, "lon", ["", "", "", "lon", "deg"], lookup)
        == 7
    )
    conn.rollback.assert_called_once()


def test_resolve_variable_id_insert_returning():
    cur = mock.Mock()
    conn = mock.Mock()
    cur.fetchone.side_effect = [None, (11,)]
    lookup = {}
    assert (
        pu._resolve_variable_id(cur, conn, "depth", ["", "", "", "depth", "m"], lookup)
        == 11
    )
    assert lookup["depth"] == 11


def test_dataframe_to_buffer_and_migrate():
    proc_obs = [[timezone.utc, 1, "1.0", 2, 3]]
    buffer = pu._dataframe_to_buffer(proc_obs, 1)
    assert isinstance(buffer, StringIO)

    cur = mock.Mock()
    conn = mock.Mock()
    elapsed = pu._migrate_proc_observations(cur, conn, buffer, 9, 1)
    assert isinstance(elapsed, float)
    cur.copy_from.assert_called_once()

    cur.copy_from.side_effect = Exception("db")
    assert pu._migrate_proc_observations(cur, conn, buffer, 9, 0) is False
    conn.rollback.assert_called()


def test_migrate_records_procedure_steps():
    cur = mock.Mock()
    conn = mock.Mock()
    conn.notices = ["stale\n"]

    def call(*_args):
        conn.notices.extend(
            [
                'NOTICE:  table "migration_position_match" does not exist, skipping\n',
                'NOTICE:  tagbase.step {"step" : "time_series", "ms" : 5, "rows" : 3}\n',
                "NOTICE:  tagbase.step {not json}\n",
            ]
        )

    cur.execute.side_effect = call
    timings = {}
    pu._migrate_proc_observations(cur, conn, StringIO("x"), 9, 0, timings)
    assert set(timings) == {"copy", "procedure", "procedure_steps"}
    assert timings["procedure_steps"] == [{"step": "time_series", "ms": 5, "rows": 3}]


def test_migration_steps_from_notices_ignores_non_lists():
    assert pu.migration_steps_from_notices(mock.Mock()) == []


@mock.patch("tagbase_server.utils.processing_utils.get_dataset_properties")
@mock.patch("tagbase_server.utils.processing_utils.compute_file_sha256")
@mock.patch("tagbase_server.utils.processing_utils.make_hash_sha256")
def test_compute_submission_hashes(mock_make, mock_file, mock_props):
    mock_make.side_effect = ["content", "meta"]
    mock_file.return_value = "filehash"
    result = pu._compute_submission_hashes("f.txt", "content", "meta")
    assert result == ("content", "meta", "filehash")


@mock.patch("tagbase_server.utils.processing_utils._migrate_proc_observations")
@mock.patch("tagbase_server.utils.processing_utils._dataframe_to_buffer")
@mock.patch("tagbase_server.utils.processing_utils._build_proc_observations")
@mock.patch("tagbase_server.utils.processing_utils.insert_metadata")
@mock.patch("tagbase_server.utils.processing_utils.is_only_metadata_change")
@mock.patch("tagbase_server.utils.processing_utils.process_global_attributes_metadata")
@mock.patch("tagbase_server.utils.processing_utils.insert_new_submission")
@mock.patch("tagbase_server.utils.processing_utils.get_submission_id")
@mock.patch("tagbase_server.utils.processing_utils.get_tag_id")
@mock.patch("tagbase_server.utils.processing_utils.get_dataset_id")
@mock.patch("tagbase_server.utils.processing_utils.detect_duplicate_file")
@mock.patch("tagbase_server.utils.processing_utils._compute_submission_hashes")
@mock.patch("tagbase_server.utils.processing_utils.get_dataset_properties")
@mock.patch("tagbase_server.utils.processing_utils.connect")
def test_process_etuff_file_full_path(
    mock_connect,
    mock_props,
    mock_hashes,
    mock_dup,
    mock_dataset,
    mock_tag,
    mock_sub,
    mock_insert,
    mock_meta,
    mock_meta_only,
    mock_insert_meta,
    mock_build,
    mock_buffer,
    mock_migrate,
):
    conn = mock.MagicMock()
    cur = mock.MagicMock()
    mock_connect.return_value = conn
    conn.__enter__.return_value = conn
    conn.cursor.return_value.__enter__.return_value = cur
    mock_props.return_value = ("i", "s", "p", "pl", 1, ["line"], [":a = 1"], 0)
    mock_hashes.return_value = (
        "ch",
        "mh",
        "fh",
    )
    mock_dup.return_value = False
    mock_dataset.return_value = 1
    mock_tag.return_value = 2
    mock_sub.return_value = None
    mock_insert.return_value = 3
    mock_meta.return_value = [("3", "1", "v")]
    mock_meta_only.return_value = False
    mock_build.return_value = ([[timezone.utc, 1, "1", 3, 2]], 1)
    mock_buffer.return_value = StringIO("x")
    mock_migrate.return_value = 0.1
    assert (
        pu.process_etuff_file(
            "/tmp/5fb7423d-tagbase-upload-cjz5",
            submission_name="2024BFT07799A.txt",
        )
        is None
    )
    assert mock_props.call_args.args[0] == "/tmp/5fb7423d-tagbase-upload-cjz5"
    assert mock_insert.call_args.args[2] == "2024BFT07799A.txt"


@mock.patch("tagbase_server.utils.processing_utils.connect")
@mock.patch("tagbase_server.utils.processing_utils._compute_submission_hashes")
@mock.patch("tagbase_server.utils.processing_utils.get_dataset_properties")
def test_process_etuff_file_duplicate(mock_hashes, mock_connect, mock_props):
    conn = mock.MagicMock()
    cur = mock.MagicMock()
    mock_connect.return_value = conn
    conn.__enter__.return_value = conn
    conn.cursor.return_value.__enter__.return_value = cur
    mock_props.return_value = ("i", "s", "p", "pl", 1, ["line"], [":a = 1"], 0)
    mock_hashes.return_value = (
        "c",
        "m",
        "f",
    )
    with mock.patch(
        "tagbase_server.utils.processing_utils.detect_duplicate_file",
        return_value=True,
    ):
        assert pu.process_etuff_file("f.txt") == 1


def test_base_model_ne_and_to_dict_branches():
    class Child(Model):
        openapi_types = {"name": str}
        attribute_map = {"name": "name"}

        def __init__(self, name="x"):
            self.name = name

    class Parent(Model):
        openapi_types = {"items": list, "nested": object, "mapping": dict, "plain": str}
        attribute_map = {
            "items": "items",
            "nested": "nested",
            "mapping": "mapping",
            "plain": "plain",
        }

        def __init__(self):
            self.items = [Child("a")]
            self.nested = Child("b")
            self.mapping = {"k": Child("c")}
            self.plain = "p"

    parent = Parent()
    as_dict = parent.to_dict()
    assert as_dict["items"][0]["name"] == "a"
    assert as_dict["nested"]["name"] == "b"
    assert as_dict["mapping"]["k"]["name"] == "c"
    a = TagPut200.from_dict({"code": "200", "message": "a"})
    b = TagPut200.from_dict({"code": "200", "message": "b"})
    assert a != b
    assert not (a != a)
