"""Test Enhanced Rate Limiter - Multi-strategy rate limiting with configurable caching."""

import time
import threading
from unittest.mock import Mock, patch

from tool_router.security.enhanced_rate_limiter import (
    EnhancedRateLimiter,
    LimitType,
    RateLimitConfig,
    RateLimitResult,
    RateLimiter,  # Backward compatibility alias
)


class TestLimitType:
    """Test LimitType enum."""

    def test_limit_type_values(self):
        """Test limit type enum values."""
        assert LimitType.PER_MINUTE.value == "minute"
        assert LimitType.PER_HOUR.value == "hour"
        assert LimitType.PER_DAY.value == "day"
        assert LimitType.BURST.value == "burst"


class TestRateLimitConfig:
    """Test RateLimitConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RateLimitConfig()

        assert config.requests_per_minute == 60
        assert config.requests_per_hour == 1000
        assert config.requests_per_day == 10000
        assert config.burst_capacity == 10
        assert config.penalty_duration == 300
        assert config.adaptive_scaling is True
        assert config.penalty_multiplier == 2.0
        assert config.cache_ttl == 60
        assert config.cache_size == 10000

    def test_custom_config(self):
        """Test custom configuration values."""
        config = RateLimitConfig(
            requests_per_minute=30,
            requests_per_hour=500,
            requests_per_day=5000,
            burst_capacity=5,
            penalty_duration=600,
            adaptive_scaling=False,
            penalty_multiplier=3.0,
            cache_ttl=120,
            cache_size=5000
        )

        assert config.requests_per_minute == 30
        assert config.requests_per_hour == 500
        assert config.requests_per_day == 5000
        assert config.burst_capacity == 5
        assert config.penalty_duration == 600
        assert config.adaptive_scaling is False
        assert config.penalty_multiplier == 3.0
        assert config.cache_ttl == 120
        assert config.cache_size == 5000


class TestRateLimitResult:
    """Test RateLimitResult dataclass."""

    def test_rate_limit_result_creation(self):
        """Test creating a rate limit result."""
        result = RateLimitResult(
            allowed=True,
            remaining=50,
            reset_time=1234567890,
            retry_after=30,
            penalty_applied=False,
            metadata={"window": "minute"}
        )

        assert result.allowed is True
        assert result.remaining == 50
        assert result.reset_time == 1234567890
        assert result.retry_after == 30
        assert result.penalty_applied is False
        assert result.metadata["window"] == "minute"

    def test_rate_limit_result_defaults(self):
        """Test rate limit result with default values."""
        result = RateLimitResult(
            allowed=False,
            remaining=0,
            reset_time=1234567890
        )

        assert result.allowed is False
        assert result.remaining == 0
        assert result.reset_time == 1234567890
        assert result.retry_after is None
        assert result.penalty_applied is False
        assert result.metadata is None


class TestEnhancedRateLimiter:
    """Test EnhancedRateLimiter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = RateLimitConfig(
            requests_per_minute=10,
            requests_per_hour=100,
            requests_per_day=1000,
            burst_capacity=5,
            cache_ttl=1,  # Short TTL for testing
            cache_size=100
        )
        self.limiter = EnhancedRateLimiter(use_redis=False, config=self.config)

    def test_initialization_default(self):
        """Test limiter initialization with default config."""
        limiter = EnhancedRateLimiter()

        assert limiter.use_redis is False
        assert limiter.redis_client is None
        assert limiter.config.requests_per_minute == 60
        assert limiter.config.cache_ttl == 60
        assert limiter.config.cache_size == 10000

    def test_initialization_custom_config(self):
        """Test limiter initialization with custom config."""
        limiter = EnhancedRateLimiter(config=self.config)

        assert limiter.config == self.config
        assert limiter.use_redis is False
        assert limiter.redis_client is None

    def test_initialization_redis_unavailable(self):
        """Test initialization when Redis is not available."""
        with patch('tool_router.security.enhanced_rate_limiter.REDIS_AVAILABLE', False):
            limiter = EnhancedRateLimiter(use_redis=True)
            assert limiter.use_redis is False
            assert limiter.redis_client is None

    def test_check_rate_limit_allowed(self):
        """Test rate limit check when request is allowed."""
        identifier = "test_user"
        result = self.limiter.check_rate_limit(identifier)

        assert result.allowed is True
        assert result.remaining == 9  # 10 - 1 used
        assert result.reset_time > time.time()
        assert result.penalty_applied is False

    def test_check_rate_limit_exceeded(self):
        """Test rate limit check when limit is exceeded."""
        identifier = "test_user"

        # Use up the limit
        for _ in range(10):
            result = self.limiter.check_rate_limit(identifier)
            assert result.allowed is True

        # Next request should be blocked
        result = self.limiter.check_rate_limit(identifier)
        assert result.allowed is False
        assert result.remaining == 0
        assert result.retry_after is not None

    def test_check_rate_limit_different_identifiers(self):
        """Test rate limiting works independently for different identifiers."""
        user1_result = self.limiter.check_rate_limit("user1")
        user2_result = self.limiter.check_rate_limit("user2")

        assert user1_result.allowed is True
        assert user2_result.allowed is True
        assert user1_result.remaining == 9
        assert user2_result.remaining == 9

    def test_check_rate_limit_with_custom_config(self):
        """Test rate limit check with custom configuration."""
        custom_config = RateLimitConfig(requests_per_minute=5)
        limiter = EnhancedRateLimiter(config=custom_config)

        # Use up the custom limit
        for _ in range(5):
            result = limiter.check_rate_limit("test_user")
            assert result.allowed is True

        # Next request should be blocked
        result = limiter.check_rate_limit("test_user")
        assert result.allowed is False

    def test_burst_limiting(self):
        """Test burst capacity limiting."""
        identifier = "test_user"

        # Make rapid requests within burst window
        for _ in range(5):  # Within burst capacity
            result = self.limiter.check_rate_limit(identifier)
            assert result.allowed is True

        # Next request should exceed burst limit
        result = self.limiter.check_rate_limit(identifier)
        assert result.allowed is False

    def test_penalty_application(self):
        """Test penalty application and enforcement."""
        identifier = "test_user"

        # Apply penalty
        self.limiter.apply_penalty(identifier, 60)  # 60 second penalty

        # Request should be blocked due to penalty
        result = self.limiter.check_rate_limit(identifier)
        assert result.allowed is False
        assert result.penalty_applied is True
        assert result.retry_after > 0

    def test_penalty_expiration(self):
        """Test penalty expiration."""
        identifier = "test_user"

        # Apply short penalty
        self.limiter.apply_penalty(identifier, 1)  # 1 second penalty

        # Wait for penalty to expire
        time.sleep(1.1)

        # Request should be allowed now
        result = self.limiter.check_rate_limit(identifier)
        assert result.allowed is True
        assert result.penalty_applied is False

    def test_clear_penalties(self):
        """Test clearing penalties."""
        identifier = "test_user"

        # Apply penalty
        self.limiter.apply_penalty(identifier, 60)

        # Clear penalty
        self.limiter.clear_penalties(identifier)

        # Request should be allowed
        result = self.limiter.check_rate_limit(identifier)
        assert result.allowed is True
        assert result.penalty_applied is False

    def test_adaptive_scaling(self):
        """Test adaptive scaling when enabled."""
        config = RateLimitConfig(
            requests_per_minute=10,
            adaptive_scaling=True,
            penalty_multiplier=2.0
        )
        limiter = EnhancedRateLimiter(config=config)

        identifier = "test_user"

        # Use up most of the limit to trigger adaptive scaling
        for _ in range(8):  # Use 8 out of 10 (80%)
            result = limiter.check_rate_limit(identifier)
            assert result.allowed is True

        # Check if adaptive scaling was applied
        result = limiter.check_rate_limit(identifier)
        if result.allowed and result.metadata.get('adaptive_scaling_applied'):
            # Remaining should be reduced due to adaptive scaling
            assert result.remaining < 2

    def test_adaptive_scaling_disabled(self):
        """Test adaptive scaling when disabled."""
        config = RateLimitConfig(
            requests_per_minute=10,
            adaptive_scaling=False
        )
        limiter = EnhancedRateLimiter(config=config)

        identifier = "test_user"

        # Use up most of the limit
        for _ in range(8):
            result = limiter.check_rate_limit(identifier)
            assert result.allowed is True

        # Adaptive scaling should not be applied
        result = limiter.check_rate_limit(identifier)
        assert result.metadata.get('adaptive_scaling_applied') is None

    def test_get_usage_stats(self):
        """Test getting usage statistics."""
        identifier = "test_user"

        # Make some requests
        for _ in range(3):
            self.limiter.check_rate_limit(identifier)

        stats = self.limiter.get_usage_stats(identifier)

        assert 'minute' in stats
        assert 'hour' in stats
        assert 'day' in stats
        assert stats['minute']['count'] == 3
        assert stats['penalty_active'] is False

    def test_get_usage_stats_with_penalty(self):
        """Test getting usage statistics with active penalty."""
        identifier = "test_user"

        # Apply penalty
        self.limiter.apply_penalty(identifier, 60)

        stats = self.limiter.get_usage_stats(identifier)

        assert stats['penalty_active'] is True
        assert 'penalty_end' in stats

    def test_cache_metrics(self):
        """Test cache performance metrics."""
        identifier = "test_user"

        # Make some requests to populate cache
        for _ in range(3):
            self.limiter.check_rate_limit(identifier)

        # Get stats (should use cache)
        self.limiter.get_usage_stats(identifier)
        self.limiter.get_usage_stats(identifier)

        metrics = self.limiter.get_cache_metrics()

        assert 'cache_hit_rate' in metrics
        assert 'total_hits' in metrics
        assert 'total_misses' in metrics
        assert 'total_requests' in metrics
        assert 'cache_sizes' in metrics
        assert metrics['redis_enabled'] is False
        assert metrics['redis_connected'] is False

    def test_clear_caches(self):
        """Test clearing all caches."""
        identifier = "test_user"

        # Populate caches
        self.limiter.check_rate_limit(identifier)
        self.limiter.get_usage_stats(identifier)

        # Clear caches
        self.limiter.clear_caches()

        # Check cache metrics
        metrics = self.limiter.get_cache_metrics()
        assert metrics['total_hits'] == 0
        assert metrics['total_misses'] == 0

    def test_cleanup_expired_data(self):
        """Test cleanup of expired rate limit data."""
        identifier = "test_user"

        # Make some requests
        for _ in range(3):
            self.limiter.check_rate_limit(identifier)

        # Cleanup should not remove recent data
        self.limiter.cleanup_expired_data()

        # Should still be able to get stats
        stats = self.limiter.get_usage_stats(identifier)
        assert stats['minute']['count'] >= 3

    def test_thread_safety(self):
        """Test thread safety of rate limiter."""
        identifier = "test_user"
        results = []

        def make_requests():
            for _ in range(5):
                result = self.limiter.check_rate_limit(identifier)
                results.append(result.allowed)

        # Create multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=make_requests)
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Should have made 15 total requests, but only 10 allowed
        allowed_count = sum(results)
        assert allowed_count == 10  # Only 10 should be allowed

    def test_backward_compatibility_alias(self):
        """Test backward compatibility alias."""
        assert RateLimiter == EnhancedRateLimiter

        # Create instance using alias
        limiter = RateLimiter(config=self.config)
        assert isinstance(limiter, EnhancedRateLimiter)

        # Test basic functionality
        result = limiter.check_rate_limit("test_user")
        assert result.allowed is True

    def test_redis_connection_failure(self):
        """Test fallback when Redis connection fails."""
        with patch('redis.from_url') as mock_redis:
            mock_redis.side_effect = Exception("Connection failed")

            limiter = EnhancedRateLimiter(use_redis=True, redis_url="redis://localhost")

            # Should fallback to memory storage
            assert limiter.use_redis is False
            assert limiter.redis_client is None

    def test_redis_operation_failure(self):
        """Test fallback when Redis operations fail."""
        with patch('redis.from_url') as mock_redis:
            mock_client = Mock()
            mock_client.ping.return_value = True
            mock_redis.return_value = mock_client

            # Make Redis operations fail
            mock_client.pipeline.side_effect = Exception("Redis error")

            limiter = EnhancedRateLimiter(use_redis=True, redis_url="redis://localhost")

            # Should still work with memory fallback
            result = limiter.check_rate_limit("test_user")
            assert result.allowed is True

    def test_hourly_rate_limiting(self):
        """Test hourly rate limiting."""
        identifier = "test_user"

        # This would require many requests to test hourly limit
        # Instead, test with a very small hourly limit
        config = RateLimitConfig(requests_per_hour=2)
        limiter = EnhancedRateLimiter(config=config)

        # Use up hourly limit
        for _ in range(2):
            result = limiter.check_rate_limit(identifier)
            assert result.allowed is True

        # Next request should be blocked by hourly limit
        result = limiter.check_rate_limit(identifier)
        assert result.allowed is False

    def test_daily_rate_limiting(self):
        """Test daily rate limiting."""
        identifier = "test_user"

        # Test with very small daily limit
        config = RateLimitConfig(requests_per_day=2)
        limiter = EnhancedRateLimiter(config=config)

        # Use up daily limit
        for _ in range(2):
            result = limiter.check_rate_limit(identifier)
            assert result.allowed is True

        # Next request should be blocked by daily limit
        result = limiter.check_rate_limit(identifier)
        assert result.allowed is False

    def test_cache_ttl_behavior(self):
        """Test cache TTL behavior."""
        identifier = "test_user"

        # Make request
        result1 = self.limiter.check_rate_limit(identifier)

        # Should be cached (same result)
        result2 = self.limiter.check_rate_limit(identifier)

        # Results should be the same (cached)
        assert result1.remaining == result2.remaining

        # Wait for cache to expire
        time.sleep(1.1)  # Wait longer than TTL

        # Should get fresh result
        result3 = self.limiter.check_rate_limit(identifier)
        assert result3.remaining < result2.remaining
