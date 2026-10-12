import logging
import os
import tempfile
import time
import uuid
from functools import partial
from multiprocessing import cpu_count
from urllib.parse import urlparse

import parmap
from tqdm import tqdm as std_tqdm

from tagbase_server.archives import (
    ArchiveError,
    logical_filename,
    materialize,
    preflight,
)
from tagbase_server.ingest_jobs import IngestJobError, enqueue_job, fetch_job
from tagbase_server.models.ingest200 import Ingest200  # noqa: E501
from tagbase_server.problem import (
    TYPE_HTTP,
    TagbaseClientError,
    as_json,
    current_trace_id,
)
from tagbase_server.telemetry import get_tracer, record_ingest_request
from tagbase_server.upload_stream import job_max_bytes, staged_upload, sync_max_bytes
from tagbase_server.utils.io_utils import (
    TEMP_DIR,
    process_get_input_data,
    process_post_input_data,
)
from tagbase_server.utils.processing_utils import process_etuff_file

logger = logging.getLogger(__name__)

SUPPORTED_INGEST_FILE_TYPE = "etuff"


def _resolve_ingest_file_type(type):
    ingest_file_type = type if type is not None else SUPPORTED_INGEST_FILE_TYPE
    if ingest_file_type != SUPPORTED_INGEST_FILE_TYPE:
        raise TagbaseClientError(
            f"Unsupported ingest file type '{ingest_file_type}'; only '{SUPPORTED_INGEST_FILE_TYPE}' is supported."
        )
    return ingest_file_type


def _ingest_progress_bar(data_file):
    """Create a standard stdout progress bar for ingestion."""
    return partial(std_tqdm, desc=f"Ingesting: {data_file}")


def _ingest_member(item, version=None, notes=None):
    path, name = item
    return process_etuff_file(path, version=version, notes=notes, submission_name=name)


def _run_ingest_queue(prepared, version, notes, data_file):
    members = list(zip(prepared.files, prepared.submission_names(), strict=True))
    parmap.map(
        _ingest_member,
        members,
        version=version,
        notes=notes,
        pm_parallel=False,
        pm_processes=cpu_count(),
        pm_pbar=_ingest_progress_bar(data_file),
    )


def _ingest_with_telemetry(operation_name, work):
    tracer = get_tracer()
    start = time.perf_counter()
    outcome = "success"
    try:
        with tracer.start_as_current_span("ingest.handle") as span:
            span.set_attribute("ingest.operation", operation_name)
            return work()
    except TagbaseClientError:
        outcome = "client_error"
        raise
    except ValueError as exc:
        outcome = "client_error"
        raise TagbaseClientError(str(exc)) from exc
    except Exception:
        outcome = "server_error"
        raise
    finally:
        record_ingest_request(outcome, time.perf_counter() - start)


def _logical_from_url(file_url: str) -> str:
    path = urlparse(file_url).path or file_url
    return os.path.basename(path.rstrip("/"))


def _safe_remove(path: str | None) -> None:
    if not path:
        return
    try:
        if os.path.isfile(path):
            os.remove(path)
    except OSError:
        logger.exception("Failed to delete ingest file %s", path)


def _process_members(data_file, logical_name, version, notes, started):
    prepared = materialize(data_file, logical_name)
    try:
        logger.info("eTUFF ingestion queue: %s", prepared.submission_names())
        _run_ingest_queue(prepared, version, notes, data_file)
        elapsed = round(time.perf_counter() - started, 2)
        return as_json(
            Ingest200.from_dict(
                {
                    "code": "200",
                    "elapsed": elapsed,
                    "trace_id": current_trace_id(),
                    "message": f"Processing {len(prepared.files)} file(s) - {prepared.files}",
                }
            )
        )
    finally:
        try:
            prepared.cleanup()
        except OSError:
            logger.exception("Failed to delete extracted workspace for %s", data_file)


