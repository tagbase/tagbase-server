import os
import logging
from datetime import datetime as dt
from io import StringIO
import time

import pandas as pd
import psycopg2.extras
import pytz
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from tzlocal import get_localzone

from tagbase_server.utils.db_utils import connect

logger = logging.getLogger(__name__)
slack_token = os.environ.get("SLACK_BOT_TOKEN", "")
slack_channel = os.environ.get("SLACK_BOT_CHANNEL", "tagbase-server")
client = WebClient(token=slack_token)


def process_global_attributes(
    line, cur, submission_id, metadata, submission_filename, line_counter
):
    tokens = line.strip()[1:].split(" = ")
    cur.execute(
        "SELECT attribute_id FROM metadata_types WHERE attribute_name = %s",
        (tokens[0],),
    )
    rows = cur.fetchall()
    if len(rows) == 0:
        msg = (
            f"*{submission_filename}* _line:{line_counter}_ - "
            f"Unable to locate attribute_name *{tokens[0]}* in _metadata_types_ table."
        )

        logger.warning(msg)
        try:
            client.chat_postMessage(
                channel=slack_channel, text="<!channel> :warning: " + msg
            )
        except SlackApiError as e:
            logger.error(e)
    else:
        str_submission_id = str(submission_id)
        str_row = str(rows[0][0])
        metadata.append((str_submission_id, str_row, tokens[1]))


def process_etuff_file(file, solution_id, notes=None):
    start = time.perf_counter()
    submission_filename = file[file.rindex("/") + 1 :]
    logger.info(
        "Processing etuff file: %s",
        submission_filename,
    )
    conn = connect()
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

            cur.execute("SELECT currval('submission_submission_id_seq')")
            submission_id = cur.fetchone()[0]

            metadata = []
            proc_obs = []
            s_time = time.perf_counter()
            with open(file, "rb") as data:
                lines = [line.decode("utf-8", "ignore") for line in data.readlines()]
                variable_lookup = {}
                line_counter = 0
                for line in lines:
                    line_counter += 1
                    if line.startswith("//"):
                        continue
                    elif line.strip().startswith(":"):
                        process_global_attributes(
                            line,
                            cur,
                            submission_id,
                            metadata,
                            submission_filename,
                            line_counter,
                        )
                    else:
                        # Parse proc_observations
                        tokens = line.split(",")
                        tokens = [token.replace('"', "") for token in tokens]
                        if tokens:
                            variable_name = tokens[3]
                            if variable_name in variable_lookup:
                                variable_id = variable_lookup[variable_name]
                            else:
                                cur.execute(
                                    "SELECT variable_id FROM observation_types WHERE variable_name = %s",
                                    (variable_name,),
                                )
                                row = cur.fetchone()
                                if row:
                                    variable_id = row[0]
                                else:
                                    try:
                                        logger.info(variable_name, tokens.strip())
                                        cur.execute(
                                            "INSERT INTO observation_types("
                                            "variable_name, variable_units) VALUES (%s, %s) "
                                            "ON CONFLICT (variable_name) DO NOTHING",
                                            (variable_name, tokens[4].strip()),
                                        )
                                    except (
                                        Exception,
                                        psycopg2.DatabaseError,
                                    ) as error:
                                        logger.error(
                                            "variable_id '%s' already exists in 'observation_types'. tokens:"
                                            " '%s. \nerror: " % s,
                                            variable_name,
                                            tokens,
                                            error,
                                        )
                                        conn.rollback()
                                    cur.execute(
                                        "SELECT nextval('observation_types_variable_id_seq')"
                                    )
                                    variable_id = cur.fetchone()[0]
                                variable_lookup[variable_name] = variable_id
                            date_time = None
                            if tokens[0] != '""' and tokens[0] != "":
                                if tokens[0].startswith('"'):
                                    tokens[0].replace('"', "")
                                date_time = dt.strptime(
                                    tokens[0], "%Y-%m-%d %H:%M:%S"
                                ).astimezone(pytz.utc)
                            else:
                                stripped_line = line.strip("\n")
                                msg = (
                                    f"*{submission_filename}* _line:{line_counter}_ - "
                                    f"No datetime... skipping line: {stripped_line}"
                                )
                                logger.warning(msg)
                                try:
                                    client.chat_postMessage(
                                        channel=slack_channel,
                                        text="<!channel> :warning: " + msg,
                                    )
                                except SlackApiError as e:
                                    logger.error(e)
                                continue
                            proc_obs.append(
                                [
                                    date_time,
                                    variable_id,
                                    tokens[2],
                                    submission_id,
                                    str(submission_id),
                                ]
                            )
            len_proc_obs = len(proc_obs)
            e_time = time.perf_counter()
            sub_elapsed = round(e_time - s_time, 2)
            logger.info(
                "Built raw 'proc_observations' data structure from %s observations in: %s second(s)",
                len_proc_obs,
                sub_elapsed,
            )

            for x in metadata:
                a = x[0]
                b = x[1]
                c = x[2]
                mog = cur.mogrify("(%s, %s, %s, %s)", (a, b, str(c), submission_id))
                cur.execute(
                    "INSERT INTO metadata (submission_id, attribute_id, attribute_value, tag_id) VALUES "
                    + mog.decode("utf-8")
                )
            logger.debug("metadata: %s", metadata)

            # build pandas df
            s_time = time.perf_counter()
            df = pd.DataFrame.from_records(
                proc_obs,
                columns=[
                    "date_time",
                    "variable_id",
                    "variable_value",
                    "submission_id",
                    "tag_id",
                ],
            )
            e_time = time.perf_counter()
            sub_elapsed = round(e_time - s_time, 2)
            logger.info(
                "Built Pandas DF from %s records. Time elapsed: %s second(s)",
                len_proc_obs,
                sub_elapsed,
            )
            logger.debug("DF Info: %s", df.info)
            logger.debug("DF Memory Usage: %s", df.memory_usage(True))

            # save dataframe to StringIO memory buffer
            s_time = time.perf_counter()
            buffer = StringIO()
            df.to_csv(buffer, header=False, index=False)
            buffer.seek(0)
            e_time = time.perf_counter()
            sub_elapsed = round(e_time - s_time, 2)
            logger.info(
                "Copied Pandas DF to StringIO memory buffer. Time elapsed: %s second(s)",
                sub_elapsed,
            )

            # copy buffer to db
            s_time = time.perf_counter()
            logger.info(
                "Copying memory buffer to 'proc_observations' and executing 'data_migration' TRIGGER."
            )
            try:
                cur.copy_from(buffer, "proc_observations", sep=",")
            except (Exception, psycopg2.DatabaseError) as error:
                logger.error("Error: %s", error)
                conn.rollback()
                return 1
            e_time = time.perf_counter()
            sub_elapsed = round(e_time - s_time, 2)
            logger.info(
                "Successful migration of %s 'proc_observations'. Elapsed time: %s second(s).",
                len_proc_obs,
                sub_elapsed,
            )

    conn.commit()

    cur.close()
    conn.close()

    finish = time.perf_counter()
    elapsed = round(finish - start, 2)
    logger.info(
        "Data file %s successfully ingested into Tagbase DB. Total time: %s second(s)",
        submission_filename,
        elapsed,
    )
