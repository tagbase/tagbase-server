# coding: utf-8


def test_ingest_etuff_get(client):
    """Test case for ingest_get with absent PostgreSQL connection credentials.

    We expect HTTP 500.
    """
    response = client.get(
        "/tagbase/api/v0.14.0/ingest",
        params={
            "file": "file:///usr/src/app/data/eTUFF-sailfish-117259.txt",
            "type": "etuff",
        },
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 500
    assert response.content
