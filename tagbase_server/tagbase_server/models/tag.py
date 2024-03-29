# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from tagbase_server.models.base_model_ import Model
from tagbase_server import util


class Tag(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, tag_id=None, filename=None):  # noqa: E501
        """Tag - a model defined in OpenAPI

        :param tag_id: The tag_id of this Tag.  # noqa: E501
        :type tag_id: int
        :param filename: The filename of this Tag.  # noqa: E501
        :type filename: str
        """
        self.openapi_types = {"tag_id": int, "filename": str}

        self.attribute_map = {"tag_id": "tag_id", "filename": "filename"}

        self._tag_id = tag_id
        self._filename = filename

    @classmethod
    def from_dict(cls, dikt) -> "Tag":
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The Tag of this Tag.  # noqa: E501
        :rtype: Tag
        """
        return util.deserialize_model(dikt, cls)

    @property
    def tag_id(self):
        """Gets the tag_id of this Tag.

        Unique numeric Tag ID associated with the ingested tag eTUFF data file  # noqa: E501

        :return: The tag_id of this Tag.
        :rtype: int
        """
        return self._tag_id

    @tag_id.setter
    def tag_id(self, tag_id):
        """Sets the tag_id of this Tag.

        Unique numeric Tag ID associated with the ingested tag eTUFF data file  # noqa: E501

        :param tag_id: The tag_id of this Tag.
        :type tag_id: int
        """

        self._tag_id = tag_id

    @property
    def filename(self):
        """Gets the filename of this Tag.

        Full name and extension of the ingested eTUFF tag data file  # noqa: E501

        :return: The filename of this Tag.
        :rtype: str
        """
        return self._filename

    @filename.setter
    def filename(self, filename):
        """Sets the filename of this Tag.

        Full name and extension of the ingested eTUFF tag data file  # noqa: E501

        :param filename: The filename of this Tag.
        :type filename: str
        """

        self._filename = filename
