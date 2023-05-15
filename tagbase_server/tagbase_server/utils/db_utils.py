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
                "to the Tagbase PostgreSQL database.",
                "more_info": "Contact the service administrator - {email}".format(
                    email=os.getenv("PGADMIN_DEFAULT_EMAIL")
                ),
                "trace": poe,
            }
        )
    logger.debug("Successfully connected to TagbaseDB.")
    return conn


def detect_duplicate(hash_sha256):
    """
    Detect a duplicate file by performing a lookup on submission SHA256 hash.
    Returns True if duplicate.

    :param hash_sha256: A SHA256 hash.
    :type hash_sha256: str
    """
    conn = connect()
    conn.autocommit = True
    with conn:
        with conn.cursor() as cur:
            logger.info("Querying...")
            cur.execute(
                "SELECT hash_sha256 FROM submission WHERE hash_sha256 = %s",
                (hash_sha256,),
            )
            duplicate = cur.fetchone()[0]
            logger.info(duplicate)
            if duplicate is not None:
                return True
            else:
                return False
