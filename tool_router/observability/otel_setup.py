"""OpenTelemetry bootstrap for MCP Gateway.

Initialises TracerProvider, MeterProvider, and log context injection.
All OTel dependencies are optional — the gateway degrades gracefully
when opentelemetry packages are not installed.

Configuration is driven by standard OTel environment variables:

  OTEL_SERVICE_NAME          (default: forge-mcp-gateway)
  OTEL_EXPORTER_OTLP_ENDPOINT (default: none — console exporter used)
  OTEL_TRACES_EXPORTER       (default: console)
  OTEL_METRICS_EXPORTER      (default: prometheus)
  OTEL_LOG_LEVEL             (default: WARNING)
  OTEL_ENABLED               (default: true)
"""

from __future__ import annotations

import functools
import logging
import os
from typing import Any


logger = logging.getLogger(__name__)

# Capability flags — set at import time.
_OTEL_API_AVAILABLE = False
_OTEL_SDK_AVAILABLE = False
_OTEL_FASTAPI_AVAILABLE = False
_OTEL_HTTPX_AVAILABLE = False
_OTEL_PROM_AVAILABLE = False

try:
    from opentelemetry import trace  # noqa: F401

    _OTEL_API_AVAILABLE = True
except ImportError:
    pass

try:
    from opentelemetry.sdk.resources import Resource  # noqa: F401
    from opentelemetry.sdk.trace import TracerProvider  # noqa: F401
    from opentelemetry.sdk.trace.export import (  # noqa: F401
        BatchSpanProcessor,
        ConsoleSpanExporter,
    )

    _OTEL_SDK_AVAILABLE = True
except ImportError:
    pass

try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # noqa: F401

    _OTEL_FASTAPI_AVAILABLE = True
except ImportError:
    pass

try:
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor  # noqa: F401

    _OTEL_HTTPX_AVAILABLE = True
except ImportError:
    pass

try:
    from opentelemetry.exporter.prometheus import PrometheusMetricReader  # noqa: F401

    _OTEL_PROM_AVAILABLE = True
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def is_otel_available() -> bool:
    """Return True when the OTel API + SDK packages are importable."""
    return _OTEL_API_AVAILABLE and _OTEL_SDK_AVAILABLE


def is_otel_enabled() -> bool:
    """Check both availability and the OTEL_ENABLED env flag."""
    return is_otel_available() and os.getenv("OTEL_ENABLED", "true").lower() in ("1", "true", "yes")


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------


@functools.lru_cache(maxsize=1)
def init_otel() -> dict[str, Any]:
    """One-shot OTel initialisation.  Safe to call multiple times (cached).

    Returns a dict with keys:
        tracer_provider, meter_provider, tracer, meter
    all set to ``None`` when OTel is unavailable or disabled.
    """
    result: dict[str, Any] = {
        "tracer_provider": None,
        "meter_provider": None,
        "tracer": None,
        "meter": None,
    }

    if not is_otel_enabled():
        logger.info("OpenTelemetry disabled or packages not installed — skipping init")
        return result

    # --- Resource ---------------------------------------------------------
    from opentelemetry.sdk.resources import Resource

    service_name = os.getenv("OTEL_SERVICE_NAME", "forge-mcp-gateway")
    service_version = os.getenv("OTEL_SERVICE_VERSION", "1.9.0")

    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": service_version,
            "deployment.environment": os.getenv("OTEL_DEPLOYMENT_ENV", "development"),
        }
    )

    # --- Traces -----------------------------------------------------------
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

    tracer_provider = TracerProvider(resource=resource)

    exporter_name = os.getenv("OTEL_TRACES_EXPORTER", "console")
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")

    if otlp_endpoint and exporter_name != "console":
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )

            tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint)))
            logger.info("OTel OTLP trace exporter → %s", otlp_endpoint)
        except ImportError:
            logger.warning("OTLP trace exporter requested but package not installed — falling back to console")
            tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    else:
        tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        logger.info("OTel console trace exporter active")

    trace.set_tracer_provider(tracer_provider)
    result["tracer_provider"] = tracer_provider
    result["tracer"] = trace.get_tracer("forge.mcp.gateway")

    # --- Metrics ----------------------------------------------------------
    metrics_exporter = os.getenv("OTEL_METRICS_EXPORTER", "prometheus")
    if metrics_exporter == "prometheus" and _OTEL_PROM_AVAILABLE:
        try:
            from opentelemetry.exporter.prometheus import PrometheusMetricReader
            from opentelemetry.sdk.metrics import MeterProvider

            reader = PrometheusMetricReader()
            meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
            result["meter_provider"] = meter_provider
            result["meter"] = meter_provider.get_meter("forge.mcp.gateway")
            logger.info("OTel Prometheus metric reader active")
        except Exception:
            logger.warning("Failed to initialise Prometheus metric reader", exc_info=True)
    elif otlp_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
                OTLPMetricExporter,
            )
            from opentelemetry.sdk.metrics import MeterProvider
            from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

            reader = PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=otlp_endpoint))
            meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
            result["meter_provider"] = meter_provider
            result["meter"] = meter_provider.get_meter("forge.mcp.gateway")
            logger.info("OTel OTLP metric exporter → %s", otlp_endpoint)
        except ImportError:
            logger.warning("OTLP metric exporter requested but package not installed")

    logger.info(
        "OpenTelemetry initialised: service=%s traces=%s metrics=%s",
        service_name,
        "ok" if result["tracer"] else "off",
        "ok" if result["meter"] else "off",
    )
    return result


