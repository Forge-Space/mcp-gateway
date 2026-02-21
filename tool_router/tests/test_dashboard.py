"""Test cache performance dashboard."""

from __future__ import annotations

import time
from unittest.mock import Mock, patch

from tool_router.cache.dashboard import (
    CacheAlert,
    CacheAlertManager,
    CachePerformanceCollector,
    CachePerformanceDashboard,
    CachePerformanceMetrics,
    CachePerformanceSnapshot,
    get_cache_performance_dashboard,
    start_dashboard_collection,
    stop_dashboard_collection,
)


class TestCachePerformanceMetrics:
    """Test cache performance metrics."""

    def test_metrics_creation(self):
        """Test metrics creation."""
        metrics = CachePerformanceMetrics(
            timestamp=time.time(),
            cache_name="test_cache",
            backend_type="memory",
            hits=100,
            misses=20,
            total_requests=120,
        )

        assert metrics.cache_name == "test_cache"
        assert metrics.backend_type == "memory"
        assert metrics.hits == 100
        assert metrics.misses == 20
        assert metrics.total_requests == 120
        # hit_rate is calculated by collector, default is 0.0
        assert metrics.hit_rate == 0.0


class TestCacheAlert:
    """Test cache alert."""

    def test_alert_creation(self):
        """Test alert creation."""
        alert = CacheAlert(
            alert_id="test_alert",
            alert_type="high_miss_rate",
            severity="warning",
            message="High miss rate detected",
            cache_name="test_cache",
            timestamp=time.time(),
        )

        assert alert.alert_id == "test_alert"
        assert alert.alert_type == "high_miss_rate"
        assert alert.severity == "warning"
        assert alert.cache_name == "test_cache"
        assert not alert.resolved
        assert alert.resolved_at is None

    def test_alert_resolution(self):
        """Test alert resolution."""
        alert = CacheAlert(
            alert_id="test_alert",
            alert_type="high_miss_rate",
            severity="warning",
            message="High miss rate detected",
            cache_name="test_cache",
            timestamp=time.time(),
        )

        # Resolve alert
        alert.resolved = True
        alert.resolved_at = time.time()

        assert alert.resolved
        assert alert.resolved_at is not None


