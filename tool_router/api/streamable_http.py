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
from typing import Any

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


async def _prune_sessions() -> None:
    async with _sessions_lock:
        if len(_sessions) <= _MAX_SESSIONS:
            return
        by_last_seen = sorted(_sessions.items(), key=lambda kv: kv[1].get("last_seen", 0))
        to_remove = len(_sessions) - _MAX_SESSIONS
        for key, _ in by_last_seen[:to_remove]:
            del _sessions[key]


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
    accept: str = Header(default="application/json"),
    mcp_session_id: str | None = Header(default=None, alias="Mcp-Session-Id"),
):
    from tool_router.security.security_middleware import SecurityContext

    ctx = SecurityContext(
        user_id=request.headers.get("X-User-Id", "anonymous"),
        session_id=mcp_session_id or str(uuid.uuid4()),
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("User-Agent", ""),
        request_id=request.headers.get("X-Request-Id", str(uuid.uuid4())),
    )

    async with _sessions_lock:
        if mcp_session_id and mcp_session_id not in _sessions:
            raise HTTPException(status_code=404, detail="Session not found")

        if not mcp_session_id:
            session_id = str(uuid.uuid4())
            _sessions[session_id] = {
                "created": time.time(),
                "last_seen": time.time(),
            }
        else:
            session_id = mcp_session_id
            _sessions[session_id]["last_seen"] = time.time()

    await _prune_sessions()

    wants_stream = "text/event-stream" in accept

    if wants_stream and body.method == "tools/call":
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
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": body.id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {body.method}",
                },
            },
            headers={"Mcp-Session-Id": session_id},
        )

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
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": body.id,
                "error": {
                    "code": error_code,
                    "message": (exc.detail if isinstance(exc.detail, str) else str(exc.detail)),
                },
            },
            headers={"Mcp-Session-Id": session_id},
        )
    except Exception as exc:
        logger.exception("MCP handler error for method %s", body.method)
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": body.id,
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": {"detail": str(exc)},
                },
            },
            headers={"Mcp-Session-Id": session_id},
        )


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
    mcp_session_id: str = Header(alias="Mcp-Session-Id"),
) -> None:
    async with _sessions_lock:
        if mcp_session_id not in _sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        del _sessions[mcp_session_id]
