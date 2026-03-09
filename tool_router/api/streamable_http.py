"""Streamable HTTP transport per MCP spec 2025-03-26.

Single POST /mcp endpoint that accepts JSON-RPC requests and returns
either a direct JSON response or upgrades to SSE streaming based on
the Accept header.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from tool_router.api.rpc_handler import (
    RPC_METHOD_HANDLERS,
    JsonRpcRequest,
    _get_rate_limit_headers,
    _stream_tool_call,
)


logger = logging.getLogger(__name__)

router = APIRouter(tags=["mcp"])

_sessions: dict[str, dict[str, Any]] = {}
_sessions_lock = asyncio.Lock()

_MAX_SESSIONS = 1000


def _safe_log_value(value: str) -> str:
    return "".join(ch if ch.isprintable() and ch not in "\r\n\t" else "_" for ch in value)


def _jsonrpc_error_response(
    request_id: int | str | None,
    session_id: str,
    code: int,
    message: str,
) -> JSONResponse:
    return JSONResponse(
        content={
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": code, "message": message},
        },
        headers={"Mcp-Session-Id": session_id},
    )


async def _prune_sessions() -> None:
    async with _sessions_lock:
        if len(_sessions) <= _MAX_SESSIONS:
            return
        by_last_seen = sorted(_sessions.items(), key=lambda kv: kv[1].get("last_seen", 0))
        to_remove = len(_sessions) - _MAX_SESSIONS
        for key, _ in by_last_seen[:to_remove]:
            del _sessions[key]


async def _resolve_session(session_header: str | None) -> str:
    session_id = session_header or str(uuid.uuid4())
    now = time.time()

    async with _sessions_lock:
        if session_header and session_id not in _sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        if session_id in _sessions:
            _sessions[session_id]["last_seen"] = now
        else:
            _sessions[session_id] = {"created": now, "last_seen": now}

    await _prune_sessions()
    return session_id


def _build_security_context(request: Request, session_id: str):
    from tool_router.security.security_middleware import SecurityContext

    return SecurityContext(
        user_id=request.headers.get("X-User-Id", "anonymous"),
        session_id=session_id,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("User-Agent", ""),
        request_id=request.headers.get("X-Request-Id", str(uuid.uuid4())),
    )


def _as_str_detail(detail: Any) -> str:
    return detail if isinstance(detail, str) else str(detail)


@router.post(
    "/mcp",
    summary="MCP Streamable HTTP endpoint",
    description=(
        "Unified MCP endpoint per the 2025-03-26 spec. "
        "Accepts JSON-RPC 2.0 requests. Returns JSON by default, "
        "or upgrades to SSE streaming when Accept includes text/event-stream."
    ),
    response_model=None,
    responses={
        200: {"description": "JSON-RPC response or SSE stream"},
        400: {"description": "Invalid request"},
        404: {"description": "Session not found"},
    },
)
async def mcp_endpoint(
    request: Request,
    body: JsonRpcRequest,
    accept: Annotated[str, Header()] = "application/json",
    mcp_session_id: Annotated[str | None, Header(alias="Mcp-Session-Id")] = None,
) -> StreamingResponse | JSONResponse:
    session_id = await _resolve_session(mcp_session_id)
    ctx = _build_security_context(request, session_id)

    if "text/event-stream" in accept and body.method == "tools/call":
        params = body.params
        name = params.get("name")
        if not name:
            raise HTTPException(status_code=400, detail="Missing 'name' in params")
        arguments = params.get("arguments", {})

        headers = {
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Mcp-Session-Id": session_id,
            **_get_rate_limit_headers(ctx),
        }

        return StreamingResponse(
            _stream_tool_call(name, arguments, ctx),
            media_type="text/event-stream",
            headers=headers,
        )

    handler = RPC_METHOD_HANDLERS.get(body.method)
    if handler is None:
        return _jsonrpc_error_response(body.id, session_id, -32601, f"Method not found: {body.method}")

    try:
        result = handler(body.params, ctx)
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": body.id,
                "result": result,
            },
            headers={"Mcp-Session-Id": session_id},
        )
    except HTTPException as exc:
        error_code = -32602 if exc.status_code == 400 else -32603
        return _jsonrpc_error_response(body.id, session_id, error_code, _as_str_detail(exc.detail))
    except Exception:
        logger.exception("MCP handler error for method %s", _safe_log_value(body.method))
        return _jsonrpc_error_response(body.id, session_id, -32603, "Internal error")


@router.delete(
    "/mcp",
    summary="Close MCP session",
    description="Terminate an active MCP session.",
    responses={
        204: {"description": "Session terminated"},
        404: {"description": "Session not found"},
    },
    status_code=204,
)
async def mcp_close_session(
    mcp_session_id: Annotated[str, Header(alias="Mcp-Session-Id")],
) -> None:
    async with _sessions_lock:
        if mcp_session_id not in _sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        del _sessions[mcp_session_id]
