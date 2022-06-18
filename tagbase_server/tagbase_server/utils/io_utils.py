import logging
import os
import re
import tempfile
from urllib.request import urlopen

logger = logging.getLogger(__name__)


def process_get_input_data(file):
    """
    Capable of acquiring data over HTTP, HTTPS, FTP and FILE protocols.
    Data not already on the filesystem is saved to /tmp.

    :param file: The data file requested through the GET operation.
    :type file: str

    """
    data_file = file
    local_data_file = data_file[
        re.search(r"[file|ftp|http|https]://[^/]*", data_file).end() :
    ]
    logger.info(f"Acquiring: {local_data_file}")
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
    return data_file, submission_filename
