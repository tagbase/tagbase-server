"""Unit tests for optional Pyroscope profiling (no profiler process required)."""

import builtins
import logging
import sys
import types
from unittest import mock

from opentelemetry.sdk.trace import TracerProvider

from tagbase_server import profiling


def setup_function():
    profiling.reset_profiling_state_for_tests()


def teardown_function():
    profiling.reset_profiling_state_for_tests()


def test_disabled_does_not_import_pyroscope(monkeypatch):
    monkeypatch.delenv("TAGBASE_PYROSCOPE_ENABLED", raising=False)
    real_import = builtins.__import__

    def guarded(name, *args, **kwargs):
        if name == "pyroscope" or name.startswith("pyroscope."):
            raise AssertionError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded)
    assert profiling.setup_profiling("ingest_worker") is False
    with profiling.phase("read", file="a.txt"):
        pass


def test_enabled_without_package_warns_and_stays_a_noop(monkeypatch, caplog):
    monkeypatch.setenv("TAGBASE_PYROSCOPE_ENABLED", "true")
    sys.modules.pop("pyroscope", None)
    sys.modules.pop("pyroscope.otel", None)
    real_import = builtins.__import__

    def guarded(name, *args, **kwargs):
        if name == "pyroscope" or name.startswith("pyroscope."):
            raise ImportError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded)
    with caplog.at_level(logging.WARNING):
        assert profiling.setup_profiling("ingest_worker") is False
    assert "not installed" in caplog.text
    with profiling.phase("build_rows", submission_id=1):
        pass


def _install_fake_pyroscope(monkeypatch):
    pyro = types.ModuleType("pyroscope")
    pyro.__path__ = []
    pyro.configure = mock.Mock()
    pyro.tag_wrapper = mock.Mock(return_value=mock.MagicMock())
    otel = types.ModuleType("pyroscope.otel")
    otel.PyroscopeSpanProcessor = mock.Mock(return_value="span-processor")
    monkeypatch.setitem(sys.modules, "pyroscope", pyro)
    monkeypatch.setitem(sys.modules, "pyroscope.otel", otel)
    provider = mock.Mock()
    monkeypatch.setattr(
        profiling.trace, "get_tracer_provider", mock.Mock(return_value=provider)
    )
    return pyro, provider


def _expected_configure(application_name, component):
    return {
        "application_name": application_name,
        "server_address": "http://alloy:4040",
        "oncpu": False,
        "gil_only": False,
        "mem_enabled": True,
        "report_thread_name": True,
        "report_thread_id": True,
        "tags": {"component": component},
    }


def test_enabled_configures_profiler_and_tags_phases(monkeypatch):
    monkeypatch.setenv("TAGBASE_PYROSCOPE_ENABLED", "true")
    monkeypatch.setenv("PYROSCOPE_SERVER_ADDRESS", "http://alloy:4040")
    monkeypatch.delenv("PYROSCOPE_APPLICATION_NAME", raising=False)
    pyro, provider = _install_fake_pyroscope(monkeypatch)

    assert profiling.setup_profiling("ingest_worker") is True
    assert profiling.setup_profiling("ingest_worker") is True
    pyro.configure.assert_called_once_with(
        **_expected_configure("tagbase_server.ingest_worker", "ingest_worker")
    )
    added = [call.args[0] for call in provider.add_span_processor.call_args_list]
    assert added[0] == "span-processor"
    assert isinstance(added[1], profiling.IngestSpanProfileLinker)
    assert len(added) == 2

    with profiling.phase("build_rows", submission_id=12, file=None):
        pass
    pyro.tag_wrapper.assert_called_once_with(
        {"phase": "build_rows", "submission_id": "12"}
    )


def test_api_component_appends_to_application_name(monkeypatch):
    monkeypatch.setenv("TAGBASE_PYROSCOPE_ENABLED", "true")
    monkeypatch.setenv("PYROSCOPE_APPLICATION_NAME", "custom")
    pyro, _provider = _install_fake_pyroscope(monkeypatch)

    assert profiling.setup_profiling("api") is True
    pyro.configure.assert_called_once_with(**_expected_configure("custom.api", "api"))


def _linked_tracer():
    provider = TracerProvider()
    provider.add_span_processor(profiling.IngestSpanProfileLinker())
    return provider.get_tracer(__name__)


def _span_id(span):
    return format(span.get_span_context().span_id, "016x")


def test_linker_leaves_root_ingest_span_alone():
    tracer = _linked_tracer()
    with tracer.start_as_current_span("ingest.persist") as span:
        pass
    assert profiling.PROFILE_ID_ATTRIBUTE not in span.attributes


def test_linker_copies_root_id_onto_nested_ingest_spans():
    tracer = _linked_tracer()
    with tracer.start_as_current_span("request") as root:
        with tracer.start_as_current_span("ingest.handle") as handle:
            with tracer.start_as_current_span("ingest.parse_etuff") as parse:
                pass
            with tracer.start_as_current_span("ingest.persist") as persist:
                pass
    assert parse.attributes[profiling.PROFILE_ID_ATTRIBUTE] == _span_id(root)
    assert persist.attributes[profiling.PROFILE_ID_ATTRIBUTE] == _span_id(root)
    assert profiling.PROFILE_ID_ATTRIBUTE not in handle.attributes


def test_linker_uses_the_current_root_after_the_previous_one_ends():
    tracer = _linked_tracer()
    with tracer.start_as_current_span("first"):
        pass
    with tracer.start_as_current_span("second") as root:
        with tracer.start_as_current_span("ingest.persist") as persist:
            pass
    assert persist.attributes[profiling.PROFILE_ID_ATTRIBUTE] == _span_id(root)
