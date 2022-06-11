import logging
import os
from logging.handlers import RotatingFileHandler

LOGGER_NAME = "tagbase_server"


def create_logger():
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
        f"./logs/{LOGGER_NAME}.log", mode="a", maxBytes=100000, backupCount=10
    )
    rf_handler.setFormatter(formatter)
    logger.addHandler(rf_handler)

    return logger
