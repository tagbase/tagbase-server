# coding: utf-8

"""Unit-level ingest controller checks (no Postgres).

Full ingest success paths live under test/integration/.
"""

import shutil
from pathlib import Path

from tagbase_server.test.helpers import API_PREFIX, ETUFF_FIXTURE


def test_ingest_get_rejects_netcdf_ingest_file_type(client):
    dest = Path("/tmp/tb-etuff-unit.txt")
    shutil.copyfile(ETUFF_FIXTURE, dest)
    response = client.get(
        f"{API_PREFIX}/ingest",
        params={"file": f"file://{dest}", "type": "netcdf"},
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 400
    body = response.json()
    assert body["status"] == 400
    assert body["type"] == "urn:tagbase:problem:bad-request"
    assert "trace_id" in body
    assert response.headers["content-type"].startswith("application/problem+json")


def test_ingest_post_rejects_netcdf_ingest_file_type(client):
    response = client.post(
        f"{API_PREFIX}/ingest",
        params={"filename": "minimal-etuff.txt", "type": "netcdf"},
        headers={
            "Accept": "application/json",
            "Content-Type": "text/plain",
        },
        data=ETUFF_FIXTURE.read_bytes(),
    )
    assert response.status_code == 400
    body = response.json()
    assert body["type"] == "urn:tagbase:problem:bad-request"
    assert "Unsupported ingest file type" in body["detail"]
