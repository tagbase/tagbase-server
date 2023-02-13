import logging
import os
import psycopg2
import psycopg2.extras

psycopg2.extras.register_uuid()
logger = logging.getLogger("rabbitmq_subscriber")


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
        return {
            "code": "500",
            "message": "Encountered psycopg2.OperationalError when attempting to establish a connection "
            "to the Tagbase database.",
            "more_info": "Contact the service administrator - {email}".format(
                email=os.getenv("PGADMIN_DEFAULT_EMAIL")
            ),
            "trace": poe,
        }
    logger.debug("Successfully connected to TagbaseDB.")
    return conn


def create_event(
    event_category=None,
    event_id=None,
    event_name=None,
    event_status=None,
    time_start=None,
):
    """
    Create a new event in the events_log table. Note the event_id UUID is not automatically generated.
    It must be passed to this function call.
    """
    logger.debug("Creating new event: %s in events log...", event_id)
    event_conn = connect()
    with event_conn:
        with event_conn.cursor() as event_cur:
            event_cur.execute(
                "INSERT INTO events_log (event_id, event_category, event_name, time_start, event_status) "
                "VALUES (%s, %s, %s, %s, %s)",
                (event_id, event_category, event_name, time_start, event_status),
            )
            logger.info(
                "CREATED new event: '%s'",
                str(event_id),
            )
    event_conn.commit()
    event_cur.close()
    event_conn.close()


def update_event(
    duration=None,
    event_id=None,
    event_status=None,
    submission_id=None,
    tag_id=None,
    time_end=None,
):
    """
    Update existing event in the events_log table with new data.
    """
    logger.debug(
        "Updating event: '%s' in events log...",
        event_id,
    )
    conn = connect()
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE events_log "
                "SET submission_id = %s, tag_id = %s, event_id = %s, time_end = %s, duration = %s, event_status = %s"
                " WHERE event_id = %s",
                (
                    submission_id,
                    tag_id,
                    event_id,
                    time_end,
                    duration,
                    event_status,
                    event_id,
                ),
            )
            logger.info(
                "UPDATED event: '%s'",
                str(event_id),
            )
    conn.commit()
    cur.close()
    conn.close()
