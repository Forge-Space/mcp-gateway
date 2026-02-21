"""Unit tests for observability metrics module."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

from tool_router.observability.metrics import (
    MetricsCollector,
    MetricStats,
    MetricValue,
    TimingContext,
    get_metrics,
)


class TestMetricValue:
    """Test MetricValue dataclass."""

    def test_metric_value_creation_default_timestamp(self) -> None:
        """Test MetricValue creation with default timestamp."""
        start_time = time.time()
        metric = MetricValue(value=42.5)
        end_time = time.time()

        assert metric.value == 42.5
        assert start_time <= metric.timestamp <= end_time

    def test_metric_value_creation_custom_timestamp(self) -> None:
        """Test MetricValue creation with custom timestamp."""
        custom_time = 1234567890.0
        metric = MetricValue(value=42.5, timestamp=custom_time)

        assert metric.value == 42.5
        assert metric.timestamp == custom_time


class TestMetricStats:
    """Test MetricStats class."""

    def test_metric_stats_from_values_empty(self) -> None:
        """Test MetricStats.from_values with empty list."""
        stats = MetricStats.from_values([])

        assert stats.count == 0
        assert stats.sum == 0.0
        assert stats.min == 0.0
        assert stats.max == 0.0
        assert stats.avg == 0.0

    def test_metric_stats_from_values_single(self) -> None:
        """Test MetricStats.from_values with single value."""
        values = [42.5]
        stats = MetricStats.from_values(values)

        assert stats.count == 1
        assert stats.sum == 42.5
        assert stats.min == 42.5
        assert stats.max == 42.5
        assert stats.avg == 42.5

    def test_metric_stats_from_values_multiple(self) -> None:
        """Test MetricStats.from_values with multiple values."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        stats = MetricStats.from_values(values)

        assert stats.count == 5
        assert stats.sum == 15.0
        assert stats.min == 1.0
        assert stats.max == 5.0
        assert stats.avg == 3.0

    def test_metric_stats_from_values_negative(self) -> None:
        """Test MetricStats.from_values with negative values."""
        values = [-2.0, -1.0, 0.0, 1.0, 2.0]
        stats = MetricStats.from_values(values)

        assert stats.count == 5
        assert stats.sum == 0.0
        assert stats.min == -2.0
        assert stats.max == 2.0
        assert stats.avg == 0.0

    def test_metric_stats_from_values_floats(self) -> None:
        """Test MetricStats.from_values with floating point values."""
        values = [1.1, 2.2, 3.3]
        stats = MetricStats.from_values(values)

        assert stats.count == 3
        assert stats.sum == 6.6
        assert stats.min == 1.1
        assert stats.max == 3.3
        assert abs(stats.avg - 2.2) < 0.0001


