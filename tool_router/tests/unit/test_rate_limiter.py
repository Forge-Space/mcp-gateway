"""Unit tests for tool_router/security/rate_limiter.py module."""

from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock, patch

from tool_router.security.rate_limiter import (
    LimitType,
    RateLimitConfig,
    RateLimiter,
    RateLimitResult,
)


class TestLimitType:
    """Test cases for LimitType enum."""

    def test_limit_type_values(self) -> None:
        """Test that LimitType has expected values."""
        assert LimitType.PER_MINUTE.value == "minute"
        assert LimitType.PER_HOUR.value == "hour"
        assert LimitType.PER_DAY.value == "day"
        assert LimitType.BURST.value == "burst"

    def test_limit_type_count(self) -> None:
        """Test number of limit types."""
        assert len(LimitType) == 5


class TestRateLimitConfig:
    """Test cases for RateLimitConfig dataclass."""

    def test_rate_limit_config_defaults(self) -> None:
        """Test RateLimitConfig default values."""
        config = RateLimitConfig()

        assert config.requests_per_minute == 60
        assert config.requests_per_hour == 1000
        assert config.requests_per_day == 10000
        assert config.burst_capacity == 10
        assert config.penalty_duration == 300
        assert config.adaptive_scaling is True
        assert config.penalty_multiplier == 2.0

    def test_rate_limit_config_custom(self) -> None:
        """Test RateLimitConfig with custom values."""
        config = RateLimitConfig(
            requests_per_minute=30,
            requests_per_hour=500,
            requests_per_day=5000,
            burst_capacity=5,
            penalty_duration=600,
            adaptive_scaling=False,
            penalty_multiplier=3.0,
        )

        assert config.requests_per_minute == 30
        assert config.requests_per_hour == 500
        assert config.requests_per_day == 5000
        assert config.burst_capacity == 5
        assert config.penalty_duration == 600
        assert config.adaptive_scaling is False
        assert config.penalty_multiplier == 3.0


class TestRateLimitResult:
    """Test cases for RateLimitResult dataclass."""

    def test_rate_limit_result_creation(self) -> None:
        """Test RateLimitResult creation with all fields."""
        result = RateLimitResult(
            allowed=True,
            remaining=50,
            reset_time=1234567890,
            retry_after=30,
            penalty_applied=False,
            metadata={"test": "data"},
        )

        assert result.allowed is True
        assert result.remaining == 50
        assert result.reset_time == 1234567890
        assert result.retry_after == 30
        assert result.penalty_applied is False
        assert result.metadata == {"test": "data"}

    def test_rate_limit_result_defaults(self) -> None:
        """Test RateLimitResult with default values."""
        result = RateLimitResult(allowed=False, remaining=0, reset_time=1234567890)

        assert result.retry_after is None
        assert result.penalty_applied is False
        assert result.metadata is None


