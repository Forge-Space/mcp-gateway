"""Observability module for health checks, logging, metrics, and tracing."""

from tool_router.observability.health import HealthCheck, HealthStatus
from tool_router.observability.logger import get_logger, setup_logging
from tool_router.observability.metrics import MetricsCollector, get_metrics
from tool_router.observability.otel_setup import (
    get_trace_context,
    get_tracer,
    init_otel,
    instrument_fastapi,
    is_otel_available,
    is_otel_enabled,
)


__all__ = [
    "HealthCheck",
    "HealthStatus",
    "MetricsCollector",
    "get_logger",
    "get_metrics",
    "get_trace_context",
    "get_tracer",
    "init_otel",
    "instrument_fastapi",
    "is_otel_available",
    "is_otel_enabled",
    "setup_logging",
]
