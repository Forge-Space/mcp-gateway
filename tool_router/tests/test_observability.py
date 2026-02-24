"""Tests for observability modules."""

from __future__ import annotations

import logging
import time

from tool_router.observability.health import (
    ComponentHealth,
    HealthCheck,
    HealthCheckResult,
    HealthStatus,
)
from tool_router.observability.logger import (
    ContextLoggerAdapter,
    LogContext,
    StructuredFormatter,
    get_logger,
    setup_logging,
)
from tool_router.observability.metrics import (
    MetricsCollector,
    MetricStats,
    MetricValue,
    TimingContext,
)


class TestHealthStatus:
    """Test cases for HealthStatus enum."""

    def test_health_status_values(self) -> None:
        expected = {"healthy", "degraded", "unhealthy"}
        actual = {s.value for s in HealthStatus}
        assert actual == expected

    def test_health_status_access(self) -> None:
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"


class TestComponentHealth:
    """Test cases for ComponentHealth dataclass."""

    def test_create_healthy_component(self) -> None:
        comp = ComponentHealth(
            name="gateway",
            status=HealthStatus.HEALTHY,
            message="OK",
            latency_ms=42.0,
        )
        assert comp.name == "gateway"
        assert comp.status == HealthStatus.HEALTHY
        assert comp.latency_ms == 42.0
        assert comp.metadata is None

    def test_create_with_metadata(self) -> None:
        comp = ComponentHealth(
            name="db",
            status=HealthStatus.UNHEALTHY,
            message="Connection refused",
            latency_ms=0.0,
            metadata={"host": "localhost"},
        )
        assert comp.metadata == {"host": "localhost"}


class TestHealthCheckResult:
    """Test cases for HealthCheckResult dataclass."""

    def test_create_result(self) -> None:
        comp = ComponentHealth(
            name="test",
            status=HealthStatus.HEALTHY,
            message="OK",
        )
        result = HealthCheckResult(
            status=HealthStatus.HEALTHY,
            components=[comp],
            timestamp=time.time(),
        )
        assert result.status == HealthStatus.HEALTHY
        assert len(result.components) == 1
        assert result.timestamp > 0

    def test_to_dict(self) -> None:
        comp = ComponentHealth(
            name="gw",
            status=HealthStatus.HEALTHY,
            message="OK",
            latency_ms=10.0,
        )
        result = HealthCheckResult(
            status=HealthStatus.HEALTHY,
            components=[comp],
            timestamp=time.time(),
        )
        d = result.to_dict()
        assert d["status"] == "healthy"
        assert "components" in d
        assert "timestamp" in d


class TestHealthCheck:
    """Test cases for HealthCheck."""

    def test_initialization_without_config(self) -> None:
        hc = HealthCheck()
        assert hc is not None

    def test_check_liveness_without_config(self) -> None:
        hc = HealthCheck()
        assert hc.check_liveness() is False

    def test_check_configuration_without_config(self) -> None:
        hc = HealthCheck()
        comp = hc.check_configuration()
        assert isinstance(comp, ComponentHealth)
        assert comp.name == "configuration"

    def test_check_all(self) -> None:
        hc = HealthCheck()
        result = hc.check_all()
        assert isinstance(result, HealthCheckResult)
        assert result.status in list(HealthStatus)
        assert len(result.components) > 0


class TestStructuredFormatter:
    """Test cases for StructuredFormatter."""

    def test_format_record(self) -> None:
        fmt = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="hello",
            args=(),
            exc_info=None,
        )
        output = fmt.format(record)
        assert "hello" in output

    def test_format_includes_structured_data(self) -> None:
        fmt = StructuredFormatter()
        record = logging.LogRecord(
            name="test.module",
            level=logging.WARNING,
            pathname="test.py",
            lineno=42,
            msg="warn msg",
            args=(),
            exc_info=None,
        )
        output = fmt.format(record)
        assert "warn msg" in output