class TestCachePerformanceCollector:
    """Test cache performance collector."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_cache_manager = Mock()
        self.mock_cache = Mock()
        self.mock_cache_manager.get_cache.return_value = self.mock_cache
        self.mock_cache_manager._metrics = {}
        self.collector = CachePerformanceCollector(self.mock_cache_manager)

    def test_collect_metrics_memory_cache(self):
        """Test collecting metrics from memory cache."""
        # Setup mock cache
        self.mock_cache.__len__.return_value = 50
        self.mock_cache.maxsize = 100

        # Setup metrics
        from tool_router.cache.types import CacheMetrics

        metrics = CacheMetrics()
        metrics.hits = 80
        metrics.misses = 20
        metrics.total_requests = 100
        metrics.evictions = 5
        self.mock_cache_manager._metrics["test_cache"] = metrics

        # Collect metrics
        result = self.collector.collect_metrics("test_cache")

        assert result.cache_name == "test_cache"
        assert result.backend_type == "memory"
        assert result.hits == 80
        assert result.misses == 20
        assert result.hit_rate == 80.0
        assert result.current_size == 50
        assert result.max_size == 100
        assert result.redis_connected is False

    def test_collect_metrics_redis_cache(self):
        """Test collecting metrics from Redis cache."""
        # Setup mock Redis cache
        from tool_router.cache.redis_cache import RedisCache

        mock_redis_cache = Mock(spec=RedisCache)
        mock_redis_cache._redis_client = Mock()
        mock_redis_cache._is_healthy = True
        mock_redis_cache.get_info.return_value = {"memory_usage": 1024000, "key_count": 25}
        self.mock_cache_manager.get_cache.return_value = mock_redis_cache

        # Setup metrics
        from tool_router.cache.types import CacheMetrics

        metrics = CacheMetrics()
        metrics.hits = 90
        metrics.misses = 10
        metrics.total_requests = 100
        self.mock_cache_manager._metrics["redis_cache"] = metrics

        # Collect metrics
        result = self.collector.collect_metrics("redis_cache")

        assert result.cache_name == "redis_cache"
        assert result.backend_type == "hybrid"
        assert result.redis_connected is True
        assert result.redis_memory_usage == 1024000
        assert result.redis_key_count == 25

    def test_timing_recording(self):
        """Test recording operation timings."""
        # Record some timings
        self.collector.record_get_time(5.2)
        self.collector.record_set_time(3.1)
        self.collector.record_delete_time(1.8)

        # Verify timings were recorded
        assert len(self.collector._get_times) == 1
        assert len(self.collector._set_times) == 1
        assert len(self.collector._delete_times) == 1
        assert self.collector._get_times[0] == 5.2
        assert self.collector._set_times[0] == 3.1
        assert self.collector._delete_times[0] == 1.8


class TestCacheAlertManager:
    """Test cache alert manager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.alert_manager = CacheAlertManager()

    def test_high_miss_rate_alert(self):
        """Test high miss rate alert detection."""
        # Create metrics with high miss rate
        metrics = CachePerformanceMetrics(
            timestamp=time.time(),
            cache_name="test_cache",
            backend_type="memory",
            hits=20,
            misses=80,
            total_requests=100,
        )

        # Check for alerts
        alerts = self.alert_manager.check_alerts(metrics)

        assert len(alerts) == 1
        assert alerts[0].alert_type == "high_miss_rate"
        assert alerts[0].severity == "warning"
        assert "High miss rate: 80.0%" in alerts[0].message

    def test_low_hit_rate_alert(self):
        """Test low hit rate alert detection."""
        # Create metrics with low hit rate
        metrics = CachePerformanceMetrics(
            timestamp=time.time(),
            cache_name="test_cache",
            backend_type="memory",
            hits=30,
            misses=70,
            total_requests=100,
        )

        # Check for alerts
        alerts = self.alert_manager.check_alerts(metrics)

        assert len(alerts) == 1
        assert alerts[0].alert_type == "low_hit_rate"
        assert alerts[0].severity == "warning"
        assert "Low hit rate: 30.0%" in alerts[0].message

    def test_redis_connection_alert(self):
        """Test Redis connection alert."""
        # Create metrics with Redis disconnected
        metrics = CachePerformanceMetrics(
            timestamp=time.time(),
            cache_name="redis_cache",
            backend_type="redis",
            hits=50,
            misses=50,
            total_requests=100,
            redis_connected=False,
        )

        # Check for alerts
        alerts = self.alert_manager.check_alerts(metrics)

        assert len(alerts) == 1
        assert alerts[0].alert_type == "connection_error"
        assert alerts[0].severity == "error"
        assert "Redis connection lost" in alerts[0].message

    def test_alert_resolution(self):
        """Test alert resolution."""
        # Create metrics with high miss rate
        metrics_high = CachePerformanceMetrics(
            timestamp=time.time(),
            cache_name="test_cache",
            backend_type="memory",
            hits=20,
            misses=80,
            total_requests=100,
        )

        # Check for alerts (should trigger)
        alerts = self.alert_manager.check_alerts(metrics_high)
        assert len(alerts) == 1

        # Create metrics with normal miss rate
        metrics_normal = CachePerformanceMetrics(
            timestamp=time.time() + 1,
            cache_name="test_cache",
            backend_type="memory",
            hits=80,
            misses=20,
            total_requests=100,
        )

        # Check for alerts (should resolve)
        alerts = self.alert_manager.check_alerts(metrics_normal)
        assert len(alerts) == 0

        # Verify alert is resolved
        alert = self.alert_manager._alerts["high_miss_rate_test_cache"]
        assert alert.resolved
        assert alert.resolved_at is not None

    def test_active_alerts(self):
        """Test getting active alerts."""
        # Create metrics with alert
        metrics = CachePerformanceMetrics(
            timestamp=time.time(),
            cache_name="test_cache",
            backend_type="memory",
            hits=20,
            misses=80,
            total_requests=100,
        )

        # Check for alerts
        self.alert_manager.check_alerts(metrics)

        # Get active alerts
        active_alerts = self.alert_manager.get_active_alerts()
        assert len(active_alerts) == 1
        assert active_alerts[0].alert_type == "high_miss_rate"


