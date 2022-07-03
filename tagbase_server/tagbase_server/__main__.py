#!/usr/bin/env python3

import connexion
import logging
import os
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

# s_handler = logging.StreamHandler()
# s_handler.setFormatter(formatter)
# logger.addHandler(s_handler)

rf_handler = RotatingFileHandler(
    f"./logs/{LOGGER_NAME}_log.txt", mode="a", maxBytes=100000, backupCount=10
)
rf_handler.setFormatter(formatter)
logger.addHandler(rf_handler)

app = connexion.App(__name__, specification_dir="./openapi/")
app.app.json_encoder = encoder.JSONEncoder
app.add_api(
    "openapi.yaml",
    arguments={"title": "tagbase-server API"},
    #base_path='api',
    pythonic_params=True,
    strict_validation=True,
)
# app.run(host="0.0.0.0", port=5433)
