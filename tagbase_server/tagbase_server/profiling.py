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

``PyroscopeSpanProcessor`` writes ``pyroscope.profile.id`` on root spans only.
``ingest.parse_etuff`` and ``ingest.persist`` are those roots, so Tempo can
open a flame graph from either span. A parent span would take the attribute
instead. Each API worker starts the profiler after fork, so its request
root spans link the same way.
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager

from opentelemetry import trace

logger = logging.getLogger(__name__)

_DEFAULT_APPLICATION = "tagbase_server"
_DEFAULT_SERVER = "http://alloy:4040"

_active = False
_pyroscope = None


def _flag_enabled() -> bool:
    return os.getenv("TAGBASE_PYROSCOPE_ENABLED", "").strip().lower() in {
        "true",
        "1",
        "yes",
    }


def _application_name(component: str) -> str:
    base = (
        os.getenv("PYROSCOPE_APPLICATION_NAME", _DEFAULT_APPLICATION).strip()
        or _DEFAULT_APPLICATION
    )
    return f"{base}.{component}"


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
    server_address = (
        os.getenv("PYROSCOPE_SERVER_ADDRESS", _DEFAULT_SERVER).strip()
        or _DEFAULT_SERVER
    )
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
    if not _active or _pyroscope is None:
        yield
        return
    labels = {"phase": str(name)}
    for key, value in tags.items():
        if value is None:
            continue
        labels[key] = value if isinstance(value, str) else str(value)
    with _pyroscope.tag_wrapper(labels):
        yield


def reset_profiling_state_for_tests() -> None:
    """Clear the init guard. Does not stop a profiler started in-process."""
    global _active, _pyroscope
    _active = False
    _pyroscope = None
