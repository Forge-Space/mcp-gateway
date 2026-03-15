"""Tests for tool_router/api/performance.py HTTP endpoints.

All cache/database interactions are mocked so tests are fast and hermetic.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tool_router.api.performance import router as performance_router


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _mock_cache_metrics() -> dict:
    return {
        "global": {
            "hit_rate": 0.85,
            "hits": 850,
            "misses": 150,
            "total_requests": 1000,
            "cache_sizes": {"ai_selector": 50, "gateway": 30},
            "hits_by_type": {"ai_selector": 600, "gateway": 250},
            "misses_by_type": {"ai_selector": 100, "gateway": 50},
        }
    }


def _mock_query_cache() -> MagicMock:
    qc = MagicMock()
    qc.config.enabled = True
    qc.get_stats.return_value = {"hits": 100, "misses": 20, "size": 50}
    qc.get_metrics.return_value = {"hits": 100, "misses": 20, "size": 50, "enabled": True}
    return qc


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(performance_router)
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# GET /monitoring/health
# ---------------------------------------------------------------------------


class TestMonitoringHealth:
    def test_returns_200(self, client: TestClient) -> None:
        mock_cm = MagicMock()
        mock_cm._caches = {"a": 1, "b": 2}
        with (
            patch("tool_router.api.performance.cache_manager", mock_cm),
            patch("tool_router.api.performance.get_query_cache", return_value=_mock_query_cache()),
        ):
            resp = client.get("/monitoring/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("healthy", "degraded")
        assert "checks" in data
        assert "uptime_seconds" in data["checks"]

    def test_status_healthy_when_all_up(self, client: TestClient) -> None:
        mock_cm = MagicMock()
        mock_cm._caches = {"a": 1}
        with (
            patch("tool_router.api.performance.cache_manager", mock_cm),
            patch("tool_router.api.performance.get_query_cache", return_value=_mock_query_cache()),
        ):
            resp = client.get("/monitoring/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


# ---------------------------------------------------------------------------
# GET /monitoring/metrics/cache
# ---------------------------------------------------------------------------


class TestCacheMetrics:
    def test_returns_cache_hit_rate(self, client: TestClient) -> None:
        with patch(
            "tool_router.api.performance._get_cache_metrics_data",
            return_value=_mock_cache_metrics(),
        ):
            resp = client.get("/monitoring/metrics/cache")
        assert resp.status_code == 200
        data = resp.json()
        assert data["cache_hit_rate"] == pytest.approx(0.85)
        assert data["total_hits"] == 850
        assert data["total_misses"] == 150

    def test_returns_500_on_exception(self, client: TestClient) -> None:
        with patch(
            "tool_router.api.performance._get_cache_metrics_data",
            side_effect=RuntimeError("cache down"),
        ):
            resp = client.get("/monitoring/metrics/cache")
        assert resp.status_code == 500

    def test_empty_metrics_returns_zeros(self, client: TestClient) -> None:
        with patch(
            "tool_router.api.performance._get_cache_metrics_data",
            return_value={},
        ):
            resp = client.get("/monitoring/metrics/cache")
        assert resp.status_code == 200
        assert resp.json()["cache_hit_rate"] == 0.0


# ---------------------------------------------------------------------------
# GET /monitoring/metrics/system
# ---------------------------------------------------------------------------


class TestSystemMetrics:
    def test_returns_200(self, client: TestClient) -> None:
        with (
            patch(
                "tool_router.api.performance._get_cache_metrics_data",
                return_value=_mock_cache_metrics(),
            ),
            patch("tool_router.api.performance.get_query_cache", return_value=_mock_query_cache()),
        ):
            resp = client.get("/monitoring/metrics/system")
        assert resp.status_code == 200
        data = resp.json()
        assert "timestamp" in data
        assert "uptime" in data
        assert "cache_metrics" in data

    def test_returns_500_on_exception(self, client: TestClient) -> None:
        with patch(
            "tool_router.api.performance._get_cache_metrics_data",
            side_effect=RuntimeError("cache failure"),
        ):
            resp = client.get("/monitoring/metrics/system")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# POST /monitoring/metrics/reset
# ---------------------------------------------------------------------------


class TestResetCacheMetrics:
    def test_returns_200_on_success(self, client: TestClient) -> None:
        mock_cm = MagicMock()
        with patch("tool_router.api.performance.cache_manager", mock_cm):
            resp = client.post("/monitoring/metrics/cache/reset")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"

    def test_accepts_cache_name_param(self, client: TestClient) -> None:
        mock_cm = MagicMock()
        with patch("tool_router.api.performance.cache_manager", mock_cm):
            resp = client.post("/monitoring/metrics/cache/reset?cache_name=ai_selector")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /monitoring/performance  (summary endpoint)
# ---------------------------------------------------------------------------


class TestPerformanceSummary:
    def test_returns_200(self, client: TestClient) -> None:
        with (
            patch(
                "tool_router.api.performance._get_cache_metrics_data",
                return_value=_mock_cache_metrics(),
            ),
            patch("tool_router.api.performance.get_query_cache", return_value=_mock_query_cache()),
        ):
            resp = client.get("/monitoring/performance")
        assert resp.status_code == 200
        data = resp.json()
        assert "uptime_seconds" in data
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)
