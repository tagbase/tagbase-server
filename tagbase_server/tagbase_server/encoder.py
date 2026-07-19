# coding: utf-8

from connexion.jsonifier import JSONEncoder as ConnexionJSONEncoder
from connexion.jsonifier import Jsonifier

from tagbase_server.models.base_model_ import Model


class ModelJSONEncoder(ConnexionJSONEncoder):
    """JSON encoder that serializes generated OpenAPI models."""

    include_nulls = False

    def default(self, o):
        if isinstance(o, Model):
            dikt = {}
            for attr in o.openapi_types:
                value = getattr(o, attr)
                if value is None and not self.include_nulls:
                    continue
                attr = o.attribute_map[attr]
                dikt[attr] = value
            return dikt
        return super().default(o)


def create_jsonifier():
    return Jsonifier(cls=ModelJSONEncoder)


# Backwards-compatible alias used by app bootstrap.
JSONEncoder = create_jsonifier
