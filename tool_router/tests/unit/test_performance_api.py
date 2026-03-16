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

    def test_returns_500_on_exception(self, client: TestClient) -> None:
        with patch(
            "tool_router.api.performance._get_cache_metrics_data",
            side_effect=RuntimeError("perf failure"),
        ):
            resp = client.get("/monitoring/performance")
        assert resp.status_code == 500

    def test_recommendation_low_hit_rate(self, client: TestClient) -> None:
        """Lines 342-343: hit_rate < 0.5 → recommendation about increasing TTL/size."""
        low_hit_metrics = {
            "global": {
                "hit_rate": 0.3,
                "hits": 30,
                "misses": 70,
                "total_requests": 100,
                "cache_sizes": {},
                "hits_by_type": {},
                "misses_by_type": {},
            }
        }
        qc = MagicMock()
        qc.get_metrics.return_value = {"enabled": True, "cache_size": 0, "metrics": {"cache_hit_rate": 0.5}}
        with (
            patch("tool_router.api.performance._get_cache_metrics_data", return_value=low_hit_metrics),
            patch("tool_router.api.performance.get_query_cache", return_value=qc),
        ):
            resp = client.get("/monitoring/performance")
        assert resp.status_code == 200
        recs = resp.json()["recommendations"]
        assert any("cache TTL" in r or "hit rate" in r.lower() for r in recs)

    def test_recommendation_high_hit_rate(self, client: TestClient) -> None:
        """Line 345: hit_rate > 0.9 → recommendation about reducing cache size."""
        high_hit_metrics = {
            "global": {
                "hit_rate": 0.95,
                "hits": 950,
                "misses": 50,
                "total_requests": 1000,
                "cache_sizes": {},
                "hits_by_type": {},
                "misses_by_type": {},
            }
        }
        qc = MagicMock()
        qc.get_metrics.return_value = {"enabled": True, "cache_size": 0, "metrics": {"cache_hit_rate": 0.8}}
        with (
            patch("tool_router.api.performance._get_cache_metrics_data", return_value=high_hit_metrics),
            patch("tool_router.api.performance.get_query_cache", return_value=qc),
        ):
            resp = client.get("/monitoring/performance")
        assert resp.status_code == 200
        recs = resp.json()["recommendations"]
        assert any("reducing cache size" in r or "memory" in r.lower() for r in recs)

    def test_recommendation_no_issues(self, client: TestClient) -> None:
        """Line 356: no specific issues → 'no immediate recommendations' fallback."""
        mid_hit_metrics = {
            "global": {
                "hit_rate": 0.75,
                "hits": 750,
                "misses": 250,
                "total_requests": 1000,
                "cache_sizes": {},
                "hits_by_type": {},
                "misses_by_type": {},
            }
        }
        qc = MagicMock()
        # query cache hit rate >= 0.3 to avoid that recommendation
        qc.get_metrics.return_value = {"enabled": True, "cache_size": 0, "metrics": {"cache_hit_rate": 0.5}}
        with (
            patch("tool_router.api.performance._get_cache_metrics_data", return_value=mid_hit_metrics),
            patch("tool_router.api.performance.get_query_cache", return_value=qc),
            # Patch _start_time to a value far in the past so uptime > 300s
            patch("tool_router.api.performance._start_time", 0.0),
        ):
            resp = client.get("/monitoring/performance")
        assert resp.status_code == 200
        recs = resp.json()["recommendations"]
        assert any("no immediate recommendations" in r.lower() for r in recs)


# ---------------------------------------------------------------------------
# POST /monitoring/metrics/cache/reset — error path (lines 211-213)
# ---------------------------------------------------------------------------


class TestResetCacheMetricsErrors:
    def test_returns_500_on_exception(self, client: TestClient) -> None:
        with patch(
            "tool_router.api.performance._reset_cache_metrics_data",
            side_effect=RuntimeError("reset failure"),
        ):
            resp = client.post("/monitoring/metrics/cache/reset")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# POST /monitoring/cache/clear (lines 223-244)
# ---------------------------------------------------------------------------


class TestClearCache:
    def test_clear_specific_cache(self, client: TestClient) -> None:
        with patch("tool_router.cache.clear_cache") as mock_clear:
            resp = client.post("/monitoring/cache/clear?cache_name=ai_selector")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "ai_selector" in data["message"]
        mock_clear.assert_called_once_with("ai_selector")

    def test_clear_all_caches(self, client: TestClient) -> None:
        with patch("tool_router.cache.clear_all_caches") as mock_clear_all:
            resp = client.post("/monitoring/cache/clear")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "all" in data["message"].lower()
        mock_clear_all.assert_called_once()

    def test_returns_500_on_exception(self, client: TestClient) -> None:
        with patch("tool_router.cache.clear_all_caches", side_effect=RuntimeError("clear failure")):
            resp = client.post("/monitoring/cache/clear")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# GET /monitoring/cache/info (lines 253-257)
# ---------------------------------------------------------------------------


class TestGetCacheInfo:
    def test_returns_cache_info(self, client: TestClient) -> None:
        mock_cm = MagicMock()
        mock_cm.get_cache_info.return_value = {"ai_selector": {"size": 50, "max_size": 500}}
        with patch("tool_router.api.performance.cache_manager", mock_cm):
            resp = client.get("/monitoring/cache/info")
        assert resp.status_code == 200
        assert "ai_selector" in resp.json()

    def test_returns_500_on_exception(self, client: TestClient) -> None:
        mock_cm = MagicMock()
        mock_cm.get_cache_info.side_effect = RuntimeError("info failure")
        with patch("tool_router.api.performance.cache_manager", mock_cm):
            resp = client.get("/monitoring/cache/info")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# POST /monitoring/query-cache/invalidate (lines 267-286)
# ---------------------------------------------------------------------------


class TestInvalidateQueryCache:
    def test_invalidates_specific_table(self, client: TestClient) -> None:
        mock_qc = MagicMock()
        with patch("tool_router.api.performance.get_query_cache", return_value=mock_qc):
            resp = client.post("/monitoring/query-cache/invalidate?table=users")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "users" in data["message"]
        mock_qc.invalidate_table.assert_called_once_with("users")

    def test_invalidates_all_tables(self, client: TestClient) -> None:
        mock_qc = MagicMock()
        with patch("tool_router.api.performance.get_query_cache", return_value=mock_qc):
            resp = client.post("/monitoring/query-cache/invalidate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "all" in data["message"].lower()
        mock_qc.invalidate_all.assert_called_once()

    def test_returns_500_on_exception(self, client: TestClient) -> None:
        with patch("tool_router.api.performance.get_query_cache", side_effect=RuntimeError("qc fail")):
            resp = client.post("/monitoring/query-cache/invalidate")
        assert resp.status_code == 500
