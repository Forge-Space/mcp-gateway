"""Test Redis cache integration."""

from unittest.mock import Mock, patch

from tool_router.cache.config import CacheBackendConfig, get_cache_backend_config
from tool_router.cache.redis_cache import RedisCache, RedisConfig


class TestRedisCache:
    """Test Redis cache functionality."""

    def test_redis_config_defaults(self):
        """Test Redis configuration defaults."""
        config = RedisConfig()
        assert config.host == "localhost"
        assert config.port == 6379
        assert config.db == 0
        assert config.password is None
        assert config.socket_timeout == 5
        assert config.socket_connect_timeout == 5
        assert config.retry_on_timeout is True
        assert config.health_check_interval == 30
        assert config.max_connections == 10

    def test_redis_config_custom(self):
        """Test Redis configuration with custom values."""
        config = RedisConfig(
            host="redis.example.com",
            port=6380,
            db=1,
            password="secret",
            socket_timeout=10,
            max_connections=20,
        )
        assert config.host == "redis.example.com"
        assert config.port == 6380
        assert config.db == 1
        assert config.password == "secret"
        assert config.socket_timeout == 10
        assert config.max_connections == 20

    @patch("tool_router.cache.redis_cache.REDIS_AVAILABLE", False)
    def test_redis_cache_without_redis(self):
        """Test Redis cache behavior when Redis is not available."""
        config = RedisConfig()
        cache = RedisCache(config)

        # Should fall back to local cache only
        assert cache._redis_client is None
        assert cache._is_healthy is False
        assert cache.fallback_cache is not None

    @patch("tool_router.cache.redis_cache.redis")
    def test_redis_cache_with_mock_redis(self, mock_redis):
        """Test Redis cache with mocked Redis client."""
        # Setup mock Redis client
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_redis.Redis.return_value = mock_client

        config = RedisConfig()
        cache = RedisCache(config)

        # Should initialize Redis connection
        assert cache._redis_client is mock_client
        assert cache._is_healthy is True

    def test_cache_key_namespacing(self):
        """Test cache key namespacing."""
        config = RedisConfig(key_prefix="test_prefix:")
        cache = RedisCache(config)

        assert cache._make_key("user:123") == "test_prefix:user:123"
        assert cache._make_key("session:abc") == "test_prefix:session:abc"

    def test_serialization_pickle(self):
        """Test pickle serialization."""
        config = RedisConfig(serializer="pickle")
        cache = RedisCache(config)

        test_data = {"key": "value", "number": 42}
        serialized = cache._serialize(test_data)
        deserialized = cache._deserialize(serialized)

        assert deserialized == test_data

    def test_serialization_json(self):
        """Test JSON serialization."""
        config = RedisConfig(serializer="json")
        cache = RedisCache(config)

        test_data = {"key": "value", "number": 42}
        serialized = cache._serialize(test_data)
        deserialized = cache._deserialize(serialized)

        assert deserialized == test_data


class TestCacheBackendConfig:
    """Test cache backend configuration."""

    def test_from_environment_defaults(self):
        """Test configuration from environment with defaults."""
        with patch.dict("os.environ", {}, clear=True):
            config = CacheBackendConfig.from_environment()

            assert config.backend_type == "memory"
            assert config.redis_config is None
            assert config.fallback_config is not None
            assert config.fallback_config.max_size == 1000
            assert config.fallback_config.ttl == 3600

    def test_from_environment_redis(self):
        """Test Redis configuration from environment."""
        env_vars = {
            "CACHE_BACKEND": "redis",
            "REDIS_HOST": "redis.example.com",
            "REDIS_PORT": "6380",
            "REDIS_PASSWORD": "secret123",
            "CACHE_FALLBACK_MAX_SIZE": "500",
            "CACHE_FALLBACK_TTL": "1800",
        }

        with patch.dict("os.environ", env_vars, clear=True):
            config = CacheBackendConfig.from_environment()

            assert config.backend_type == "redis"
            assert config.redis_config is not None
            assert config.redis_config.host == "redis.example.com"
            assert config.redis_config.port == 6380
            assert config.redis_config.password == "secret123"
            assert config.fallback_config.max_size == 500
            assert config.fallback_config.ttl == 1800

    def test_from_environment_hybrid(self):
        """Test hybrid configuration from environment."""
        env_vars = {
            "CACHE_BACKEND": "hybrid",
            "REDIS_HOST": "localhost",
            "REDIS_PORT": "6379",
        }

        with patch.dict("os.environ", env_vars, clear=True):
            config = CacheBackendConfig.from_environment()

            assert config.backend_type == "hybrid"
            assert config.redis_config is not None
            assert config.fallback_config is not None


class TestCacheIntegration:
    """Test cache integration scenarios."""

    @patch("tool_router.cache.redis_cache.REDIS_AVAILABLE", False)
    def test_fallback_only_mode(self):
        """Test cache behavior when Redis is unavailable."""
        config = CacheBackendConfig(
            backend_type="redis",
            redis_config=RedisConfig(),
            fallback_config=CacheConfig(max_size=10, ttl=60),
        )

        cache = RedisCache(
            config=config.redis_config, fallback_config=config.fallback_config
        )

        # Test basic operations work with fallback only
        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"
        assert cache.exists("test_key") is True
        assert cache.delete("test_key") is True
        assert cache.exists("test_key") is False

    @patch("tool_router.cache.redis_cache.redis")
    def test_redis_with_fallback(self, mock_redis):
        """Test Redis cache with fallback behavior."""
        # Setup mock Redis
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_client.get.return_value = None  # Simulate cache miss
        mock_client.set.return_value = True
        mock_client.setex.return_value = True
        mock_client.delete.return_value = 1
        mock_client.exists.return_value = 0
        mock_redis.Redis.return_value = mock_client

        config = CacheBackendConfig(
            backend_type="hybrid",
            redis_config=RedisConfig(),
            fallback_config=CacheConfig(max_size=10, ttl=60),
        )

        cache = RedisCache(
            config=config.redis_config, fallback_config=config.fallback_config
        )

        # Test operations
        cache.set("test_key", "test_value", ttl=300)
        assert cache.get("test_key") == "test_value"
        assert cache.exists("test_key") is True

        # Test batch operations
        batch_data = {"key1": "value1", "key2": "value2"}
        assert cache.set_many(batch_data) is True

        results = cache.get_many(["key1", "key2"])
        assert results == {"key1": "value1", "key2": "value2"}

        # Test clear operation
        assert cache.clear() is True


if __name__ == "__main__":
    # Simple manual test
    print("Testing Redis cache integration...")

    # Test configuration
    config = get_cache_backend_config()
    print(f"Backend type: {config.backend_type}")
    print(f"Redis enabled: {config.redis_config is not None}")
    print(f"Fallback config: {config.fallback_config is not None}")

    # Test basic cache operations
    from tool_router.cache.cache_manager import CacheConfig
    from tool_router.cache.redis_cache import create_redis_cache

    try:
        cache = create_redis_cache(
            config=RedisConfig(host="localhost", port=6379),
            fallback_config=CacheConfig(max_size=10, ttl=60),
        )

        print("Cache created successfully")

        # Test operations
        cache.set("test", "value")
        result = cache.get("test")
        print(f"Get result: {result}")

        cache.delete("test")
        exists = cache.exists("test")
        print(f"Exists after delete: {exists}")

        # Get cache info
        info = cache.get_info()
        print(f"Cache info: {info}")

        cache.close()
        print("Cache test completed successfully")

    except Exception as e:
        print(f"Cache test failed: {e}")
        print("This is expected if Redis is not running locally")
