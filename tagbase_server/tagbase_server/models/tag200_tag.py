# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from tagbase_server.models.base_model_ import Model
from tagbase_server import util


class Tag200Tag(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(
        self,
        date_time=None,
        filename=None,
        submission_id=None,
        tag_id=None,
        version=None,
    ):  # noqa: E501
        """Tag200Tag - a model defined in OpenAPI

        :param date_time: The date_time of this Tag200Tag.  # noqa: E501
        :type date_time: str
        :param filename: The filename of this Tag200Tag.  # noqa: E501
        :type filename: str
        :param submission_id: The submission_id of this Tag200Tag.  # noqa: E501
        :type submission_id: int
        :param tag_id: The tag_id of this Tag200Tag.  # noqa: E501
        :type tag_id: int
        :param version: The version of this Tag200Tag.  # noqa: E501
        :type version: str
        """
        self.openapi_types = {
            "date_time": str,
            "filename": str,
            "submission_id": int,
            "tag_id": int,
            "version": str,
        }

        self.attribute_map = {
            "date_time": "date_time",
            "filename": "filename",
            "submission_id": "submission_id",
            "tag_id": "tag_id",
            "version": "version",
        }

        self._date_time = date_time
        self._filename = filename
        self._submission_id = submission_id
        self._tag_id = tag_id
        self._version = version

    @classmethod
    def from_dict(cls, dikt) -> "Tag200Tag":
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The Tag200_tag of this Tag200Tag.  # noqa: E501
        :rtype: Tag200Tag
        """
        return util.deserialize_model(dikt, cls)

    @property
    def date_time(self):
        """Gets the date_time of this Tag200Tag.

        Local datetime stamp at the time of eTUFF tag data file ingestion  # noqa: E501

        :return: The date_time of this Tag200Tag.
        :rtype: str
        """
        return self._date_time

    @date_time.setter
    def date_time(self, date_time):
        """Sets the date_time of this Tag200Tag.

        Local datetime stamp at the time of eTUFF tag data file ingestion  # noqa: E501

        :param date_time: The date_time of this Tag200Tag.
        :type date_time: str
        """

        self._date_time = date_time

    @property
    def filename(self):
        """Gets the filename of this Tag200Tag.

        Full name and extension of the ingested eTUFF tag data file  # noqa: E501

        :return: The filename of this Tag200Tag.
        :rtype: str
        """
        return self._filename

    @filename.setter
    def filename(self, filename):
        """Sets the filename of this Tag200Tag.

        Full name and extension of the ingested eTUFF tag data file  # noqa: E501

        :param filename: The filename of this Tag200Tag.
        :type filename: str
        """

        self._filename = filename

    @property
    def submission_id(self):
        """Gets the submission_id of this Tag200Tag.

        Unique numeric ID assigned upon submission of a tag eTUFF data file for ingest/importation into Tagbase  # noqa: E501

        :return: The submission_id of this Tag200Tag.
        :rtype: int
        """
        return self._submission_id

    @submission_id.setter
    def submission_id(self, submission_id):
        """Sets the submission_id of this Tag200Tag.

        Unique numeric ID assigned upon submission of a tag eTUFF data file for ingest/importation into Tagbase  # noqa: E501

        :param submission_id: The submission_id of this Tag200Tag.
        :type submission_id: int
        """

        self._submission_id = submission_id

    @property
    def tag_id(self):
        """Gets the tag_id of this Tag200Tag.

        Unique numeric Tag ID associated with the ingested tag eTUFF data file  # noqa: E501

        :return: The tag_id of this Tag200Tag.
        :rtype: int
        """
        return self._tag_id

    @tag_id.setter
    def tag_id(self, tag_id):
        """Sets the tag_id of this Tag200Tag.

        Unique numeric Tag ID associated with the ingested tag eTUFF data file  # noqa: E501

        :param tag_id: The tag_id of this Tag200Tag.
        :type tag_id: int
        """

        self._tag_id = tag_id

    @property
    def version(self):
        """Gets the version of this Tag200Tag.

        Version identifier for the eTUFF tag data file ingested  # noqa: E501

        :return: The version of this Tag200Tag.
        :rtype: str
        """
        return self._version

    @version.setter
    def version(self, version):
        """Sets the version of this Tag200Tag.

        Version identifier for the eTUFF tag data file ingested  # noqa: E501

        :param version: The version of this Tag200Tag.
        :type version: str
        """

        self._version = version
