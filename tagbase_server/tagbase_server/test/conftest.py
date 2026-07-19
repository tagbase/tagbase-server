# coding: utf-8

import logging
from pathlib import Path

import pytest
from connexion import FlaskApp
from connexion.options import SwaggerUIOptions

from tagbase_server import encoder

OPENAPI_DIR = Path(__file__).resolve().parents[1] / "openapi"


def create_test_app():
    """Build a Connexion FlaskApp for tests."""
    logging.getLogger("connexion.operation").setLevel("ERROR")
    swagger_ui_options = SwaggerUIOptions(swagger_ui=False)
    app = FlaskApp(
        __name__,
        specification_dir=str(OPENAPI_DIR),
        swagger_ui_options=swagger_ui_options,
        jsonifier=encoder.create_jsonifier(),
    )
    app.add_api("openapi.yaml", pythonic_params=True, strict_validation=True)
    return app


@pytest.fixture
def app():
    return create_test_app()


@pytest.fixture
def client(app):
    with app.test_client() as test_client:
        yield test_client