def _reject_sync_body(body) -> bytes:
    payload = body if isinstance(body, (bytes, bytearray)) else bytes(body)
    if len(payload) == 0:
        raise TagbaseClientError("Request body is empty.")
    if len(payload) > sync_max_bytes():
        raise TagbaseClientError(
            "Synchronous ingest accepts at most 100 MiB. Use POST /ingest/jobs.",
            title="Payload Too Large",
            type_=TYPE_HTTP,
            status=413,
        )
    return payload


def ingest_get(file, notes=None, type=None, type_=None, version=None):  # noqa: E501
    """Get network accessible file and execute ingestion."""

    def _work():
        ingest_file_type = _resolve_ingest_file_type(
            type_ if type_ is not None else type
        )
        logger.info("Ingest file type: %s", ingest_file_type)
        started = time.perf_counter()
        data_file = process_get_input_data(file)
        local = urlparse(file).path
        owned = data_file != local
        try:
            return _process_members(
                data_file,
                _logical_from_url(file),
                version,
                notes,
                started,
            )
        finally:
            if owned:
                _safe_remove(data_file)

    return _ingest_with_telemetry("get", _work)


def ingest_post(
    filename, body, notes=None, type=None, type_=None, version=None
):  # noqa: E501
    """Post a local file and perform a ingest operation."""

    def _work():
        ingest_file_type = _resolve_ingest_file_type(
            type_ if type_ is not None else type
        )
        logger.info("Ingest file type: %s", ingest_file_type)
        started = time.perf_counter()
        payload = _reject_sync_body(body)
        safe_name = logical_filename(filename)
        data_file = process_post_input_data(safe_name, payload)
        try:
            return _process_members(data_file, safe_name, version, notes, started)
        finally:
            _safe_remove(data_file)

    return _ingest_with_telemetry("post", _work)


def _stage_job_body(filename, body) -> str:
    staged = staged_upload.get()
    if staged:
        return staged
    payload = body if isinstance(body, (bytes, bytearray)) else bytes(body)
    if len(payload) == 0:
        raise TagbaseClientError("Request body is empty.")
    if len(payload) > job_max_bytes():
        raise TagbaseClientError(
            "Ingest jobs accept at most 2 GiB.",
            title="Payload Too Large",
            type_=TYPE_HTTP,
            status=413,
        )
    handle = tempfile.NamedTemporaryFile(
        dir=TEMP_DIR,
        prefix="tagbase-upload-",
        delete=False,
    )
    try:
        view = memoryview(payload)
        for offset in range(0, len(view), 1024 * 1024):
            handle.write(view[offset : offset + 1024 * 1024])
    finally:
        handle.close()
    return handle.name


def _isolate_upload(source_path):
    """Keep a POST body off the caller-supplied name so a later post cannot overwrite it."""
    unique = os.path.join(
        TEMP_DIR, f"{uuid.uuid4().hex}-{os.path.basename(source_path)}"
    )
    os.replace(source_path, unique)
    return unique


def create_ingest_job(
    filename, body, notes=None, type=None, type_=None, version=None
):  # noqa: E501
    """Stream a large upload into the ingest queue and return 202."""
    started = time.perf_counter()
    outcome = "accepted"
    stored = None
    try:
        _resolve_ingest_file_type(type_ if type_ is not None else type)
        staged = _stage_job_body(filename, body)
        try:
            preflight(staged, filename)
        except ArchiveError as exc:
            _safe_remove(staged)
            raise TagbaseClientError(str(exc)) from exc
        stored = _isolate_upload(staged)
        job_id = enqueue_job(
            source_path=stored,
            filename=filename,
            version=version,
            notes=notes,
        )
        return as_json({"id": job_id, "status": "queued"}, 202)
    except TagbaseClientError:
        outcome = "client_error"
        _safe_remove(stored)
        raise
    except IngestJobError:
        outcome = "server_error"
        _safe_remove(stored)
        logger.exception("Failed to queue ingest for %s", filename)
        raise
    except Exception:
        outcome = "server_error"
        _safe_remove(stored)
        raise
    finally:
        record_ingest_request(outcome, time.perf_counter() - started)


def get_ingest_job(job_id):  # noqa: E501
    """Return one ingest job."""
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
