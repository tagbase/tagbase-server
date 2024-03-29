# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from tagbase_server.models.base_model_ import Model
from tagbase_server import util


class Response500(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(
        self, code=None, message=None, more_info=None, trace=None
    ):  # noqa: E501
        """Response500 - a model defined in OpenAPI

        :param code: The code of this Response500.  # noqa: E501
        :type code: str
        :param message: The message of this Response500.  # noqa: E501
        :type message: str
        :param more_info: The more_info of this Response500.  # noqa: E501
        :type more_info: str
        :param trace: The trace of this Response500.  # noqa: E501
        :type trace: str
        """
        self.openapi_types = {
            "code": str,
            "message": str,
            "more_info": str,
            "trace": str,
        }

        self.attribute_map = {
            "code": "code",
            "message": "message",
            "more_info": "more_info",
            "trace": "trace",
        }

        self._code = code
        self._message = message
        self._more_info = more_info
        self._trace = trace

    @classmethod
    def from_dict(cls, dikt) -> "Response500":
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The Response500 of this Response500.  # noqa: E501
        :rtype: Response500
        """
        return util.deserialize_model(dikt, cls)

    @property
    def code(self):
        """Gets the code of this Response500.

        HTTP status code  # noqa: E501

        :return: The code of this Response500.
        :rtype: str
        """
        return self._code

    @code.setter
    def code(self, code):
        """Sets the code of this Response500.

        HTTP status code  # noqa: E501

        :param code: The code of this Response500.
        :type code: str
        """

        self._code = code

    @property
    def message(self):
        """Gets the message of this Response500.

        A string detailing specifics of the HTTP 500 response  # noqa: E501

        :return: The message of this Response500.
        :rtype: str
        """
        return self._message

    @message.setter
    def message(self, message):
        """Sets the message of this Response500.

        A string detailing specifics of the HTTP 500 response  # noqa: E501

        :param message: The message of this Response500.
        :type message: str
        """

        self._message = message

    @property
    def more_info(self):
        """Gets the more_info of this Response500.

        Additional details (if available) to diagnose the 500 response.  # noqa: E501

        :return: The more_info of this Response500.
        :rtype: str
        """
        return self._more_info

    @more_info.setter
    def more_info(self, more_info):
        """Sets the more_info of this Response500.

        Additional details (if available) to diagnose the 500 response.  # noqa: E501

        :param more_info: The more_info of this Response500.
        :type more_info: str
        """

        self._more_info = more_info

    @property
    def trace(self):
        """Gets the trace of this Response500.

        Trace diagnostic information related to the response  # noqa: E501

        :return: The trace of this Response500.
        :rtype: str
        """
        return self._trace

    @trace.setter
    def trace(self, trace):
        """Sets the trace of this Response500.

        Trace diagnostic information related to the response  # noqa: E501

        :param trace: The trace of this Response500.
        :type trace: str
        """

        self._trace = trace
