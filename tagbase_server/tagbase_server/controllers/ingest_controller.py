import os
import re
import tempfile
from datetime import datetime as dt, timedelta
from time import time
from urllib.request import urlopen

import pytz
from tagbase_server.db_utils import connect
from tagbase_server.models.ingest200 import Ingest200  # noqa: E501
from tzlocal import get_localzone


def ingest_get(file, type=None):  # noqa: E501
    """Get network accessible file and execute ingestion

    Get network accessible file and execute ingestion # noqa: E501

    :param file: Location of a network accessible (file, ftp, http, https) file e.g. &#39;file:///usr/src/app/data/eTUFF-sailfish-117259.txt&#39;
    :type file: str
    :param type: Type of file to be ingested, defaults to &#39;etuff&#39;
    :type type: str

    :rtype: Ingest200
    """
    start = time()
    variable_lookup = {}
    # Check if file exists locally, if not download it to /tmp
    data_file = file
    local_data_file = data_file[
        re.search(r"[file|ftp|http|https]://[^/]*", data_file).end() :
    ]
    # app.logger.info("Locating %s" % local_data_file)
    if os.path.isfile(local_data_file):
        data_file = local_data_file
    else:
        # Download data file
        filename = tempfile.TemporaryFile(
            dir="/tmp/" + data_file[data_file.rindex("/") + 1 :], mode='"w+"'
        )
        response = urlopen(data_file)
        chunk_size = 16 * 1024
        with open(filename, "wb") as f:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)

        data_file = filename
    submission_filename = data_file[data_file.rindex("/") + 1 :]

    conn = connect()
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO submission (tag_id, filename, date_time) "
                "VALUES ((SELECT COALESCE(MAX(tag_id), NEXTVAL('submission_tag_id_seq')) "
                "FROM submission WHERE filename = %s), %s, %s)",
                (
                    submission_filename,
                    submission_filename,
                    dt.now(tz=pytz.utc).astimezone(get_localzone()),
                ),
            )
            # app.logger.info("Successfully staged INSERT into tagbase.submission")
            cur.execute("SELECT currval('submission_submission_id_seq')")
            submission_id = cur.fetchone()[0]

            if data_file.endswith(".gz"):
                filename = tempfile.TemporaryFile(
                    dir="/tmp/" + data_file[data_file.rindex("/") + 1 : -3], mode='"w+"'
                )
                with gzip.open(data_file, "rb") as f_in:
                    with open(filename, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                        data_file = filename

            metadata = []
            proc_obs = []
            with open(data_file, "r") as data:
                lines = data.readlines()
                etag = False
                for line in lines:
                    if line.startswith("//"):
                        if "etag" in line:
                            etag = True
                        else:
                            etag = False
                    elif line.strip().startswith(":"):
                        if etag:
                            # Parse global attributes
                            tokens = line.strip()[1:].split(" = ")
                            cur.execute(
                                "SELECT attribute_id FROM metadata_types WHERE attribute_name = %s",
                                (tokens[0],),
                            )
                            rows = cur.fetchall()
                            if len(rows) == 0:
                                # app.logger.warning(
                                # "Unable to locate attribute_name = %s in metadata_types" % tokens[0])
                                continue
                            else:
                                str_submission_id = str(submission_id)
                                str_row = str(rows[0][0])
                                metadata.append(
                                    (str_submission_id, str_row, tokens[1])
                                )  # .replace('"', '')
                    else:
                        # Parse variable values
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
                                    # Log error if variable_name doesn't already exist in observation_types
                                    cur.execute(
                                        "INSERT INTO observation_types(variable_name, variable_units) VALUES (%s, %s) "
                                        "ON CONFLICT (variable_name) DO NOTHING",
                                        (variable_name, tokens[4].strip()),
                                    )
                                    # app.logger.info("Successfully staged INSERT into tagbase.proc_observations")
                                    cur.execute(
                                        "SELECT currval('observation_types_variable_id_seq')"
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
                                # row begins with an empty datetime string, ignore
                                continue

                            proc_obs.append(
                                (date_time, variable_id, tokens[2], submission_id)
                            )
            for x in metadata:
                a = x[0]
                b = x[1]
                c = x[2]
                mog = cur.mogrify("(%s, %s, %s, %s)", (a, b, c, str(submission_id)))
                cur.execute(
                    "INSERT INTO metadata (submission_id, attribute_id, attribute_value, tag_id) VALUES "
                    + mog.decode("utf-8")
                )
                # app.logger.info("Successfully staged INSERT into tagbase.metadata")

            # The following logic is necessary in order to automate the execution of the data migration trigger.
            # We do this by making an explicit reference to a 'final_value' column in the proc_observations table
            # where the 'final_value' is indicated with a FALSE boolean value unless it is the last observation
            # (last row insert) meaning that its value is changed to TRUE. A TRUE value trigger a data migration.
            for x in proc_obs[:-1]:
                a = x[0]
                b = x[1]
                c = x[2]
                d = x[3]

                mog = cur.mogrify(
                    "(%s, %s, %s, %s, %s, %s)",
                    (a, b, c, d, str(submission_id), "FALSE"),
                )
                cur.execute(
                    "INSERT INTO proc_observations ("
                    "date_time, variable_id, variable_value, submission_id, tag_id, final_value) VALUES "
                    + mog.decode("utf-8")
                )

            # For the final value sensor reading we enter a 'final_value' of
            # TRUE to invoke the trigger function for migration.
            x = proc_obs[-1]
            a = x[0]
            b = x[1]
            c = x[2]
            d = x[3]

            mog = cur.mogrify(
                "(%s, %s, %s, %s, %s, %s)", (a, b, c, d, str(submission_id), "TRUE")
            )
            cur.execute(
                "INSERT INTO proc_observations ("
                "date_time, variable_id, variable_value, submission_id, tag_id, final_value) VALUES "
                + mog.decode("utf-8")
            )
            # app.logger.info("Successfully staged INSERT into tagbase.proc_observations")

    conn.commit()

    cur.close()
    conn.close()

    end = time()
    # app.logger.info(
    # "Data file %s has been ingested into tagbase. Time took to ingest file: %s s" % (data, (end - start)))
    return Ingest200.from_dict(
        {
            "code": "200",
            "elapsed": str(timedelta(seconds=(end - start))),
            "message": "Data file %s successfully ingested into Tagbase DB."
            % submission_filename,
        }
    )


def tz_aware(dt):
    """Convenience function to determine whether a datetime
    has been localized or not. If it has, tzinfo and utcoffset
    information will be present.
    """
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        return False
    elif dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None:
        return True


def ingest_post(type=None, etuff_body=None):  # noqa: E501
    """Post a local file and perform a ingest operation

    Post a local file and perform a ingest operation # noqa: E501

    :param type: Type of file to be ingested, defaults to &#39;etuff&#39;
    :type type: str
    :param etuff_body:
    :type etuff_body: str

    :rtype: Ingest200
    """
    return "do some magic!"