class TestGetLogger:
    """Test cases for get_logger function."""

    def test_returns_logger(self) -> None:
        lg = get_logger("mylogger")
        assert isinstance(lg, logging.Logger)
        assert lg.name == "mylogger"

    def test_same_name_returns_same_logger(self) -> None:
        lg1 = get_logger("shared")
        lg2 = get_logger("shared")
        assert lg1 is lg2


class TestSetupLogging:
    """Test cases for setup_logging function."""

    def test_setup_default(self) -> None:
        setup_logging()

    def test_setup_with_level(self) -> None:
        setup_logging(level="DEBUG")

    def test_setup_without_structured(self) -> None:
        setup_logging(structured=False)


class TestLogContext:
    """Test cases for LogContext context manager."""

    def test_log_context_returns_adapter(self) -> None:
        lg = logging.getLogger("ctx_test")
        with LogContext(lg, request_id="abc") as adapter:
            assert isinstance(adapter, ContextLoggerAdapter)

    def test_log_context_extra_fields(self) -> None:
        lg = logging.getLogger("ctx_test2")
        with LogContext(lg, user="bob", action="login") as adapter:
            assert adapter.extra["user"] == "bob"
            assert adapter.extra["action"] == "login"


class TestMetricValue:
    """Test cases for MetricValue dataclass."""

    def test_create_metric_value(self) -> None:
        mv = MetricValue(value=42.5, timestamp=1000.0)
        assert mv.value == 42.5
        assert mv.timestamp == 1000.0


class TestMetricStats:
    """Test cases for MetricStats dataclass."""

    def test_create_metric_stats(self) -> None:
        ms = MetricStats(count=10, sum=100.0, min=5.0, max=20.0, avg=10.0)
        assert ms.count == 10
        assert ms.avg == 10.0


class TestMetricsCollector:
    """Test cases for MetricsCollector."""

    def test_initialization(self) -> None:
        mc = MetricsCollector()
        assert mc is not None

    def test_record_and_get_timing(self) -> None:
        mc = MetricsCollector()
        mc.record_timing("op1", 100.0)
        mc.record_timing("op1", 200.0)
        stats = mc.get_stats("op1")
        assert stats is not None
        assert stats.count == 2
        assert stats.min == 100.0
        assert stats.max == 200.0
        assert stats.avg == 150.0

    def test_get_stats_nonexistent(self) -> None:
        mc = MetricsCollector()
        assert mc.get_stats("nope") is None

    def test_increment_and_get_counter(self) -> None:
        mc = MetricsCollector()
        mc.increment_counter("requests")
        mc.increment_counter("requests")
        mc.increment_counter("requests", 3)
        assert mc.get_counter("requests") == 5

    def test_get_counter_nonexistent(self) -> None:
        mc = MetricsCollector()
        assert mc.get_counter("nope") == 0

    def test_get_all_metrics(self) -> None:
        mc = MetricsCollector()
        mc.record_timing("a", 10.0)
        mc.increment_counter("b")
        result = mc.get_all_metrics()
        assert isinstance(result, dict)

    def test_reset(self) -> None:
        mc = MetricsCollector()
        mc.record_timing("x", 1.0)
        mc.increment_counter("y")
        mc.reset()
        assert mc.get_stats("x") is None
        assert mc.get_counter("y") == 0

    def test_concurrent_recording(self) -> None:
        import threading

        mc = MetricsCollector()

        def record(tid: int) -> None:
            for i in range(20):
                mc.record_timing(f"thread_{tid}", float(i))

        threads = [threading.Thread(target=record, args=(t,)) for t in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        for tid in range(5):
            stats = mc.get_stats(f"thread_{tid}")
            assert stats is not None
            assert stats.count == 20


class TestTimingContext:
    """Test cases for TimingContext."""

    def test_timing_records_metric(self) -> None:
        mc = MetricsCollector()
        with TimingContext("my_op", mc):
            time.sleep(0.01)
        stats = mc.get_stats("my_op")
        assert stats is not None
        assert stats.count == 1
        assert stats.min > 0

    def test_timing_context_returns_self(self) -> None:
        mc = MetricsCollector()
        with TimingContext("op", mc) as ctx:
            assert isinstance(ctx, TimingContext)
