# coding: utf-8

import importlib
from unittest import mock

import pytest

from tagbase_server.utils import db_utils
from tagbase_server.utils import slack_utils as slack_utils_mod


def _reload_slack_utils():
    """Undo conftest mute_slack Mock and pick up a fresh module."""
    return importlib.reload(slack_utils_mod)


def test_post_msg_skips_when_token_missing(monkeypatch):
    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)
    su = _reload_slack_utils()
    with mock.patch.object(su, "WebClient") as mock_web_client:
        su.post_msg("hello")
        mock_web_client.assert_not_called()


def test_post_msg_skips_when_token_not_bot(monkeypatch):
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxp-not-a-bot")
    su = _reload_slack_utils()
    with mock.patch.object(su, "WebClient") as mock_web_client:
        su.post_msg("hello")
        mock_web_client.assert_not_called()


def test_post_msg_posts_with_bot_token(monkeypatch):
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-valid-token")
    su = _reload_slack_utils()
    with mock.patch.object(su, "WebClient") as mock_web_client:
        client = mock_web_client.return_value
        su.post_msg("hello")
        mock_web_client.assert_called_once_with(token="xoxb-valid-token")
        client.chat_postMessage.assert_called_once()
        _args, kwargs = client.chat_postMessage.call_args
        assert kwargs["channel"] == "metadata_ops"
        assert "hello" in kwargs["text"]


def test_post_msg_handles_slack_api_and_generic_errors(monkeypatch):
    from slack_sdk.errors import SlackApiError

    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-valid-token")
    su = _reload_slack_utils()
    client = mock.Mock()
    with mock.patch.object(su, "WebClient", return_value=client):
        client.chat_postMessage.side_effect = SlackApiError(
            "fail", response=mock.Mock()
        )
        su.post_msg("api-fail")
        client.chat_postMessage.side_effect = RuntimeError("boom")
        su.post_msg("generic-fail")


def test_connect_reraises_when_schema_missing(monkeypatch):
    db_utils._SCHEMA_READY = False
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


def test_assert_schema_ready_raises_when_missing():
    db_utils._SCHEMA_READY = False
    cur = mock.Mock()
    cur.fetchone.return_value = (None,)
    conn = mock.Mock()
    conn.cursor.return_value.__enter__ = mock.Mock(return_value=cur)
    conn.cursor.return_value.__exit__ = mock.Mock(return_value=False)

    with pytest.raises(RuntimeError, match="submission"):
        db_utils.assert_schema_ready(conn)
    assert db_utils._SCHEMA_READY is False


def test_assert_schema_ready_caches_success():
    db_utils._SCHEMA_READY = False
    cur = mock.Mock()
    cur.fetchone.return_value = ("submission",)
    conn = mock.Mock()
    conn.cursor.return_value.__enter__ = mock.Mock(return_value=cur)
    conn.cursor.return_value.__exit__ = mock.Mock(return_value=False)

    db_utils.assert_schema_ready(conn)
    assert db_utils._SCHEMA_READY is True
    db_utils.assert_schema_ready(conn)
    assert conn.cursor.call_count == 1