# ---------------------------------------------------------------------------
# FastAPI instrumentation
# ---------------------------------------------------------------------------


def instrument_fastapi(app: Any) -> None:
    """Instrument a FastAPI application with OTel auto-instrumentation.

    No-op when OTel is unavailable or the FastAPI instrumentor is missing.
    """
    if not is_otel_enabled():
        return

    # Ensure providers are initialised
    init_otel()

    if _OTEL_FASTAPI_AVAILABLE:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI OTel auto-instrumentation enabled")
    else:
        logger.debug("opentelemetry-instrumentation-fastapi not installed — skipping")

    if _OTEL_HTTPX_AVAILABLE:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument()
        logger.info("HTTPX OTel auto-instrumentation enabled")
    else:
        logger.debug("opentelemetry-instrumentation-httpx not installed — skipping")


# ---------------------------------------------------------------------------
# Trace context for structured logs
# ---------------------------------------------------------------------------


def get_trace_context() -> dict[str, str]:
    """Return current span's trace_id and span_id as hex strings.

    Returns empty dict when OTel is not active or no span is in-flight.
    """
    if not _OTEL_API_AVAILABLE:
        return {}

    from opentelemetry import trace

    span = trace.get_current_span()
    ctx = span.get_span_context()
    if ctx and ctx.trace_id:
        return {
            "trace_id": format(ctx.trace_id, "032x"),
            "span_id": format(ctx.span_id, "016x"),
        }
    return {}


# ---------------------------------------------------------------------------
# Convenience tracer/meter accessors
# ---------------------------------------------------------------------------


def get_tracer(name: str = "forge.mcp.gateway") -> Any:
    """Return an OTel tracer, or a no-op proxy when OTel is off."""
    if not is_otel_enabled():
        return _NoopTracer()
    from opentelemetry import trace

    return trace.get_tracer(name)


def get_meter(name: str = "forge.mcp.gateway") -> Any:
    """Return an OTel meter, or None when OTel is off."""
    otel = init_otel()
    return otel.get("meter")


# ---------------------------------------------------------------------------
# No-op fallback
# ---------------------------------------------------------------------------


class _NoopSpan:
    """Minimal span stand-in when OTel is unavailable."""

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        pass

    def set_attribute(self, _k, _v):
        pass

    def set_status(self, *_a, **_kw):
        pass

    def record_exception(self, *_a, **_kw):
        pass

    def add_event(self, *_a, **_kw):
        pass

    def end(self):
        pass


class _NoopTracer:
    """Minimal tracer stand-in when OTel is unavailable."""

    def start_as_current_span(self, _name: str, **_kw):
        return _NoopSpan()

    def start_span(self, _name: str, **_kw):
        return _NoopSpan()
