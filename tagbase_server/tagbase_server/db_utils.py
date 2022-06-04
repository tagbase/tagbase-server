import os
import psycopg2

from tagbase_server.__main__ import logger
from tagbase_server.models.response500 import Response500  # noqa: E501


def connect():
    """
    Make and return a connection to TagbaseDB. This function also improves handling of Operational errors
    if they occur.
    :rtype: connection
    """
    logger.info("Attempting connection to TagbaseDB...")
    try:
        conn = psycopg2.connect(
            "dbname='%s' user='%s' host='%s' port=%d password='%s'"
            % (
                "tagbase",
                "tagbase",
                "postgres",
                5432,
                "tagbase",
            )  # os.getenv("POSTGRES_PORT"), os.getenv("POSTGRES_PASSWORD"))
        )
    except psycopg2.OperationalError as poe:
        # app.logger.error("Unable to connect to the database")
        return Response500.from_dict(
            {
                "code": "500",
                "message": "Encountered psycopg2.OperationalError when attempting to establish a connection "
                "to the Tagbase PostgreSQL database.",
                "more_info": "Contact the service administrator - "
                + os.getenv("PGADMIN_DEFAULT_EMAIL"),
                "trace": poe,
            }
        )
    logger.info("Successfully connected to TagbaseDB.")
    return conn
