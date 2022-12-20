import logging
from multiprocessing import cpu_count
import time
import parmap

from tagbase_server.models.ingest200 import Ingest200  # noqa: E501
from tagbase_server.utils.io_utils import (
    process_get_input_data,
    process_post_input_data,
)
from tagbase_server.utils.io_utils import unpack_compressed_binary
from tagbase_server.utils.processing_utils import process_etuff_file

logger = logging.getLogger(__name__)


def ingest_get(file, notes=None, type=None, version=None):  # noqa: E501
    """Get network accessible file and execute ingestion

    Get network accessible file and execute ingestion # noqa: E501

    :param file: Location of a network accessible (file, ftp, http, https) file e.g. &#39;file:///usr/src/app/data/eTUFF-sailfish-117259.txt&#39;.
    :type file: str
    :param notes: Free-form text field where details of submitted eTUFF file for ingest can be provided e.g. submitter name, etuff data contents (tag metadata and measurements + primary position data, or just secondary solution-positional meta/data)
    :type notes: str
    :param type: Type of file to be ingested, defaults to &#39;etuff&#39;
    :type type: str
    :param version: Version identifier for the eTUFF tag data file ingested
    :type version: str

    :rtype: Union[Ingest200, Tuple[Ingest200, int], Tuple[Ingest200, int, Dict[str, str]]
    """
    start = time.perf_counter()
    data_file = process_get_input_data(file)
    etuff_files = []
    if not data_file.endswith(".txt"):
        etuff_files = unpack_compressed_binary(data_file)
    else:
        etuff_files.append(data_file)
    logger.info("etuff ingestion queue: %s", etuff_files)
    # if synchronous ingestion is desired then use parmap.map
    result = parmap.map_async(
        process_etuff_file,
        etuff_files,
        version=version,
        notes=notes,
        pm_parallel=True,
        pm_processes=cpu_count(),
    )
    finish = time.perf_counter()
    elapsed = round(finish - start, 2)
    return Ingest200.from_dict(
        {
            "code": "200",
            "elapsed": elapsed,
            "message": "Asynchronously ingesting %s file(s) into Tagbase DB."
            % len(etuff_files),
        }
    )


def ingest_post(
    filename=None, notes=None, type=None, version=None, body=None
):  # noqa: E501
    """Post a local file and perform a ingest operation

    Post a local file and perform a ingest operation # noqa: E501

    :param notes: Free-form text field to explicitly define the name of the file to be persisted
    :type notes: str
    :param notes: Free-form text field where details of submitted eTUFF file for ingest can be provided e.g. submitter name, etuff data contents (tag metadata and measurements + primary position data, or just secondary solution-positional meta/data)
    :type notes: str
    :param type: Type of file to be ingested, defaults to &#39;etuff&#39;
    :type type: str
    :param version: Version identifier for the eTUFF tag data file ingested
    :type version: str
    :param body: Payload body
    :type body: str

    :rtype: Union[Ingest200, Tuple[Ingest200, int], Tuple[Ingest200, int, Dict[str, str]]
    """
    start = time.perf_counter()
    data_file = process_post_input_data(filename, body)
    etuff_files = []
    if not data_file.endswith(".txt"):
        etuff_files = unpack_compressed_binary(data_file)
    else:
        etuff_files.append(data_file)
    logger.info("etuff ingestion queue: %s", etuff_files)
    # if synchronous ingestion is desired then use parmap.map
    result = parmap.map_async(
        process_etuff_file,
        etuff_files,
        version=version,
        notes=notes,
        pm_parallel=True,
        pm_processes=cpu_count(),
    )
    finish = time.perf_counter()
    elapsed = round(finish - start, 2)
    return Ingest200.from_dict(
        {
            "code": "200",
            "elapsed": elapsed,
            "message": "Asynchronously ingesting %s file(s) into Tagbase DB."
            % len(etuff_files),
        }
    )
