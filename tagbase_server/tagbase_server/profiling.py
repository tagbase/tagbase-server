"""Optional Pyroscope profiling for the ingest worker and the API workers.

Off unless ``TAGBASE_PYROSCOPE_ENABLED`` is true. The ``pyroscope`` package is
imported only then, so the default image (which does not install it) stays
unaffected.

When enabled, each process pushes wall-clock samples from every thread,
including threads blocked in C without the GIL, plus sampled heap
allocations. Samples carry the thread name and id. The SDK ignores
``native``, so C frames inside pandas, NumPy, and libpq appear only as the
Python call that entered them. Heap samples are allocations, not peak
resident memory. Time inside Postgres is not in the profile.

``PyroscopeSpanProcessor`` tags samples with the id of the local root span
and writes that id as ``pyroscope.profile.id`` on the root span only. In the
ingest worker ``ingest.parse_etuff`` and ``ingest.persist`` are roots. On the
synchronous API path they run under the Flask request span, so
``IngestSpanProfileLinker`` copies the root's id onto them as well. Tempo can
then open a flame graph from either span on both paths.
"""

from __future__ import annotations

import logging
import os
import threading
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.sdk.trace import SpanProcessor

logger = logging.getLogger(__name__)

_DEFAULT_APPLICATION = "tagbase_server"
_DEFAULT_SERVER = "http://alloy:4040"
PROFILE_ID_ATTRIBUTE = "pyroscope.profile.id"
LINKED_SPAN_NAMES = frozenset({"ingest.parse_etuff", "ingest.persist"})

_active = False
_pyroscope = None


def _flag_enabled() -> bool:
    return os.getenv("TAGBASE_PYROSCOPE_ENABLED", "").strip().lower() in {
        "true",
        "1",
        "yes",
    }


def _env_or_default(name: str, default: str) -> str:
    return os.getenv(name, default).strip() or default


def _application_name(component: str) -> str:
    base = _env_or_default("PYROSCOPE_APPLICATION_NAME", _DEFAULT_APPLICATION)
    return f"{base}.{component}"


def _is_root_span(span) -> bool:
    # Same test as pyroscope-otel, so the id matches its sample tag.
    return span.parent is None or span.parent.is_remote


class IngestSpanProfileLinker(SpanProcessor):
    """Copy the local root span id onto nested ingest spans.

    Pyroscope tags samples per thread, so the root id is kept per thread.
    """

    def __init__(self):
        self._local = threading.local()

    def on_start(self, span, parent_context=None) -> None:
        if _is_root_span(span):
            self._local.root_id = format(span.context.span_id, "016x")
            return
        if span.name not in LINKED_SPAN_NAMES:
            return
        root_id = getattr(self._local, "root_id", None)
        if root_id is not None:
            span.set_attribute(PROFILE_ID_ATTRIBUTE, root_id)

    def on_end(self, span) -> None:
        if _is_root_span(span):
            self._local.root_id = None


def setup_profiling(component: str) -> bool:
    """Start the profiler and attach span linking. No-op when disabled.

    ``component`` is appended to ``PYROSCOPE_APPLICATION_NAME`` (default
    ``tagbase_server``), so the ingest worker and the API workers are
    separate Pyroscope services. A missing ``pyroscope`` package logs a
    warning and returns False. Safe to call more than once in one process.
    """
    global _active, _pyroscope
    if _active:
        return True
    if not _flag_enabled():
        return False
    try:
        import pyroscope
        from pyroscope.otel import PyroscopeSpanProcessor
    except ImportError:
        logger.warning(
            "Pyroscope profiling requested but the pyroscope package is not installed"
        )
        return False

    application_name = _application_name(component)
    server_address = _env_or_default("PYROSCOPE_SERVER_ADDRESS", _DEFAULT_SERVER)
    pyroscope.configure(
        application_name=application_name,
        server_address=server_address,
        oncpu=False,
        gil_only=False,
        mem_enabled=True,
        report_thread_name=True,
        report_thread_id=True,
        tags={"component": component},
    )
    provider = trace.get_tracer_provider()
    add_span_processor = getattr(provider, "add_span_processor", None)
    if add_span_processor is None:
        logger.warning(
            "Pyroscope span linking skipped; OpenTelemetry has no tracer provider"
        )
    else:
        add_span_processor(PyroscopeSpanProcessor())
        add_span_processor(IngestSpanProfileLinker())
    _pyroscope = pyroscope
    _active = True
    logger.info(
        "Pyroscope profiling enabled; pushing to %s (application=%s)",
        server_address,
        application_name,
    )
    return True


@contextmanager
def phase(name, **tags):
    """Tag samples with the ingest phase. A no-op while profiling is off."""
    if not _active:
        yield
        return
    labels = {"phase": str(name)}
    for key, value in tags.items():
        if value is not None:
            labels[key] = str(value)
    with _pyroscope.tag_wrapper(labels):
        yield


def reset_profiling_state_for_tests() -> None:
    """Clear the init guard. Does not stop a profiler started in-process."""
    global _active, _pyroscope
    _active = False
    _pyroscope = None
