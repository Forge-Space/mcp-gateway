"""Metrics collection for tool router performance monitoring."""

from __future__ import annotations

import functools
import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Any


@dataclass
class MetricValue:
    """Single metric value with timestamp."""

    value: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class MetricStats:
    """Statistical summary of a metric."""

    count: int
    sum: float
    min: float
    max: float
    avg: float

    @classmethod
    def from_values(cls, values: list[float]) -> MetricStats:
        """Calculate stats from list of values."""
        if not values:
            return cls(count=0, sum=0.0, min=0.0, max=0.0, avg=0.0)

        return cls(
            count=len(values),
            sum=sum(values),
            min=min(values),
            max=max(values),
            avg=sum(values) / len(values),
        )


class MetricsCollector:
    """Thread-safe metrics collector for performance monitoring."""

    def __init__(self, max_samples: int = 1000, max_metric_names: int = 100) -> None:
        """Initialize metrics collector.

        Args:
            max_samples: Maximum number of samples to keep per metric
            max_metric_names: Maximum number of unique metric names to track
        """
        self.max_samples = max_samples
        self.max_metric_names = max_metric_names
        self._metrics: dict[str, list[MetricValue]] = {}
        self._counters: dict[str, int] = {}
        self._lock = Lock()

    def record_timing(self, metric_name: str, duration_milliseconds: float) -> None:
        """Record a timing metric.

        Args:
            metric_name: Metric name
            duration_milliseconds: Duration in milliseconds
        """
        with self._lock:
            # Check if we need to create a new metric
            if metric_name not in self._metrics:
                if len(self._metrics) >= self.max_metric_names:
                    # Drop oldest metric (FIFO eviction)
                    oldest_key = next(iter(self._metrics))
                    del self._metrics[oldest_key]
                self._metrics[metric_name] = []

            metric_values_list = self._metrics[metric_name]
            metric_values_list.append(MetricValue(value=duration_milliseconds))

            # Keep only recent samples
            if len(metric_values_list) > self.max_samples:
                metric_values_list.pop(0)

    def increment_counter(self, name: str, value: int = 1) -> None:
        """Increment a counter metric.

        Args:
            name: Counter name
            value: Amount to increment (default 1)
        """
        with self._lock:
            # Check if we need to create a new counter
            if name not in self._counters:
                if len(self._counters) >= self.max_metric_names:
                    # Drop oldest counter (FIFO eviction)
                    oldest_key = next(iter(self._counters))
                    del self._counters[oldest_key]
                self._counters[name] = 0

            self._counters[name] += value

    def get_stats(self, name: str) -> MetricStats | None:
        """Get statistical summary for a metric.

        Args:
            name: Metric name

        Returns:
            Metric statistics or None if metric doesn't exist
        """
        with self._lock:
            if name not in self._metrics:
                return None

            values = [m.value for m in self._metrics[name]]
            return MetricStats.from_values(values)

    def get_counter(self, name: str) -> int:
        """Get current counter value.

        Args:
            name: Counter name

        Returns:
            Counter value (0 if counter doesn't exist)
        """
        with self._lock:
            return self._counters.get(name, 0)

    def get_all_metrics(self) -> dict[str, Any]:
        """Get all metrics as a dictionary.

        Returns:
            Dictionary with all metrics and counters
        """
        with self._lock:
            result: dict[str, Any] = {
                "timings": {},
                "counters": dict(self._counters),
            }

            for name, values in self._metrics.items():
                if values:
                    stats = MetricStats.from_values([m.value for m in values])
                    result["timings"][name] = {
                        "count": stats.count,
                        "avg_ms": round(stats.avg, 2),
                        "min_ms": round(stats.min, 2),
                        "max_ms": round(stats.max, 2),
                        "total_ms": round(stats.sum, 2),
                    }

            return result

    def reset(self) -> None:
        """Reset all metrics and counters."""
        with self._lock:
            self._metrics.clear()
            self._counters.clear()


@functools.lru_cache(maxsize=1)
def get_metrics() -> MetricsCollector:
    """Get or create global metrics collector instance (singleton).

    Returns:
        Global MetricsCollector instance
    """
    return MetricsCollector()


class TimingContext:
    """Context manager for timing operations."""

    def __init__(self, metric_name: str, metrics: MetricsCollector | None = None):
        """Initialize timing context.

        Args:
            metric_name: Name of the metric to record
            metrics: MetricsCollector instance (uses global if None)
        """
        self.metric_name = metric_name
        self.metrics = metrics or get_metrics()
        self.start_time: float = 0.0

    def __enter__(self) -> TimingContext:
        """Start timing."""
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args: Any) -> None:
        """Stop timing and record metric."""
        duration_milliseconds = (time.perf_counter() - self.start_time) * 1000
        self.metrics.record_timing(self.metric_name, duration_milliseconds)
