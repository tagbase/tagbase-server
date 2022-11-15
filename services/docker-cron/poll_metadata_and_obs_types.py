import configparser
import logging
import os
import psycopg
import requests


config = configparser.ConfigParser()
config.read('config.ini')


def pull_resource(key=None, param=None):
    r = requests.get(config.get(key, param))
    with open(param + '.csv', 'w') as fd:
        fd.write(r.text)
    fd.close()
    conn.autocommit = True
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO submission (tag_id, filename, date_time, notes, solution_id) "
                "VALUES ((SELECT COALESCE(MAX(tag_id), NEXTVAL('submission_tag_id_seq')) "
                "FROM submission WHERE filename = %s), %s, %s, %s, %s)",
                (
                    submission_filename,
                    submission_filename,
                    dt.now(tz=pytz.utc).astimezone(get_localzone()),
                    notes,
                    solution_id,
                ),
            )
            logger.info(
                "Successful INSERT of '%s' into 'submission' table.",
                submission_filename,
            )


def connect():
    """
    Make and return a connection to TagbaseDB.
    :rtype: connection
    """
    try:
        tbc_connect = psycopg.connect(
            dbname="tagbase",
            user="tagbase",
            host="postgres",
            port=os.getenv("POSTGRES_PORT"),
            password=os.getenv("POSTGRES_PASSWORD"),
        )
    except psycopg.OperationalError as poe:
        print("Error connecting to DB: {}.", poe)
    return tbc_connect


def get_obs():
    return pull_resource('DATA', 'observation_types')


def get_metadata():
    return pull_resource('DATA', 'metadata_inventory')


if __name__ == "__main__":
    conn = connect()
    pull_resource(get_obs(), conn)
    pull_resource(get_metadata(), conn)
