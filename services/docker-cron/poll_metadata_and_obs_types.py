#!/usr/bin/env python3
import configparser
import os
import psycopg2
import requests


config = configparser.ConfigParser()
config.read("config.ini")


def pull_resource(connection=None, key=None, param=None):
    """

    :param connection: An instantiated connection to TagbaseDB.
    :param key: The key to lookup in config.ini
    :param param: The value to lookup in config.ini
    """
    r = requests.get(config.get(key, param))
    file_name = param + ".csv"
    with open(file_name, "w") as f:
        f.write(r.text)
    f.close()
    with connection:
        with connection.cursor() as cur:
            # cur.execute(f"TRUNCATE {param};")
            f = open(file_name, "r", encoding="utf-8")
            if param == "metadata_types":
                cur.copy_from(
                    f,
                    param,
                    sep=",",
                    columns=(
                        "attribute_id",
                        "category",
                        "attribute_name",
                        "description",
                        "example",
                        "comments",
                        "necessity",
                    ),
                )
            else:
                # must be observation_types
                cur.copy_from(
                    f,
                    param,
                    sep=",",
                    columns=(
                        "variable_id",
                        "variable_name",
                        "standard_name",
                        "variable_source",
                        "variable_units",
                        "notes",
                        "standard_units",
                    ),
                )
            f.close()
            print("Successfully updated '%s' table.", param)


def connect():
    """
    Make and return a connection to TagbaseDB.
    :rtype: connection
    """
    try:
        conn = psycopg2.connect(
            dbname="tagbase",
            user="tagbase",
            host="postgres",
            port=os.getenv("POSTGRES_PORT"),
            password=os.getenv("POSTGRES_PASSWORD"),
        )
    except psycopg2.OperationalError as poe:
        print("Error connecting to DB: ", poe)
    return conn


def get_metadata(connection):
    return pull_resource(connection, "DATA", "metadata_types")


def get_obs(connection=None):
    return pull_resource(connection, "DATA", "observation_types")


if __name__ == "__main__":
    conn = connect()
    get_metadata(conn)
    get_obs(conn)
