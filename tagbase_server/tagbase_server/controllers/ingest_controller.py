import logging
import os
import time
import uuid

from tagbase_server.ingest_jobs import IngestJobError, enqueue_job, fetch_job
from tagbase_server.problem import TYPE_HTTP, TagbaseClientError, as_json
from tagbase_server.telemetry import record_ingest_request
from tagbase_server.utils.io_utils import (
    TEMP_DIR,
    process_get_input_data,
    process_post_input_data,
)

logger = logging.getLogger(__name__)

SUPPORTED_INGEST_FILE_TYPE = "etuff"


def _resolve_ingest_file_type(type):
    ingest_file_type = type if type is not None else SUPPORTED_INGEST_FILE_TYPE
    if ingest_file_type != SUPPORTED_INGEST_FILE_TYPE:
        raise TagbaseClientError(
            f"Unsupported ingest file type '{ingest_file_type}'; only '{SUPPORTED_INGEST_FILE_TYPE}' is supported."
        )
    return ingest_file_type


def _isolate_upload(source_path):
    """Keep a POST body off the caller-supplied name so a later post cannot overwrite it."""
    unique = os.path.join(
        TEMP_DIR, f"{uuid.uuid4().hex}-{os.path.basename(source_path)}"
    )
    os.replace(source_path, unique)
    return unique


def _accept(source_path, filename, version, notes, started):
    try:
        job_id = enqueue_job(
            source_path=source_path,
            filename=filename,
            version=version,
            notes=notes,
        )
    except IngestJobError:
        logger.exception("Failed to queue ingest for %s", filename)
        raise
    record_ingest_request("accepted", round(time.perf_counter() - started, 2))
    return as_json({"id": job_id, "status": "queued"}, 202)


def ingest_get(file, notes=None, type=None, type_=None, version=None):  # noqa: E501
    """Get network accessible file and execute ingestion

    :param file: Location of a network accessible (file, ftp, http, https) file
    :type file: str
    :param notes: Free-form text field
    :type notes: str
    :param type: Type of file to be ingested, defaults to 'etuff'
    :type type: str
    :param type_: Connexion pythonic alias for OpenAPI parameter ``type``
    :type type_: str
    :param version: Version identifier for the eTUFF tag data file ingested
    :type version: str

    :rtype: tuple
    """
    started = time.perf_counter()
    ingest_file_type = _resolve_ingest_file_type(type_ if type_ is not None else type)
    logger.info("Ingest file type: %s", ingest_file_type)
    try:
        data_file = process_get_input_data(file)
    except ValueError as exc:
        raise TagbaseClientError(str(exc)) from exc
    return _accept(data_file, os.path.basename(data_file), version, notes, started)


def ingest_post(
    filename, body, notes=None, type=None, type_=None, version=None
):  # noqa: E501
    """Post a local file and perform a ingest operation

    :param filename: Name of the file to be persisted
    :type filename: str
    :param body:
    :type body: str
    :param notes: Free-form text field
    :type notes: str
    :param type: Type of file to be ingested, defaults to 'etuff'
    :type type: str
    :param type_: Connexion pythonic alias for OpenAPI parameter ``type``
    :type type_: str
    :param version: Version identifier for the eTUFF tag data file ingested
    :type version: str

    :rtype: tuple
    """
    started = time.perf_counter()
    ingest_file_type = _resolve_ingest_file_type(type_ if type_ is not None else type)
    logger.info("Ingest file type: %s", ingest_file_type)
    data_file = process_post_input_data(filename, body)
    stored = _isolate_upload(data_file)
    return _accept(stored, filename, version, notes, started)


def get_ingest_job(job_id):  # noqa: E501
    """Return one ingest job.

    :param job_id: Job id returned by POST or GET /ingest
    :type job_id: str

    :rtype: tuple
    """
    try:
        job = fetch_job(job_id)
    except IngestJobError:
        logger.exception("Failed to read ingest job %s", job_id)
        raise
    if job is None:
        raise TagbaseClientError(
            f"Ingest job '{job_id}' was not found.",
            title="Not Found",
            type_=TYPE_HTTP,
            status=404,
        )
    return as_json(job)
