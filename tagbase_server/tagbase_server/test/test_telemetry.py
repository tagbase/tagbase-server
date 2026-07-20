"""Unit tests for OpenTelemetry enablement and bootstrap (no collector required)."""

import logging
from unittest import mock

import pytest

from tagbase_server import telemetry


@pytest.fixture(autouse=True)
def _reset_telemetry_env(monkeypatch):
    telemetry.reset_telemetry_state_for_tests()
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    monkeypatch.delenv("OTEL_SDK_DISABLED", raising=False)
    monkeypatch.delenv("OTEL_SERVICE_NAME", raising=False)
    yield
    telemetry.reset_telemetry_state_for_tests()
    # Drop any mock handlers left on the root logger by setup_telemetry stubs.
    root = logging.getLogger()
    for handler in list(root.handlers):
        if isinstance(handler, mock.Mock):
            root.removeHandler(handler)


def test_telemetry_disabled_without_endpoint():
    assert telemetry.telemetry_enabled() is False
    assert telemetry.setup_telemetry() is False


def test_telemetry_disabled_when_sdk_flag_set(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    monkeypatch.setenv("OTEL_SDK_DISABLED", "true")
    assert telemetry.telemetry_enabled() is False


def test_telemetry_enabled_when_endpoint_set(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    assert telemetry.telemetry_enabled() is True


def test_record_rows_written_skips_non_positive():
    telemetry.record_rows_written(0)
    telemetry.record_rows_written(-1)
    assert telemetry._ingest_rows_written is None


def _stub_setup_dependencies(monkeypatch):
    """Keep setup_telemetry offline and free of global provider conflicts."""
    monkeypatch.setattr(telemetry.trace, "set_tracer_provider", mock.Mock())
    monkeypatch.setattr(telemetry.metrics, "set_meter_provider", mock.Mock())
    monkeypatch.setattr(telemetry, "Resource", mock.Mock())
    monkeypatch.setattr(telemetry, "TracerProvider", mock.Mock())
    monkeypatch.setattr(telemetry, "BatchSpanProcessor", mock.Mock())
    monkeypatch.setattr(telemetry, "OTLPSpanExporter", mock.Mock())
    monkeypatch.setattr(telemetry, "PeriodicExportingMetricReader", mock.Mock())
    monkeypatch.setattr(telemetry, "OTLPMetricExporter", mock.Mock())
    monkeypatch.setattr(telemetry, "MeterProvider", mock.Mock())
    monkeypatch.setattr(telemetry, "LoggerProvider", mock.Mock())
    monkeypatch.setattr(telemetry, "BatchLogRecordProcessor", mock.Mock())
    monkeypatch.setattr(telemetry, "OTLPLogExporter", mock.Mock())

    otel_handler = mock.Mock()
    otel_handler.level = logging.NOTSET
    monkeypatch.setattr(
        telemetry, "LoggingHandler", mock.Mock(return_value=otel_handler)
    )
    monkeypatch.setattr(
        telemetry,
        "LoggingInstrumentor",
        mock.Mock(return_value=mock.Mock()),
    )
    monkeypatch.setattr(
        telemetry,
        "Psycopg2Instrumentor",
        mock.Mock(return_value=mock.Mock()),
    )
    monkeypatch.setattr(telemetry, "_ensure_instruments", mock.Mock())
    return otel_handler


def test_setup_telemetry_initializes_and_is_idempotent(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    monkeypatch.setenv("OTEL_SERVICE_NAME", "   ")  # blank → default SERVICE_NAME
    _stub_setup_dependencies(monkeypatch)

    assert telemetry.setup_telemetry() is True
    assert telemetry.setup_telemetry() is True  # already initialized
    telemetry._ensure_instruments.assert_called_once()


def test_setup_telemetry_instruments_flask_app(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    _stub_setup_dependencies(monkeypatch)

    flask_app = mock.Mock()
    flask_instrumentor = mock.Mock()
    with mock.patch(
        "opentelemetry.instrumentation.flask.FlaskInstrumentor",
        return_value=flask_instrumentor,
    ):
        assert telemetry.setup_telemetry(flask_app=flask_app) is True

    flask_instrumentor.instrument_app.assert_called_once_with(flask_app)


def test_record_helpers_use_instruments(monkeypatch):
    requests = mock.Mock()
    duration = mock.Mock()
    rows = mock.Mock()
    errors = mock.Mock()
    meter = mock.Mock()
    meter.create_counter.side_effect = [requests, rows, errors]
    meter.create_histogram.return_value = duration
    monkeypatch.setattr(telemetry, "get_meter", lambda: meter)

    telemetry.record_ingest_request("success", 0.01)
    requests.add.assert_called_once_with(1, {"outcome": "success"})
    duration.record.assert_called_once_with(0.01, {"outcome": "success"})

    telemetry.record_rows_written(3)
    rows.add.assert_called_once_with(3)

    telemetry.record_db_error("connect")
    errors.add.assert_called_once_with(1, {"operation": "connect"})
