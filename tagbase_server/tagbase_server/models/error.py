# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from tagbase_server.models.base_model_ import Model
from tagbase_server import util


class Error(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, code=None, message=None, more_info=None):  # noqa: E501
        """Error - a model defined in OpenAPI

        :param code: The code of this Error.  # noqa: E501
        :type code: str
        :param message: The message of this Error.  # noqa: E501
        :type message: str
        :param more_info: The more_info of this Error.  # noqa: E501
        :type more_info: str
        """
        self.openapi_types = {
            'code': str,
            'message': str,
            'more_info': str
        }

        self.attribute_map = {
            'code': 'code',
            'message': 'message',
            'more_info': 'more_info'
        }

        self._code = code
        self._message = message
        self._more_info = more_info

    @classmethod
    def from_dict(cls, dikt) -> 'Error':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The Error of this Error.  # noqa: E501
        :rtype: Error
        """
        return util.deserialize_model(dikt, cls)

    @property
    def code(self):
        """Gets the code of this Error.

        The error code.  # noqa: E501

        :return: The code of this Error.
        :rtype: str
        """
        return self._code

    @code.setter
    def code(self, code):
        """Sets the code of this Error.

        The error code.  # noqa: E501

        :param code: The code of this Error.
        :type code: str
        """
        allowed_values = ["internal_server_error", "bad_request", "unauthorized", "service_unavailable"]  # noqa: E501
        if code not in allowed_values:
            raise ValueError(
                "Invalid value for `code` ({0}), must be one of {1}"
                .format(code, allowed_values)
            )

        self._code = code

    @property
    def message(self):
        """Gets the message of this Error.

        The error message.  # noqa: E501

        :return: The message of this Error.
        :rtype: str
        """
        return self._message

    @message.setter
    def message(self, message):
        """Sets the message of this Error.

        The error message.  # noqa: E501

        :param message: The message of this Error.
        :type message: str
        """

        self._message = message

    @property
    def more_info(self):
        """Gets the more_info of this Error.

        Additional info about the error.  # noqa: E501

        :return: The more_info of this Error.
        :rtype: str
        """
        return self._more_info

    @more_info.setter
    def more_info(self, more_info):
        """Sets the more_info of this Error.

        Additional info about the error.  # noqa: E501

        :param more_info: The more_info of this Error.
        :type more_info: str
        """

        self._more_info = more_info
