# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from tagbase_server.models.base_model_ import Model
from tagbase_server import util


class TagPut200(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, code=None, message=None):  # noqa: E501
        """TagPut200 - a model defined in OpenAPI

        :param code: The code of this TagPut200.  # noqa: E501
        :type code: str
        :param message: The message of this TagPut200.  # noqa: E501
        :type message: str
        """
        self.openapi_types = {"code": str, "message": str}

        self.attribute_map = {"code": "code", "message": "message"}

        self._code = code
        self._message = message

    @classmethod
    def from_dict(cls, dikt) -> "TagPut200":
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The TagPut200 of this TagPut200.  # noqa: E501
        :rtype: TagPut200
        """
        return util.deserialize_model(dikt, cls)

    @property
    def code(self):
        """Gets the code of this TagPut200.

        HTTP status code  # noqa: E501

        :return: The code of this TagPut200.
        :rtype: str
        """
        return self._code

    @code.setter
    def code(self, code):
        """Sets the code of this TagPut200.

        HTTP status code  # noqa: E501

        :param code: The code of this TagPut200.
        :type code: str
        """

        self._code = code

    @property
    def message(self):
        """Gets the message of this TagPut200.

        A string detailing specifics of an HTTP operation  # noqa: E501

        :return: The message of this TagPut200.
        :rtype: str
        """
        return self._message

    @message.setter
    def message(self, message):
        """Sets the message of this TagPut200.

        A string detailing specifics of an HTTP operation  # noqa: E501

        :param message: The message of this TagPut200.
        :type message: str
        """

        self._message = message