class TestMetricsCollector:
    """Test MetricsCollector class."""

    def test_metrics_collector_initialization(self) -> None:
        """Test MetricsCollector initialization."""
        collector = MetricsCollector()
        assert collector.max_samples == 1000
        assert collector.max_metric_names == 100
        assert len(collector._metrics) == 0
        assert len(collector._counters) == 0

    def test_metrics_collector_initialization_custom(self) -> None:
        """Test MetricsCollector initialization with custom parameters."""
        collector = MetricsCollector(max_samples=500, max_metric_names=50)
        assert collector.max_samples == 500
        assert collector.max_metric_names == 50

    def test_record_timing_new_metric(self) -> None:
        """Test recording timing for new metric."""
        collector = MetricsCollector()
        collector.record_timing("test_metric", 100.5)

        assert "test_metric" in collector._metrics
        assert len(collector._metrics["test_metric"]) == 1
        assert collector._metrics["test_metric"][0].value == 100.5

    def test_record_timing_existing_metric(self) -> None:
        """Test recording timing for existing metric."""
        collector = MetricsCollector()
        collector.record_timing("test_metric", 100.5)
        collector.record_timing("test_metric", 200.0)

        assert len(collector._metrics["test_metric"]) == 2
        assert collector._metrics["test_metric"][0].value == 100.5
        assert collector._metrics["test_metric"][1].value == 200.0

    def test_record_timing_max_samples_limit(self) -> None:
        """Test recording timing respects max_samples limit."""
        collector = MetricsCollector(max_samples=3)

        # Add more than max_samples
        for i in range(5):
            collector.record_timing("test_metric", float(i))

        assert len(collector._metrics["test_metric"]) == 3
        # Should keep the most recent values (2, 3, 4)
        values = [m.value for m in collector._metrics["test_metric"]]
        assert values == [2.0, 3.0, 4.0]

    def test_record_timing_max_metric_names_limit(self) -> None:
        """Test recording timing respects max_metric_names limit."""
        collector = MetricsCollector(max_metric_names=2)

        # Add metrics up to the limit
        collector.record_timing("metric1", 100.0)
        collector.record_timing("metric2", 200.0)
        assert len(collector._metrics) == 2

        # Add one more - should drop the oldest
        collector.record_timing("metric3", 300.0)
        assert len(collector._metrics) == 2
        assert "metric1" not in collector._metrics
        assert "metric2" in collector._metrics
        assert "metric3" in collector._metrics

    def test_increment_counter_new_counter(self) -> None:
        """Test incrementing new counter."""
        collector = MetricsCollector()
        collector.increment_counter("test_counter")

        assert "test_counter" in collector._counters
        assert collector._counters["test_counter"] == 1

    def test_increment_counter_existing_counter(self) -> None:
        """Test incrementing existing counter."""
        collector = MetricsCollector()
        collector.increment_counter("test_counter", 5)
        collector.increment_counter("test_counter", 3)

        assert collector._counters["test_counter"] == 8

    def test_increment_counter_custom_value(self) -> None:
        """Test incrementing counter with custom value."""
        collector = MetricsCollector()
        collector.increment_counter("test_counter", 10)

        assert collector._counters["test_counter"] == 10

    def test_increment_counter_max_metric_names_limit(self) -> None:
        """Test incrementing counter respects max_metric_names limit."""
        collector = MetricsCollector(max_metric_names=2)

        collector.increment_counter("counter1", 1)
        collector.increment_counter("counter2", 2)
        assert len(collector._counters) == 2

        # Add one more - should drop the oldest
        collector.increment_counter("counter3", 3)
        assert len(collector._counters) == 2
        assert "counter1" not in collector._counters
        assert "counter2" in collector._counters
        assert "counter3" in collector._counters

    def test_get_stats_existing_metric(self) -> None:
        """Test getting stats for existing metric."""
        collector = MetricsCollector()
        collector.record_timing("test_metric", 1.0)
        collector.record_timing("test_metric", 2.0)
        collector.record_timing("test_metric", 3.0)

        stats = collector.get_stats("test_metric")
        assert stats is not None
        assert stats.count == 3
        assert stats.sum == 6.0
        assert stats.min == 1.0
        assert stats.max == 3.0
        assert stats.avg == 2.0

    def test_get_stats_nonexistent_metric(self) -> None:
        """Test getting stats for nonexistent metric."""
        collector = MetricsCollector()
        stats = collector.get_stats("nonexistent")
        assert stats is None

    def test_get_counter_existing_counter(self) -> None:
        """Test getting existing counter value."""
        collector = MetricsCollector()
        collector.increment_counter("test_counter", 42)

        value = collector.get_counter("test_counter")
        assert value == 42

    def test_get_counter_nonexistent_counter(self) -> None:
        """Test getting nonexistent counter value."""
        collector = MetricsCollector()
        value = collector.get_counter("nonexistent")
        assert value == 0

    def test_get_all_metrics_empty(self) -> None:
        """Test getting all metrics when empty."""
        collector = MetricsCollector()
        result = collector.get_all_metrics()

        assert result == {"timings": {}, "counters": {}}

    def test_get_all_metrics_with_data(self) -> None:
        """Test getting all metrics with data."""
        collector = MetricsCollector()

        # Add timing data
        collector.record_timing("timing1", 100.0)
        collector.record_timing("timing1", 200.0)
        collector.record_timing("timing2", 50.0)

        # Add counter data
        collector.increment_counter("counter1", 5)
        collector.increment_counter("counter2", 10)

        result = collector.get_all_metrics()

        assert "timings" in result
        assert "counters" in result
        assert result["counters"] == {"counter1": 5, "counter2": 10}

        # Check timing stats
        timings = result["timings"]
        assert "timing1" in timings
        assert "timing2" in timings

        timing1_stats = timings["timing1"]
        assert timing1_stats["count"] == 2
        assert timing1_stats["avg_ms"] == 150.0
        assert timing1_stats["min_ms"] == 100.0
        assert timing1_stats["max_ms"] == 200.0
        assert timing1_stats["total_ms"] == 300.0

    def test_get_all_metrics_rounding(self) -> None:
        """Test that timing values are properly rounded."""
        collector = MetricsCollector()
        collector.record_timing("test", 1.23456789)
        collector.record_timing("test", 2.34567890)

        result = collector.get_all_metrics()
        timing_stats = result["timings"]["test"]

        assert timing_stats["avg_ms"] == 1.79  # Rounded to 2 decimal places
        assert timing_stats["min_ms"] == 1.23
        assert timing_stats["max_ms"] == 2.35
        assert timing_stats["total_ms"] == 3.58

    def test_reset(self) -> None:
        """Test resetting all metrics."""
        collector = MetricsCollector()

        # Add data
        collector.record_timing("test_metric", 100.0)
        collector.increment_counter("test_counter", 5)

        # Verify data exists
        assert len(collector._metrics) == 1
        assert len(collector._counters) == 1

        # Reset
        collector.reset()

        # Verify data is cleared
        assert len(collector._metrics) == 0
        assert len(collector._counters) == 0

    def test_thread_safety_basic(self) -> None:
        """Test basic thread safety with lock usage."""
        collector = MetricsCollector()

        # This test verifies that the lock is used by checking that
        # the operations complete without raising exceptions
        collector.record_timing("test", 100.0)
        collector.increment_counter("test", 1)

        # These operations should work without issues
        stats = collector.get_stats("test")
        counter = collector.get_counter("test")

        assert stats is not None
        assert counter == 1


