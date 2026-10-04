# coding: utf-8

import json
from pathlib import Path

from tagbase_server.api_prefix import API_PREFIX

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
ETUFF_FIXTURE = FIXTURES_DIR / "etuff" / "minimal-etuff.txt"
ETUFF_ZIP_FIXTURE = FIXTURES_DIR / "etuff" / "minimal-etuff.zip"

__all__ = [
    "API_PREFIX",
    "ETUFF_FIXTURE",
    "ETUFF_ZIP_FIXTURE",
    "FIXTURES_DIR",
    "response_json",
]


def response_json(response):
    return json.loads(response.content)


def finish_accepted_ingest(client, response):
    """Assert the upload was accepted, then run queued jobs in this process."""
    from tagbase_server.ingest_worker import process_available

    assert response.status_code == 202
    accepted = response_json(response)
    assert accepted["status"] == "queued"
    assert accepted["id"]
    process_available()
    job = client.get(
        f"{API_PREFIX}/ingest/jobs/{accepted['id']}",
        headers={"Accept": "application/json"},
    )
    assert job.status_code == 200
    body = response_json(job)
    assert body["status"] == "succeeded", body
    return body
