"""Structured tracing helpers for MCP Gateway hot paths.

Provides lightweight decorators and context managers that add OTel spans
to key operations. All helpers degrade gracefully when OTel is unavailable.
"""

from __future__ import annotations

import functools
import logging
from collections.abc import Callable
from typing import Any

from tool_router.observability.otel_setup import get_tracer


logger = logging.getLogger(__name__)

_tracer = get_tracer("forge.mcp.gateway")


# ---------------------------------------------------------------------------
# Decorator API
# ---------------------------------------------------------------------------


def trace(
    span_name: str | None = None,
    *,
    attributes: dict[str, Any] | None = None,
    record_exception: bool = True,
) -> Callable:
    """Decorator that wraps a sync or async function in an OTel span.

    Usage::

        @trace("ai.tool_selection")
        def select_tool(self, task, tools, ...):
            ...

        @trace("rpc.tools_list", attributes={"rpc.method": "tools/list"})
        async def handle_tools_list(params, ctx):
            ...
    """

    def decorator(fn: Callable) -> Callable:
        import inspect

        name = span_name or f"{fn.__module__}.{fn.__qualname__}"

        if inspect.iscoroutinefunction(fn):

            @functools.wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                with _tracer.start_as_current_span(name) as span:
                    if attributes:
                        for k, v in attributes.items():
                            span.set_attribute(k, v)
                    try:
                        result = await fn(*args, **kwargs)
                        span.set_attribute("outcome", "success")
                        return result
                    except Exception as exc:
                        if record_exception:
                            span.record_exception(exc)
                        span.set_attribute("outcome", "error")
                        raise

            return async_wrapper

        @functools.wraps(fn)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            with _tracer.start_as_current_span(name) as span:
                if attributes:
                    for k, v in attributes.items():
                        span.set_attribute(k, v)
                try:
                    result = fn(*args, **kwargs)
                    span.set_attribute("outcome", "success")
                    return result
                except Exception as exc:
                    if record_exception:
                        span.record_exception(exc)
                    span.set_attribute("outcome", "error")
                    raise

        return sync_wrapper

    return decorator


def span(name: str, **attrs: Any):
    """Context manager returning an OTel span with optional attributes.

    Usage::

        with span("gateway.select_tool", task_length=len(task)) as s:
            result = expensive_operation()
            s.set_attribute("result_count", len(result))
    """
    s = _tracer.start_as_current_span(name)
    # Enter the context to get the actual span object
    active = s.__enter__()
    for k, v in attrs.items():
        try:
            active.set_attribute(k, str(v) if not isinstance(v, (bool, int, float, str)) else v)
        except Exception:
            pass
    return active


class SpanContext:
    """Simple context manager wrapping a named OTel span."""

    def __init__(self, name: str, **attrs: Any) -> None:
        self._name = name
        self._attrs = attrs
        self._ctx = None
        self._span = None

    def __enter__(self) -> Any:
        self._ctx = _tracer.start_as_current_span(self._name)
        self._span = self._ctx.__enter__()
        for k, v in self._attrs.items():
            try:
                self._span.set_attribute(k, v)
            except Exception:
                pass
        return self._span

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        if self._ctx is not None:
            if exc_val is not None:
                try:
                    self._span.record_exception(exc_val)
                except Exception:
                    pass
            self._ctx.__exit__(exc_type, exc_val, exc_tb)
        return False
