# coding: utf-8

from __future__ import absolute_import

from tagbase_server.models.base_model_ import Model
from tagbase_server import util


class Problem(Model):
    """RFC7807 problem details body."""

    def __init__(
        self,
        type=None,
        title=None,
        status=None,
        detail=None,
        instance=None,
        trace_id=None,
    ):
        self.openapi_types = {
            "type": str,
            "title": str,
            "status": int,
            "detail": str,
            "instance": str,
            "trace_id": str,
        }
        self.attribute_map = {
            "type": "type",
            "title": "title",
            "status": "status",
            "detail": "detail",
            "instance": "instance",
            "trace_id": "trace_id",
        }
        self._type = type
        self._title = title
        self._status = status
        self._detail = detail
        self._instance = instance
        self._trace_id = trace_id

    @classmethod
    def from_dict(cls, dikt) -> "Problem":
        return util.deserialize_model(dikt, cls)

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, type):
        self._type = type

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title):
        self._title = title

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status):
        self._status = status

    @property
    def detail(self):
        return self._detail

    @detail.setter
    def detail(self, detail):
        self._detail = detail

    @property
    def instance(self):
        return self._instance

    @instance.setter
    def instance(self, instance):
        self._instance = instance

    @property
    def trace_id(self):
        return self._trace_id

    @trace_id.setter
    def trace_id(self, trace_id):
        self._trace_id = trace_id
