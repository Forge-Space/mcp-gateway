"""
Basic Cache Tests

Tests for the basic cache functionality that works with the existing implementation.
"""

from unittest.mock import Mock

import pytest

from tool_router.cache.cache_manager import CacheManager
from tool_router.cache.config import (
    CacheBackendConfig,
    get_redis_url,
    is_redis_enabled,
    validate_cache_config,
)
from tool_router.cache.types import CacheConfig, CacheMetrics


def test_cache_imports():
    """Test that we can import basic cache modules."""
    assert CacheConfig is not None

    config = CacheConfig()
    assert config.max_size == 1000
    assert config.ttl == 3600
    assert config.cleanup_interval == 300
    assert config.enable_metrics is True


def test_cache_config_creation():
    """Test cache configuration creation."""
    default_config = CacheConfig()
    assert default_config.max_size == 1000
    assert default_config.ttl == 3600
    assert default_config.enable_metrics is True

    custom_config = CacheConfig(max_size=2000, ttl=7200, cleanup_interval=600, enable_metrics=False)
    assert custom_config.max_size == 2000
    assert custom_config.ttl == 7200
    assert custom_config.cleanup_interval == 600
    assert custom_config.enable_metrics is False


def test_cache_metrics():
    """Test cache metrics functionality."""
    metrics = CacheMetrics()
    assert metrics.hits == 0
    assert metrics.misses == 0
    assert metrics.evictions == 0
    assert metrics.total_requests == 0
    assert metrics.hit_rate == 0.0
    assert metrics.cache_size == 0

    metrics.hits = 100
    metrics.misses = 25
    metrics.total_requests = 125
    metrics.hit_rate = metrics.hits / metrics.total_requests

    assert metrics.hits == 100
    assert metrics.misses == 25
    assert metrics.total_requests == 125
    assert metrics.hit_rate == 0.8


def test_cache_backend_config():
    """Test cache backend configuration."""
    default_config = CacheBackendConfig()
    assert default_config.backend_type == "memory"
    assert default_config.redis_config is None

    env_config = CacheBackendConfig.from_environment()
    assert env_config.backend_type in ["memory", "redis", "hybrid"]
    assert env_config.fallback_config is not None


def test_cache_validation():
    """Test cache configuration validation."""
    is_valid = validate_cache_config()
    assert isinstance(is_valid, bool)


def test_cache_redis_functions():
    """Test Redis-related utility functions."""
    redis_enabled = is_redis_enabled()
    assert isinstance(redis_enabled, bool)

    redis_url = get_redis_url()
    assert isinstance(redis_url, str)
    assert redis_url.startswith("redis://")


def test_cache_manager_integration():
    """Test cache manager integration."""
    manager = CacheManager()
    assert manager is not None

    assert hasattr(manager, "create_ttl_cache")
    assert hasattr(manager, "create_lru_cache")
    assert hasattr(manager, "get_cache")
    assert hasattr(manager, "clear_cache")
    assert hasattr(manager, "clear_all_caches")
    assert hasattr(manager, "get_metrics")


def test_cache_performance_monitoring():
    """Test cache performance monitoring."""
    manager = CacheManager()

    if hasattr(manager, "get_metrics"):
        metrics = manager.get_metrics()
        assert metrics is not None


class TestCacheOperations:
    """Test cache operations with mock data."""

    def setup_method(self):
        """Setup test environment."""
        self.manager = CacheManager()
        self.mock_cache = Mock()

    def test_basic_cache_operations(self):
        """Test basic cache operations."""
        assert hasattr(self.manager, "create_ttl_cache")
        assert hasattr(self.manager, "get_cache")
        assert hasattr(self.manager, "clear_cache")

    def test_cache_with_expiration(self):
        """Test cache operations with expiration."""
        cache = self.manager.create_ttl_cache("test_ttl", CacheConfig(ttl=3600))
        assert cache is not None
        cache["key1"] = "value1"
        assert cache["key1"] == "value1"

    def test_cache_batch_operations(self):
        """Test batch cache operations."""
        cache = self.manager.create_lru_cache("test_lru", CacheConfig(max_size=100))
        assert cache is not None
        for i in range(10):
            cache[f"key_{i}"] = f"value_{i}"
        assert len(cache) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
