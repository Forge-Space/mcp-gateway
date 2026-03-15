"""Unit tests for observability module."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

from tool_router.observability import (
    HealthCheck,
    HealthStatus,
    MetricsCollector,
    get_logger,
    get_metrics,
    setup_logging,
)
from tool_router.observability.logger import LogContext
from tool_router.observability.metrics import MetricStats, TimingContext


class TestHealthCheck:
    """Tests for health check functionality."""

    @patch("tool_router.observability.health.HTTPGatewayClient")
    def test_check_gateway_connection_healthy(self, mock_client_class):
        """Test successful gateway connection check."""
        mock_client = MagicMock()
        mock_client.get_tools.return_value = [{"name": "test_tool"}]
        mock_client_class.return_value = mock_client

        health = HealthCheck()
        result = health.check_gateway_connection()

        assert result.status == HealthStatus.HEALTHY
        assert result.name == "gateway"
        assert result.latency_ms is not None
        assert result.metadata["tool_count"] == 1

    @patch("tool_router.observability.health.HTTPGatewayClient")
    def test_check_gateway_connection_degraded(self, mock_client_class):
        """Test gateway connection with no tools."""
        mock_client = MagicMock()
        mock_client.get_tools.return_value = []
        mock_client_class.return_value = mock_client

        health = HealthCheck()
        result = health.check_gateway_connection()

        assert result.status == HealthStatus.DEGRADED
        assert result.metadata["tool_count"] == 0

    @patch("tool_router.observability.health.HTTPGatewayClient")
    def test_check_gateway_connection_unhealthy(self, mock_client_class):
        """Test gateway connection failure."""
        mock_client = MagicMock()
        mock_client.get_tools.side_effect = ValueError("Connection failed")
        mock_client_class.return_value = mock_client

        health = HealthCheck()
        result = health.check_gateway_connection()

        assert result.status == HealthStatus.UNHEALTHY
        assert "Connection failed" in result.message

    def test_check_configuration_valid(self):
        """Test valid configuration check."""
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(
            url="http://localhost:4444",
            jwt="test-jwt-token",
            timeout_ms=120000,
            max_retries=3,
            retry_delay_ms=2000,
        )

        health = HealthCheck(config)
        result = health.check_configuration()

        assert result.name == "configuration"
        assert result.status == HealthStatus.HEALTHY

    def test_check_configuration_missing_jwt(self):
        """Test configuration check with missing JWT."""
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(
            url="http://localhost:4444",
            jwt="",
            timeout_ms=120000,
            max_retries=3,
            retry_delay_ms=2000,
        )

        health = HealthCheck(config)
        result = health.check_configuration()

        assert result.status == HealthStatus.UNHEALTHY
        assert "JWT token not configured" in result.message

    @patch("tool_router.observability.health.HTTPGatewayClient")
    def test_check_all_aggregates_status(self, mock_client_class):
        """Test check_all aggregates component statuses correctly."""
        mock_client = MagicMock()
        mock_client.get_tools.return_value = [{"name": "test"}]
        mock_client_class.return_value = mock_client

        health = HealthCheck()
        result = health.check_all()

        assert result.status in [
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED,
            HealthStatus.UNHEALTHY,
        ]
        assert len(result.components) == 2
        assert result.timestamp > 0

    def test_check_readiness(self):
        """Test readiness check returns boolean."""
        health = HealthCheck()
        result = health.check_readiness()
        assert isinstance(result, bool)

    def test_check_liveness(self):
        """Test liveness check returns boolean."""
        health = HealthCheck()
        result = health.check_liveness()
        assert isinstance(result, bool)

    def test_health_check_result_to_dict(self):
        """Test health check result serialization."""
        from tool_router.observability.health import ComponentHealth, HealthCheckResult

        components = [
            ComponentHealth(
                name="test",
                status=HealthStatus.HEALTHY,
                message="OK",
                latency_ms=10.5,
            )
        ]
        result = HealthCheckResult(status=HealthStatus.HEALTHY, components=components, timestamp=time.time())

        data = result.to_dict()
        assert data["status"] == "healthy"
        assert len(data["components"]) == 1
        assert data["components"][0]["name"] == "test"


class TestMetricsCollector:
    """Tests for metrics collection."""

    def test_record_timing(self):
        """Test recording timing metrics."""
        metrics = MetricsCollector()
        metrics.record_timing("test_operation", 100.5)

        stats = metrics.get_stats("test_operation")
        assert stats is not None
        assert stats.count == 1
        assert stats.avg == 100.5

    def test_increment_counter(self):
        """Test incrementing counters."""
        metrics = MetricsCollector()
        metrics.increment_counter("test_counter")
        metrics.increment_counter("test_counter", 5)

        count = metrics.get_counter("test_counter")
        assert count == 6

    def test_get_stats_nonexistent(self):
        """Test getting stats for nonexistent metric."""
        metrics = MetricsCollector()
        stats = metrics.get_stats("nonexistent")
        assert stats is None

    def test_get_counter_nonexistent(self):
        """Test getting nonexistent counter."""
        metrics = MetricsCollector()
        count = metrics.get_counter("nonexistent")
        assert count == 0

    def test_max_samples_limit(self):
        """Test that metrics are limited to max_samples."""
        metrics = MetricsCollector(max_samples=5)

        for i in range(10):
            metrics.record_timing("test", float(i))

        stats = metrics.get_stats("test")
        assert stats.count == 5

    def test_get_all_metrics(self):
        """Test getting all metrics."""
        metrics = MetricsCollector()
        metrics.record_timing("op1", 10.0)
        metrics.record_timing("op1", 20.0)
        metrics.increment_counter("count1", 5)

        all_metrics = metrics.get_all_metrics()
        assert "timings" in all_metrics
        assert "counters" in all_metrics
        assert "op1" in all_metrics["timings"]
        assert all_metrics["counters"]["count1"] == 5

    def test_reset(self):
        """Test resetting all metrics."""
        metrics = MetricsCollector()
        metrics.record_timing("test", 10.0)
        metrics.increment_counter("test_count")

        metrics.reset()

        assert metrics.get_stats("test") is None
        assert metrics.get_counter("test_count") == 0

    def test_timing_context(self):
        """Test timing context manager."""
        metrics = MetricsCollector()

        with TimingContext("test_op", metrics):
            time.sleep(0.01)

        stats = metrics.get_stats("test_op")
        assert stats is not None
        assert stats.count == 1
        assert stats.avg >= 10.0

    def test_metric_stats_from_values(self):
        """Test MetricStats calculation."""
        values = [10.0, 20.0, 30.0]
        stats = MetricStats.from_values(values)

        assert stats.count == 3
        assert stats.sum == 60.0
        assert stats.min == 10.0
        assert stats.max == 30.0
        assert stats.avg == 20.0

    def test_metric_stats_empty_values(self):
        """Test MetricStats with empty values."""
        stats = MetricStats.from_values([])

        assert stats.count == 0
        assert stats.sum == 0.0


class TestLogging:
    """Tests for logging configuration."""

    def test_setup_logging(self):
        """Test logging setup."""
        setup_logging(level="DEBUG", structured=False)
        logger = get_logger("test")
        assert logger.level <= 10

    def test_get_logger(self):
        """Test getting logger instance."""
        logger = get_logger("test_module")
        assert logger.name == "test_module"

    def test_log_context(self):
        """Test log context manager."""
        logger = get_logger("test")

        with LogContext(logger, request_id="123", user="test"):
            pass

    def test_structured_formatter(self):
        """Test structured log formatting."""
        from tool_router.observability.logger import StructuredFormatter

        formatter = StructuredFormatter()
        import logging

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)
        assert "level=INFO" in formatted
        assert "message=Test message" in formatted


class TestGlobalMetrics:
    """Tests for global metrics instance."""

    def test_get_metrics_singleton(self):
        """Test that get_metrics returns singleton instance."""
        metrics1 = get_metrics()
        metrics2 = get_metrics()
        assert metrics1 is metrics2

    def test_get_metrics_thread_safe(self):
        """Test that get_metrics is thread-safe."""
        import threading

        results = []

        def get_instance():
            results.append(get_metrics())

        threads = [threading.Thread(target=get_instance) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert all(m is results[0] for m in results)


# ---------------------------------------------------------------------------
# Tests migrated from test_observability.py (root) — unique coverage
# ---------------------------------------------------------------------------


class TestStructuredFormatterExtra:
    """Extra StructuredFormatter tests not covered in TestLogging."""

    def test_format_record_basic(self) -> None:
        from tool_router.observability.logger import StructuredFormatter

        fmt = StructuredFormatter()
        record = __import__("logging").LogRecord(
            name="test",
            level=__import__("logging").INFO,
            pathname="",
            lineno=0,
            msg="hello",
            args=(),
            exc_info=None,
        )
        output = fmt.format(record)
        assert "hello" in output

    def test_format_includes_level_and_message(self) -> None:
        from tool_router.observability.logger import StructuredFormatter

        fmt = StructuredFormatter()
        record = __import__("logging").LogRecord(
            name="test.module",
            level=__import__("logging").WARNING,
            pathname="test.py",
            lineno=42,
            msg="warn msg",
            args=(),
            exc_info=None,
        )
        output = fmt.format(record)
        assert "warn msg" in output


class TestGetLoggerExtra:
    """Additional get_logger tests."""

    def test_returns_logger_instance(self) -> None:
        lg = get_logger("mylogger_x")
        assert hasattr(lg, "info") and hasattr(lg, "error")

    def test_same_name_returns_same_logger(self) -> None:
        lg1 = get_logger("shared_x")
        lg2 = get_logger("shared_x")
        assert lg1 is lg2


class TestSetupLoggingExtra:
    """Additional setup_logging tests."""

    def test_setup_default_no_error(self) -> None:
        setup_logging()

    def test_setup_with_debug_level(self) -> None:
        setup_logging(level="DEBUG")

    def test_setup_without_structured(self) -> None:
        setup_logging(structured=False)


class TestLogContextExtra:
    """Additional LogContext tests."""

    def test_log_context_returns_adapter(self) -> None:
        import logging as _logging

        from tool_router.observability.logger import ContextLoggerAdapter

        lg = _logging.getLogger("ctx_test_x")
        with LogContext(lg, request_id="abc") as adapter:
            assert isinstance(adapter, ContextLoggerAdapter)

    def test_log_context_extra_fields(self) -> None:
        import logging as _logging

        lg = _logging.getLogger("ctx_test2_x")
        with LogContext(lg, user="bob", action="login") as adapter:
            assert adapter.extra["user"] == "bob"
            assert adapter.extra["action"] == "login"


class TestMetricValueAndStats:
    """Tests for MetricValue and MetricStats dataclasses."""

    def test_create_metric_value(self) -> None:
        from tool_router.observability.metrics import MetricValue

        mv = MetricValue(value=42.5, timestamp=1000.0)
        assert mv.value == 42.5
        assert mv.timestamp == 1000.0

    def test_create_metric_stats(self) -> None:
        ms = MetricStats(count=10, sum=100.0, min=5.0, max=20.0, avg=10.0)
        assert ms.count == 10
        assert ms.avg == 10.0


class TestTimingContextExtra:
    """Additional TimingContext tests."""

    def test_timing_records_metric(self) -> None:
        import time as _time

        from tool_router.observability.metrics import TimingContext

        mc = MetricsCollector()
        with TimingContext("my_op_x", mc):
            _time.sleep(0.01)
        stats = mc.get_stats("my_op_x")
        assert stats is not None
        assert stats.count == 1
        assert stats.min > 0

    def test_timing_context_returns_self(self) -> None:
        from tool_router.observability.metrics import TimingContext

        mc = MetricsCollector()
        with TimingContext("op_x", mc) as ctx:
            assert ctx is not None


# ---------------------------------------------------------------------------
# Tests migrated from test_observability/test_health.py — unique test
# ---------------------------------------------------------------------------


class TestHealthCheckLivenessExtra:
    """Extra liveness check tests."""

    def test_check_liveness_no_jwt(self) -> None:
        from tool_router.core.config import GatewayConfig

        config = GatewayConfig(url="http://localhost:4444", jwt="")
        hc = HealthCheck(config=config)
        assert hc.check_liveness() is False
