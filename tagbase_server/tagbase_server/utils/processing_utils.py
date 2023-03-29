import logging
from datetime import datetime as dt
from io import StringIO
import time

import pandas as pd
import psycopg2.extras
import pytz
from tzlocal import get_localzone

from tagbase_server.utils.db_utils import connect
from tagbase_server.utils.slack_utils import post_msg

logger = logging.getLogger(__name__)


def process_all_lines_for_global_attributes(
    global_attributes_lines,
    cur,
    submission_id,
    metadata,
    submission_filename,
    line_counter,
):
    attrbs_map = {}
    for line in global_attributes_lines:
        line = line.strip()
        logger.debug("Processing global attribute: %s", line)
        tokens = line[1:].split(" = ")
        # attribute_name = tokens[0], attribute_value = tokens[1]
        if len(tokens) > 1:
            attrbs_map[tokens[0]] = tokens[1]
        else:
            logger.warning("Metadata line %s NOT in expected format!", line)

    attrbs_names = ", ".join(
        ["'{}'".format(attrib_name) for attrib_name in attrbs_map.keys()]
    )
    attrbs_ids_query = (
        "SELECT attribute_id, attribute_name FROM metadata_types "
        "WHERE attribute_name IN ({})".format(attrbs_names)
    )
    logger.debug("Query=%s", attrbs_ids_query)
    cur.execute(attrbs_ids_query)
    rows = cur.fetchall()

    str_submission_id = str(submission_id)
    for row in rows:
        attribute_id = row[0]
        attribute_name = row[1]
        attribute_value = attrbs_map[attribute_name]
        metadata.append((str_submission_id, str(attribute_id), attribute_value))
        attrbs_map.pop(attribute_name)

    if len(attrbs_map.keys()) > 0:
        not_found_attributes = ", ".join(attrbs_map.keys())
        msg = (
            f"*{submission_filename}* _line:{line_counter}_ - "
            f"Unable to locate attribute_names *{not_found_attributes}* in _metadata_types_ table."
        )
        post_msg(msg)


def process_global_attributes(lines, cur, submission_id, metadata, submission_filename):
    processed_lines = 0
    global_attributes = []
    for line in lines:
        processed_lines += 1
        if line.startswith("//"):
            continue
        elif line.strip().startswith(":"):
            global_attributes.append(line)
        else:
            break

    process_all_lines_for_global_attributes(
        global_attributes,
        cur,
        submission_id,
        metadata,
        submission_filename,
        processed_lines,
    )
    return processed_lines - 1 if processed_lines > 0 else 0


def process_etuff_file(file, version=None, notes=None):
    start = time.perf_counter()
    submission_filename = file  # full path name is now preferred rather than - file[file.rindex("/") + 1 :]
    logger.info(
        "Processing etuff file: %s",
        submission_filename,
    )
    conn = connect()
    conn.autocommit = True
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO submission (tag_id, filename, date_time, notes, version) "
                "VALUES ((SELECT COALESCE(MAX(tag_id), NEXTVAL('submission_tag_id_seq')) "
                "FROM submission WHERE filename = %s), %s, %s, %s, %s)",
                (
                    submission_filename,
                    submission_filename,
                    dt.now(tz=pytz.utc).astimezone(get_localzone()),
                    notes,
                    version,
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
            lines_length = len(lines)

            line_counter = 0
            variable_lookup = {}

            metadata_lines = process_global_attributes(
                lines, cur, submission_id, metadata, submission_filename
            )
            line_counter += metadata_lines

            for counter in range(metadata_lines, lines_length):
                line = lines[line_counter]
                line_counter += 1
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
                                logger.debug(
                                    "variable_name=%s\ttokens=%s", variable_name, tokens
                                )
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
                                    " '%s. \nerror: %s",
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
                        post_msg(msg)
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
