import logging
from datetime import datetime as dt
from io import StringIO
import time

import pandas as pd
import psycopg2.extras
import pytz
from tzlocal import get_localzone

from tagbase_server.utils.db_utils import connect
from tagbase_server.utils.io_utils import compute_file_sha256, make_hash_sha256
from tagbase_server.utils.slack_utils import post_msg

logger = logging.getLogger(__name__)


def process_global_attributes_metadata(
    global_attributes_lines,
    cur,
    submission_id,
    submission_filename,
    line_counter,
):
    attributes_map = {}
    metadata = []
    for line in global_attributes_lines:
        line = line.strip()
        logger.debug("Processing global attribute: %s", line)
        tokens = line[1:].split(" = ")
        # attribute_name = tokens[0], attribute_value = tokens[1]
        if len(tokens) > 1:
            attributes_map[tokens[0]] = tokens[1]
        else:
            logger.warning("Metadata line %s NOT in expected format!", line)

    attributes_names = ", ".join(
        ["'{}'".format(attrib_name) for attrib_name in attributes_map.keys()]
    )
    attribute_ids_query = (
        "SELECT attribute_id, attribute_name FROM metadata_types "
        "WHERE attribute_name IN ({})".format(attributes_names)
    )
    logger.debug("Query=%s", attribute_ids_query)
    cur.execute(attribute_ids_query)
    rows = cur.fetchall()

    str_submission_id = str(submission_id)
    for row in rows:
        attribute_id = row[0]
        attribute_name = row[1]
        attribute_value = attributes_map[attribute_name]
        metadata.append((str_submission_id, str(attribute_id), attribute_value))
        attributes_map.pop(attribute_name)

    if len(attributes_map.keys()) > 0:
        not_found_attributes = ", ".join(attributes_map.keys())
        msg = (
            f"*{submission_filename}* _line:{line_counter}_ - "
            f"Unable to locate attribute_names *{not_found_attributes}* in _metadata_types_ table."
        )
        post_msg(msg)
    return metadata


def get_tag_id(cur, dataset_id):
    """
    Retrieve a 'tag_id' for a submission by performing a lookup on the 'dataset_id'.
    If an entry exists for the dataset then grab the existing associated tag_id. If not,
    create a new tag_id.

    :param cur: A database cursor
    :type cur: cursor connection

    :param dataset_id: Dataset ID as described above.
    :type dataset_id: str
    """
    sql_query = "SELECT COALESCE(MAX(tag_id), NEXTVAL('submission_tag_id_seq')) FROM submission WHERE dataset_id = '{}'".format(
        dataset_id
    )
    logger.debug("Executing: %s", sql_query)
    cur.execute(sql_query)
    result = cur.fetchone()[0]
    logger.debug("Result: %s", result)
    return result


def get_dataset_id(cur, instrument_name, serial_number, ptt, platform):
    """
    Retreive or create a dataset entry for a submission. If a dataset entry exists then grab the existing
    id, if not, create a new one.

    :param cur: A database cursor
    :type cur: cursor connection

    :param instrument_name: A unique instrument name, made clear to the end user that it is the primary identifier, e.g., iccat_gbyp0008
    :type instrument_name: str

    :param serial_number: A the device internal ID, e.g., 18P0201
    :type serial_number: str

    :param ptt: A satellite platform ID, e.g., 62342
    :type ptt: str

    :param platform: The species code/common name on which the device was deployed, e.g., Thunnus thynnus
    :type platform: str
    """
    cur.execute(
        "SELECT COALESCE(MAX(dataset_id), NEXTVAL('dataset_dataset_id_seq')) FROM dataset WHERE instrument_name = '{}' AND serial_number = '{}' AND ptt = '{}' AND platform = '{}'".format(
            instrument_name, serial_number, ptt, platform
        )
    )
    dataset_id = cur.fetchone()[0]
    logger.debug("Computed dataset_id: %s", dataset_id)

    cur.execute(
        "INSERT INTO dataset (dataset_id, instrument_name, serial_number, ptt, platform) VALUES ('{}', '{}', '{}', '{}', '{}') ON CONFLICT DO NOTHING".format(
            dataset_id, instrument_name, serial_number, ptt, platform
        )
    )
    logger.debug(
        "Successful INSERT of '%s' into 'dataset' table.",
        dataset_id,
    )
    return dataset_id


