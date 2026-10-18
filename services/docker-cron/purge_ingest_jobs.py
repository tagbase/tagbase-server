#!/usr/bin/env python3
"""Delete terminal ingest_job rows older than the retention window."""

import os
import sys

import psycopg2

DEFAULT_RETENTION_DAYS = 30


def retention_days():
    raw = os.getenv("INGEST_JOB_RETENTION_DAYS", str(DEFAULT_RETENTION_DAYS))
    return int(raw)


def connect():
    try:
        return psycopg2.connect(
            dbname="tagbase",
            user="tagbase",
            host="postgis",
            port=os.getenv("POSTGRES_PORT", "5432"),
            password=os.getenv("POSTGRES_PASSWORD", "tagbase"),
        )
    except psycopg2.OperationalError as error:
        print("Error connecting to DB: ", error)
        sys.exit(1)


def purge(connection, days):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            DELETE FROM ingest_job
            WHERE status IN ('succeeded', 'failed')
              AND updated_at < now() - (%s * interval '1 day')
            """,
            (days,),
        )
        deleted = cursor.rowcount
    connection.commit()
    return deleted


if __name__ == "__main__":
    window = retention_days()
    conn = connect()
    try:
        removed = purge(conn, window)
    finally:
        conn.close()
    print(f"Purged {removed} ingest_job row(s) older than {window} day(s)")
