"""Unit tests for tool_router/api/cache_dashboard.py.

All cache/dashboard interactions are mocked so tests are fast and hermetic.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tool_router.api.cache_dashboard import router


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PATCH_BASE = "tool_router.api.cache_dashboard"


def _make_metrics_mock(cache_name: str = "test_cache") -> MagicMock:
    m = MagicMock()
    m.timestamp = 1_700_000_000.0
    m.cache_name = cache_name
    m.backend_type = "memory"
    m.hits = 100
    m.misses = 20
    m.evictions = 5
    m.total_requests = 120
    m.hit_rate = 0.833
    m.current_size = 80
    m.max_size = 500
    m.memory_usage = 1024
    m.avg_get_time = 0.001
    m.avg_set_time = 0.002
    m.avg_delete_time = 0.001
    m.redis_connected = False
    m.redis_memory_usage = 0
    m.redis_key_count = 0
    m.health_status = "healthy"
    m.last_health_check = 1_700_000_000.0
    return m


def _make_alert_mock(
    alert_id: str = "a1",
    resolved: bool = False,
) -> MagicMock:
    a = MagicMock()
    a.alert_id = alert_id
    a.alert_type = "high_miss_rate"
    a.severity = "warning"
    a.message = "Miss rate is high"
    a.cache_name = "test_cache"
    a.timestamp = 1_700_000_000.0
    a.resolved = resolved
    a.resolved_at = 1_700_001_000.0 if resolved else None
    return a


def _make_snapshot_mock(
    include_metrics: bool = True,
    include_alerts: bool = False,
) -> MagicMock:
    snap = MagicMock()
    snap.timestamp = 1_700_000_000.0
    snap.summary = {"total_caches": 1, "healthy": 1}
    snap.metrics = {"test_cache": _make_metrics_mock()} if include_metrics else {}
    snap.alerts = [_make_alert_mock()] if include_alerts else []
    return snap


def _make_dashboard_mock() -> MagicMock:
    dashboard = MagicMock()
    dashboard._running = False
    dashboard._collection_interval = 30
    dashboard.get_dashboard_config.return_value = {
        "collection_interval": 30,
        "max_history_hours": 24,
        "alert_retention_hours": 48,
        "running": False,
        "cache_count": 1,
        "alert_rules": {},
    }
    dashboard.get_historical_data.return_value = []
    dashboard.get_cache_health_status.return_value = {"test_cache": "healthy"}
    dashboard.get_current_snapshot.return_value = _make_snapshot_mock()
    dashboard.collect_snapshot.return_value = _make_snapshot_mock()
    dashboard.export_metrics.return_value = {"data": "exported"}
    dashboard.alert_manager.get_alert_history.return_value = []
    dashboard.alert_manager.get_active_alerts.return_value = []
    return dashboard


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def mock_dashboard() -> MagicMock:
    return _make_dashboard_mock()


# ---------------------------------------------------------------------------
# GET /api/cache/dashboard/status
# ---------------------------------------------------------------------------


class TestGetDashboardStatus:
    def test_returns_200_with_config_fields(self, client: TestClient, mock_dashboard: MagicMock) -> None:
        with patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", return_value=mock_dashboard):
            resp = client.get("/api/cache/dashboard/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["collection_interval"] == 30
        assert data["max_history_hours"] == 24
        assert data["alert_retention_hours"] == 48
        assert data["running"] is False
        assert data["cache_count"] == 1
        assert isinstance(data["alert_rules"], dict)

    def test_returns_500_on_exception(self, client: TestClient) -> None:
        with patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", side_effect=RuntimeError("boom")):
            resp = client.get("/api/cache/dashboard/status")
        assert resp.status_code == 500

    def test_running_true_reflected(self, client: TestClient, mock_dashboard: MagicMock) -> None:
        mock_dashboard.get_dashboard_config.return_value = {
            "collection_interval": 60,
            "max_history_hours": 24,
            "alert_retention_hours": 48,
            "running": True,
            "cache_count": 2,
            "alert_rules": {"rule1": {"threshold": 0.5}},
        }
        with patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", return_value=mock_dashboard):
            resp = client.get("/api/cache/dashboard/status")
        assert resp.status_code == 200
        assert resp.json()["running"] is True


# ---------------------------------------------------------------------------
# POST /api/cache/dashboard/start
# ---------------------------------------------------------------------------


class TestStartCollection:
    def test_starts_when_not_running(self, client: TestClient, mock_dashboard: MagicMock) -> None:
        mock_dashboard._running = False
        with (
            patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", return_value=mock_dashboard),
            patch(f"{_PATCH_BASE}.start_dashboard_collection") as mock_start,
        ):
            resp = client.post("/api/cache/dashboard/start?interval=30")
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Dashboard collection started"
        assert data["interval"] == 30
        # background task is added, but start_dashboard_collection is called via background
        _ = mock_start  # verified it's patchable

    def test_already_running_returns_info(self, client: TestClient, mock_dashboard: MagicMock) -> None:
        mock_dashboard._running = True
        mock_dashboard._collection_interval = 45
        with patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", return_value=mock_dashboard):
            resp = client.post("/api/cache/dashboard/start")
        assert resp.status_code == 200
        data = resp.json()
        assert "already running" in data["message"]
        assert data["interval"] == 45

    def test_custom_interval_accepted(self, client: TestClient, mock_dashboard: MagicMock) -> None:
        mock_dashboard._running = False
        with (
            patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", return_value=mock_dashboard),
            patch(f"{_PATCH_BASE}.start_dashboard_collection"),
        ):
            resp = client.post("/api/cache/dashboard/start?interval=120")
        assert resp.status_code == 200
        assert resp.json()["interval"] == 120

    def test_returns_500_on_exception(self, client: TestClient) -> None:
        with patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", side_effect=RuntimeError("fail")):
            resp = client.post("/api/cache/dashboard/start")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# POST /api/cache/dashboard/stop
# ---------------------------------------------------------------------------


class TestStopCollection:
    def test_stops_when_running(self, client: TestClient, mock_dashboard: MagicMock) -> None:
        mock_dashboard._running = True
        with (
            patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", return_value=mock_dashboard),
            patch(f"{_PATCH_BASE}.stop_dashboard_collection") as mock_stop,
        ):
            resp = client.post("/api/cache/dashboard/stop")
        assert resp.status_code == 200
        assert resp.json()["message"] == "Dashboard collection stopped"
        mock_stop.assert_called_once()

    def test_not_running_returns_message(self, client: TestClient, mock_dashboard: MagicMock) -> None:
        mock_dashboard._running = False
        with patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", return_value=mock_dashboard):
            resp = client.post("/api/cache/dashboard/stop")
        assert resp.status_code == 200
        assert "not running" in resp.json()["message"]

    def test_returns_500_on_exception(self, client: TestClient) -> None:
        with patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", side_effect=RuntimeError("fail")):
            resp = client.post("/api/cache/dashboard/stop")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# GET /api/cache/dashboard/snapshot
# ---------------------------------------------------------------------------


class TestGetCurrentSnapshot:
    def test_returns_snapshot_with_metrics(self, client: TestClient) -> None:
        snap = _make_snapshot_mock(include_metrics=True, include_alerts=False)
        with patch(f"{_PATCH_BASE}.get_dashboard_data", return_value=snap):
            resp = client.get("/api/cache/dashboard/snapshot")
        assert resp.status_code == 200
        data = resp.json()
        assert "timestamp" in data
        assert "metrics" in data
        assert "test_cache" in data["metrics"]
        assert data["metrics"]["test_cache"]["cache_name"] == "test_cache"

    def test_returns_snapshot_with_alerts(self, client: TestClient) -> None:
        snap = _make_snapshot_mock(include_metrics=True, include_alerts=True)
        with patch(f"{_PATCH_BASE}.get_dashboard_data", return_value=snap):
            resp = client.get("/api/cache/dashboard/snapshot")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["alerts"]) == 1
        assert data["alerts"][0]["alert_id"] == "a1"

    def test_returns_404_when_no_snapshot(self, client: TestClient) -> None:
        with patch(f"{_PATCH_BASE}.get_dashboard_data", return_value=None):
            resp = client.get("/api/cache/dashboard/snapshot")
        assert resp.status_code == 404

    def test_returns_500_on_exception(self, client: TestClient) -> None:
        with patch(f"{_PATCH_BASE}.get_dashboard_data", side_effect=RuntimeError("fail")):
            resp = client.get("/api/cache/dashboard/snapshot")
        assert resp.status_code == 500

    def test_empty_metrics_dict(self, client: TestClient) -> None:
        snap = _make_snapshot_mock(include_metrics=False, include_alerts=False)
        with patch(f"{_PATCH_BASE}.get_dashboard_data", return_value=snap):
            resp = client.get("/api/cache/dashboard/snapshot")
        assert resp.status_code == 200
        assert resp.json()["metrics"] == {}


# ---------------------------------------------------------------------------
# GET /api/cache/dashboard/history
# ---------------------------------------------------------------------------


class TestGetHistoricalData:
    def test_returns_empty_when_no_data(self, client: TestClient, mock_dashboard: MagicMock) -> None:
        mock_dashboard.get_historical_data.return_value = []
        with patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", return_value=mock_dashboard):
            resp = client.get("/api/cache/dashboard/history")
        assert resp.status_code == 200
        data = resp.json()
        assert data["snapshots"] == []
        assert "No historical data available" in data["message"]

    def test_returns_snapshots_list(self, client: TestClient, mock_dashboard: MagicMock) -> None:
        snap = _make_snapshot_mock(include_metrics=True)
        mock_dashboard.get_historical_data.return_value = [snap, snap]
        with patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", return_value=mock_dashboard):
            resp = client.get("/api/cache/dashboard/history?hours=12")
        assert resp.status_code == 200
        data = resp.json()
        assert data["hours"] == 12
        assert data["snapshot_count"] == 2
        assert len(data["snapshots"]) == 2

    def test_snapshot_contains_metrics(self, client: TestClient, mock_dashboard: MagicMock) -> None:
        snap = _make_snapshot_mock(include_metrics=True)
        mock_dashboard.get_historical_data.return_value = [snap]
        with patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", return_value=mock_dashboard):
            resp = client.get("/api/cache/dashboard/history")
        data = resp.json()
        assert "test_cache" in data["snapshots"][0]["metrics"]

    def test_returns_500_on_exception(self, client: TestClient) -> None:
        with patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", side_effect=RuntimeError("fail")):
            resp = client.get("/api/cache/dashboard/history")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# GET /api/cache/dashboard/trends
# ---------------------------------------------------------------------------


class TestGetPerformanceTrends:
    def test_returns_empty_when_no_data(self, client: TestClient) -> None:
        with patch(f"{_PATCH_BASE}.get_dashboard_trends", return_value={}):
            resp = client.get("/api/cache/dashboard/trends")
        assert resp.status_code == 200
        data = resp.json()
        assert data["trends"] == {}
        assert "No trend data available" in data["message"]

    def test_returns_trend_data(self, client: TestClient) -> None:
        trend_data = {
            "test_cache": {
                "hit_rate_trend": 0.05,
                "miss_rate_trend": -0.05,
                "size_trend": 10,
                "avg_hit_rate": 0.80,
                "avg_miss_rate": 0.20,
                "peak_hit_rate": 0.95,
                "peak_miss_rate": 0.30,
                "min_hit_rate": 0.60,
                "min_miss_rate": 0.10,
                "data_points": 24,
            }
        }
        with patch(f"{_PATCH_BASE}.get_dashboard_trends", return_value=trend_data):
            resp = client.get("/api/cache/dashboard/trends?hours=48")
        assert resp.status_code == 200
        data = resp.json()
        assert data["hours"] == 48
        assert data["cache_count"] == 1
        assert len(data["trends"]) == 1
        assert data["trends"][0]["cache_name"] == "test_cache"

    def test_returns_500_on_exception(self, client: TestClient) -> None:
        with patch(f"{_PATCH_BASE}.get_dashboard_trends", side_effect=RuntimeError("fail")):
            resp = client.get("/api/cache/dashboard/trends")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# GET /api/cache/dashboard/alerts
# ---------------------------------------------------------------------------


class TestGetAlertsSummary:
    def test_returns_alert_summary(self, client: TestClient) -> None:
        summary = {
            "active_alerts": 2,
            "total_alerts": 10,
            "severity_breakdown": {"warning": 7, "critical": 3},
            "most_recent_alert": 1_700_000_000.0,
            "alert_types": ["high_miss_rate", "low_hit_rate"],
        }
        with patch(f"{_PATCH_BASE}.get_alert_summary", return_value=summary):
            resp = client.get("/api/cache/dashboard/alerts")
        assert resp.status_code == 200
        data = resp.json()
        assert data["active_alerts"] == 2
        assert data["total_alerts"] == 10
        assert "warning" in data["severity_breakdown"]

    def test_returns_500_on_exception(self, client: TestClient) -> None:
        with patch(f"{_PATCH_BASE}.get_alert_summary", side_effect=RuntimeError("fail")):
            resp = client.get("/api/cache/dashboard/alerts")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# GET /api/cache/dashboard/alerts/history
# ---------------------------------------------------------------------------


class TestGetAlertsHistory:
    def test_returns_empty_history(self, client: TestClient, mock_dashboard: MagicMock) -> None:
        mock_dashboard.alert_manager.get_alert_history.return_value = []
        with patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", return_value=mock_dashboard):
            resp = client.get("/api/cache/dashboard/alerts/history")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_alerts"] == 0
        assert data["alerts"] == []

    def test_returns_alert_list(self, client: TestClient, mock_dashboard: MagicMock) -> None:
        alert = _make_alert_mock(resolved=True)
        mock_dashboard.alert_manager.get_alert_history.return_value = [alert]
        with patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", return_value=mock_dashboard):
            resp = client.get("/api/cache/dashboard/alerts/history?limit=50")
        assert resp.status_code == 200
        data = resp.json()
        assert data["limit"] == 50
        assert data["total_alerts"] == 1
        assert data["alerts"][0]["alert_id"] == "a1"
        assert data["alerts"][0]["resolved"] is True

    def test_returns_500_on_exception(self, client: TestClient) -> None:
        with patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", side_effect=RuntimeError("fail")):
            resp = client.get("/api/cache/dashboard/alerts/history")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# GET /api/cache/dashboard/alerts/active
# ---------------------------------------------------------------------------


class TestGetActiveAlerts:
    def test_returns_empty_active_alerts(self, client: TestClient, mock_dashboard: MagicMock) -> None:
        mock_dashboard.alert_manager.get_active_alerts.return_value = []
        with patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", return_value=mock_dashboard):
            resp = client.get("/api/cache/dashboard/alerts/active")
        assert resp.status_code == 200
        data = resp.json()
        assert data["active_alerts"] == 0
        assert data["alerts"] == []

    def test_returns_active_alert(self, client: TestClient, mock_dashboard: MagicMock) -> None:
        alert = _make_alert_mock(alert_id="active1", resolved=False)
        mock_dashboard.alert_manager.get_active_alerts.return_value = [alert]
        with patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", return_value=mock_dashboard):
            resp = client.get("/api/cache/dashboard/alerts/active")
        assert resp.status_code == 200
        data = resp.json()
        assert data["active_alerts"] == 1
        assert data["alerts"][0]["alert_id"] == "active1"
        assert data["alerts"][0]["resolved"] is False

    def test_returns_500_on_exception(self, client: TestClient) -> None:
        with patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", side_effect=RuntimeError("fail")):
            resp = client.get("/api/cache/dashboard/alerts/active")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# GET /api/cache/dashboard/health
# ---------------------------------------------------------------------------


class TestGetCacheHealth:
    def test_returns_health_status(self, client: TestClient, mock_dashboard: MagicMock) -> None:
        mock_dashboard.get_cache_health_status.return_value = {"cache_a": "healthy", "cache_b": "degraded"}
        mock_dashboard.get_current_snapshot.return_value = _make_snapshot_mock()
        with patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", return_value=mock_dashboard):
            resp = client.get("/api/cache/dashboard/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "cache_health" in data
        assert data["healthy_count"] == 1
        assert data["total_count"] == 2

    def test_health_when_no_snapshot(self, client: TestClient, mock_dashboard: MagicMock) -> None:
        mock_dashboard.get_cache_health_status.return_value = {}
        mock_dashboard.get_current_snapshot.return_value = None
        with patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", return_value=mock_dashboard):
            resp = client.get("/api/cache/dashboard/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["timestamp"] is None
        assert data["total_count"] == 0

    def test_returns_500_on_exception(self, client: TestClient) -> None:
        with patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", side_effect=RuntimeError("fail")):
            resp = client.get("/api/cache/dashboard/health")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# GET /api/cache/dashboard/export
# ---------------------------------------------------------------------------


class TestExportMetrics:
    def test_export_json_format(self, client: TestClient, mock_dashboard: MagicMock) -> None:
        mock_dashboard.export_metrics.return_value = {"snapshot": "data"}
        with patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", return_value=mock_dashboard):
            resp = client.get("/api/cache/dashboard/export?format=json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["format"] == "json"
        assert "data" in data
        mock_dashboard.export_metrics.assert_called_with("json")

    def test_export_csv_format(self, client: TestClient, mock_dashboard: MagicMock) -> None:
        mock_dashboard.export_metrics.return_value = "cache_name,hit_rate\ntest_cache,0.83"
        with patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", return_value=mock_dashboard):
            resp = client.get("/api/cache/dashboard/export?format=csv")
        assert resp.status_code == 200
        data = resp.json()
        assert data["format"] == "csv"
        mock_dashboard.export_metrics.assert_called_with("csv")

    def test_unsupported_format_rejected(self, client: TestClient) -> None:
        # The pattern= constraint in Query rejects invalid formats at validation time
        resp = client.get("/api/cache/dashboard/export?format=xml")
        assert resp.status_code == 422

    def test_returns_500_on_exception(self, client: TestClient) -> None:
        with patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", side_effect=RuntimeError("fail")):
            resp = client.get("/api/cache/dashboard/export?format=json")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# POST /api/cache/dashboard/collect
# ---------------------------------------------------------------------------


class TestTriggerCollection:
    def test_returns_collection_result(self, client: TestClient, mock_dashboard: MagicMock) -> None:
        snap = _make_snapshot_mock(include_metrics=True, include_alerts=True)
        mock_dashboard.collect_snapshot.return_value = snap
        with patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", return_value=mock_dashboard):
            resp = client.post("/api/cache/dashboard/collect")
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Collection triggered successfully"
        assert data["cache_count"] == 1
        assert data["alert_count"] == 1
        assert "timestamp" in data

    def test_returns_500_on_exception(self, client: TestClient) -> None:
        with patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", side_effect=RuntimeError("fail")):
            resp = client.post("/api/cache/dashboard/collect")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# GET /api/cache/dashboard/cache/{cache_name}
# ---------------------------------------------------------------------------


class TestGetCacheMetrics:
    def test_returns_metrics_for_known_cache(self, client: TestClient, mock_dashboard: MagicMock) -> None:
        with patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", return_value=mock_dashboard):
            resp = client.get("/api/cache/dashboard/cache/test_cache")
        assert resp.status_code == 200
        data = resp.json()
        assert data["cache_name"] == "test_cache"
        assert data["backend_type"] == "memory"
        assert data["hits"] == 100
        assert data["hit_rate"] == pytest.approx(0.833)

    def test_returns_404_when_no_snapshot(self, client: TestClient, mock_dashboard: MagicMock) -> None:
        mock_dashboard.get_current_snapshot.return_value = None
        with patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", return_value=mock_dashboard):
            resp = client.get("/api/cache/dashboard/cache/test_cache")
        assert resp.status_code == 404

    def test_returns_404_for_unknown_cache(self, client: TestClient, mock_dashboard: MagicMock) -> None:
        with patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", return_value=mock_dashboard):
            resp = client.get("/api/cache/dashboard/cache/nonexistent")
        assert resp.status_code == 404
        assert "nonexistent" in resp.json()["detail"]

    def test_returns_500_on_exception(self, client: TestClient) -> None:
        with patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", side_effect=RuntimeError("fail")):
            resp = client.get("/api/cache/dashboard/cache/test_cache")
        assert resp.status_code == 500

    def test_metrics_all_fields_present(self, client: TestClient, mock_dashboard: MagicMock) -> None:
        with patch(f"{_PATCH_BASE}.get_cache_performance_dashboard", return_value=mock_dashboard):
            resp = client.get("/api/cache/dashboard/cache/test_cache")
        data = resp.json()
        expected_fields = {
            "timestamp",
            "cache_name",
            "backend_type",
            "hits",
            "misses",
            "evictions",
            "total_requests",
            "hit_rate",
            "current_size",
            "max_size",
            "memory_usage",
            "avg_get_time",
            "avg_set_time",
            "avg_delete_time",
            "redis_connected",
            "redis_memory_usage",
            "redis_key_count",
            "health_status",
            "last_health_check",
        }
        assert expected_fields.issubset(data.keys())
