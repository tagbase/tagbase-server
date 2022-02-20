#!/usr/bin/env python3

import connexion
import logging

from logging.handlers import RotatingFileHandler
from logging import Formatter

from tagbase_server import encoder


def main():
    handler = RotatingFileHandler("tagbase.log", maxBytes=10000, backupCount=10)
    handler.setLevel(logging.INFO)
    handler.setFormatter(
        Formatter(
            "%(asctime)s %(levelname)s: %(message)s " "[in %(pathname)s:%(lineno)d]"
        )
    )

    logger = logging.getLogger("werkzeug")
    logger.addHandler(handler)

    app = connexion.App(__name__, specification_dir="openapi/")
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api(
        "openapi.yaml", arguments={"title": "tagbase-server API"}, pythonic_params=True
    )
    app.run(port=5433, host="0.0.0.0", threaded=True)


if __name__ == "__main__":
    main()