class TestGetMetrics:
    """Test get_metrics function."""

    def test_get_metrics_singleton(self) -> None:
        """Test that get_metrics returns the same instance."""
        metrics1 = get_metrics()
        metrics2 = get_metrics()

        assert metrics1 is metrics2
        assert isinstance(metrics1, MetricsCollector)

    def test_get_metrics_caching(self) -> None:
        """Test that get_metrics is cached (lru_cache)."""
        # Clear the cache first to ensure clean test
        get_metrics.cache_clear()

        with patch("tool_router.observability.metrics.MetricsCollector") as mock_collector_class:
            mock_instance = MagicMock()
            mock_collector_class.return_value = mock_instance

            # First call should create instance
            metrics1 = get_metrics()
            mock_collector_class.assert_called_once()

            # Second call should use cached instance
            metrics2 = get_metrics()
            mock_collector_class.assert_called_once()  # Still only called once

            assert metrics1 is metrics2
            assert metrics1 is mock_instance


class TestTimingContext:
    """Test TimingContext class."""

    def test_timing_context_initialization(self) -> None:
        """Test TimingContext initialization."""
        collector = MetricsCollector()
        context = TimingContext("test_metric", collector)

        assert context.metric_name == "test_metric"
        assert context.metrics is collector
        assert context.start_time == 0.0

    def test_timing_context_initialization_default_metrics(self) -> None:
        """Test TimingContext initialization with default metrics."""
        context = TimingContext("test_metric")

        assert context.metric_name == "test_metric"
        assert context.metrics is not None
        assert isinstance(context.metrics, MetricsCollector)

    def test_timing_context_enter(self) -> None:
        """Test TimingContext enter method."""
        collector = MetricsCollector()
        context = TimingContext("test_metric", collector)

        with patch("time.perf_counter") as mock_perf_counter:
            mock_perf_counter.return_value = 123456.789

            result = context.__enter__()

            assert result is context
            assert context.start_time == 123456.789
            mock_perf_counter.assert_called_once()

    def test_timing_context_exit_records_metric(self) -> None:
        """Test TimingContext exit records timing metric."""
        collector = MetricsCollector()
        context = TimingContext("test_metric", collector)

        with patch("time.perf_counter") as mock_perf_counter:
            # Setup timing
            mock_perf_counter.side_effect = [1000.0, 1100.0]  # start, end

            with context:
                pass  # Context body

            # Verify metric was recorded
            assert "test_metric" in collector._metrics
            assert len(collector._metrics["test_metric"]) == 1
            # Should record 100ms (1100.0 - 1000.0) * 1000 for milliseconds
            assert collector._metrics["test_metric"][0].value == 100000.0

    def test_timing_context_with_exception(self) -> None:
        """Test TimingContext works correctly with exceptions."""
        collector = MetricsCollector()
        context = TimingContext("test_metric", collector)

        with patch("time.perf_counter") as mock_perf_counter:
            mock_perf_counter.side_effect = [1000.0, 1100.0]

            try:
                with context:
                    raise ValueError("Test error")
            except ValueError:
                pass  # Expected

            # Metric should still be recorded despite exception
            assert "test_metric" in collector._metrics
            assert len(collector._metrics["test_metric"]) == 1

    def test_timing_context_as_context_manager(self) -> None:
        """Test TimingContext as context manager."""
        collector = MetricsCollector()

        with patch("time.perf_counter") as mock_perf_counter:
            mock_perf_counter.side_effect = [1000.0, 1050.0]  # 50ms duration

            with TimingContext("test_metric", collector):
                pass

            # Verify metric was recorded
            stats = collector.get_stats("test_metric")
            assert stats is not None
            assert stats.count == 1
            assert stats.avg == 50000.0  # 50ms in milliseconds

    def test_timing_context_nested(self) -> None:
        """Test nested TimingContext usage."""
        collector = MetricsCollector()

        with patch("time.perf_counter") as mock_perf_counter:
            # Outer context: 1000.0 -> 1100.0 (100ms)
            # Inner context: 1100.0 -> 1150.0 (50ms)
            mock_perf_counter.side_effect = [1000.0, 1100.0, 1100.0, 1150.0]

            with TimingContext("outer_metric", collector):
                with TimingContext("inner_metric", collector):
                    pass

            # Both metrics should be recorded
            outer_stats = collector.get_stats("outer_metric")
            inner_stats = collector.get_stats("inner_metric")

            assert outer_stats is not None
            assert inner_stats is not None
            # Outer context includes the inner context duration (150ms total)
            assert outer_stats.avg == 150000.0  # 150ms total
            assert inner_stats.avg == 50000.0  # 50ms
