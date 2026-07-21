# coding: utf-8

"""Nginx Basic Auth + TLS proxy stack tests.

Requires: docker compose -f docker-compose.test.yml --profile stack up -d
Env (defaults match compose file):
  TAGBASE_STACK_BASE=https://localhost:443
  TAGBASE_STACK_USER=testuser
  TAGBASE_STACK_PASS=testpass
"""

import os

import httpx
import pytest

pytestmark = pytest.mark.stack

API = "/tagbase/api/v0.14.0"


def _base():
    return os.getenv("TAGBASE_STACK_BASE", "https://localhost:443").rstrip("/")


def _auth():
    return (
        os.getenv("TAGBASE_STACK_USER", "testuser"),
        os.getenv("TAGBASE_STACK_PASS", "testpass"),
    )


def _stack_up():
    try:
        with httpx.Client(verify=False, timeout=2.0) as client:
            client.get(_base() + "/", auth=_auth())
        return True
    except Exception:
        return False


@pytest.fixture(scope="module", autouse=True)
def require_stack():
    if not _stack_up():
        pytest.skip(
            "nginx stack not reachable; start docker-compose.test.yml --profile stack"
        )


def test_unauthenticated_api_returns_401():
    with httpx.Client(verify=False, timeout=10.0) as client:
        response = client.get(_base() + f"{API}/tags")
    assert response.status_code == 401
    assert "Basic" in response.headers.get("WWW-Authenticate", "")


def test_wrong_password_returns_401():
    with httpx.Client(verify=False, timeout=10.0) as client:
        response = client.get(
            _base() + f"{API}/tags",
            auth=(_auth()[0], "wrong-password"),
        )
    assert response.status_code == 401


def test_valid_basic_auth_proxies_tags_api():
    with httpx.Client(verify=False, timeout=30.0) as client:
        response = client.get(_base() + f"{API}/tags", auth=_auth())
    assert response.status_code == 200
    body = response.json()
    assert "count" in body
    assert "tags" in body


def test_http_port_redirects_to_https():
    with httpx.Client(verify=False, timeout=10.0, follow_redirects=False) as client:
        response = client.get("http://localhost:81/tagbase/api/v0.14.0/tags")
    assert response.status_code in (301, 302)
    location = response.headers.get("Location", "")
    assert location.startswith("https://")


def test_docs_with_auth_reaches_upstream():
    with httpx.Client(verify=False, timeout=30.0) as client:
        response = client.get(_base() + "/docs", auth=_auth())
    assert response.status_code != 401


def test_grafana_health_with_basic_auth_does_not_rechallenge():
    """Nginx Basic Auth must not be forwarded to Grafana (no upstream 401)."""
    with httpx.Client(verify=False, timeout=10.0) as client:
        response = client.get(_base() + "/grafana/api/health", auth=_auth())
    if response.status_code in (502, 503, 504):
        pytest.skip("Grafana not reachable; start with --profile observability")
    assert response.status_code == 200, (
        f"expected 200 from Grafana health, got {response.status_code}: "
        f"{response.text[:200]}"
    )
    assert "invalid username or password" not in response.text.lower()
