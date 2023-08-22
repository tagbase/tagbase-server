import hashlib
import logging
import os
import re
import tempfile
from time import time
from pyunpack import Archive
from urllib.request import urlopen

logger = logging.getLogger(__name__)


def compute_file_sha256(file_name):
    """
    A memory optimised way of computing SHA256 hash for a file.

    :param file_name: The data file to compute a SHA256 hash for.
    :type file_name: str
    """
    hash_sha256 = hashlib.sha256()
    with open(file_name, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def make_hash_sha256(o):
    hasher = hashlib.sha256()
    hasher.update(repr(make_hashable(o)).encode())
    return hasher.hexdigest()


def make_hashable(o):
    if isinstance(o, (tuple, list)):
        return tuple((make_hashable(e) for e in o))

    if isinstance(o, dict):
        return tuple(sorted((k, make_hashable(v)) for k, v in o.items()))

    if isinstance(o, (set, frozenset)):
        return tuple(sorted(make_hashable(e) for e in o))

    return o


def process_get_input_data(file):
    """
    Capable of acquiring data over HTTP, HTTPS, FTP and FILE protocols.
    Data not already on the filesystem is saved to /tmp.
    No explicit cleanup is performed per-se however details of the implementation
    can be found in https://docs.python.org/3/library/tempfile.html#tempfile.TemporaryFile
    All input is expected to have utf-8 encoding.

    :param file: The data file requested through the GET operation.
    :type file: str

    """
    data_file = file
    local_data_file = data_file[
        re.search(r"[file|ftp|http|https]://[^/]*", data_file).end() :
    ]
    if os.path.isfile(local_data_file):
        data_file = local_data_file
        logger.info("Found '%s' on filesystem.", local_data_file)
    else:
        logger.info("Acquiring '%s' from remote source.", data_file)
        filename = tempfile.TemporaryFile(
            dir="/tmp/" + data_file[data_file.rindex("/") + 1 :],
            encoding="utf-8",
            mode='"w"',
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
    logger.info(data_file)
    return data_file


def process_post_input_data(filename, body):
    """
    Writes POST data (application/octet-stream or text/plain) to /tmp
    No explicit /tmp cleanup is performed per-se however details of the implementation
    can be found in https://docs.python.org/3/library/tempfile.html#tempfile.TemporaryFile
    All input is expected to have utf-8 encoding.

    :param filename: Explicit name of the file to be written to disk.
    :type filename: str
    :param body: The data submitted via the POST operation.
    :type body: str

    """
    data = body
    filepath = "/tmp/" + filename
    with open(filepath, mode="wb") as f:
        f.write(data)
    f.close()
    logger.debug(filepath)
    return filepath


def unpack_compressed_binary(file):
    """
    Unpack a variety of compressed input files storing all .txt contents to /tmp.
    No explicit cleanup is performed per-se however details of the implementation
    can be found in https://docs.python.org/3/library/tempfile.html#tempfile.TemporaryFile
    For a list of files which can be processed, see
    https://pypi.org/project/patool/, and
    https://github.com/ponty/pyunpack

    :param file: The .zip or .tar.gz file containing one or more eTUFF .txt files.
    :type file: str
    """
    etuff_files = []
    temp_dir = "/tmp/" + str(time())
    if not os.path.exists(temp_dir):
        os.mkdir(temp_dir)
    logger.info("Unpacking %s archive to %s", file, temp_dir)
    Archive(file).extractall(temp_dir)
    for root, dirs, files in os.walk(temp_dir):
        for file in files:
            if file.endswith(".txt"):
                etuff_files.append(os.path.join(root, file))
    return etuff_files
