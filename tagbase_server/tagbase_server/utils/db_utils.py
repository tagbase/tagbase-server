import logging
import os
import psycopg2

from tagbase_server.models.response500 import Response500  # noqa: E501
from tagbase_server.telemetry import record_db_error

logger = logging.getLogger(__name__)

_SCHEMA_READY = False


def assert_schema_ready(conn):
    """Fail fast with a clear message when tagbase tables were never initialized.

    Common cause: kartoza skipped /docker-entrypoint-initdb.d after a stale
    SCRIPTS_LOCKFILE_DIR lock while postgis-data was recreated.
    """
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return
    with conn.cursor() as cur:
        cur.execute("SELECT to_regclass('public.submission')")
        if cur.fetchone()[0] is None:
            raise RuntimeError(
                "Tagbase schema is missing (relation 'submission' does not exist). "
                "Ensure services/postgis/tagbase_schema_tables.sql ran on init "
                "(reset postgis-data and clear SCRIPTS_LOCKFILE_DIR / postgis-lockfiles "
                "so kartoza does not skip init scripts)."
            )
    # End the implicit transaction so callers can still set conn.autocommit.
    conn.rollback()
    _SCHEMA_READY = True


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
            host=os.getenv("POSTGRES_HOST", "postgis"),
            port=os.getenv("POSTGRES_PORT"),
            password=os.getenv("POSTGRES_PASSWORD"),
        )
    except psycopg2.OperationalError as poe:
        record_db_error("connect")
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
    try:
        assert_schema_ready(conn)
    except RuntimeError:
        record_db_error("schema")
        logger.exception("Tagbase schema readiness check failed")
        raise
    logger.debug("Successfully connected to TagbaseDB.")
    return conn
