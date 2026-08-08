# coding: utf-8

from unittest import mock

import pytest

from tagbase_server.utils import db_utils


def test_connect_reraises_when_schema_missing(monkeypatch):
    monkeypatch.setattr(db_utils, "_SCHEMA_READY", False)
    fake_conn = mock.Mock()
    cur = mock.Mock()
    cur.fetchone.return_value = (None,)
    fake_conn.cursor.return_value.__enter__ = mock.Mock(return_value=cur)
    fake_conn.cursor.return_value.__exit__ = mock.Mock(return_value=False)

    monkeypatch.setattr(db_utils.psycopg2, "connect", mock.Mock(return_value=fake_conn))
    monkeypatch.setattr(db_utils, "record_db_error", mock.Mock())

    with pytest.raises(RuntimeError, match="submission"):
        db_utils.connect()
    db_utils.record_db_error.assert_called_with("schema")


def test_assert_schema_ready_raises_when_missing(monkeypatch):
    monkeypatch.setattr(db_utils, "_SCHEMA_READY", False)
    cur = mock.Mock()
    cur.fetchone.return_value = (None,)
    conn = mock.Mock()
    conn.cursor.return_value.__enter__ = mock.Mock(return_value=cur)
    conn.cursor.return_value.__exit__ = mock.Mock(return_value=False)

    with pytest.raises(RuntimeError, match="submission"):
        db_utils.assert_schema_ready(conn)
    assert db_utils._SCHEMA_READY is False


def test_assert_schema_ready_caches_success(monkeypatch):
    monkeypatch.setattr(db_utils, "_SCHEMA_READY", False)
    cur = mock.Mock()
    cur.fetchone.return_value = ("submission",)
    conn = mock.Mock()
    conn.cursor.return_value.__enter__ = mock.Mock(return_value=cur)
    conn.cursor.return_value.__exit__ = mock.Mock(return_value=False)

    db_utils.assert_schema_ready(conn)
    assert db_utils._SCHEMA_READY is True
    conn.rollback.assert_called_once()
    db_utils.assert_schema_ready(conn)
    assert conn.cursor.call_count == 1
    assert conn.rollback.call_count == 1
