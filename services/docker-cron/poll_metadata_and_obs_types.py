#!/usr/bin/env python3
import configparser
import os
import pandas as pd
import psycopg2
import requests

from io import StringIO


config = configparser.ConfigParser()
workdir = os.path.dirname(os.path.abspath(__file__))
configfile = os.path.join(workdir, "config.ini")
config.read(configfile)


def pull_resource(connection=None, key=None, param=None):
    """
    :param connection: An instantiated connection to TagbaseDB.
    :param key: The key to lookup in config.ini
    :param param: The value to lookup in config.ini
    """
    col_names = []
    if param == "metadata_types":
        col_names=[
            "attribute_id",
            "category",
            "attribute_name",
            "description",
            "example",
            "comments",
            "necessity"]
    else:
        # must be observation_types
        col_names=[
            "variable_id",
            "variable_name",
            "standard_name",
            "variable_source",
            "variable_units",
            "notes",
            "standard_unit"]
    df = pd.read_csv(config.get(key, param), names=col_names, 
        encoding="utf-8", 
        on_bad_lines="error", 
        quotechar='"', 
        header=0, 
        index_col=False)

    with connection:
        with connection.cursor() as cur:
            try:
                cur.execute(f"TRUNCATE TABLE {param} CASCADE;")
                connection.commit()
                print("Successfully truncated table:", param)
            except (Exception, psycopg2.DatabaseError) as error:
                print("Error truncating table:", param)
                conn.rollback()
                return 1
            buffer = StringIO()
            df.to_csv(buffer, columns=col_names, header=False, index=False)
            buffer.seek(0)
            try:
                cur.copy_from(buffer, param, sep=",", null="NaN")
                connection.commit()
            except (Exception, psycopg2.DatabaseError) as error:
                print("Error writing data to table:", param, error)
                conn.rollback()
                return 1
            print("Successfully updated table:", param)


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