def get_submission_id(cur, tag_id, dataset_id, data_sha256):
    cur.execute(
        "SELECT submission_id FROM submission"
        " WHERE tag_id = '{}' AND dataset_id = '{}'"
        " AND data_sha256 = '{}'".format(tag_id, dataset_id, data_sha256)
    )
    db_results = cur.fetchone()
    if not db_results:
        return None
    submission_id = db_results[0]
    logger.debug("Found submission_id: %s", submission_id)
    return submission_id


def insert_new_submission(
    cur,
    tag_id,
    submission_filename,
    notes,
    version,
    file_sha256,
    dataset_id,
    md_sha256,
    data_sha256,
):
    cur.execute(
        "INSERT INTO submission (tag_id, filename, date_time, notes, version, file_sha256, dataset_id, md_sha256, data_sha256) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (
            tag_id,
            submission_filename,
            dt.now(tz=pytz.utc).astimezone(get_localzone()),
            notes,
            version,
            file_sha256,
            dataset_id,
            md_sha256,
            data_sha256,
        ),
    )
    logger.info(
        "Successful INSERT of '%s' into 'submission' table.",
        submission_filename,
    )


def detect_duplicate_file(cursor, file_sha256):
    """
    Detect a duplicate file by performing a lookup on submission.file_sha256.
    Returns True if duplicate.

    :param file_sha256: A SHA256 hash of an entire eTUFF file.
    :type file_sha256: str

    :param cursor: A database cursor
    :type cursor: cursor connection
    """
    logger.debug("Detecting duplicate file submission...")
    cursor.execute(
        "SELECT file_sha256 FROM submission WHERE file_sha256 = %s",
        (file_sha256,),
    )
    db_results = cursor.fetchone()

    if not db_results:
        return False
    duplicate = db_results[0]

    logger.info(
        "Computed hash: %s Duplicate: %s",
        file_sha256,
        duplicate,
    )
    if duplicate is not None:
        return True
    else:
        return False


def get_dataset_properties(submission_filename):
    """
    Extract 'instrument_name', 'serial_number', 'ptt', 'platform' and
    'referencetrack_included' values from global attributesaa and calculate
    an SHA256 signature for the global metadata.

    :param submission_filename: The file from which we wish to extract certain global attributes
    :type submission_filename: str
    """
    global_attributes = {
        "instrument_name": "unknown",
        "serial_number": "unknown",
        "ppt": "unknown",
        "platform": "unknown",
        "referencetrack_included": "0",
    }

    content = []
    metadata_content = []
    processed_lines = 0
    with open(submission_filename, "rb") as file:
        for line in file:
            line = line.decode("utf-8", "ignore").strip()
            if line.startswith("//"):
                continue
            if line.startswith(":"):
                processed_lines += 1
                # keeping all metadata together
                metadata_content.append(line)
                value = line[1:].split(" = ")[1].replace('"', "")
                if line.startswith(":instrument_name"):
                    global_attributes["instrument_name"] = value
                elif line.startswith(":serial_number"):
                    global_attributes["serial_number"] = value
                elif line.startswith(":ptt"):
                    global_attributes["ppt"] = value
                elif line.startswith(":platform"):
                    global_attributes["platform"] = value
                elif line.startswith(":referencetrack_included"):
                    global_attributes["referencetrack_included"] = int(value)
            else:
                content.append(line)

    # we use zero-based indexing for accessing array of lines later on
    processed_lines = processed_lines - 1 if processed_lines > 0 else 0

    return (
        global_attributes["instrument_name"],
        global_attributes["serial_number"],
        global_attributes["ppt"],
        global_attributes["platform"],
        global_attributes["referencetrack_included"],
        content,
        metadata_content,
        processed_lines,
    )


def is_only_metadata_change(cursor, metadata_hash, file_data_hash):
    logger.debug("Detecting metadata submitted...")
    cursor.execute(
        "SELECT md_sha256 FROM submission WHERE md_sha256 <> %s AND data_sha256 = %s ",
        (
            metadata_hash,
            file_data_hash,
        ),
    )
    db_results = cursor.fetchone()

    if not db_results:
        return False
    different_metadata_stored = db_results[0]

    logger.info(
        "Computed metadata hash: %s stored: %s",
        metadata_hash,
        different_metadata_stored,
    )
    if different_metadata_stored:
        return True
    else:
        return False


def insert_metadata(cur, metadata, tag_id):
    for x in metadata:
        a = x[0]
        b = x[1]
        c = x[2]
        mog = cur.mogrify("(%s, %s, %s, %s)", (a, b, str(c).strip('"'), tag_id))
        cur.execute(
            "INSERT INTO metadata (submission_id, attribute_id, attribute_value, tag_id) VALUES "
            + mog.decode("utf-8")
        )