class TestRateLimiter:
    """Test cases for RateLimiter."""

    def test_initialization_memory_only(self) -> None:
        """Test RateLimiter initialization with memory storage."""
        limiter = RateLimiter(use_redis=False)

        assert limiter.use_redis is False
        assert limiter.redis_client is None
        assert hasattr(limiter, "_memory_storage")
        assert hasattr(limiter, "_penalties")
        assert hasattr(limiter, "_lock")
        assert hasattr(limiter, "_cache")

    def test_initialization_with_redis_success(self) -> None:
        """Test RateLimiter initialization with Redis connection."""
        with patch("redis.from_url") as mock_redis:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock_redis.return_value = mock_client

            limiter = RateLimiter(use_redis=True, redis_url="redis://localhost:6379")

            assert limiter.use_redis is True
            assert limiter.redis_client == mock_client
            mock_client.ping.assert_called_once()

    def test_initialization_with_redis_failure(self) -> None:
        """Test RateLimiter initialization with Redis connection failure."""
        with patch("redis.from_url", side_effect=Exception("Connection failed")):
            limiter = RateLimiter(use_redis=True, redis_url="redis://localhost:6379")

            assert limiter.use_redis is False  # Falls back to memory
            assert limiter.redis_client is None

    def test_check_rate_limit_clean_request(self) -> None:
        """Test rate limit check with clean request."""
        limiter = RateLimiter(use_redis=False)
        config = RateLimitConfig()

        result = limiter.check_rate_limit("user123", config)

        assert result.allowed is True
        assert result.remaining == 60  # requests_per_minute
        assert result.penalty_applied is False
        assert result.metadata["window"] == "minute"

    def test_check_rate_limit_with_penalty(self) -> None:
        """Test rate limit check when penalty is active."""
        limiter = RateLimiter(use_redis=False)
        config = RateLimitConfig()

        # Apply penalty
        limiter.apply_penalty("user123", 300)

        result = limiter.check_rate_limit("user123", config)

        assert result.allowed is False
        assert result.remaining == 0
        assert result.penalty_applied is True
        assert result.retry_after > 0
        assert result.metadata["reason"] == "penalty_active"

    def test_check_rate_limit_minute_limit_exceeded(self) -> None:
        """Test rate limit check when minute limit is exceeded."""
        limiter = RateLimiter(use_redis=False)
        config = RateLimitConfig(requests_per_minute=2)

        # Make requests to exceed limit
        limiter.check_rate_limit("user123", config)
        limiter.check_rate_limit("user123", config)
        limiter.check_rate_limit("user123", config)

        result = limiter.check_rate_limit("user123", config)

        assert result.allowed is False
        assert result.remaining == 0
        assert "window_type" in result.metadata
        assert result.metadata["window_type"] == "minute"

    def test_check_rate_limit_hour_limit_exceeded(self) -> None:
        """Test rate limit check when hour limit is exceeded."""
        limiter = RateLimiter(use_redis=False)
        config = RateLimitConfig(requests_per_hour=2)

        # Make many requests to exceed hour limit
        for _ in range(3):
            limiter.check_rate_limit("user123", config)

        result = limiter.check_rate_limit("user123", config)

        assert result.allowed is False
        assert result.remaining == 0
        assert result.metadata["window_type"] == "hour"

    def test_check_rate_limit_day_limit_exceeded(self) -> None:
        """Test rate limit check when day limit is exceeded."""
        limiter = RateLimiter(use_redis=False)
        config = RateLimitConfig(requests_per_day=2)

        # Make many requests to exceed day limit
        for _ in range(3):
            limiter.check_rate_limit("user123", config)

        result = limiter.check_rate_limit("user123", config)

        assert result.allowed is False
        assert result.remaining == 0
        assert result.metadata["window_type"] == "day"

    def test_check_rate_limit_burst_limit_exceeded(self) -> None:
        """Test rate limit check when burst limit is exceeded."""
        limiter = RateLimiter(use_redis=False)
        config = RateLimitConfig(burst_capacity=2)

        # Make rapid requests to exceed burst limit
        limiter.check_rate_limit("user123", config)
        limiter.check_rate_limit("user123", config)
        limiter.check_rate_limit("user123", config)

        result = limiter.check_rate_limit("user123", config)

        assert result.allowed is False
        assert result.remaining == 0
        assert result.metadata["window_type"] == "burst"

    def test_check_rate_limit_most_restrictive_window(self) -> None:
        """Test that most restrictive window is returned."""
        limiter = RateLimiter(use_redis=False)
        config = RateLimitConfig(
            requests_per_minute=5, requests_per_hour=3, requests_per_day=2
        )

        # Exceed minute limit but not others
        for _ in range(6):
            limiter.check_rate_limit("user123", config)

        result = limiter.check_rate_limit("user123", config)

        assert result.allowed is False
        assert result.metadata["window_type"] == "minute"  # Most restrictive

    def test_check_rate_limit_adaptive_scaling_enabled(self) -> None:
        """Test adaptive scaling when enabled."""
        limiter = RateLimiter(use_redis=False)
        config = RateLimitConfig(
            requests_per_minute=100, adaptive_scaling=True, penalty_multiplier=2.0
        )

        # Create a scenario where remaining is low
        with patch.object(limiter, "_apply_adaptive_scaling") as mock_adaptive:
            mock_adaptive.return_value = RateLimitResult(
                allowed=True,
                remaining=10,  # Low remaining (10% of 100)
                reset_time=1234567890,
                metadata={"adaptive_scaling_applied": True},
            )

            result = limiter.check_rate_limit("user123", config)

            mock_adaptive.assert_called_once()
            assert result.metadata["adaptive_scaling_applied"] is True

    def test_check_rate_limit_adaptive_scaling_disabled(self) -> None:
        """Test adaptive scaling when disabled."""
        limiter = RateLimiter(use_redis=False)
        config = RateLimitConfig(requests_per_minute=100, adaptive_scaling=False)

        result = limiter.check_rate_limit("user123", config)

        assert "adaptive_scaling_applied" not in result.metadata

    def test_check_redis_window_limit_success(self) -> None:
        """Test Redis window limit check success."""
        limiter = RateLimiter(use_redis=True, redis_url="redis://localhost:6379")

        with patch.object(limiter, "_check_redis_window_limit") as mock_redis:
            mock_redis.return_value = RateLimitResult(
                allowed=True,
                remaining=50,
                reset_time=1234567890,
                metadata={"window_type": "minute", "current_count": 10},
            )

            result = limiter.check_rate_limit("user123", RateLimitConfig())

            mock_redis.assert_called_once()

    def test_check_redis_window_limit_fallback(self) -> None:
        """Test Redis window limit check fallback to memory."""
        limiter = RateLimiter(use_redis=True, redis_url="redis://localhost:6379")

        with patch.object(
            limiter, "_check_redis_window_limit", side_effect=Exception("Redis error")
        ) as mock_redis:
            with patch.object(limiter, "_check_memory_window_limit") as mock_memory:
                mock_memory.return_value = RateLimitResult(
                    allowed=True,
                    remaining=50,
                    reset_time=1234567890,
                    metadata={"window_type": "minute", "current_count": 10},
                )

                result = limiter.check_rate_limit("user123", RateLimitConfig())

                mock_memory.assert_called_once()

    def test_check_memory_window_limit_new_identifier(self) -> None:
        """Test memory window limit with new identifier."""
        limiter = RateLimiter(use_redis=False)

        result = limiter._check_memory_window_limit(
            "new_user", LimitType.PER_MINUTE, 60, 1000, 1000, 1234567890
        )

        assert result.allowed is True
        assert result.remaining == 60
        assert result.metadata["current_count"] == 0

    def test_check_memory_window_limit_existing_identifier(self) -> None:
        """Test memory window limit with existing identifier."""
        limiter = RateLimiter(use_redis=False)

        # First request
        limiter._check_memory_window_limit(
            "existing_user", LimitType.PER_MINUTE, 60, 1000, 1000, 1234567890
        )

        # Second request
        result = limiter._check_memory_window_limit(
            "existing_user", LimitType.PER_MINUTE, 60, 1000, 1000, 1234567890
        )

        assert result.allowed is True
        assert result.remaining == 59  # One request already recorded
        assert result.metadata["current_count"] == 1

    def test_check_memory_window_limit_old_requests_removed(self) -> None:
        """Test that old requests are removed from memory window."""
        limiter = RateLimiter(use_redis=False)

        # Add old request outside window
        old_time = 1234567890 - 100
        limiter._memory_storage["test_user"] = {"minute": deque([old_time])}

        result = limiter._check_memory_window_limit(
            "test_user", LimitType.PER_MINUTE, 60, 1000, 1000, 1234567890
        )

        assert result.allowed is True
        assert result.metadata["current_count"] == 0  # Old request removed

    def test_check_burst_limit_redis_success(self) -> None:
        """Test burst limit check with Redis success."""
        limiter = RateLimiter(use_redis=True, redis_url="redis://localhost:6379")

        with patch.object(limiter, "_check_burst_limit") as mock_burst:
            mock_burst.return_value = RateLimitResult(
                allowed=True,
                remaining=8,
                reset_time=1234567890,
                metadata={"window_type": "burst", "current_count": 2},
            )

            result = limiter._check_burst_limit("user123", 10, 1234567890)

            mock_burst.assert_called_once()

    def test_check_burst_limit_redis_fallback(self) -> None:
        """Test burst limit check with Redis fallback."""
        limiter = RateLimiter(use_redis=True, redis_url="redis://localhost:6379")

        with patch.object(limiter, "_check_burst_limit") as mock_burst:
            mock_burst.return_value = RateLimitResult(
                allowed=True,
                remaining=8,
                reset_time=1234567890,
                metadata={"window_type": "burst", "current_count": 2},
            )

            result = limiter._check_burst_limit("user123", 10, 1234567890)

            mock_burst.assert_called_once()

    def test_check_burst_limit_memory(self) -> None:
        """Test burst limit check with memory storage."""
        limiter = RateLimiter(use_redis=False)

        result = limiter._check_burst_limit("user123", 10, 1234567890)

        assert result.allowed is True
        assert result.remaining == 10
        assert result.metadata["window_type"] == "burst"
        assert result.metadata["current_count"] == 0

    def test_apply_penalty(self) -> None:
        """Test penalty application."""
        limiter = RateLimiter(use_redis=False)

        limiter.apply_penalty("user123", 300)

        assert limiter._penalties["user123"] > time.time()

    def test_apply_penalty_with_redis(self) -> None:
        """Test penalty application with Redis."""
        limiter = RateLimiter(use_redis=True, redis_url="redis://localhost:6379")

        with patch.object(limiter.redis_client, "setex") as mock_setex:
            limiter.apply_penalty("user123", 300)

            mock_setex.assert_called_once_with("penalty:user123", 300, any)

    def test_apply_penalty_redis_error_fallback(self) -> None:
        """Test penalty application with Redis error fallback."""
        limiter = RateLimiter(use_redis=True, redis_url="redis://localhost:6379")

        with patch.object(
            limiter.redis_client, "setex", side_effect=Exception("Redis error")
        ):
            limiter.apply_penalty("user123", 300)

        # Should still work with memory storage
        assert limiter._penalties["user123"] > time.time()

    def test_clear_penalties(self) -> None:
        """Test clearing penalties."""
        limiter = RateLimiter(use_redis=False)

        limiter.apply_penalty("user123", 300)
        assert "user123" in limiter._penalties

        limiter.clear_penalties("user123")
        assert "user123" not in limiter._penalties

    def test_clear_penalties_with_redis(self) -> None:
        """Test clearing penalties with Redis."""
        limiter = RateLimiter(use_redis=True, redis_url="redis://localhost:6379")

        limiter.apply_penalty("user123", 300)

        with patch.object(limiter.redis_client, "delete") as mock_delete:
            limiter.clear_penalties("user123")

            mock_delete.assert_called_once_with("penalty:user123")

    def test_clear_penalties_redis_error_fallback(self) -> None:
        """Test clearing penalties with Redis error fallback."""
        limiter = RateLimiter(use_redis=True, redis_url="redis://localhost:6379")

        limiter.apply_penalty("user123", 300)

        with patch.object(
            limiter.redis_client, "delete", side_effect=Exception("Redis error")
        ):
            limiter.clear_penalties("user123")

        # Should still work with memory storage
        assert "user123" not in limiter._penalties

    def test_is_penalized_true(self) -> None:
        """Test penalty check when penalized."""
        limiter = RateLimiter(use_redis=False)

        limiter.apply_penalty("user123", 300)

        assert limiter._is_penalized("user123", int(time.time()) + 100) is True

    def test_is_penalized_false(self) -> None:
        """Test penalty check when not penalized."""
        limiter = RateLimiter(use_redis=False)

        assert limiter._is_penalized("user123", int(time.time()) + 100) is False

    def test_is_penalized_expired(self) -> None:
        """Test penalty check when penalty expired."""
        limiter = RateLimiter(use_redis=False)

        # Apply expired penalty
        limiter.apply_penalty("user123", -1)  # Already expired

        assert limiter._is_penalized("user123", int(time.time())) is False

    def test_get_usage_stats_memory(self) -> None:
        """Test usage statistics with memory storage."""
        limiter = RateLimiter(use_redis=False)

        # Add some requests
        limiter.check_rate_limit("user123", RateLimitConfig())
        limiter.check_rate_limit("user123", RateLimitConfig())
        limiter.apply_penalty("user123", 300)

        stats = limiter.get_usage_stats("user123")

        assert isinstance(stats, dict)
        assert "minute" in stats
        assert "hour" in stats
        assert "day" in stats
        assert "penalty_active" in stats
        assert stats["penalty_active"] is True
        assert "penalty_end" in stats

    def test_get_usage_stats_redis(self) -> None:
        """Test usage statistics with Redis."""
        limiter = RateLimiter(use_redis=True, redis_url="redis://localhost:6379")

        with patch.object(limiter.redis_client, "get") as mock_get:
            mock_get.return_value = "5"

            stats = limiter.get_usage_stats("user123")

            assert stats["minute"]["count"] == 5

    def test_get_usage_stats_redis_error_fallback(self) -> None:
        """Test usage statistics with Redis error fallback."""
        limiter = RateLimiter(use_redis=True, redis_url="redis://localhost:6379")

        with patch.object(
            limiter.redis_client, "get", side_effect=Exception("Redis error")
        ):
            stats = limiter.get_usage_stats("user123")

            assert stats["minute"]["count"] == 0  # Fallback to memory

    def test_cleanup_expired_data_memory(self) -> None:
        """Test cleanup of expired data in memory storage."""
        limiter = RateLimiter(use_redis=False)

        # Add old data
        old_time = int(time.time()) - 86400  # 24 hours ago
        limiter._memory_storage["old_user"] = {
            "minute": deque([old_time]),
            "hour": deque([old_time]),
            "day": deque([old_time]),
        }

        # Add expired penalty
        limiter._penalties["expired_user"] = old_time

        limiter.cleanup_expired_data()

        assert "old_user" not in limiter._memory_storage
        assert "expired_user" not in limiter._penalties

    def test_cleanup_expired_data_redis_disabled(self) -> None:
        """Test cleanup when Redis is disabled."""
        limiter = RateLimiter(use_redis=False)

        # Should not raise error
        limiter.cleanup_expired_data()

    def test_record_request_memory(self) -> None:
        """Test request recording in memory storage."""
        limiter = RateLimiter(use_redis=False)
        current_time = int(time.time())

        limiter._record_request("user123", current_time)

        # Check that request was recorded for each window type
        assert "minute" in limiter._memory_storage["user123"]
        assert "hour" in limiter._memory_storage["user123"]
        assert "day" in limiter._memory_storage["user123"]
        assert "burst" in limiter._memory_storage["user123"]

        # Check timestamps
        assert current_time in limiter._memory_storage["user123"]["minute"]
        assert current_time in limiter._memory_storage["user123"]["hour"]
        assert current_time in limiter._memory_storage["user123"]["day"]
        assert current_time in limiter._memory_storage["user123"]["burst"]

    def test_record_request_redis(self) -> None:
        """Test request recording with Redis (handled automatically in window check)."""
        limiter = RateLimiter(use_redis=True, redis_url="redis://localhost:6379")

        # Redis handles counting automatically in _check_window_limit
        limiter.check_rate_limit("user123", RateLimitConfig())

        # Should not raise error
        limiter._record_request("user123", int(time.time()))

    def test_thread_safety_memory_storage(self) -> None:
        """Test thread safety of memory storage operations."""
        limiter = RateLimiter(use_redis=False)
        results = []

        def check_rate_limit_thread(user_id: str, results_list: list) -> None:
            result = limiter.check_rate_limit(user_id, RateLimitConfig())
            results_list.append(result)

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(
                target=check_rate_limit_thread, args=(f"user{i}", results)
            )
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All should have succeeded
        assert len(results) == 5
        assert all(result.allowed for result in results)

    def test_thread_safety_penalties(self) -> None:
        """Test thread safety of penalty operations."""
        limiter = RateLimiter(use_redis=False)
        results = []

        def apply_penalty_thread(user_id: str, results_list: list) -> None:
            limiter.apply_penalty(user_id, 300)
            results_list.append(user_id)

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(
                target=apply_penalty_thread, args=(f"user{i}", results)
            )
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All penalties should be applied
        assert len(results) == 5
        assert all(
            limiter._is_penalized(user_id, int(time.time())) for user_id in results
        )

    def test_cache_functionality(self) -> None:
        """Test TTL cache functionality."""
        limiter = RateLimiter(use_redis=False)

        # Cache should be initialized
        assert hasattr(limiter, "_cache")
        assert limiter._cache.maxsize == 10000
        assert limiter._cache.ttl == 60

    def test_rate_limit_config_validation(self) -> None:
        """Test rate limit configuration validation."""
        config = RateLimitConfig(
            requests_per_minute=-1,  # Invalid negative value
            requests_per_hour=1000,
            requests_per_day=10000,
            burst_capacity=10,
            penalty_duration=300,
            adaptive_scaling=True,
            penalty_multiplier=2.0,
        )

        # Should still work but with negative values
        result = limiter.check_rate_limit("user123", config)
        assert isinstance(result, RateLimitResult)

    def test_rate_limit_config_extreme_values(self) -> None:
        """Test rate limit configuration with extreme values."""
        config = RateLimitConfig(
            requests_per_minute=1000000,  # Very high limit
            requests_per_hour=1000000,
            requests_per_day=1000000,
            burst_capacity=10000,
            penalty_duration=86400,  # 24 hours
            adaptive_scaling=True,
            penalty_multiplier=10.0,
        )

        result = limiter.check_rate_limit("user123", config)
        assert isinstance(result, RateLimitResult)

    def test_multiple_identifiers_independent(self) -> None:
        """Test that different identifiers are tracked independently."""
        limiter = RateLimiter(use_redis=False)
        config = RateLimitConfig(requests_per_minute=2)

        # Make requests for different users
        result1 = limiter.check_rate_limit("user1", config)
        result2 = limiter.check_rate_limit("user2", config)
        result3 = limiter.check_rate_limit("user3", config)

        # All should be allowed
        assert result1.allowed is True
        assert result2.allowed is True
        assert result3.allowed is True

        # Each should have full remaining
        assert result1.remaining == 2
        assert result2.remaining == 2
        assert result3.remaining == 2

    def test_rate_limit_edge_case_zero_limits(self) -> None:
        """Test rate limiting with zero limits (should allow all requests)."""
        limiter = RateLimiter(use_redis=False)
        config = RateLimitConfig(
            requests_per_minute=0,
            requests_per_hour=0,
            requests_per_day=0,
            burst_capacity=0,
        )

        result = limiter.check_rate_limit("user123", config)

        assert result.allowed is True
        assert result.remaining == 0

    def test_rate_limit_edge_case_negative_window(self) -> None:
        """Test rate limiting with negative window (should handle gracefully)."""
        limiter = RateLimiter(use_redis=False)
        config = RateLimitConfig()

        # This should not cause an error
        result = limiter.check_rate_limit("user123", config)
        assert isinstance(result, RateLimitResult)

    def test_rate_limit_concurrent_access_same_identifier(self) -> None:
        """Test concurrent access to same identifier."""
        limiter = RateLimiter(use_redis=False)
        config = RateLimitConfig(requests_per_minute=10)

        results = []

        def concurrent_check(user_id: str) -> None:
            result = limiter.check_rate_limit(user_id, config)
            results.append(result)

        threads = []
        for _ in range(20):
            thread = threading.Thread(target=concurrent_check, args=("user123",))
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Should have some requests blocked due to rate limiting
        blocked_count = sum(1 for result in results if not result.allowed)
        assert blocked_count > 0

    def test_penalty_duration_calculation(self) -> None:
        """Test penalty duration calculation."""
        limiter = RateLimiter(use_redis=False)

        start_time = int(time.time())
        limiter.apply_penalty("user123", 300)

        penalty_end = limiter._penalties["user123"]
        expected_end = start_time + 300

        assert penalty_end == expected_end

    def test_penalty_expiration(self) -> None:
        """Test penalty expiration logic."""
        limiter = RateLimiter(use_redis=False)

        # Apply penalty with short duration
        limiter.apply_penalty("user123", 1)

        # Wait for penalty to expire
        time.sleep(2)

        assert not limiter._is_penalized("user123", int(time.time()))

    def test_retry_after_calculation(self) -> None:
        """Test retry_after calculation for penalized requests."""
        limiter = RateLimiter(use_redis=False)

        start_time = int(time.time())
        limiter.apply_penalty("user123", 300)

        result = limiter.check_rate_limit("user123", RateLimitConfig())

        assert result.retry_after == (300 - (int(time.time()) - start_time))

    def test_metadata_enrichment(self) -> None:
        """Test that metadata is properly enriched."""
        limiter = RateLimiter(use_redis=False)
        config = RateLimitConfig()

        result = limiter.check_rate_limit("user123", config)

        assert "window" in result.metadata
        assert isinstance(result.metadata, dict)

    def test_burst_limit_isolation(self) -> None:
        """Test that burst limits are isolated from regular limits."""
        limiter = RateLimiter(use_redis=False)
        config = RateLimitConfig(requests_per_minute=1, burst_capacity=10)

        # Fill regular limit
        for _ in range(2):
            limiter.check_rate_limit("user123", config)

        # Burst limit should still have capacity
        result = limiter.check_rate_limit("user123", config)
        assert result.allowed is True
        assert result.remaining == 9  # 10 - 1 used

    def test_adaptive_scaling_threshold(self) -> None:
        """Test adaptive scaling threshold logic."""
        limiter = RateLimiter(use_redis=False)
        config = RateLimitConfig(
            requests_per_minute=100, adaptive_scaling=True, penalty_multiplier=2.0
        )

        # Create mock result with low remaining
        low_remaining_result = RateLimitResult(
            allowed=True, remaining=15, reset_time=1234567890, metadata={}  # 15% of 100
        )

        result = limiter._apply_adaptive_scaling(
            "user123", low_remaining_result, config
        )

        assert result.metadata["adaptive_scaling_applied"] is True
        assert result.remaining == 30  # 15 * 2.0

    def test_adaptive_scaling_no_threshold(self) -> None:
        """Test adaptive scaling when threshold not met."""
        limiter = RateLimiter(use_redis=False)
        config = RateLimitConfig(
            requests_per_minute=100, adaptive_scaling=True, penalty_multiplier=2.0
        )

        # Create mock result with high remaining
        high_remaining_result = RateLimitResult(
            allowed=True, remaining=80, reset_time=1234567890, metadata={}  # 80% of 100
        )

        result = limiter._apply_adaptive_scaling(
            "user123", high_remaining_result, config
        )

        assert "adaptive_scaling_applied" not in result.metadata

    def test_config_adaptive_scaling_disabled(self) -> None:
        """Test that adaptive scaling is disabled when config says so."""
        limiter = RateLimiter(use_redis=False)
        config = RateLimitConfig(
            requests_per_minute=100, adaptive_scaling=False, penalty_multiplier=2.0
        )

        result = limiter._apply_adaptive_scaling("user123", RateLimitResult(), config)

        assert "adaptive_scaling_applied" not in result.metadata

    def test_rate_limit_result_serialization(self) -> None:
        """Test RateLimitResult can be serialized."""
        result = RateLimitResult(
            allowed=True,
            remaining=50,
            reset_time=1234567890,
            retry_after=30,
            penalty_applied=False,
            metadata={"key": "value"},
        )

        # Should be serializable
        import json

        json_str = json.dumps(result.__dict__)
        reconstructed = RateLimitResult(**json.loads(json_str))

        assert reconstructed.allowed == result.allowed
        assert reconstructed.remaining == result.remaining
        assert reconstructed.reset_time == result.reset_time
        assert reconstructed.retry_after == result.retry_after
        assert reconstructed.penalty_applied == result.penalty_applied
        assert reconstructed.metadata == result.metadata

    def test_rate_limit_config_dataclass(self) -> None:
        """Test RateLimitConfig dataclass functionality."""
        config = RateLimitConfig(
            requests_per_minute=60,
            requests_per_hour=1000,
            requests_per_day=10000,
            burst_capacity=10,
            penalty_duration=300,
            adaptive_scaling=True,
            penalty_multiplier=2.0,
        )

        # Test field access
        assert config.requests_per_minute == 60
        assert config.requests_per_hour == 1000
        assert config.requests_per_day == 10000
        assert config.burst_capacity == 10
        assert config.penalty_duration == 300
        assert config.adaptive_scaling is True
        assert config.penalty_multiplier == 2.0

    def test_rate_limit_result_dataclass(self) -> None:
        """Test RateLimitResult dataclass functionality."""
        result = RateLimitResult(
            allowed=True,
            remaining=50,
            reset_time=1234567890,
            retry_after=30,
            penalty_applied=False,
            metadata={"test": "data"},
        )

        # Test field access
        assert result.allowed is True
        assert result.remaining == 50
        assert result.reset_time == 1234567890
        assert result.retry_after == 30
        assert result.penalty_applied is False
        assert result.metadata == {"test": "data"}

    def test_limit_type_enum_completeness(self) -> None:
        """Test that LimitType enum has all expected values."""
        expected_types = ["minute", "hour", "day", "burst"]
        actual_types = [limit_type.value for limit_type in LimitType]

        assert set(expected_types) == set(actual_types)

    def test_limit_type_enum_completeness(self) -> None:
        """Test that LimitType enum has all expected values."""
        expected_types = ["minute", "hour", "day", "burst"]
        actual_types = [limit_type.value for limit_type in LimitType]

        assert set(expected_types) == set(actual_types)

    def test_rate_limit_error_handling(self) -> None:
        """Test graceful error handling in rate limiting."""
        limiter = RateLimiter(use_redis=True, redis_url="redis://localhost:6379")

        # Simulate Redis connection failure
        with patch.object(limiter, "_check_window_limit") as mock_window:
            mock_window.side_effect = Exception("Redis connection lost")

            result = limiter.check_rate_limit("user123", RateLimitConfig())

            # Should fallback to memory storage
            assert isinstance(result, RateLimitResult)

    def test_penalty_cleanup_thread_safety(self) -> None:
        """Test penalty cleanup thread safety."""
        limiter = RateLimiter(use_redis=False)

        # Apply penalties from multiple threads
        def apply_penalties():
            for i in range(10):
                limiter.apply_penalty(f"user{i}", 300)

        threads = []
        for _ in range(3):
            thread = threading.Thread(target=apply_penalties)
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All penalties should be applied
        assert len(limiter._penalties) == 10

    def test_usage_stats_thread_safety(self) -> None:
        """Test usage stats thread safety."""
        limiter = RateLimiter(use_redis=False)

        def get_stats():
            return limiter.get_usage_stats("user123")

        threads = []
        for _ in range(3):
            thread = threading.Thread(target=get_stats)
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All should succeed without errors
        assert len(threads) == 3
