"""Tests for observability modules."""

from datetime import datetime, timedelta
from unittest.mock import patch

from tool_router.observability.health import HealthChecker, HealthStatus
from tool_router.observability.logger import StructuredLogger
from tool_router.observability.metrics import MetricsCollector, PerformanceMetric


class TestHealthStatus:
    """Test cases for HealthStatus enum."""

    def test_health_status_values(self) -> None:
        """Test that all expected health status values are present."""
        expected_statuses = {"healthy", "degraded", "unhealthy"}
        actual_statuses = {status.value for status in HealthStatus}
        assert actual_statuses == expected_statuses


class TestHealthChecker:
    """Test cases for HealthChecker."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            "gateway_url": "http://test:4444",
            "gateway_jwt": "test-token",
            "timeout_ms": 5000
        }
        self.health_checker = HealthChecker(self.config)

    def test_initialization(self) -> None:
        """Test HealthChecker initialization."""
        assert self.health_checker.config == self.config
        assert self.health_checker.gateway_client is not None

    def test_check_health_healthy(self) -> None:
        """Test health check when all components are healthy."""
        with patch.object(self.health_checker.gateway_client, "test_connection") as mock_connection:
            mock_connection.return_value = True

            result = self.health_checker.check_health()

            assert result.status == HealthStatus.HEALTHY
            assert result.gateway_reachable is True
            assert result.response_time_ms < 5000
            assert "checks" in result
            assert all(check["status"] == "pass" for check in result["checks"])

    def test_check_health_gateway_unreachable(self) -> None:
        """Test health check when gateway is unreachable."""
        with patch.object(self.health_checker.gateway_client, "test_connection") as mock_connection:
            mock_connection.return_value = False

            result = self.health_checker.check_health()

            assert result.status == HealthStatus.UNHEALTHY
            assert result.gateway_reachable is False
            assert "error" in result
            assert result.response_time_ms is None

    def test_check_health_slow_response(self) -> None:
        """Test health check with slow response time."""
        with patch.object(self.health_checker, "_measure_response_time") as mock_measure, \
             patch.object(self.health_checker.gateway_client, "test_connection") as mock_connection:

            # Mock slow response
            mock_connection.return_value = True
            mock_measure.return_value = 6000  # 6 seconds

            result = self.health_checker.check_health()

            assert result.status == HealthStatus.DEGRADED
            assert result.gateway_reachable is True
            assert result.response_time_ms == 6000
            assert "performance_issues" in result

    def test_check_database_connection(self) -> None:
        """Test database connection check."""
        with patch.object(self.health_checker, "_check_database_connection") as mock_db:
            mock_db.return_value = True

            result = self.health_checker.check_health()

            assert result.database_connected is True
            assert "database_check" in result["checks"]
            assert result["checks"]["database_check"]["status"] == "pass"

    def test_check_database_connection_failed(self) -> None:
        """Test database connection check failure."""
        with patch.object(self.health_checker, "_check_database_connection") as mock_db:
            mock_db.return_value = False

            result = self.health_checker.check_health()

            assert result.database_connected is False
            assert "database_check" in result["checks"]
            assert result["checks"]["database_check"]["status"] == "fail"

    def test_get_health_summary(self) -> None:
        """Test health summary generation."""
        with patch.object(self.health_checker, "check_health") as mock_check:
            mock_check.return_value = {
                "status": "healthy",
                "gateway_reachable": True,
                "database_connected": True,
                "response_time_ms": 150,
                "checks": [
                    {"name": "gateway", "status": "pass", "response_time_ms": 150},
                    {"name": "database", "status": "pass", "response_time_ms": 100}
                ]
            }

            summary = self.health_checker.get_health_summary()

            assert "overall_status" in summary
            assert "component_status" in summary
            assert "performance_metrics" in summary
            assert summary["overall_status"] == "healthy"
            assert len(summary["component_status"]) == 2

    def test_health_check_with_timeout(self) -> None:
        """Test health check with custom timeout."""
        with patch.object(self.health_checker.gateway_client, "test_connection") as mock_connection:
            mock_connection.return_value = True

            # Set custom timeout
            self.health_checker.timeout_ms = 1000
            result = self.health_checker.check_health()

            assert result.status == HealthStatus.HEALTHY
            assert result.response_time_ms <= 1000


class TestStructuredLogger:
    """Test cases for StructuredLogger."""

    def setup_method(self):
        """Set up test fixtures."""
        self.logger = StructuredLogger("test_logger")

    def test_initialization(self) -> None:
        """Test StructuredLogger initialization."""
        assert self.logger.name == "test_logger"
        assert self.logger.logger is not None

    def test_log_info_message(self) -> None:
        """Test logging info message."""
        with patch.object(self.logger.logger, "info") as mock_log:
            self.logger.info("Test message", {"key": "value"})

            # Verify logger was called
            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            assert args[0] == "Test message"
            assert kwargs == {"extra": {"key": "value"}}

    def test_log_warning_message(self) -> None:
        """Test logging warning message."""
        with patch.object(self.logger.logger, "warning") as mock_log:
            self.logger.warning("Warning message", {"severity": "medium"})

            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            assert args[0] == "Warning message"
            assert kwargs == {"extra": {"severity": "medium"}}

    def test_log_error_message(self) -> None:
        """Test logging error message."""
        with patch.object(self.logger.logger, "error") as mock_log:
            self.logger.error("Error message", {"error_code": 500})

            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            assert args[0] == "Error message"
            assert kwargs == {"extra": {"error_code": 500}}

    def test_log_with_context(self) -> None:
        """Test logging with rich context."""
        context = {
            "request_id": "req-123",
            "user_id": "user-456",
            "endpoint": "/api/test"
        }

        with patch.object(self.logger.logger, "info") as mock_log:
            self.logger.info("Request processed", context)

            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            assert args[0] == "Request processed"
            assert kwargs["extra"]["request_id"] == "req-123"

    def test_log_performance_timing(self) -> None:
        """Test logging with performance timing."""
        with patch.object(self.logger, "_measure_execution_time") as mock_measure, \
             patch.object(self.logger.logger, "info") as mock_log:

            mock_measure.return_value = 150.5
            self.logger.info("Operation completed", {"operation": "test"})

            mock_measure.assert_called_once()
            mock_log.assert_called_once()
            args, kwargs = mock_log.call_args
            assert kwargs["extra"]["execution_time_ms"] == 150.5

    def test_structured_log_formatting(self) -> None:
        """Test structured log formatting."""
        with patch.object(self.logger.logger, "info") as mock_log:
            self.logger.info("Test message", {"structured": True})

            # The mock should capture the formatted log
            mock_log.assert_called_once()

    def test_log_level_filtering(self) -> None:
        """Test log level filtering."""
        # Set logger to WARNING level
        self.logger.logger.setLevel(logging.WARNING)

        with patch.object(self.logger.logger, "info") as mock_log:
            self.logger.info("Info message")  # Should not be logged
            self.logger.warning("Warning message")  # Should be logged

            mock_log.assert_called_once()
            assert "Warning message" in mock_log.call_args[0]

    def test_get_logger_statistics(self) -> None:
        """Test getting logger statistics."""
        with patch.object(self.logger, "_get_statistics") as mock_stats:
            mock_stats.return_value = {
                "total_logs": 1000,
                "error_count": 50,
                "warning_count": 100,
                "info_count": 850,
                "average_execution_time": 45.2
            }

            stats = self.logger.get_statistics()

            assert stats["total_logs"] == 1000
            assert stats["error_count"] == 50
            assert stats["warning_count"] == 100
            assert stats["info_count"] == 850


class TestMetricsCollector:
    """Test cases for MetricsCollector."""

    def setup_method(self):
        """Set up test fixtures."""
        self.metrics = MetricsCollector()

    def test_initialization(self) -> None:
        """Test MetricsCollector initialization."""
        assert self.metrics.metrics == {}
        assert self.metrics.lock is not None

    def test_record_metric(self) -> None:
        """Test recording a single metric."""
        metric = PerformanceMetric(
            name="test_operation",
            value=1.5,
            unit="seconds",
            timestamp=datetime.now(),
            metadata={"operation_type": "test"}
        )

        self.metrics.record_metric(metric)

        assert "test_operation" in self.metrics.metrics
        assert len(self.metrics.metrics["test_operation"]) == 1
        assert self.metrics.metrics["test_operation"][0] == metric

    def test_record_multiple_metrics(self) -> None:
        """Test recording multiple metrics."""
        metrics = [
            PerformanceMetric("op1", 1.0, "ms", datetime.now()),
            PerformanceMetric("op2", 2.0, "ms", datetime.now()),
            PerformanceMetric("op1", 1.5, "ms", datetime.now())
        ]

        for metric in metrics:
            self.metrics.record_metric(metric)

        assert len(self.metrics.metrics["op1"]) == 2
        assert len(self.metrics.metrics["op2"]) == 1
        assert len(self.metrics.metrics["op1"]) == 2

    def test_get_metric_statistics(self) -> None:
        """Test getting metric statistics."""
        # Add test metrics
        self.metrics.record_metric(PerformanceMetric("test", 1.0, "ms", datetime.now()))
        self.metrics.record_metric(PerformanceMetric("test", 2.0, "ms", datetime.now()))
        self.metrics.record_metric(PerformanceMetric("test", 3.0, "ms", datetime.now()))

        stats = self.metrics.get_metric_statistics("test")

        assert stats["count"] == 3
        assert stats["mean"] == 2.0
        assert stats["min"] == 1.0
        assert stats["max"] == 3.0
        assert "percentiles" in stats
        assert stats["percentiles"]["p50"] == 2.0

    def test_get_metric_statistics_empty(self) -> None:
        """Test getting statistics for non-existent metric."""
        stats = self.metrics.get_metric_statistics("nonexistent")

        assert stats["count"] == 0
        assert stats["mean"] == 0.0
        assert stats["min"] == 0.0
        assert stats["max"] == 0.0

    def test_get_all_statistics(self) -> None:
        """Test getting all metrics statistics."""
        # Add test metrics
        self.metrics.record_metric(PerformanceMetric("op1", 1.0, "ms", datetime.now()))
        self.metrics.record_metric(PerformanceMetric("op2", 2.0, "ms", datetime.now()))

        stats = self.metrics.get_all_statistics()

        assert "op1" in stats
        assert "op2" in stats
        assert stats["op1"]["count"] == 1
        assert stats["op2"]["count"] == 1
        assert "total_metrics" in stats
        assert stats["total_metrics"] == 2

    def test_clear_metrics(self) -> None:
        """Test clearing all metrics."""
        # Add some metrics first
        self.metrics.record_metric(PerformanceMetric("test", 1.0, "ms", datetime.now()))

        assert len(self.metrics.metrics) == 1

        self.metrics.clear_metrics()

        assert len(self.metrics.metrics) == 0

    def test_concurrent_metric_recording(self) -> None:
        """Test thread-safe metric recording."""
        import threading

        def record_metrics(metrics_collector, start_id, end_id):
            for i in range(start_id, end_id):
                metric = PerformanceMetric(
                    name=f"op_{i}",
                    value=float(i),
                    unit="ms",
                    timestamp=datetime.now()
                )
                metrics_collector.record_metric(metric)

        # Create multiple threads to record metrics concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(
                target=record_metrics,
                args=(self.metrics, i * 10, (i + 1) * 10)
            )
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all metrics were recorded
        assert len(self.metrics.metrics) == 50  # 5 threads * 10 metrics each

    def test_metric_with_metadata(self) -> None:
        """Test recording metric with rich metadata."""
        metadata = {
            "operation_type": "database_query",
            "table": "users",
            "query_complexity": "high",
            "cache_hit": False
        }

        metric = PerformanceMetric(
            name="db_query",
            value=150.0,
            unit="ms",
            timestamp=datetime.now(),
            metadata=metadata
        )

        self.metrics.record_metric(metric)

        recorded = self.metrics.metrics["db_query"][0]
        assert recorded.metadata == metadata

    def test_metric_time_series_analysis(self) -> None:
        """Test time series analysis of metrics."""
        # Record metrics over time
        base_time = datetime.now()
        for i in range(10):
            timestamp = base_time + timedelta(seconds=i * 10)
            metric = PerformanceMetric(
                name="time_series_test",
                value=float(i),
                unit="count",
                timestamp=timestamp
            )
            self.metrics.record_metric(metric)

        analysis = self.metrics.analyze_time_series("time_series_test",
                                                      start_time=base_time,
                                                      end_time=base_time + timedelta(seconds=90))

        assert "trend" in analysis
        assert "slope" in analysis
        assert "data_points" in analysis
        assert len(analysis["data_points"]) == 10

    def test_export_metrics(self) -> None:
        """Test exporting metrics to different formats."""
        # Add test metrics
        self.metrics.record_metric(PerformanceMetric("export_test", 1.0, "ms", datetime.now()))

        # Test JSON export
        json_data = self.metrics.export_metrics("json")
        assert "export_test" in json_data
        assert json_data["export_test"][0]["value"] == 1.0

        # Test CSV export
        csv_data = self.metrics.export_metrics("csv")
        assert "name,value,unit,timestamp,metadata" in csv_data
        assert "export_test,1.0,ms" in csv_data