def get_current_submission_id(cur):
    cur.execute("SELECT currval('submission_submission_id_seq')")
    submission_id = cur.fetchone()[0]
    logger.debug("New submission_id=%d", submission_id)
    return submission_id


def update_submission_metadata(
    cur, tag_id, metadata, submission_id, dataset_id, metadata_hash
):
    # update submission information
    current_time = dt.now(tz=pytz.utc).astimezone(get_localzone())
    update_submission_info_query = (
        "UPDATE submission SET md_sha256 = '{}', date_time = '{}' "
        "WHERE tag_id = {} AND dataset_id = {} AND submission_id = {}".format(
            metadata_hash, current_time, tag_id, dataset_id, submission_id
        )
    )
    cur.execute(update_submission_info_query)
    logger.info(
        "Submission_id=%s updated with metadata hash=%s", submission_id, metadata_hash
    )

    # delete previous metadata since we are going to override it
    delete_md_query = (
        "DELETE FROM metadata WHERE submission_id = {} AND tag_id = {}".format(
            submission_id, tag_id
        )
    )
    cur.execute(delete_md_query)
    logger.debug(
        "Removed old metadata from submission_id=%s tag_id=%s", submission_id, tag_id
    )

    # insert new metadata
    insert_metadata(cur, metadata, submission_id)
    logger.info("Updated metadata attributes: %s", metadata)


def process_etuff_file(file, version=None, notes=None):
    start = time.perf_counter()
    submission_filename = file  # full path name is now preferred rather than - file[file.rindex("/") + 1 :]
    logger.info(
        "Processing etuff file: %s",
        submission_filename,
    )

    conn = connect()
    conn.autocommit = True

    (
        instrument_name,
        serial_number,
        ptt,
        platform,
        referencetrack_included,
        file_content,
        metadata_content,
        number_global_attributes_lines,
    ) = get_dataset_properties(submission_filename)
    content_hash = make_hash_sha256(file_content)
    metadata_hash = make_hash_sha256(metadata_content)
    entire_file_hash = compute_file_sha256(submission_filename)
    logger.debug(
        "Content Hash: %s\tMetadata Hash: %s\tFile Hash: %s",
        content_hash,
        metadata_hash,
        entire_file_hash,
    )

    with conn:
        with conn.cursor() as cur:
            if detect_duplicate_file(cur, entire_file_hash):
                logger.info(
                    "Data file '%s' with SHA256 hash '%s' identified as exact duplicate. No ingestion performed.",
                    submission_filename,
                    entire_file_hash,
                )
                return 1

            dataset_id = get_dataset_id(
                cur, instrument_name, serial_number, ptt, platform
            )
            tag_id = get_tag_id(cur, dataset_id)
            submission_id = get_submission_id(
                cur,
                tag_id,
                dataset_id,
                content_hash,
            )

            if not submission_id:
                insert_new_submission(
                    cur,
                    tag_id,
                    submission_filename,
                    notes,
                    version,
                    entire_file_hash,
                    dataset_id,
                    metadata_hash,
                    content_hash,
                )
                submission_id = get_current_submission_id(cur)

            # compute global attributes which are considered as metadata
            metadata = process_global_attributes_metadata(
                metadata_content,
                cur,
                submission_id,
                submission_filename,
                number_global_attributes_lines,
            )

            if is_only_metadata_change(cur, metadata_hash, content_hash):
                update_submission_metadata(
                    cur, tag_id, metadata, submission_id, dataset_id, metadata_hash
                )
                return 1

            # at this point we have already read form the file all global attribute lines
            proc_obs = []
            variable_lookup = {}

            s_time = time.perf_counter()
            num_lines_content = len(file_content)
            logger.debug(
                "len number_global_atttributes_lines: '%s' len lines_length: '%s'",
                number_global_attributes_lines,
                num_lines_content,
            )

            for counter in range(0, num_lines_content):
                line = file_content[counter]
                counter += 1
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
                                    "variable_name=%s\ttokens=%s",
                                    variable_name,
                                    tokens,
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
                            f"*{submission_filename}* _line:{counter}_ - "
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
                            tag_id,
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

            insert_metadata(cur, metadata, tag_id)

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
                "Copying memory buffer to 'proc_observations' and executing data migration."
            )
            try:
                cur.copy_from(buffer, "proc_observations", sep=",")
                ref = bool(referencetrack_included)
                logger.debug(
                    "Executing sp_execute_data_migration(%s, %s);",
                    int(submission_id),
                    ref,
                )
                cur.execute(
                    "CALL sp_execute_data_migration(%s, %s);", (int(submission_id), ref)
                )
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