class TestCachePerformanceDashboard:
    """Test cache performance dashboard."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_cache_manager = Mock()
        self.mock_cache_manager._caches = {"test_cache": Mock()}
        self.dashboard = CachePerformanceDashboard(self.mock_cache_manager)

    def test_collect_snapshot(self):
        """Test collecting a snapshot."""
        # Mock the collector
        self.dashboard.collector.collect_metrics = Mock(
            return_value=CachePerformanceMetrics(
                timestamp=time.time(),
                cache_name="test_cache",
                backend_type="memory",
                hits=50,
                misses=50,
                total_requests=100,
            )
        )

        # Collect snapshot
        snapshot = self.dashboard.collect_snapshot()

        assert isinstance(snapshot, CachePerformanceSnapshot)
        assert "test_cache" in snapshot.metrics
        assert snapshot.summary is not None

    def test_get_current_snapshot(self):
        """Test getting current snapshot."""
        # Mock collection
        snapshot = CachePerformanceSnapshot(timestamp=time.time(), metrics={}, alerts=[], summary={})
        self.dashboard._snapshots.append(snapshot)

        # Get current snapshot
        current = self.dashboard.get_current_snapshot()

        assert current is snapshot

    def test_get_current_snapshot_empty(self):
        """Test getting current snapshot when empty."""
        current = self.dashboard.get_current_snapshot()
        assert current is None

    def test_start_stop_collection(self):
        """Test starting and stopping collection."""
        # Start collection
        thread = self.dashboard.start_collection(interval=1)
        assert thread is not None
        assert self.dashboard._running is True

        # Stop collection
        self.dashboard.stop_collection()
        assert self.dashboard._running is False

    def test_export_metrics_json(self):
        """Test exporting metrics as JSON."""
        # Mock snapshot
        snapshot = CachePerformanceSnapshot(timestamp=time.time(), metrics={}, alerts=[], summary={"test": "data"})
        self.dashboard._snapshots.append(snapshot)

        # Export as JSON
        json_data = self.dashboard.export_metrics("json")
        assert "test" in json_data
        assert "data" in json_data

    def test_export_metrics_csv(self):
        """Test exporting metrics as CSV."""
        # Mock snapshot with metrics
        metrics = CachePerformanceMetrics(
            timestamp=time.time(),
            cache_name="test_cache",
            backend_type="memory",
            hits=50,
            misses=50,
            total_requests=100,
        )
        snapshot = CachePerformanceSnapshot(
            timestamp=time.time(), metrics={"test_cache": metrics}, alerts=[], summary={}
        )
        self.dashboard._snapshots.append(snapshot)

        # Export as CSV
        csv_data = self.dashboard.export_metrics("csv")
        assert "timestamp" in csv_data
        assert "test_cache" in csv_data


class TestGlobalFunctions:
    """Test global dashboard functions."""

    @patch("tool_router.cache.dashboard._cache_performance_dashboard")
    def test_get_cache_performance_dashboard(self, mock_global):
        """Test getting global dashboard."""
        mock_dashboard = Mock()
        mock_global.return_value = mock_dashboard

        result = get_cache_performance_dashboard()
        assert result is mock_dashboard

    @patch("tool_router.cache.dashboard.get_cache_performance_dashboard")
    def test_start_dashboard_collection(self, mock_get_dashboard):
        """Test starting dashboard collection."""
        mock_dashboard = Mock()
        mock_get_dashboard.return_value = mock_dashboard

        start_dashboard_collection(interval=30)
        mock_dashboard.start_collection.assert_called_once_with(30)

    @patch("tool_router.cache.dashboard.get_cache_performance_dashboard")
    def test_stop_dashboard_collection(self, mock_get_dashboard):
        """Test stopping dashboard collection."""
        mock_dashboard = Mock()
        mock_get_dashboard.return_value = mock_dashboard

        stop_dashboard_collection()
        mock_dashboard.stop_collection.assert_called_once()


if __name__ == "__main__":
    # Simple manual test
    print("Testing cache performance dashboard...")

    from tool_router.cache.cache_manager import CacheManager

    cache_manager = CacheManager()
    dashboard = CachePerformanceDashboard(cache_manager)

    # Test collection
    print("Testing metrics collection...")
    snapshot = dashboard.collect_snapshot()
    print(f"Collected snapshot with {len(snapshot.metrics)} caches")

    # Test alert management
    print("Testing alert management...")
    alert_manager = CacheAlertManager()

    # Create metrics that should trigger alerts
    metrics = CachePerformanceMetrics(
        timestamp=time.time(), cache_name="test_cache", backend_type="memory", hits=10, misses=90, total_requests=100
    )

    alerts = alert_manager.check_alerts(metrics)
    print(f"Generated {len(alerts)} alerts")

    for alert in alerts:
        print(f"  - {alert.alert_type}: {alert.message}")

    print("Dashboard tests completed successfully!")
