#!/usr/bin/env python3

import connexion

from tagbase_server import encoder
from tagbase_server.log_config import create_logger

logger = create_logger()


def main():

    app = connexion.App(__name__, specification_dir="openapi/")
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api(
        "openapi.yaml",
        arguments={"title": "tagbase-server API"},
        pythonic_params=True,
        strict_validation=True,
    )
    app.run(server="tornado", port=5433, host="0.0.0.0")


if __name__ == "__main__":
    main()
