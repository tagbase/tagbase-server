# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from tagbase_server.models.base_model_ import Model
from tagbase_server.models.tags200_tags_inner import Tags200TagsInner
from tagbase_server import util

from tagbase_server.models.tags200_tags_inner import Tags200TagsInner  # noqa: E501


class Tags200(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, count=None, tags=None):  # noqa: E501
        """Tags200 - a model defined in OpenAPI

        :param count: The count of this Tags200.  # noqa: E501
        :type count: int
        :param tags: The tags of this Tags200.  # noqa: E501
        :type tags: List[Tags200TagsInner]
        """
        self.openapi_types = {"count": int, "tags": List[Tags200TagsInner]}

        self.attribute_map = {"count": "count", "tags": "tags"}

        self._count = count
        self._tags = tags

    @classmethod
    def from_dict(cls, dikt) -> "Tags200":
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The Tags200 of this Tags200.  # noqa: E501
        :rtype: Tags200
        """
        return util.deserialize_model(dikt, cls)

    @property
    def count(self):
        """Gets the count of this Tags200.

        Total count of unique tags  # noqa: E501

        :return: The count of this Tags200.
        :rtype: int
        """
        return self._count

    @count.setter
    def count(self, count):
        """Sets the count of this Tags200.

        Total count of unique tags  # noqa: E501

        :param count: The count of this Tags200.
        :type count: int
        """

        self._count = count

    @property
    def tags(self):
        """Gets the tags of this Tags200.

        List of unique numeric Tag IDs and associated filename  # noqa: E501

        :return: The tags of this Tags200.
        :rtype: List[Tags200TagsInner]
        """
        return self._tags

    @tags.setter
    def tags(self, tags):
        """Sets the tags of this Tags200.

        List of unique numeric Tag IDs and associated filename  # noqa: E501

        :param tags: The tags of this Tags200.
        :type tags: List[Tags200TagsInner]
        """

        self._tags = tags
