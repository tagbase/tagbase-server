"""OpenTelemetry bootstrap for tagbase-server.

SDK is off unless ``OTEL_EXPORTER_OTLP_ENDPOINT`` is set and
``OTEL_SDK_DISABLED`` is not true. Prefer standard OTEL_* environment variables.
"""

from __future__ import annotations

import logging
import os

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ALWAYS_ON

logger = logging.getLogger(__name__)

SERVICE_NAME = "tagbase_server"
SERVICE_VERSION = "v0.14.0"
METER_NAME = "tagbase_server"
TRACER_NAME = "tagbase_server"

_initialized = False
_ingest_requests = None
_ingest_duration = None
_ingest_rows_written = None
_db_errors = None


def telemetry_enabled() -> bool:
    disabled = os.getenv("OTEL_SDK_DISABLED", "").strip().lower()
    if disabled in ("true", "1", "yes"):
        return False
    return bool(os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip())


def get_tracer():
    return trace.get_tracer(TRACER_NAME)


def get_meter():
    return metrics.get_meter(METER_NAME)


def _ensure_instruments():
    global _ingest_requests, _ingest_duration, _ingest_rows_written, _db_errors
    meter = get_meter()
    if _ingest_requests is None:
        _ingest_requests = meter.create_counter(
            name="tagbase.ingest.requests",
            description="Ingest API requests by outcome",
            unit="1",
        )
    if _ingest_duration is None:
        _ingest_duration = meter.create_histogram(
            name="tagbase.ingest.duration",
            description="Ingest API wall time",
            unit="s",
        )
    if _ingest_rows_written is None:
        _ingest_rows_written = meter.create_counter(
            name="tagbase.ingest.rows_written",
            description="Observation rows written during successful ingest",
            unit="1",
        )
    if _db_errors is None:
        _db_errors = meter.create_counter(
            name="tagbase.db.errors",
            description="Database errors by operation",
            unit="1",
        )


def record_ingest_request(outcome: str, duration_seconds: float) -> None:
    _ensure_instruments()
    _ingest_requests.add(1, {"outcome": outcome})
    _ingest_duration.record(duration_seconds, {"outcome": outcome})


def record_rows_written(count: int) -> None:
    if count <= 0:
        return
    _ensure_instruments()
    _ingest_rows_written.add(count)


def record_db_error(operation: str) -> None:
    _ensure_instruments()
    _db_errors.add(1, {"operation": operation})


def setup_telemetry(flask_app=None) -> bool:
    """Initialize OTel providers and optional Flask instrumentation.

    Safe to call multiple times; subsequent calls are no-ops.
    Returns True when telemetry was (or already is) active.
    """
    global _initialized
    if _initialized:
        return True
    if not telemetry_enabled():
        logger.debug(
            "OpenTelemetry disabled (set OTEL_EXPORTER_OTLP_ENDPOINT to enable)"
        )
        return False

    endpoint = os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"].strip()
    service_name = os.getenv("OTEL_SERVICE_NAME", SERVICE_NAME).strip() or SERVICE_NAME
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": SERVICE_VERSION,
        }
    )

    # Traces — 100% sampling (v1)
    tracer_provider = TracerProvider(resource=resource, sampler=ALWAYS_ON)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(endpoint=endpoint, insecure=True),
        )
    )
    trace.set_tracer_provider(tracer_provider)

    # Metrics
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=endpoint, insecure=True),
        export_interval_millis=10000,
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    # Logs → OTLP (keep existing file/stdout handlers elsewhere)
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(
            OTLPLogExporter(endpoint=endpoint, insecure=True),
        )
    )
    otel_handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
    logging.getLogger().addHandler(otel_handler)

    LoggingInstrumentor().instrument(set_logging_format=True)
    Psycopg2Instrumentor().instrument()

    if flask_app is not None:
        from opentelemetry.instrumentation.flask import FlaskInstrumentor

        FlaskInstrumentor().instrument_app(flask_app)

    _ensure_instruments()
    _initialized = True
    logger.info(
        "OpenTelemetry enabled; exporting OTLP to %s (service.name=%s)",
        endpoint,
        service_name,
    )
    return True


def reset_telemetry_state_for_tests() -> None:
    """Test helper to clear init guards (does not shutdown SDK)."""
    global _initialized
    global _ingest_requests, _ingest_duration, _ingest_rows_written, _db_errors
    _initialized = False
    _ingest_requests = None
    _ingest_duration = None
    _ingest_rows_written = None
    _db_errors = None
