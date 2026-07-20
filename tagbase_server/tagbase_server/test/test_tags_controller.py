# coding: utf-8

"""Tags controller unit smoke (no Postgres).

CRUD success paths live under test/integration/test_tags_api.py.
"""

from tagbase_server.test.helpers import API_PREFIX


def test_list_tags_without_postgres_returns_server_error(client):
    response = client.get(
        f"{API_PREFIX}/tags",
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 500
    body = response.json()
    assert body["status"] == 500
    assert body["type"] == "urn:tagbase:problem:internal-error"
    assert "traceId" in body
    assert response.headers["content-type"].startswith("application/problem+json")
