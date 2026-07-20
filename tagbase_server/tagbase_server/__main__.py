#!/usr/bin/env python3

import logging
import os
from logging.handlers import RotatingFileHandler

from connexion import FlaskApp
from connexion.options import SwaggerUIOptions
from flask_cors import CORS

from tagbase_server import encoder
from tagbase_server.problem import register_problem_handlers
from tagbase_server.telemetry import setup_telemetry

LOGGER_NAME = "tagbase_server"


def parse_cors_origins(env_value=None):
    raw = (
        env_value
        if env_value is not None
        else os.environ.get("TAGBASE_CORS_ORIGINS", "")
    )
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def configure_cors(flask_app, cors_factory=CORS):
    origins = parse_cors_origins()
    if origins:
        cors_factory(flask_app, resources={r"/*": {"origins": origins}})


if not os.path.exists("./logs"):
    os.makedirs("./logs")
logger = logging.getLogger(LOGGER_NAME)
if logger.hasHandlers():
    logger.handlers = []
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

s_handler = logging.StreamHandler()
s_handler.setFormatter(formatter)
logger.addHandler(s_handler)

rf_handler = RotatingFileHandler(
    f"./logs/{LOGGER_NAME}_log.txt", mode="a", maxBytes=100000, backupCount=10
)
rf_handler.setFormatter(formatter)
logger.addHandler(rf_handler)

swagger_ui_options = SwaggerUIOptions(
    swagger_ui=True,
    swagger_ui_path="/ui",
    swagger_ui_config={
        "url": "https://raw.githubusercontent.com/tagbase/tagbase-server/main/openapi.yaml"
    },
)
app = FlaskApp(
    __name__,
    specification_dir="./openapi/",
    swagger_ui_options=swagger_ui_options,
    jsonifier=encoder.create_jsonifier(),
)
app.add_api(
    "openapi.yaml",
    arguments={"title": "tagbase-server API"},
    pythonic_params=True,
    strict_validation=True,
)

configure_cors(app.app)
register_problem_handlers(app.app)

# When not under Gunicorn (e.g. local/tests), init here. Under Gunicorn,
# post_fork in gunicorn.conf.py initializes per worker after fork.
setup_telemetry(flask_app=app.app)
