import logging
import os
import psycopg2

from tagbase_server.models.response500 import Response500  # noqa: E501

logger = logging.getLogger(__name__)


def connect():
    """
    Make and return a connection to TagbaseDB. This function also improves handling of Operational errors
    if they occur.
    :rtype: connection
    """
    logger.debug("Attempting connection to TagbaseDB...")
    try:
        conn = psycopg2.connect(
            dbname="tagbase",
            user="tagbase",
            host="postgis",
            port=os.getenv("POSTGRES_PORT"),
            password=os.getenv("POSTGRES_PASSWORD"),
        )
    except psycopg2.OperationalError as poe:
        logger.error("Unable to connect to the database")
        return Response500.from_dict(
            {
                "code": "500",
                "message": "Encountered psycopg2.OperationalError when attempting to establish a connection "
                "to the Tagbase database.",
                "more_info": "Contact the service administrator - {email}".format(
                    email=os.getenv("PGADMIN_DEFAULT_EMAIL")
                ),
                "trace": poe,
            }
        )
    logger.debug("Successfully connected to TagbaseDB.")
    return conn
