# coding: utf-8

import shutil
from pathlib import Path

import pytest

from tagbase_server.test.helpers import API_PREFIX, ETUFF_FIXTURE, response_json

pytestmark = pytest.mark.integration


@pytest.fixture
def short_etuff_file_url(tmp_path):
    """OpenAPI caps the ingest file query param at 100 chars."""
    dest = Path("/tmp/tb-etuff.txt")
    shutil.copyfile(ETUFF_FIXTURE, dest)
    return f"file://{dest}"


def test_post_ingest_etuff_makes_tag_listable_and_gettable(
    client, clean_db, etuff_bytes
):
    response = client.post(
        f"{API_PREFIX}/ingest",
        params={
            "filename": "minimal-etuff.txt",
            "notes": "integration ingest notes",
            "version": "1",
        },
        headers={
            "Accept": "application/json",
            "Content-Type": "text/plain",
        },
        data=etuff_bytes,
    )
    assert response.status_code == 200
    body = response_json(response)
    assert body["code"] == "200"
    assert "minimal-etuff.txt" in body["message"]

    listed = client.get(f"{API_PREFIX}/tags", headers={"Accept": "application/json"})
    assert listed.status_code == 200
    listed_body = response_json(listed)
    assert listed_body["count"] == 1
    tag_id = listed_body["tags"][0]["tag_id"]

    detail = client.get(
        f"{API_PREFIX}/tags/{tag_id}",
        headers={"Accept": "application/json"},
    )
    assert detail.status_code == 200
    tag = response_json(detail)["tag"]
    assert len(tag) == 1
    assert tag[0]["filename"].endswith("minimal-etuff.txt")
    assert tag[0]["notes"] == "integration ingest notes"
    assert tag[0]["version"] == "1"
    assert tag[0]["metadata"]["ptt"] == "117464"
    assert tag[0]["metadata"]["instrument_name"] == "test_instrument_117464"


def test_post_ingest_duplicate_etuff_keeps_single_submission(
    client, clean_db, etuff_bytes
):
    params = {"filename": "minimal-etuff.txt", "version": "1"}
    headers = {"Accept": "application/json", "Content-Type": "text/plain"}
    first = client.post(
        f"{API_PREFIX}/ingest", params=params, headers=headers, data=etuff_bytes
    )
    second = client.post(
        f"{API_PREFIX}/ingest", params=params, headers=headers, data=etuff_bytes
    )
    assert first.status_code == 200
    assert second.status_code == 200

    listed = response_json(
        client.get(f"{API_PREFIX}/tags", headers={"Accept": "application/json"})
    )
    assert listed["count"] == 1
    tag_id = listed["tags"][0]["tag_id"]
    detail = response_json(
        client.get(
            f"{API_PREFIX}/tags/{tag_id}",
            headers={"Accept": "application/json"},
        )
    )
    assert len(detail["tag"]) == 1


def test_post_ingest_zip_etuff_makes_tag_retrievable(client, clean_db, etuff_zip_bytes):
    response = client.post(
        f"{API_PREFIX}/ingest",
        params={"filename": "minimal-etuff.zip", "version": "1"},
        headers={
            "Accept": "application/json",
            "Content-Type": "application/octet-stream",
        },
        data=etuff_zip_bytes,
    )
    assert response.status_code == 200
    listed = response_json(
        client.get(f"{API_PREFIX}/tags", headers={"Accept": "application/json"})
    )
    assert listed["count"] >= 1


def test_get_ingest_file_url_makes_tag_listable(client, clean_db, short_etuff_file_url):
    response = client.get(
        f"{API_PREFIX}/ingest",
        params={
            "file": short_etuff_file_url,
            "notes": "get ingest",
            "version": "1",
        },
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 200
    listed = response_json(
        client.get(f"{API_PREFIX}/tags", headers={"Accept": "application/json"})
    )
    assert listed["count"] == 1


def test_get_ingest_missing_file_errors(client, clean_db):
    response = client.get(
        f"{API_PREFIX}/ingest",
        params={"file": "file:///tmp/no-such-etuff.txt"},
        headers={"Accept": "application/json"},
    )
    assert response.status_code >= 400


def test_ingest_rejects_netcdf_ingest_file_type(
    client, clean_db, etuff_bytes, short_etuff_file_url
):
    get_response = client.get(
        f"{API_PREFIX}/ingest",
        params={"file": short_etuff_file_url, "type": "netcdf"},
        headers={"Accept": "application/json"},
    )
    assert get_response.status_code >= 400

    post_response = client.post(
        f"{API_PREFIX}/ingest",
        params={"filename": "minimal-etuff.txt", "type": "netcdf"},
        headers={
            "Accept": "application/json",
            "Content-Type": "text/plain",
        },
        data=etuff_bytes,
    )
    assert post_response.status_code != 200


def test_ingest_defaults_omitted_type_to_etuff(client, clean_db, etuff_bytes):
    response = client.post(
        f"{API_PREFIX}/ingest",
        params={"filename": "minimal-etuff.txt"},
        headers={
            "Accept": "application/json",
            "Content-Type": "text/plain",
        },
        data=etuff_bytes,
    )
    assert response.status_code == 200
    listed = response_json(
        client.get(f"{API_PREFIX}/tags", headers={"Accept": "application/json"})
    )
    assert listed["count"] == 1
