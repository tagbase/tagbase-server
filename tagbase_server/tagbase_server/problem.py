"""RFC7807 problem+json helpers and Flask error handlers."""

from __future__ import annotations

import logging
import uuid

from flask import jsonify, request
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

PROBLEM_JSON = "application/problem+json"
JSON_HEADERS = {"Content-Type": "application/json"}
TYPE_BAD_REQUEST = "urn:tagbase:problem:bad-request"
TYPE_INTERNAL = "urn:tagbase:problem:internal-error"
TYPE_HTTP = "urn:tagbase:problem:http-error"


def as_json(body, status=200):
    """Return a Connexion-friendly JSON success tuple.

    Required when an operation documents both application/json and
    application/problem+json response media types.
    """
    return body, status, JSON_HEADERS


class TagbaseClientError(Exception):
    """Client-fixable failure mapped to HTTP 400 problem+json."""

    def __init__(
        self,
        detail,
        title="Bad Request",
        type_=TYPE_BAD_REQUEST,
        status=400,
    ):
        super().__init__(detail)
        self.detail = detail
        self.title = title
        self.type = type_
        self.status = status


def new_trace_id():
    return str(uuid.uuid4())


def problem_body(
    status,
    title,
    detail,
    type_,
    trace_id=None,
    instance=None,
):
    body = {
        "type": type_,
        "title": title,
        "status": status,
        "detail": detail,
        "traceId": trace_id or new_trace_id(),
    }
    if instance is not None:
        body["instance"] = instance
    elif request:
        body["instance"] = request.path
    return body


def problem_response(
    status,
    title,
    detail,
    type_,
    trace_id=None,
    instance=None,
):
    body = problem_body(
        status=status,
        title=title,
        detail=detail,
        type_=type_,
        trace_id=trace_id,
        instance=instance,
    )
    response = jsonify(body)
    response.status_code = status
    response.mimetype = PROBLEM_JSON
    return response


def register_problem_handlers(flask_app):
    """Register handlers so public errors are application/problem+json."""

    @flask_app.errorhandler(TagbaseClientError)
    def _handle_client_error(exc):
        trace_id = new_trace_id()
        logger.warning(
            "Client error [%s]: %s",
            trace_id,
            exc.detail,
        )
        return problem_response(
            status=exc.status,
            title=exc.title,
            detail=exc.detail,
            type_=exc.type,
            trace_id=trace_id,
        )

    @flask_app.errorhandler(HTTPException)
    def _handle_http_exception(exc):
        trace_id = new_trace_id()
        detail = exc.description or exc.name
        return problem_response(
            status=exc.code or 500,
            title=exc.name,
            detail=detail,
            type_=TYPE_HTTP,
            trace_id=trace_id,
        )

    @flask_app.errorhandler(Exception)
    def _handle_unexpected(exc):
        if isinstance(exc, TagbaseClientError):
            return _handle_client_error(exc)
        if isinstance(exc, HTTPException):
            return _handle_http_exception(exc)
        trace_id = new_trace_id()
        logger.exception("Unhandled error [%s]", trace_id)
        return problem_response(
            status=500,
            title="Internal Server Error",
            detail=(
                "An unexpected error occurred while processing the request. "
                f"Reference traceId={trace_id}."
            ),
            type_=TYPE_INTERNAL,
            trace_id=trace_id,
        )
