# coding: utf-8

from __future__ import absolute_import
import unittest

from flask import json
from six import BytesIO

from tagbase_server.models.response200 import Response200  # noqa: E501
from tagbase_server.models.response500 import Response500  # noqa: E501
from tagbase_server.test import BaseTestCase


class TestTagController(BaseTestCase):
    """TagController integration test stubs"""

    def test_get_tag(self):
        """Test case for get_tag

        Get information about an individual tag
        """
        headers = {
            "Accept": "application/json",
        }
        response = self.client.open(
            "/v0.5.0/tag/{tag_id}".format(tag_id=3.4), method="GET", headers=headers
        )
        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))

    def test_list_tags(self):
        """Test case for list_tags

        Get information about all tags
        """
        headers = {
            "Accept": "application/json",
        }
        response = self.client.open("/v0.5.0/tag", method="GET", headers=headers)
        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
