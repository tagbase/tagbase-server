# coding: utf-8


def test_delete_tag_sub(client):
    """Delete a submission for a given tag. We expect HTTP 500."""
    response = client.delete(
        "/tagbase/api/v0.14.0/tags/3/subs/3",
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 500
    assert response.content


def test_delete_tag(client):
    """Delete a tag. We expect HTTP 500."""
    response = client.delete(
        "/tagbase/api/v0.14.0/tags/3",
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 500
    assert response.content


def test_delete_tags(client):
    """Delete all tags. We expect HTTP 500."""
    response = client.delete(
        "/tagbase/api/v0.14.0/tags",
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 500
    assert response.content


def test_get_tag(client):
    """Get information about an individual tag. We expect HTTP 500."""
    response = client.get(
        "/tagbase/api/v0.14.0/tags/3",
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 500
    assert response.content


def test_list_tags(client):
    """Get information about all tags. We expect HTTP 500."""
    response = client.get(
        "/tagbase/api/v0.14.0/tags",
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 500
    assert response.content


def test_replace_tag_sub(client):
    """Update a tag submission. We expect HTTP 500."""
    response = client.put(
        "/tagbase/api/v0.14.0/tags/3/subs/6",
        params={
            "notes": "This is a test update for tag: 3 submission: 6 version: 2",
            "version": "2",
        },
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 500
    assert response.content
