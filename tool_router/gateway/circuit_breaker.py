"""Circuit breaker for AI provider failover.

States:
  CLOSED  — normal operation, requests pass through
  OPEN    — provider failing, fast-fail without calling
  HALF_OPEN — probe with single request to check recovery
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeVar


T = TypeVar("T")


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(Exception):
    """Raised when circuit is open and requests are being rejected."""

    def __init__(self, endpoint: str, retry_after: float) -> None:
        self.endpoint = endpoint
        self.retry_after = retry_after
        super().__init__(f"Circuit open for {endpoint}, retry after {retry_after:.1f}s")


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout_s: float = 30.0
    half_open_max_calls: int = 1
    success_threshold: int = 2


@dataclass
class _CircuitMetrics:
    failures: int = 0
    successes: int = 0
    last_failure_time: float = 0.0
    half_open_successes: int = 0
    total_requests: int = 0
    total_failures: int = 0
    total_short_circuits: int = 0


class CircuitBreaker:
    """Per-endpoint circuit breaker with configurable thresholds."""

    def __init__(self, config: CircuitBreakerConfig | None = None) -> None:
        self._config = config or CircuitBreakerConfig()
        self._circuits: dict[str, tuple[CircuitState, _CircuitMetrics]] = {}

    def _get_circuit(self, endpoint: str) -> tuple[CircuitState, _CircuitMetrics]:
        if endpoint not in self._circuits:
            self._circuits[endpoint] = (
                CircuitState.CLOSED,
                _CircuitMetrics(),
            )
        return self._circuits[endpoint]

    def state(self, endpoint: str) -> CircuitState:
        state, metrics = self._get_circuit(endpoint)
        if state == CircuitState.OPEN:
            elapsed = time.monotonic() - metrics.last_failure_time
            if elapsed >= self._config.recovery_timeout_s:
                self._circuits[endpoint] = (
                    CircuitState.HALF_OPEN,
                    metrics,
                )
                metrics.half_open_successes = 0
                return CircuitState.HALF_OPEN
        return state

    def call(
        self,
        endpoint: str,
        fn: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        current = self.state(endpoint)
        _, metrics = self._get_circuit(endpoint)
        metrics.total_requests += 1

        if current == CircuitState.OPEN:
            metrics.total_short_circuits += 1
            retry_after = self._config.recovery_timeout_s - (time.monotonic() - metrics.last_failure_time)
            raise CircuitOpenError(endpoint, max(0, retry_after))

        try:
            result = fn(*args, **kwargs)
            self._on_success(endpoint)
            return result
        except Exception:
            self._on_failure(endpoint)
            raise

    def _on_success(self, endpoint: str) -> None:
        state, metrics = self._get_circuit(endpoint)
        metrics.successes += 1

        if state == CircuitState.HALF_OPEN:
            metrics.half_open_successes += 1
            if metrics.half_open_successes >= self._config.success_threshold:
                self._circuits[endpoint] = (
                    CircuitState.CLOSED,
                    _CircuitMetrics(),
                )
        elif state == CircuitState.CLOSED:
            metrics.failures = 0

    def _on_failure(self, endpoint: str) -> None:
        state, metrics = self._get_circuit(endpoint)
        metrics.failures += 1
        metrics.total_failures += 1
        metrics.last_failure_time = time.monotonic()

        if state == CircuitState.HALF_OPEN or (
            state == CircuitState.CLOSED and metrics.failures >= self._config.failure_threshold
        ):
            self._circuits[endpoint] = (
                CircuitState.OPEN,
                metrics,
            )

    def reset(self, endpoint: str) -> None:
        self._circuits.pop(endpoint, None)

    def get_stats(self, endpoint: str) -> dict[str, Any]:
        _state, metrics = self._get_circuit(endpoint)
        return {
            "state": self.state(endpoint).value,
            "failures": metrics.failures,
            "total_requests": metrics.total_requests,
            "total_failures": metrics.total_failures,
            "total_short_circuits": metrics.total_short_circuits,
        }

    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        return {ep: self.get_stats(ep) for ep in self._circuits}
