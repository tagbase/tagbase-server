# coding: utf-8

import unittest

from tagbase_server.test import BaseTestCase


class TestIngestController(BaseTestCase):
    """IngestController integration tests"""

    def test_ingest_etuff_get(self):
        """Test case for ingest_etuff_get with absent PostgreSQL connection credentials.
        We expect HTTP 500.

        Get eTUFF file and execute ingestion.
        """
        query_string = [
            ("file", "file:///usr/src/app/data/eTUFF-sailfish-117259.txt"),
            ("type", "etuff"),
        ]
        headers = {
            "Accept": "application/json",
        }
        response = self.client.open(
            "/tagbase/api/v0.9.0/ingest",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert500(response, "Response body is : " + response.data.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
