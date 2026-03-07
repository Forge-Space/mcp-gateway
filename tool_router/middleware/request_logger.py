"""Request/response logging middleware for structured observability."""

from __future__ import annotations

import logging
import os
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


logger = logging.getLogger("tool_router.request_logger")

SKIP_PATHS = {"/health", "/ready", "/live", "/metrics", "/favicon.ico"}


def _is_enabled() -> bool:
    return os.getenv("REQUEST_LOGGING", "false").lower() == "true"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not _is_enabled():
            return await call_next(request)

        path = request.url.path
        if path in SKIP_PATHS:
            return await call_next(request)

        request_id = request.headers.get("x-request-id", uuid.uuid4().hex[:12])
        method = request.method
        start = time.monotonic()
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration_ms = round((time.monotonic() - start) * 1000, 2)
            status = "success" if status_code < 400 else "error"
            logger.info(
                "request completed",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "status": status,
                    "duration_ms": duration_ms,
                },
            )
