"""JSON-RPC endpoint for external tool calls (webapp → gateway)."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import AsyncGenerator
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from tool_router.security.audit_logger import SecurityAuditLogger
from tool_router.security.security_middleware import (
    SecurityContext,
    SecurityMiddleware,
)

from .dependencies import get_security_context


logger = logging.getLogger(__name__)

router = APIRouter(tags=["rpc"])

_security_middleware: SecurityMiddleware | None = None
_audit_logger: SecurityAuditLogger | None = None


def init_rpc_security(
    security_middleware: SecurityMiddleware,
    audit_logger: SecurityAuditLogger,
) -> None:
    global _security_middleware, _audit_logger
    _security_middleware = security_middleware
    _audit_logger = audit_logger


class JsonRpcRequest(BaseModel):
    """JSON-RPC 2.0 request envelope."""

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "params": {},
                    "id": 1,
                },
                {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "generate_ui",
                        "arguments": {
                            "task": "Create a login form",
                            "context": "React + Tailwind",
                        },
                    },
                    "id": 2,
                },
            ]
        }
    }

    jsonrpc: str = Field(
        default="2.0",
        pattern=r"^2\.0$",
        description="JSON-RPC protocol version (must be 2.0)",
    )
    method: str = Field(
        description="RPC method name: 'tools/list' or 'tools/call'",
    )
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="Method parameters. For tools/call: {name, arguments}",
    )
    id: str | int | None = Field(
        default=None,
        description="Request identifier echoed in the response",
    )


class JsonRpcError(BaseModel):
    """JSON-RPC 2.0 error object."""

    code: int = Field(description="Error code (-32601=method not found, -32602=invalid params, -32603=internal)")
    message: str = Field(description="Human-readable error message")
    data: dict[str, Any] | None = Field(default=None, description="Additional error details")


class JsonRpcResponse(BaseModel):
    """JSON-RPC 2.0 response envelope."""

    jsonrpc: str = "2.0"
    result: dict[str, Any] | None = Field(default=None, description="Success payload (mutually exclusive with error)")
    error: JsonRpcError | None = Field(default=None, description="Error payload (mutually exclusive with result)")
    id: str | int | None = Field(default=None, description="Echoed request identifier")


TOOL_DISPATCH: dict[str, Any] = {}


def register_tool_dispatch(tools: dict[str, Any]) -> None:
    TOOL_DISPATCH.update(tools)


def _get_available_tools() -> list[dict[str, Any]]:
    from tool_router.gateway.client import get_tools

    try:
        return get_tools()
    except (ValueError, ConnectionError):
        logger.warning("Failed to fetch tools from upstream gateway")
        return []


def _call_tool(name: str, arguments: dict[str, Any]) -> str:
    from tool_router.gateway.client import call_tool

    return call_tool(name, arguments)


def _run_security_check(
    ctx: SecurityContext,
    task: str,
    category: str,
    context_str: str,
    user_preferences: str,
) -> tuple[bool, str | None, dict[str, str]]:
    if _security_middleware is None:
        logger.warning("Security middleware not initialized — bypassing security checks")
        return True, None, {"task": task, "context": context_str}

    result = _security_middleware.check_request_security(
        context=ctx,
        task=task,
        category=category,
        context_str=context_str,
        user_preferences=user_preferences,
    )
    sanitized = result.sanitized_inputs
    if not result.allowed:
        return False, result.blocked_reason, sanitized
    return True, None, sanitized


def _handle_tools_list(
    params: dict[str, Any],
    ctx: SecurityContext,
) -> dict[str, Any]:
    if _audit_logger:
        _audit_logger.log_request_received(
            user_id=ctx.user_id,
            session_id=ctx.session_id,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
            request_id=ctx.request_id,
            endpoint="/rpc",
            details={"method": "tools/list"},
        )

    tools = _get_available_tools()
    return {"tools": tools}


def _handle_tools_call(
    params: dict[str, Any],
    ctx: SecurityContext,
) -> dict[str, Any]:
    name = params.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Missing 'name' in params")

    arguments = params.get("arguments", {})

    task = arguments.get("task", arguments.get("prompt", ""))
    category = arguments.get("category", "tool_selection")
    context_str = arguments.get("context", "")
    user_preferences = arguments.get("user_preferences", "{}")

    allowed, blocked_reason, sanitized = _run_security_check(
        ctx,
        task,
        category,
        context_str,
        user_preferences,
    )

    if _audit_logger:
        _audit_logger.log_request_received(
            user_id=ctx.user_id,
            session_id=ctx.session_id,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
            request_id=ctx.request_id,
            endpoint="/rpc",
            details={"method": "tools/call", "tool": name},
        )

    if not allowed:
        if _audit_logger:
            _audit_logger.log_request_blocked(
                user_id=ctx.user_id,
                session_id=ctx.session_id,
                ip_address=ctx.ip_address,
                user_agent=ctx.user_agent,
                request_id=ctx.request_id,
                endpoint="/rpc",
                reason=blocked_reason or "Security check failed",
                risk_score=0.8,
                details={"tool": name},
            )
        raise HTTPException(
            status_code=403,
            detail=f"Request blocked: {blocked_reason}",
        )

    if "task" in arguments:
        arguments["task"] = sanitized.get("task", task)
    if "context" in arguments:
        arguments["context"] = sanitized.get("context", context_str)

    start = time.monotonic()
    result_text = _call_tool(name, arguments)
    elapsed_ms = (time.monotonic() - start) * 1000

    logger.info(
        "Tool call completed: %s (%.0fms, user=%s)",
        name,
        elapsed_ms,
        ctx.user_id,
    )

    return {
        "content": [{"type": "text", "text": result_text}],
        "metadata": {
            "tool": name,
            "elapsed_ms": round(elapsed_ms),
            "user_id": ctx.user_id,
        },
    }


RPC_METHOD_HANDLERS = {
    "tools/list": _handle_tools_list,
    "tools/call": _handle_tools_call,
}


@router.post(
    "/rpc",
    response_model=JsonRpcResponse,
    summary="Execute JSON-RPC call",
    description="Route JSON-RPC 2.0 requests to MCP tool spokes. "
    "Supports `tools/list` and `tools/call` methods. "
    "Requires a valid Supabase JWT in the Authorization header.",
    responses={
        200: {"description": "JSON-RPC response (check `error` field for failures)"},
        401: {"description": "Missing or invalid JWT token"},
        403: {"description": "Request blocked by security middleware"},
    },
)
async def json_rpc_endpoint(
    request: JsonRpcRequest,
    security_context: Annotated[SecurityContext, Depends(get_security_context)],
) -> JsonRpcResponse:
    handler = RPC_METHOD_HANDLERS.get(request.method)
    if handler is None:
        return JsonRpcResponse(
            id=request.id,
            error=JsonRpcError(
                code=-32601,
                message=f"Method not found: {request.method}",
            ),
        )

    try:
        result = handler(request.params, security_context)
        return JsonRpcResponse(id=request.id, result=result)
    except HTTPException as exc:
        error_code = -32001 if exc.status_code == 401 else -32003
        if exc.status_code == 400:
            error_code = -32602
        return JsonRpcResponse(
            id=request.id,
            error=JsonRpcError(
                code=error_code,
                message=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            ),
        )
    except Exception as exc:
        logger.exception("RPC handler error for method %s", request.method)
        return JsonRpcResponse(
            id=request.id,
            error=JsonRpcError(
                code=-32603,
                message="Internal error",
                data={"detail": str(exc)},
            ),
        )


def _sse_event(data: dict[str, Any]) -> str:
    return f"data: {json.dumps(data)}\n\n"


async def _stream_tool_call(
    name: str,
    arguments: dict[str, Any],
    ctx: SecurityContext,
) -> AsyncGenerator[str, None]:
    yield _sse_event({"type": "start", "timestamp": int(time.time() * 1000)})

    start = time.monotonic()
    try:
        loop = asyncio.get_running_loop()
        result_text = await loop.run_in_executor(None, _call_tool, name, arguments)
    except Exception as exc:
        logger.exception("Streaming tool call failed: %s", name)
        yield _sse_event(
            {
                "type": "error",
                "message": str(exc),
                "timestamp": int(time.time() * 1000),
            }
        )
        return

    elapsed_ms = (time.monotonic() - start) * 1000
    logger.info(
        "Streaming tool call completed: %s (%.0fms, user=%s)",
        name,
        elapsed_ms,
        ctx.user_id,
    )

    chunk_size = 200
    for i in range(0, len(result_text), chunk_size):
        yield _sse_event(
            {
                "type": "chunk",
                "content": result_text[i : i + chunk_size],
                "timestamp": int(time.time() * 1000),
            }
        )

    from tool_router.api.quality_gates import run_quality_gates

    quality_report = run_quality_gates(result_text)
    yield _sse_event(
        {
            "type": "quality",
            "report": quality_report.to_dict(),
            "timestamp": int(time.time() * 1000),
        }
    )

    yield _sse_event(
        {
            "type": "complete",
            "code": result_text,
            "totalLength": len(result_text),
            "qualityPassed": quality_report.passed,
            "metadata": {
                "tool": name,
                "elapsed_ms": round(elapsed_ms),
                "user_id": ctx.user_id,
                "quality_score": quality_report.score,
            },
            "timestamp": int(time.time() * 1000),
        }
    )


@router.post(
    "/rpc/stream",
    summary="Stream JSON-RPC tool call via SSE",
    description="Execute a `tools/call` via Server-Sent Events. "
    "Returns chunked code output followed by a quality gate report. "
    "Event types: `start`, `chunk`, `quality`, `complete`, `error`.",
    responses={
        200: {"description": "SSE stream (text/event-stream)", "content": {"text/event-stream": {}}},
        400: {"description": "Missing tool name in params"},
        401: {"description": "Missing or invalid JWT token"},
        403: {"description": "Request blocked by security middleware"},
    },
)
async def json_rpc_stream_endpoint(
    request: JsonRpcRequest,
    security_context: Annotated[SecurityContext, Depends(get_security_context)],
) -> StreamingResponse:
    if request.method != "tools/call":
        error = _sse_event(
            {
                "type": "error",
                "message": f"Streaming only supports tools/call, got: {request.method}",
                "timestamp": int(time.time() * 1000),
            }
        )

        async def _error_stream() -> AsyncGenerator[str, None]:
            yield error

        return StreamingResponse(
            _error_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    params = request.params
    name = params.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Missing 'name' in params")

    arguments = params.get("arguments", {})

    task = arguments.get("task", arguments.get("prompt", ""))
    category = arguments.get("category", "tool_selection")
    context_str = arguments.get("context", "")
    user_preferences = arguments.get("user_preferences", "{}")

    allowed, blocked_reason, sanitized = _run_security_check(
        security_context,
        task,
        category,
        context_str,
        user_preferences,
    )

    if not allowed:
        if _audit_logger:
            _audit_logger.log_request_blocked(
                user_id=security_context.user_id,
                session_id=security_context.session_id,
                ip_address=security_context.ip_address,
                user_agent=security_context.user_agent,
                request_id=security_context.request_id,
                endpoint="/rpc/stream",
                reason=blocked_reason or "Security check failed",
                risk_score=0.8,
                details={"tool": name},
            )
        raise HTTPException(
            status_code=403,
            detail=f"Request blocked: {blocked_reason}",
        )

    if "task" in arguments:
        arguments["task"] = sanitized.get("task", task)
    if "context" in arguments:
        arguments["context"] = sanitized.get("context", context_str)

    if _audit_logger:
        _audit_logger.log_request_received(
            user_id=security_context.user_id,
            session_id=security_context.session_id,
            ip_address=security_context.ip_address,
            user_agent=security_context.user_agent,
            request_id=security_context.request_id,
            endpoint="/rpc/stream",
            details={"method": "tools/call", "tool": name, "streaming": True},
        )

    return StreamingResponse(
        _stream_tool_call(name, arguments, security_context),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
