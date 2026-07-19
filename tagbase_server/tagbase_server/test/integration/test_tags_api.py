# coding: utf-8

import pytest

from tagbase_server.test.helpers import API_PREFIX, response_json

pytestmark = pytest.mark.integration


def _ingest(client, etuff_bytes, notes="notes", version="1"):
    response = client.post(
        f"{API_PREFIX}/ingest",
        params={
            "filename": "minimal-etuff.txt",
            "notes": notes,
            "version": version,
        },
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
    tag_id = listed["tags"][0]["tag_id"]
    detail = response_json(
        client.get(
            f"{API_PREFIX}/tags/{tag_id}",
            headers={"Accept": "application/json"},
        )
    )
    sub_id = detail["tag"][0]["submission_id"]
    return tag_id, sub_id


def test_list_tags_empty_when_no_submissions(client, clean_db):
    response = client.get(f"{API_PREFIX}/tags", headers={"Accept": "application/json"})
    assert response.status_code == 200
    body = response_json(response)
    assert body["count"] == 0
    assert body["tags"] == []


def test_replace_tag_sub_updates_notes_and_version(client, clean_db, etuff_bytes):
    tag_id, sub_id = _ingest(client, etuff_bytes, notes="old", version="1")
    response = client.put(
        f"{API_PREFIX}/tags/{tag_id}/subs/{sub_id}",
        params={"notes": "updated notes", "version": "2"},
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 200
    body = response_json(response)
    assert body["code"] == "200"

    detail = response_json(
        client.get(
            f"{API_PREFIX}/tags/{tag_id}",
            headers={"Accept": "application/json"},
        )
    )
    assert detail["tag"][0]["notes"] == "updated notes"
    assert detail["tag"][0]["version"] == "2"


def test_delete_tag_sub_removes_submission(client, clean_db, etuff_bytes):
    tag_id, sub_id = _ingest(client, etuff_bytes)
    response = client.delete(
        f"{API_PREFIX}/tags/{tag_id}/subs/{sub_id}",
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 204

    listed = response_json(
        client.get(f"{API_PREFIX}/tags", headers={"Accept": "application/json"})
    )
    assert listed["count"] == 0


def test_delete_tag_removes_tag_from_list(client, clean_db, etuff_bytes):
    tag_id, _ = _ingest(client, etuff_bytes)
    response = client.delete(
        f"{API_PREFIX}/tags/{tag_id}",
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 204
    listed = response_json(
        client.get(f"{API_PREFIX}/tags", headers={"Accept": "application/json"})
    )
    assert listed["count"] == 0


def test_delete_tags_clears_all_tags(client, clean_db, etuff_bytes):
    _ingest(client, etuff_bytes)
    response = client.delete(
        f"{API_PREFIX}/tags",
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 204
    listed = response_json(
        client.get(f"{API_PREFIX}/tags", headers={"Accept": "application/json"})
    )
    assert listed["count"] == 0
    assert listed["tags"] == []
