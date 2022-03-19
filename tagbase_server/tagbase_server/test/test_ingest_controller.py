# coding: utf-8

from __future__ import absolute_import
import unittest

from flask import json
from six import BytesIO

from tagbase_server.models.response200 import Response200  # noqa: E501
from tagbase_server.models.response500 import Response500  # noqa: E501
from tagbase_server.test import BaseTestCase


class TestIngestController(BaseTestCase):
    """IngestController integration tests"""

    def test_ingest_etuff_get_500(self):
        """Test case for ingest_etuff_get with absent PostgreSQL connection credentials.
        We expect HTTP 500.

        Get eTUFF file and execute ingestion.
        """
        query_string = [
            ("file", "file:///usr/src/app/data/eTUFF-sailfish-117259.txt"),
            ("type", "etuff")
        ]
        headers = {
            "Accept": "application/json",
        }
        response = self.client.open(
            "/v0.4.0/ingest",
            method="GET",
            headers=headers,
            query_string=query_string,
        )
        self.assert500(response, "Response body is : " + response.data.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
