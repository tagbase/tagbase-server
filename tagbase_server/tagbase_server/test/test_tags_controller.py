# coding: utf-8

import unittest

from tagbase_server.test import BaseTestCase


class TestTagController(BaseTestCase):
    """TagController integration test stubs"""

    def test_get_tag(self):
        """Test case for get_tag

        Get information about an individual tag. We expect HTTP 500.
        """
        headers = {
            "Accept": "application/json",
        }
        response = self.client.open(
            "/tagbase/api/v0.8.0/tags/{tag_id}".format(tag_id=3),
            method="GET",
            headers=headers,
        )
        self.assert500(response, "Response body is : " + response.data.decode("utf-8"))

    def test_list_tags(self):
        """Test case for list_tags

        Get information about all tags. We expect HTTP 500.
        """
        headers = {
            "Accept": "application/json",
        }
        response = self.client.open(
            "/tagbase/api/v0.8.0/tags", method="GET", headers=headers
        )
        self.assert500(response, "Response body is : " + response.data.decode("utf-8"))

    def test_put_tag(self):
        """Test case for put_tag

        Update a tag submission. We expect HTTP 500.
        """
        headers = {
            "Accept": "application/json",
        }
        query_string = [
            ("notes", "This is a test update for tag: 3 submission: 6 solution_id: 2"),
            ("solution_id", 2),
        ]
        response = self.client.open(
            "/tagbase/api/v0.8.0/tags/{tag_id}/subs/{sub_id}".format(
                tag_id=3, sub_id=6
            ),
            method="PUT",
            headers=headers,
            query_string=query_string,
        )
        self.assert500(response, "Response body is : " + response.data.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
