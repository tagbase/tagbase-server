# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from tagbase_server.models.base_model_ import Model
from tagbase_server import util


class Ingest200(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, code=None, elapsed=None, message=None):  # noqa: E501
        """Ingest200 - a model defined in OpenAPI

        :param code: The code of this Ingest200.  # noqa: E501
        :type code: str
        :param elapsed: The elapsed of this Ingest200.  # noqa: E501
        :type elapsed: str
        :param message: The message of this Ingest200.  # noqa: E501
        :type message: str
        """
        self.openapi_types = {
            'code': str,
            'elapsed': str,
            'message': str
        }

        self.attribute_map = {
            'code': 'code',
            'elapsed': 'elapsed',
            'message': 'message'
        }

        self._code = code
        self._elapsed = elapsed
        self._message = message

    @classmethod
    def from_dict(cls, dikt) -> 'Ingest200':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The Ingest200 of this Ingest200.  # noqa: E501
        :rtype: Ingest200
        """
        return util.deserialize_model(dikt, cls)

    @property
    def code(self):
        """Gets the code of this Ingest200.

        HTTP status code  # noqa: E501

        :return: The code of this Ingest200.
        :rtype: str
        """
        return self._code

    @code.setter
    def code(self, code):
        """Sets the code of this Ingest200.

        HTTP status code  # noqa: E501

        :param code: The code of this Ingest200.
        :type code: str
        """

        self._code = code

    @property
    def elapsed(self):
        """Gets the elapsed of this Ingest200.

        Elapsed time for the operation  # noqa: E501

        :return: The elapsed of this Ingest200.
        :rtype: str
        """
        return self._elapsed

    @elapsed.setter
    def elapsed(self, elapsed):
        """Sets the elapsed of this Ingest200.

        Elapsed time for the operation  # noqa: E501

        :param elapsed: The elapsed of this Ingest200.
        :type elapsed: str
        """

        self._elapsed = elapsed

    @property
    def message(self):
        """Gets the message of this Ingest200.

        A string detailing specifics of an HTTP operation  # noqa: E501

        :return: The message of this Ingest200.
        :rtype: str
        """
        return self._message

    @message.setter
    def message(self, message):
        """Sets the message of this Ingest200.

        A string detailing specifics of an HTTP operation  # noqa: E501

        :param message: The message of this Ingest200.
        :type message: str
        """

        self._message = message
