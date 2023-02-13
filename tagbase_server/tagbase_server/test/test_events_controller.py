# coding: utf-8

from __future__ import absolute_import
import unittest

from flask import json
from six import BytesIO

from tagbase_server.models.event200 import Event200  # noqa: E501
from tagbase_server.models.event_put200 import EventPut200  # noqa: E501
from tagbase_server.models.events200 import Events200  # noqa: E501
from tagbase_server.models.response500 import Response500  # noqa: E501
from tagbase_server.test import BaseTestCase


class TestEventsController(BaseTestCase):
    """EventsController integration test stubs"""

    def test_get_event(self):
        """Test case for get_event

        Get information about an individual event
        """
        headers = {
            "Accept": "application/json",
        }
        response = self.client.open(
            "/tagbase/api/v0.7.0/events/{event_id}".format(event_id=3.4),
            method="GET",
            headers=headers,
        )
        self.assert500(response, "Response body is : " + response.data.decode("utf-8"))

    def test_list_all_events(self):
        """Test case for list_all_events

        Get information about all events
        """
        headers = {
            "Accept": "application/json",
        }
        response = self.client.open(
            "/tagbase/api/v0.7.0/events", method="GET", headers=headers
        )
        self.assert500(response, "Response body is : " + response.data.decode("utf-8"))

    def test_list_events(self):
        """Test case for list_events

        Get all events for a given tag submission
        """
        headers = {
            "Accept": "application/json",
        }
        response = self.client.open(
            "/tagbase/api/v0.7.0/tags/{tag_id}/subs/{sub_id}/events".format(
                tag_id=3.4, sub_id=3.4
            ),
            method="GET",
            headers=headers,
        )
        self.assert500(response, "Response body is : " + response.data.decode("utf-8"))

    def test_put_event(self):
        """Test case for put_event

        Update the 'notes' associated with a event
        """
        query_string = [("notes", "notes_example")]
        headers = {
            "Accept": "application/json",
        }
        response = self.client.open(
            "/tagbase/api/v0.7.0/events/{event_id}".format(event_id=3.4),
            method="PUT",
            headers=headers,
            query_string=query_string,
        )
        self.assert500(response, "Response body is : " + response.data.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
