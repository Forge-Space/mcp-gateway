"""Per-tenant token budget enforcement middleware.

Tracks cumulative token usage in Redis (with in-memory fallback) and
injects X-Token-Budget-* response headers. Blocks requests when a
tenant has exhausted their configured budget window.

Environment variables:
    TOKEN_BUDGET_ENABLED     — "true" to activate (default: false)
    TOKEN_BUDGET_DEFAULT     — tokens per window for tenants with no explicit limit (default: 500_000)
    TOKEN_BUDGET_WINDOW_SEC  — rolling window in seconds (default: 3600)
"""

from __future__ import annotations

import logging
import os
import time
from collections import defaultdict
from contextlib import suppress
from threading import Lock

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


logger = logging.getLogger("tool_router.token_budget")

_DEFAULT_BUDGET = int(os.getenv("TOKEN_BUDGET_DEFAULT", "500000"))
_WINDOW_SEC = int(os.getenv("TOKEN_BUDGET_WINDOW_SEC", "3600"))
_ENABLED = os.getenv("TOKEN_BUDGET_ENABLED", "false").lower() == "true"

_SKIP_PATHS = {"/health", "/ready", "/live", "/metrics"}


def _tenant_from_request(request: Request) -> str:
    """Extract tenant/user identifier from security context or JWT sub claim."""
    ctx = getattr(request.state, "security_context", None)
    if ctx is not None:
        return str(getattr(ctx, "tenant_id", None) or getattr(ctx, "user_id", None) or "anon")
    return request.headers.get("x-tenant-id", "anon")


def _tokens_from_response(response: Response) -> int:
    with suppress(Exception):
        raw = response.headers.get("x-tokens-used")
        if raw:
            return int(raw)
    return 0


class _InMemoryBudgetStore:
    """Thread-safe in-memory fallback when Redis is unavailable."""

    def __init__(self) -> None:
        self._usage: dict[str, list[tuple[float, int]]] = defaultdict(list)
        self._lock = Lock()

    def _prune(self, tenant: str, now: float) -> None:
        cutoff = now - _WINDOW_SEC
        self._usage[tenant] = [(ts, t) for ts, t in self._usage[tenant] if ts > cutoff]

    def add(self, tenant: str, tokens: int) -> int:
        now = time.time()
        with self._lock:
            self._prune(tenant, now)
            self._usage[tenant].append((now, tokens))
            return sum(t for _, t in self._usage[tenant])

    def get(self, tenant: str) -> int:
        now = time.time()
        with self._lock:
            self._prune(tenant, now)
            return sum(t for _, t in self._usage[tenant])


class _RedisBudgetStore:
    def __init__(self, client) -> None:
        self._r = client
        self._prefix = "tb:"

    def _key(self, tenant: str) -> str:
        window = int(time.time() // _WINDOW_SEC)
        return f"{self._prefix}{tenant}:{window}"

    def add(self, tenant: str, tokens: int) -> int:
        key = self._key(tenant)
        pipe = self._r.pipeline()
        pipe.incrby(key, tokens)
        pipe.expire(key, _WINDOW_SEC * 2)
        results = pipe.execute()
        return int(results[0])

    def get(self, tenant: str) -> int:
        key = self._key(tenant)
        val = self._r.get(key)
        return int(val) if val else 0


def _make_store():
    try:
        import redis as redis_lib

        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        client = redis_lib.from_url(url, socket_connect_timeout=2, socket_timeout=2)
        client.ping()
        logger.info("TokenBudgetMiddleware: using Redis store (%s)", url)
        return _RedisBudgetStore(client)
    except Exception as exc:
        logger.warning("TokenBudgetMiddleware: Redis unavailable (%s), using in-memory store", exc)
        return _InMemoryBudgetStore()


_store = None
_store_lock = Lock()


def _get_store():
    global _store
    if _store is None:
        with _store_lock:
            if _store is None:
                _store = _make_store()
    return _store


def _budget_for_tenant(tenant: str) -> int:
    env_key = f"TOKEN_BUDGET_{tenant.upper().replace('-', '_')}"
    raw = os.getenv(env_key)
    return int(raw) if raw else _DEFAULT_BUDGET


class TokenBudgetMiddleware(BaseHTTPMiddleware):
    """Enforce per-tenant token budgets and inject usage headers."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not _ENABLED or request.url.path in _SKIP_PATHS:
            return await call_next(request)

        tenant = _tenant_from_request(request)
        budget = _budget_for_tenant(tenant)
        store = _get_store()

        current_usage = store.get(tenant)
        if current_usage >= budget:
            logger.warning(
                "Token budget exhausted for tenant=%s used=%d budget=%d",
                tenant,
                current_usage,
                budget,
            )
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=429,
                content={
                    "error": "token_budget_exhausted",
                    "detail": f"Token budget of {budget:,} exhausted for this window. "
                    f"Resets in ~{_WINDOW_SEC // 60} minutes.",
                    "used": current_usage,
                    "budget": budget,
                },
                headers={
                    "X-Token-Budget-Used": str(current_usage),
                    "X-Token-Budget-Limit": str(budget),
                    "X-Token-Budget-Remaining": "0",
                    "Retry-After": str(_WINDOW_SEC),
                },
            )

        response = await call_next(request)

        tokens_used = _tokens_from_response(response)
        if tokens_used > 0:
            new_total = store.add(tenant, tokens_used)
            remaining = max(0, budget - new_total)

            response.headers["X-Token-Budget-Used"] = str(new_total)
            response.headers["X-Token-Budget-Limit"] = str(budget)
            response.headers["X-Token-Budget-Remaining"] = str(remaining)
            response.headers["X-Token-Budget-Window-Sec"] = str(_WINDOW_SEC)

            if remaining < budget * 0.10:
                logger.warning(
                    "Token budget low: tenant=%s remaining=%d/%d (%.0f%%)",
                    tenant,
                    remaining,
                    budget,
                    (remaining / budget) * 100,
                )

        return response
