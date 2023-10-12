#!/usr/bin/env python3

import connexion
import logging
import os
from flask_cors import CORS
from logging.handlers import RotatingFileHandler
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

options = {
    "swagger_ui": False
}
app = connexion.App(__name__, specification_dir="./openapi/", options=options)
app.app.json_encoder = encoder.JSONEncoder
app.add_api(
    "openapi.yaml",
    arguments={"title": "tagbase-server REST API"},
    pythonic_params=True,
    strict_validation=True,
)
# add CORS support
CORS(app.app)
