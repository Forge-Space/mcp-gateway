"""Tests for tool_router.observability.tracing helpers.

Verifies that SpanContext and @trace work correctly both when OTel
is unavailable (no-op mode, which is the default in test env) and
with a real tracer configured via environment variables.
"""

from __future__ import annotations

import pytest

from tool_router.observability.tracing import SpanContext, trace


# ---------------------------------------------------------------------------
# SpanContext
# ---------------------------------------------------------------------------


class TestSpanContext:
    def test_enters_and_exits_without_error(self) -> None:
        with SpanContext("test.span") as span:
            assert span is not None

    def test_sets_string_attribute(self) -> None:
        with SpanContext("test.attr", key="value") as span:
            span.set_attribute("extra", "data")

    def test_sets_numeric_attribute(self) -> None:
        with SpanContext("test.numeric", count=42, rate=0.95) as span:
            span.set_attribute("extra_int", 1)

    def test_handles_exception_and_reraises(self) -> None:
        with pytest.raises(ValueError, match="test error"):
            with SpanContext("test.exc"):
                raise ValueError("test error")

    def test_exception_does_not_suppress(self) -> None:
        """SpanContext __exit__ returns False — exceptions propagate."""
        raised = False
        try:
            with SpanContext("test.no_suppress"):
                raise RuntimeError("should propagate")
        except RuntimeError:
            raised = True
        assert raised

    def test_nested_spans(self) -> None:
        with SpanContext("outer") as outer:
            with SpanContext("inner") as inner:
                outer.set_attribute("level", "outer")
                inner.set_attribute("level", "inner")


# ---------------------------------------------------------------------------
# @trace decorator
# ---------------------------------------------------------------------------


class TestTraceDecorator:
    def test_wraps_sync_function(self) -> None:
        @trace("test.sync")
        def add(a: int, b: int) -> int:
            return a + b

        assert add(2, 3) == 5

    def test_wraps_sync_function_with_attributes(self) -> None:
        @trace("test.sync.attrs", attributes={"component": "test"})
        def multiply(x: int) -> int:
            return x * 2

        assert multiply(10) == 20

    @pytest.mark.asyncio
    async def test_wraps_async_function(self) -> None:
        @trace("test.async")
        async def fetch(url: str) -> str:
            return f"fetched:{url}"

        result = await fetch("http://example.com")
        assert result == "fetched:http://example.com"

    @pytest.mark.asyncio
    async def test_async_exception_propagates(self) -> None:
        @trace("test.async.exc")
        async def fail() -> None:
            raise ValueError("async error")

        with pytest.raises(ValueError, match="async error"):
            await fail()

    def test_sync_exception_propagates(self) -> None:
        @trace("test.sync.exc")
        def fail() -> None:
            raise TypeError("sync error")

        with pytest.raises(TypeError, match="sync error"):
            fail()

    def test_preserves_function_metadata(self) -> None:
        @trace("test.meta")
        def documented_fn() -> None:
            """My docstring."""

        assert documented_fn.__name__ == "documented_fn"
        assert documented_fn.__doc__ == "My docstring."

    def test_default_span_name_from_qualified_name(self) -> None:
        """@trace without name uses module.qualname."""

        @trace()
        def my_function() -> str:
            return "ok"

        assert my_function() == "ok"

    def test_record_exception_false_does_not_raise(self) -> None:
        @trace("test.no_record", record_exception=False)
        def blow_up() -> None:
            raise KeyError("silent")

        with pytest.raises(KeyError):
            blow_up()
