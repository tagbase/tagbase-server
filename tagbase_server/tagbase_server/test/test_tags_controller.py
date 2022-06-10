# coding: utf-8

import unittest

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
            "/v0.6.0/tags/{tag_id}".format(tag_id=3), method="GET", headers=headers
        )
        self.assert500(response, "Response body is : " + response.data.decode("utf-8"))

    def test_list_tags(self):
        """Test case for list_tags

        Get information about all tags
        """
        headers = {
            "Accept": "application/json",
        }
        response = self.client.open("/v0.6.0/tags", method="GET", headers=headers)
        self.assert500(response, "Response body is : " + response.data.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
