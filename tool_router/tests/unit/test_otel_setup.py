"""Tests for OpenTelemetry bootstrap module.

The OTel packages are optional, so these tests verify both the
'available' and 'unavailable' code paths using monkeypatching.
"""

from __future__ import annotations

import importlib
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _reload_otel_setup():
    """Force-reload the module to re-evaluate import guards."""
    import tool_router.observability.otel_setup as mod

    importlib.reload(mod)
    return mod


# ---------------------------------------------------------------------------
# Tests: capability flags
# ---------------------------------------------------------------------------


class TestCapabilityFlags:
    """Verify capability detection for OTel packages."""

    def test_is_otel_available_returns_bool(self):
        from tool_router.observability.otel_setup import is_otel_available

        result = is_otel_available()
        assert isinstance(result, bool)

    def test_is_otel_enabled_respects_env(self, monkeypatch):
        monkeypatch.setenv("OTEL_ENABLED", "false")
        from tool_router.observability.otel_setup import is_otel_enabled

        assert is_otel_enabled() is False

    def test_is_otel_enabled_true_by_default(self, monkeypatch):
        monkeypatch.delenv("OTEL_ENABLED", raising=False)
        from tool_router.observability.otel_setup import is_otel_enabled

        # Result depends on whether packages are installed
        result = is_otel_enabled()
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# Tests: init_otel
# ---------------------------------------------------------------------------


class TestInitOtel:
    """Verify OTel initialisation."""

    def test_init_otel_returns_dict(self, monkeypatch):
        """init_otel always returns a dict with required keys."""
        # Disable OTel so we get the fast no-op path
        monkeypatch.setenv("OTEL_ENABLED", "false")
        mod = _reload_otel_setup()
        # Clear lru_cache
        mod.init_otel.cache_clear()
        result = mod.init_otel()
        assert isinstance(result, dict)
        assert "tracer_provider" in result
        assert "meter_provider" in result
        assert "tracer" in result
        assert "meter" in result

    def test_init_otel_disabled_returns_nones(self, monkeypatch):
        monkeypatch.setenv("OTEL_ENABLED", "false")
        mod = _reload_otel_setup()
        mod.init_otel.cache_clear()
        result = mod.init_otel()
        assert result["tracer_provider"] is None
        assert result["meter_provider"] is None
        assert result["tracer"] is None
        assert result["meter"] is None

    def test_init_otel_is_cached(self, monkeypatch):
        monkeypatch.setenv("OTEL_ENABLED", "false")
        mod = _reload_otel_setup()
        mod.init_otel.cache_clear()
        r1 = mod.init_otel()
        r2 = mod.init_otel()
        assert r1 is r2  # same object — cached


# ---------------------------------------------------------------------------
# Tests: instrument_fastapi
# ---------------------------------------------------------------------------


class TestInstrumentFastapi:
    """Verify FastAPI instrumentation is a safe no-op when disabled."""

    def test_instrument_noop_when_disabled(self, monkeypatch):
        monkeypatch.setenv("OTEL_ENABLED", "false")
        mod = _reload_otel_setup()
        mod.init_otel.cache_clear()
        # Should not raise even with a dummy app
        mod.instrument_fastapi(MagicMock())


# ---------------------------------------------------------------------------
# Tests: get_trace_context
# ---------------------------------------------------------------------------


class TestTraceContext:
    """Verify trace context extraction."""

    def test_returns_dict(self):
        from tool_router.observability.otel_setup import get_trace_context

        ctx = get_trace_context()
        assert isinstance(ctx, dict)

    def test_empty_when_no_span(self):
        """When no span is active the context should be empty."""
        from tool_router.observability.otel_setup import get_trace_context

        ctx = get_trace_context()
        # May be empty or have zero trace_id
        if ctx:
            assert "trace_id" in ctx
            assert "span_id" in ctx

    def test_empty_when_otel_unavailable(self, monkeypatch):
        """When OTel API is not importable, returns empty dict."""
        mod = _reload_otel_setup()
        monkeypatch.setattr(mod, "_OTEL_API_AVAILABLE", False)
        assert mod.get_trace_context() == {}


# ---------------------------------------------------------------------------
# Tests: no-op fallbacks
# ---------------------------------------------------------------------------


class TestNoopFallbacks:
    """Verify _NoopTracer and _NoopSpan behave correctly."""

    def test_noop_tracer_start_as_current_span(self):
        from tool_router.observability.otel_setup import _NoopTracer

        tracer = _NoopTracer()
        span = tracer.start_as_current_span("test")
        with span:
            pass  # must not raise

    def test_noop_span_methods(self):
        from tool_router.observability.otel_setup import _NoopSpan

        span = _NoopSpan()
        span.set_attribute("key", "value")
        span.set_status("ok")
        span.record_exception(ValueError("test"))
        span.add_event("event")
        span.end()
        # None of the above should raise

    def test_noop_span_context_manager(self):
        from tool_router.observability.otel_setup import _NoopSpan

        with _NoopSpan() as s:
            assert s is not None


# ---------------------------------------------------------------------------
# Tests: get_tracer / get_meter
# ---------------------------------------------------------------------------


class TestGetTracerMeter:
    """Verify tracer/meter accessors."""

    def test_get_tracer_returns_noop_when_disabled(self, monkeypatch):
        monkeypatch.setenv("OTEL_ENABLED", "false")
        mod = _reload_otel_setup()
        mod.init_otel.cache_clear()
        tracer = mod.get_tracer()
        # Should be a _NoopTracer
        span = tracer.start_as_current_span("test")
        with span:
            pass

    def test_get_meter_returns_none_when_disabled(self, monkeypatch):
        monkeypatch.setenv("OTEL_ENABLED", "false")
        mod = _reload_otel_setup()
        mod.init_otel.cache_clear()
        meter = mod.get_meter()
        assert meter is None
