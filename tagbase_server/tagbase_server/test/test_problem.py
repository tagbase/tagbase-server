# coding: utf-8

"""Unit tests for RFC7807 problem+json helpers and Problem model."""

from werkzeug.exceptions import NotFound

from tagbase_server.models.problem import Problem
from tagbase_server.problem import (
    TYPE_BAD_REQUEST,
    TYPE_HTTP,
    TYPE_INTERNAL,
    TagbaseClientError,
    as_json,
    problem_body,
)


def test_problem_body_includes_required_fields():
    body = problem_body(
        status=400,
        title="Bad Request",
        detail="nope",
        type_=TYPE_BAD_REQUEST,
        trace_id="123e4567-e89b-12d3-a456-426614174000",
        instance="/ingest",
    )
    assert body == {
        "type": TYPE_BAD_REQUEST,
        "title": "Bad Request",
        "status": 400,
        "detail": "nope",
        "trace_id": "123e4567-e89b-12d3-a456-426614174000",
        "instance": "/ingest",
    }


def test_tagbase_client_error_defaults():
    exc = TagbaseClientError("bad input")
    assert exc.status == 400
    assert exc.type == TYPE_BAD_REQUEST
    assert TYPE_INTERNAL.startswith("urn:tagbase:")


def test_as_json_wraps_success_body():
    body, status, headers = as_json({"ok": True}, status=201)
    assert body == {"ok": True}
    assert status == 201
    assert headers["Content-Type"] == "application/json"


def test_problem_model_round_trip():
    problem = Problem(
        type=TYPE_BAD_REQUEST,
        title="Bad Request",
        status=400,
        detail="missing file",
        instance="/tagbase/api/v0.14.0/ingest",
        trace_id="abc-123",
    )
    assert problem.type == TYPE_BAD_REQUEST
    assert problem.title == "Bad Request"
    assert problem.status == 400
    assert problem.detail == "missing file"
    assert problem.instance == "/tagbase/api/v0.14.0/ingest"
    assert problem.trace_id == "abc-123"

    problem.type = TYPE_INTERNAL
    problem.title = "Internal Server Error"
    problem.status = 500
    problem.detail = "boom"
    problem.instance = "/tags"
    problem.trace_id = "def-456"
    assert problem.type == TYPE_INTERNAL
    assert problem.title == "Internal Server Error"
    assert problem.status == 500
    assert problem.detail == "boom"
    assert problem.instance == "/tags"
    assert problem.trace_id == "def-456"

    restored = Problem.from_dict(
        {
            "type": TYPE_HTTP,
            "title": "Not Found",
            "status": 404,
            "detail": "gone",
            "instance": "/missing",
            "trace_id": "ghi-789",
        }
    )
    assert restored.type == TYPE_HTTP
    assert restored.title == "Not Found"
    assert restored.status == 404
    assert restored.detail == "gone"
    assert restored.instance == "/missing"
    assert restored.trace_id == "ghi-789"


def test_problem_handlers_map_http_and_unexpected(app):
    flask_app = app.app

    @flask_app.route("/_test/not-found")
    def _raise_not_found():
        raise NotFound(description="missing resource")

    @flask_app.route("/_test/boom")
    def _raise_unexpected():
        raise RuntimeError("kaboom")

    @flask_app.route("/_test/client")
    def _raise_client():
        raise TagbaseClientError("bad")

    client = flask_app.test_client()

    not_found = client.get("/_test/not-found")
    assert not_found.status_code == 404
    assert not_found.mimetype == "application/problem+json"
    assert not_found.get_json()["type"] == TYPE_HTTP

    boom = client.get("/_test/boom")
    assert boom.status_code == 500
    assert boom.mimetype == "application/problem+json"
    assert boom.get_json()["type"] == TYPE_INTERNAL

    client_err = client.get("/_test/client")
    assert client_err.status_code == 400
    assert client_err.get_json()["type"] == TYPE_BAD_REQUEST
