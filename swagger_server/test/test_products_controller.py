# coding: utf-8

from __future__ import absolute_import

from flask import json
from six import BytesIO

from swagger_server.models.error import Error  # noqa: E501
from swagger_server.models.success import Success  # noqa: E501
from swagger_server.test import BaseTestCase


class TestProductsController(BaseTestCase):
    """ProductsController integration test stubs"""

    def test_ingest_etuff_get(self):
        """Test case for ingest_etuff_get

        Get eTUFF file and execute ingestion.
        """
        query_string = [('dmas_granule_id', 8.14),
                        ('file', 'file_example')]
        response = self.client.open(
            '/v1/tagbase/ingest/etuff',
            method='GET',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_ingest_ncingester_get(self):
        """Test case for ingest_ncingester_get

        Get X file and execute specific profile ingestion.
        """
        query_string = [('profile', 'profile_example'),
                        ('file', 'file_example')]
        response = self.client.open(
            '/v1/tagbase/ingest/ncingester',
            method='GET',
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
