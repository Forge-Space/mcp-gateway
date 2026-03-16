"""Tests for request logging middleware."""

from __future__ import annotations

import logging
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from tool_router.middleware.request_logger import RequestLoggingMiddleware


def _make_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/test")
    async def test_route():
        return {"ok": True}

    @app.get("/health")
    async def health_route():
        return {"status": "healthy"}

    @app.get("/error")
    async def error_route():
        return JSONResponse({"error": "bad"}, status_code=500)

    return app


class TestRequestLoggingMiddleware:
    def test_logs_request_when_enabled(self, caplog):
        app = _make_app()
        client = TestClient(app)

        with (
            patch(
                "tool_router.middleware.request_logger._is_enabled",
                return_value=True,
            ),
            caplog.at_level(logging.INFO, "tool_router.request_logger"),
        ):
            resp = client.get("/test")

        assert resp.status_code == 200
        assert any("request completed" in r.message for r in caplog.records)
        log = next(r for r in caplog.records if "request completed" in r.message)
        assert log.method == "GET"  # type: ignore[attr-defined]
        assert log.path == "/test"  # type: ignore[attr-defined]
        assert log.status_code == 200  # type: ignore[attr-defined]
        assert log.status == "success"  # type: ignore[attr-defined]
        assert isinstance(log.duration_ms, float)  # type: ignore[attr-defined]
        assert hasattr(log, "request_id")

    def test_skips_health_endpoints(self, caplog):
        app = _make_app()
        client = TestClient(app)

        with (
            patch(
                "tool_router.middleware.request_logger._is_enabled",
                return_value=True,
            ),
            caplog.at_level(logging.INFO, "tool_router.request_logger"),
        ):
            resp = client.get("/health")

        assert resp.status_code == 200
        assert not any("request completed" in r.message for r in caplog.records)

    def test_no_logging_when_disabled(self, caplog):
        app = _make_app()
        client = TestClient(app)

        with (
            patch(
                "tool_router.middleware.request_logger._is_enabled",
                return_value=False,
            ),
            caplog.at_level(logging.INFO, "tool_router.request_logger"),
        ):
            resp = client.get("/test")

        assert resp.status_code == 200
        assert not any("request completed" in r.message for r in caplog.records)

    def test_logs_error_status(self, caplog):
        app = _make_app()
        client = TestClient(app)

        with (
            patch(
                "tool_router.middleware.request_logger._is_enabled",
                return_value=True,
            ),
            caplog.at_level(logging.INFO, "tool_router.request_logger"),
        ):
            resp = client.get("/error")

        assert resp.status_code == 500
        log = next(r for r in caplog.records if "request completed" in r.message)
        assert log.status == "error"  # type: ignore[attr-defined]
        assert log.status_code == 500  # type: ignore[attr-defined]

    def test_uses_x_request_id_header(self, caplog):
        app = _make_app()
        client = TestClient(app)

        with (
            patch(
                "tool_router.middleware.request_logger._is_enabled",
                return_value=True,
            ),
            caplog.at_level(logging.INFO, "tool_router.request_logger"),
        ):
            client.get("/test", headers={"x-request-id": "abc-123"})

        log = next(r for r in caplog.records if "request completed" in r.message)
        assert log.request_id == "abc-123"  # type: ignore[attr-defined]

    def test_generates_request_id_when_missing(self, caplog):
        app = _make_app()
        client = TestClient(app)

        with (
            patch(
                "tool_router.middleware.request_logger._is_enabled",
                return_value=True,
            ),
            caplog.at_level(logging.INFO, "tool_router.request_logger"),
        ):
            client.get("/test")

        log = next(r for r in caplog.records if "request completed" in r.message)
        assert len(log.request_id) == 12  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Coverage gap: _is_enabled() returns False — early return path (line 25-26)
# ---------------------------------------------------------------------------


class TestRequestLoggingDisabledPath:
    """Cover the early return when REQUEST_LOGGING is disabled."""

    def test_disabled_logging_passes_through(self) -> None:
        app = _make_app()
        client = TestClient(app)

        with patch("tool_router.middleware.request_logger._is_enabled", return_value=False):
            resp = client.get("/test")

        assert resp.status_code == 200
        assert resp.json() == {"ok": True}

    def test_is_enabled_returns_false_by_default(self) -> None:
        """Call _is_enabled() directly so line 20 executes (env var not set)."""
        import os

        from tool_router.middleware.request_logger import _is_enabled

        env_bak = os.environ.pop("REQUEST_LOGGING", None)
        try:
            assert _is_enabled() is False
        finally:
            if env_bak is not None:
                os.environ["REQUEST_LOGGING"] = env_bak

    def test_is_enabled_returns_true_when_env_set(self) -> None:
        """Call _is_enabled() directly with env var true."""
        import os

        from tool_router.middleware.request_logger import _is_enabled

        os.environ["REQUEST_LOGGING"] = "true"
        try:
            assert _is_enabled() is True
        finally:
            del os.environ["REQUEST_LOGGING"]
