# coding: utf-8

from __future__ import absolute_import
import unittest

from flask import json
from six import BytesIO

from openapi_server.models.error import Error  # noqa: E501
from openapi_server.models.success import Success  # noqa: E501
from openapi_server.test import BaseTestCase


class TestProductsController(BaseTestCase):
    """ProductsController integration test stubs"""

    def test_ingest_etuff_get(self):
        """Test case for ingest_etuff_get

        Get eTUFF file and execute ingestion.
        """
        query_string = [('granule_id', 'granule_id_example'),
                        ('file', 'file_example')]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/v2/tagbase/ingest/etuff',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))

    def test_ingest_ncingester_get(self):
        """Test case for ingest_ncingester_get

        Get X file and execute specific profile ingestion.
        """
        query_string = [('source_file_path', 'source_file_path_example'),
                        ('source_ingest_file', 'source_ingest_file_example'),
                        ('profile', 'profile_example')]
        headers = { 
            'Accept': 'application/json',
        }
        response = self.client.open(
            '/v2/tagbase/ingest/ncingester',
            method='GET',
            headers=headers,
            query_string=query_string)
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
