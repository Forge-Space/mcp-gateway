"""Tests for circuit breaker."""

import time
from unittest.mock import patch

import pytest

from tool_router.gateway.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitOpenError,
    CircuitState,
)


@pytest.fixture
def breaker():
    return CircuitBreaker(
        CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout_s=1.0,
            success_threshold=2,
        )
    )


class TestCircuitBreaker:
    def test_starts_closed(self, breaker):
        assert breaker.state("test") == CircuitState.CLOSED

    def test_stays_closed_under_threshold(self, breaker):
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call("test", self._failing_fn)
        assert breaker.state("test") == CircuitState.CLOSED

    def test_opens_at_threshold(self, breaker):
        for _ in range(3):
            with pytest.raises(ValueError):
                breaker.call("test", self._failing_fn)
        assert breaker.state("test") == CircuitState.OPEN

    def test_open_circuit_raises_fast(self, breaker):
        for _ in range(3):
            with pytest.raises(ValueError):
                breaker.call("test", self._failing_fn)

        with pytest.raises(CircuitOpenError) as exc_info:
            breaker.call("test", lambda: "ok")
        assert exc_info.value.endpoint == "test"
        assert exc_info.value.retry_after > 0

    def test_transitions_to_half_open(self, breaker):
        for _ in range(3):
            with pytest.raises(ValueError):
                breaker.call("test", self._failing_fn)

        with patch("tool_router.gateway.circuit_breaker.time") as mock_time:
            base = time.monotonic()
            mock_time.monotonic.side_effect = [base + 2.0, base + 2.1]
            assert breaker.state("test") == CircuitState.HALF_OPEN

    def test_half_open_recovers_on_success(self, breaker):
        for _ in range(3):
            with pytest.raises(ValueError):
                breaker.call("test", self._failing_fn)

        _state, metrics = breaker._circuits["test"]
        metrics.last_failure_time = time.monotonic() - 2.0

        breaker.call("test", lambda: "ok")
        breaker.call("test", lambda: "ok")
        assert breaker.state("test") == CircuitState.CLOSED

    def test_half_open_reopens_on_failure(self, breaker):
        for _ in range(3):
            with pytest.raises(ValueError):
                breaker.call("test", self._failing_fn)

        _state, metrics = breaker._circuits["test"]
        metrics.last_failure_time = time.monotonic() - 2.0

        with pytest.raises(ValueError):
            breaker.call("test", self._failing_fn)
        assert breaker.state("test") == CircuitState.OPEN

    def test_success_resets_failure_count(self, breaker):
        with pytest.raises(ValueError):
            breaker.call("test", self._failing_fn)
        breaker.call("test", lambda: "ok")
        with pytest.raises(ValueError):
            breaker.call("test", self._failing_fn)
        assert breaker.state("test") == CircuitState.CLOSED

    def test_reset_clears_circuit(self, breaker):
        for _ in range(3):
            with pytest.raises(ValueError):
                breaker.call("test", self._failing_fn)
        breaker.reset("test")
        assert breaker.state("test") == CircuitState.CLOSED

    def test_get_stats(self, breaker):
        breaker.call("test", lambda: "ok")
        stats = breaker.get_stats("test")
        assert stats["state"] == "closed"
        assert stats["total_requests"] == 1

    def test_get_all_stats(self, breaker):
        breaker.call("ep1", lambda: "ok")
        breaker.call("ep2", lambda: "ok")
        all_stats = breaker.get_all_stats()
        assert "ep1" in all_stats
        assert "ep2" in all_stats

    def test_short_circuit_tracking(self, breaker):
        for _ in range(3):
            with pytest.raises(ValueError):
                breaker.call("test", self._failing_fn)

        with pytest.raises(CircuitOpenError):
            breaker.call("test", lambda: "ok")

        stats = breaker.get_stats("test")
        assert stats["total_short_circuits"] == 1

    def test_independent_endpoints(self, breaker):
        for _ in range(3):
            with pytest.raises(ValueError):
                breaker.call("bad", self._failing_fn)
        assert breaker.state("bad") == CircuitState.OPEN
        assert breaker.state("good") == CircuitState.CLOSED
        breaker.call("good", lambda: "ok")

    @staticmethod
    def _failing_fn():
        msg = "provider error"
        raise ValueError(msg)
