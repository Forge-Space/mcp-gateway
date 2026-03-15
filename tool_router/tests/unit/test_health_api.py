"""Tests for tool_router/api/health.py HTTP endpoints.

All database interactions are mocked so tests are fast and hermetic.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tool_router.api.health import router as health_router


# ---------------------------------------------------------------------------
# App fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(health_router)
    return TestClient(app, raise_server_exceptions=False)


def _healthy_db_response() -> dict[str, Any]:
    return {
        "status": "healthy",
        "database": "connected",
        "timestamp": datetime.now(UTC).isoformat(),
    }


def _unhealthy_db_response() -> dict[str, Any]:
    return {
        "status": "unhealthy",
        "database": "disconnected",
        "timestamp": datetime.now(UTC).isoformat(),
        "error": "Connection refused",
    }


# ---------------------------------------------------------------------------
# GET /health/  —  system health
# ---------------------------------------------------------------------------


class TestHealthCheck:
    def test_returns_200_when_healthy(self, client: TestClient) -> None:
        mock_client = AsyncMock()
        mock_client.health_check = AsyncMock(return_value=_healthy_db_response())
        with patch("tool_router.api.health.get_database_client", new=AsyncMock(return_value=mock_client)):
            resp = client.get("/health/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"

    def test_returns_200_unhealthy_when_db_down(self, client: TestClient) -> None:
        mock_client = AsyncMock()
        mock_client.health_check = AsyncMock(return_value=_unhealthy_db_response())
        with patch("tool_router.api.health.get_database_client", new=AsyncMock(return_value=mock_client)):
            resp = client.get("/health/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "unhealthy"

    def test_returns_200_on_exception(self, client: TestClient) -> None:
        with patch(
            "tool_router.api.health.get_database_client",
            new=AsyncMock(side_effect=ConnectionError("timeout")),
        ):
            resp = client.get("/health/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "unhealthy"
        assert "error" in data["details"]


# ---------------------------------------------------------------------------
# GET /health/database
# ---------------------------------------------------------------------------


class TestDatabaseHealth:
    def test_returns_200_when_healthy(self, client: TestClient) -> None:
        mock_client = AsyncMock()
        mock_client.health_check = AsyncMock(return_value=_healthy_db_response())
        with patch("tool_router.api.health.get_database_client", new=AsyncMock(return_value=mock_client)):
            resp = client.get("/health/database")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["connection"] == "connected"

    def test_returns_503_on_exception(self, client: TestClient) -> None:
        with patch(
            "tool_router.api.health.get_database_client",
            new=AsyncMock(side_effect=RuntimeError("DB unavailable")),
        ):
            resp = client.get("/health/database")
        assert resp.status_code == 503


# ---------------------------------------------------------------------------
# GET /health/readiness
# ---------------------------------------------------------------------------


class TestReadinessCheck:
    def test_ready_when_db_healthy(self, client: TestClient) -> None:
        mock_client = AsyncMock()
        mock_client.health_check = AsyncMock(return_value=_healthy_db_response())
        with patch("tool_router.api.health.get_database_client", new=AsyncMock(return_value=mock_client)):
            resp = client.get("/health/readiness")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ready"] is True
        assert data["checks"]["database"] is True

    def test_not_ready_when_db_unhealthy(self, client: TestClient) -> None:
        mock_client = AsyncMock()
        mock_client.health_check = AsyncMock(return_value=_unhealthy_db_response())
        with patch("tool_router.api.health.get_database_client", new=AsyncMock(return_value=mock_client)):
            resp = client.get("/health/readiness")
        assert resp.status_code == 200
        assert resp.json()["ready"] is False

    def test_not_ready_on_exception(self, client: TestClient) -> None:
        with patch(
            "tool_router.api.health.get_database_client",
            new=AsyncMock(side_effect=Exception("unexpected")),
        ):
            resp = client.get("/health/readiness")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ready"] is False


# ---------------------------------------------------------------------------
# GET /health/liveness
# ---------------------------------------------------------------------------


class TestLivenessCheck:
    def test_always_alive(self, client: TestClient) -> None:
        resp = client.get("/health/liveness")
        assert resp.status_code == 200
        data = resp.json()
        assert data["alive"] is True

    def test_timestamp_is_current_not_hardcoded(self, client: TestClient) -> None:
        """Regression: liveness previously returned '2025-01-20T00:00:00Z'."""
        resp = client.get("/health/liveness")
        assert resp.status_code == 200
        ts = resp.json()["timestamp"]
        assert ts != "2025-01-20T00:00:00Z", "Hardcoded timestamp bug still present"
        # Should be a valid ISO 8601 timestamp from ~now
        parsed = datetime.fromisoformat(ts)
        assert parsed.year >= 2026, f"Expected current year, got {ts}"


# ---------------------------------------------------------------------------
# POST /health/close
# ---------------------------------------------------------------------------


class TestCloseConnections:
    def test_returns_200_on_success(self, client: TestClient) -> None:
        with patch("tool_router.api.health.close_database_client", new=AsyncMock()):
            resp = client.post("/health/close")
        assert resp.status_code == 200
        assert resp.json()["status"] == "connections_closed"

    def test_returns_500_on_exception(self, client: TestClient) -> None:
        with patch(
            "tool_router.api.health.close_database_client",
            new=AsyncMock(side_effect=RuntimeError("could not close")),
        ):
            resp = client.post("/health/close")
        assert resp.status_code == 500
