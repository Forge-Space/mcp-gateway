"""Redis cache backend for distributed caching."""

from __future__ import annotations

import json
import logging
import pickle
import threading
import time
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass
from contextlib import contextmanager

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from cachetools import TTLCache

from .types import CacheConfig

logger = logging.getLogger(__name__)


@dataclass
class RedisConfig:
    """Configuration for Redis cache backend."""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    health_check_interval: int = 30
    max_connections: int = 10
    connection_pool_kwargs: Optional[Dict[str, Any]] = None


class RedisCache:
    """Redis-based cache implementation with fallback to TTLCache."""

    def __init__(
        self,
        config: RedisConfig,
        fallback_cache: Optional[TTLCache] = None,
        key_prefix: str = "mcp_cache:",
        serializer: str = "pickle"  # "pickle" or "json"
    ):
        self.config = config
        self.key_prefix = key_prefix
        self.serializer = serializer
        self.fallback_cache = fallback_cache
        self._redis_client = None
        self._connection_lock = threading.Lock()
        self._last_health_check = 0
        self._is_healthy = False

        # Initialize Redis connection
        self._init_redis()

    def _init_redis(self) -> None:
        """Initialize Redis connection pool."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, using fallback cache only")
            return

        try:
            # Build connection pool kwargs
            pool_kwargs = {
                "host": self.config.host,
                "port": self.config.port,
                "db": self.config.db,
                "socket_timeout": self.config.socket_timeout,
                "socket_connect_timeout": self.config.socket_connect_timeout,
                "retry_on_timeout": self.config.retry_on_timeout,
                "max_connections": self.config.max_connections,
            }

            if self.config.password:
                pool_kwargs["password"] = self.config.password

            # Add custom connection pool kwargs
            if self.config.connection_pool_kwargs:
                pool_kwargs.update(self.config.connection_pool_kwargs)

            # Create Redis client with connection pool
            self._redis_client = redis.Redis(**pool_kwargs)

            # Test connection
            self._redis_client.ping()
            self._is_healthy = True
            logger.info(f"Redis cache initialized: {self.config.host}:{self.config.port}")

        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            self._redis_client = None
            self._is_healthy = False

    def _make_key(self, key: str) -> str:
        """Create a namespaced key for Redis."""
        return f"{self.key_prefix}{key}"

    def _serialize(self, value: Any) -> bytes:
        """Serialize value for Redis storage."""
        try:
            if self.serializer == "pickle":
                return pickle.dumps(value)
            elif self.serializer == "json":
                return json.dumps(value).encode('utf-8')
            else:
                raise ValueError(f"Unsupported serializer: {self.serializer}")
        except Exception as e:
            logger.error(f"Failed to serialize value: {e}")
            raise

    def _deserialize(self, value: bytes) -> Any:
        """Deserialize value from Redis storage."""
        try:
            if self.serializer == "pickle":
                return pickle.loads(value)
            elif self.serializer == "json":
                return json.loads(value.decode('utf-8'))
            else:
                raise ValueError(f"Unsupported serializer: {self.serializer}")
        except Exception as e:
            logger.error(f"Failed to deserialize value: {e}")
            raise

    @contextmanager
    def _get_redis(self):
        """Get Redis client with health check."""
        if not self._is_healthy or not self._redis_client:
            self._check_health()

        if self._is_healthy and self._redis_client:
            yield self._redis_client
        else:
            raise ConnectionError("Redis is not available")

    def _check_health(self) -> bool:
        """Check Redis health and reconnect if needed."""
        current_time = time.time()

        # Skip health check if recently checked
        if current_time - self._last_health_check < self.config.health_check_interval:
            return self._is_healthy

        with self._connection_lock:
            try:
                if self._redis_client:
                    self._redis_client.ping()
                    self._is_healthy = True
                else:
                    self._init_redis()
            except Exception as e:
                logger.warning(f"Redis health check failed: {e}")
                self._is_healthy = False
                self._redis_client = None

            self._last_health_check = current_time
            return self._is_healthy

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache, with fallback to local cache."""
        # Try Redis first
        try:
            with self._get_redis() as redis_client:
                value = redis_client.get(self._make_key(key))
                if value is not None:
                    return self._deserialize(value)
        except (ConnectionError, Exception) as e:
            logger.debug(f"Redis get failed for key {key}: {e}")

        # Fallback to local cache
        if self.fallback_cache:
            return self.fallback_cache.get(key, default)

        return default

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""
        success = False

        # Try Redis first
        try:
            with self._get_redis() as redis_client:
                serialized_value = self._serialize(value)
                redis_key = self._make_key(key)

                if ttl is not None:
                    success = redis_client.setex(redis_key, ttl, serialized_value)
                else:
                    success = redis_client.set(redis_key, serialized_value)

                if success:
                    # Also set in fallback cache for resilience
                    if self.fallback_cache:
                        self.fallback_cache.set(key, value, ttl)
                    return True
        except (ConnectionError, Exception) as e:
            logger.debug(f"Redis set failed for key {key}: {e}")

        # Fallback to local cache only
        if self.fallback_cache:
            self.fallback_cache.set(key, value, ttl)
            return True

        return False

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        success = False

        # Try Redis first
        try:
            with self._get_redis() as redis_client:
                success = redis_client.delete(self._make_key(key))
        except (ConnectionError, Exception) as e:
            logger.debug(f"Redis delete failed for key {key}: {e}")

        # Also delete from fallback cache
        if self.fallback_cache:
            try:
                del self.fallback_cache[key]
                success = True
            except KeyError:
                pass

        return success

    def clear(self) -> bool:
        """Clear all cache entries."""
        success = False

        # Try Redis first
        try:
            with self._get_redis() as redis_client:
                # Delete all keys with our prefix
                pattern = f"{self.key_prefix}*"
                keys = redis_client.keys(pattern)
                if keys:
                    success = redis_client.delete(*keys)
        except (ConnectionError, Exception) as e:
            logger.debug(f"Redis clear failed: {e}")

        # Also clear fallback cache
        if self.fallback_cache:
            self.fallback_cache.clear()
            success = True

        return success

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        # Try Redis first
        try:
            with self._get_redis() as redis_client:
                return redis_client.exists(self._make_key(key))
        except (ConnectionError, Exception) as e:
            logger.debug(f"Redis exists check failed for key {key}: {e}")

        # Fallback to local cache
        if self.fallback_cache:
            return key in self.fallback_cache

        return False

    def get_many(self, keys: list[str]) -> Dict[str, Any]:
        """Get multiple values from cache."""
        result = {}

        # Try Redis first for batch operations
        redis_keys = [self._make_key(key) for key in keys]
        try:
            with self._get_redis() as redis_client:
                values = redis_client.mget(redis_keys)
                for i, key in enumerate(keys):
                    if values[i] is not None:
                        try:
                            result[key] = self._deserialize(values[i])
                        except Exception as e:
                            logger.debug(f"Failed to deserialize key {key}: {e}")
                            result[key] = None
        except (ConnectionError, Exception) as e:
            logger.debug(f"Redis get_many failed: {e}")

        # Get missing keys from fallback cache
        if self.fallback_cache:
            for key in keys:
                if key not in result:
                    result[key] = self.fallback_cache.get(key)

        return result

    def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values in cache."""
        success = True

        # Try Redis first for batch operations
        try:
            with self._get_redis() as redis_client:
                pipe = redis_client.pipeline()
                for key, value in mapping.items():
                    serialized_value = self._serialize(value)
                    redis_key = self._make_key(key)

                    if ttl is not None:
                        pipe.setex(redis_key, ttl, serialized_value)
                    else:
                        pipe.set(redis_key, serialized_value)

                pipe_results = pipe.execute()
                success = all(pipe_results)
        except (ConnectionError, Exception) as e:
            logger.debug(f"Redis set_many failed: {e}")
            success = False

        # Also set in fallback cache
        if self.fallback_cache:
            for key, value in mapping.items():
                self.fallback_cache.set(key, value, ttl)

        return success

    def get_info(self) -> Dict[str, Any]:
        """Get Redis cache information."""
        info = {
            "redis_available": REDIS_AVAILABLE,
            "redis_connected": self._is_healthy,
            "fallback_enabled": self.fallback_cache is not None,
            "key_prefix": self.key_prefix,
            "serializer": self.serializer,
        }

        if self._is_healthy and self._redis_client:
            try:
                redis_info = self._redis_client.info()
                info.update({
                    "redis_version": redis_info.get("redis_version"),
                    "used_memory": redis_info.get("used_memory"),
                    "used_memory_human": redis_info.get("used_memory_human"),
                    "connected_clients": redis_info.get("connected_clients"),
                    "total_commands_processed": redis_info.get("total_commands_processed"),
                })
            except Exception as e:
                logger.debug(f"Failed to get Redis info: {e}")

        if self.fallback_cache:
            info.update({
                "fallback_size": len(self.fallback_cache),
                "fallback_currsize": self.fallback_cache.currsize,
                "fallback_maxsize": self.fallback_cache.maxsize,
            })

        return info

    def close(self) -> None:
        """Close Redis connection."""
        if self._redis_client:
            try:
                self._redis_client.close()
            except Exception as e:
                logger.debug(f"Error closing Redis connection: {e}")
            finally:
                self._redis_client = None
                self._is_healthy = False


def create_redis_cache(
    config: Optional[RedisConfig] = None,
    fallback_config: Optional[CacheConfig] = None,
    **kwargs
) -> RedisCache:
    """Create a Redis cache instance with fallback."""
    if config is None:
        config = RedisConfig()

    # Create fallback cache
    fallback_cache = None
    if fallback_config:
        fallback_cache = TTLCache(
            maxsize=fallback_config.max_size,
            ttl=fallback_config.ttl
        )

    return RedisCache(
        config=config,
        fallback_cache=fallback_cache,
        **kwargs
    )
