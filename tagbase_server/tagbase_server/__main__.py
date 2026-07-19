#!/usr/bin/env python3

import logging
import os
from logging.handlers import RotatingFileHandler

from connexion import FlaskApp
from connexion.options import SwaggerUIOptions
from flask_cors import CORS

from tagbase_server import encoder

LOGGER_NAME = "tagbase_server"


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
# add CORS support
CORS(app.app)
