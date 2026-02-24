"""Cache management utilities for MCP Gateway."""

from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict
from typing import Any

from cachetools import LRUCache, TTLCache

from .redis_cache import RedisCache, RedisConfig, create_redis_cache
from .types import CacheConfig, CacheMetrics

logger = logging.getLogger(__name__)


class CacheManager:
    """Centralized cache management with metrics and cleanup."""

    def __init__(self):
        self._caches: dict[str, Any] = {}
        self._metrics: dict[str, CacheMetrics] = defaultdict(CacheMetrics)
        self._lock = threading.RLock()
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutes

        # Global metrics
        self._global_metrics = CacheMetrics()
        self._global_metrics.last_reset_time = time.time()

    def create_ttl_cache(self, name: str, config: CacheConfig | None = None) -> TTLCache:
        """Create a TTL cache with optional configuration."""
        config = config or CacheConfig()
        cache = TTLCache(maxsize=config.max_size, ttl=config.ttl)

        with self._lock:
            self._caches[name] = cache
            if config.enable_metrics:
                self._metrics[name] = CacheMetrics()
                self._metrics[name].last_reset_time = time.time()

        logger.info(f"Created TTL cache '{name}' with max_size={config.max_size}, ttl={config.ttl}s")
        return cache

    def create_lru_cache(self, name: str, config: CacheConfig | None = None) -> LRUCache:
        """Create an LRU cache with optional configuration."""
        config = config or CacheConfig()
        cache = LRUCache(maxsize=config.max_size)

        with self._lock:
            self._caches[name] = cache
            if config.enable_metrics:
                self._metrics[name] = CacheMetrics()
                self._metrics[name].last_reset_time = time.time()

        logger.info(f"Created LRU cache '{name}' with max_size={config.max_size}")
        return cache

    def create_redis_cache(
        self,
        name: str,
        redis_config: RedisConfig | None = None,
        fallback_config: CacheConfig | None = None,
        **kwargs,
    ) -> RedisCache:
        """Create a Redis cache with optional fallback configuration."""
        redis_config = redis_config or RedisConfig()
        fallback_config = fallback_config or CacheConfig()

        cache = create_redis_cache(config=redis_config, fallback_config=fallback_config, **kwargs)

        with self._lock:
            self._caches[name] = cache
            if fallback_config.enable_metrics:
                self._metrics[name] = CacheMetrics()
                self._metrics[name].last_reset_time = time.time()

        logger.info(f"Created Redis cache '{name}' with fallback")
        return cache

    def get_cache(self, name: str) -> Any:
        """Get a cache by name."""
        with self._lock:
            return self._caches.get(name)

    def record_hit(self, cache_name: str) -> None:
        """Record a cache hit for metrics."""
        with self._lock:
            if cache_name in self._metrics:
                self._metrics[cache_name].hits += 1
                self._metrics[cache_name].total_requests += 1
                self._update_hit_rate(cache_name)

            self._global_metrics.hits += 1
            self._global_metrics.total_requests += 1
            self._update_global_hit_rate()

    def record_miss(self, cache_name: str) -> None:
        """Record a cache miss for metrics."""
        with self._lock:
            if cache_name in self._metrics:
                self._metrics[cache_name].misses += 1
                self._metrics[cache_name].total_requests += 1
                self._update_hit_rate(cache_name)

            self._global_metrics.misses += 1
            self._global_metrics.total_requests += 1
            self._update_global_hit_rate()

    def record_eviction(self, cache_name: str) -> None:
        """Record a cache eviction for metrics."""
        with self._lock:
            if cache_name in self._metrics:
                self._metrics[cache_name].evictions += 1

            self._global_metrics.evictions += 1

    def _update_hit_rate(self, cache_name: str) -> None:
        """Update hit rate for a specific cache."""
        if cache_name in self._metrics:
            metrics = self._metrics[cache_name]
            if metrics.total_requests > 0:
                metrics.hit_rate = metrics.hits / metrics.total_requests

    def _update_global_hit_rate(self) -> None:
        """Update global hit rate."""
        if self._global_metrics.total_requests > 0:
            self._global_metrics.hit_rate = self._global_metrics.hits / self._global_metrics.total_requests

    def get_metrics(self, cache_name: str | None = None) -> dict[str, Any]:
        """Get cache metrics, optionally for a specific cache."""
        with self._lock:
            if cache_name:
                if cache_name in self._metrics:
                    metrics = self._metrics[cache_name]
                    return {
                        "hits": metrics.hits,
                        "misses": metrics.misses,
                        "evictions": metrics.evictions,
                        "total_requests": metrics.total_requests,
                        "hit_rate": metrics.hit_rate,
                        "cache_size": len(self._caches.get(cache_name, [])),
                        "last_reset_time": metrics.last_reset_time,
                    }
                return {"error": f"Cache '{cache_name}' not found"}
            # Return all cache metrics
            result = {
                "global": {
                    "hits": self._global_metrics.hits,
                    "misses": self._global_metrics.misses,
                    "evictions": self._global_metrics.evictions,
                    "total_requests": self._global_metrics.total_requests,
                    "hit_rate": self._global_metrics.hit_rate,
                    "last_reset_time": self._global_metrics.last_reset_time,
                }
            }

            for name, metrics in self._metrics.items():
                result[name] = {
                    "hits": metrics.hits,
                    "misses": metrics.misses,
                    "evictions": metrics.evictions,
                    "total_requests": metrics.total_requests,
                    "hit_rate": metrics.hit_rate,
                    "cache_size": len(self._caches.get(name, [])),
                    "last_reset_time": metrics.last_reset_time,
                }

            return result

    def reset_metrics(self, cache_name: str | None = None) -> None:
        """Reset metrics for a specific cache or all caches."""
        current_time = time.time()

        with self._lock:
            if cache_name:
                if cache_name in self._metrics:
                    self._metrics[cache_name] = CacheMetrics()
                    self._metrics[cache_name].last_reset_time = current_time
                    logger.info(f"Reset metrics for cache '{cache_name}'")
            else:
                # Reset all metrics
                for name in self._metrics:
                    self._metrics[name] = CacheMetrics()
                    self._metrics[name].last_reset_time = current_time

                self._global_metrics = CacheMetrics()
                self._global_metrics.last_reset_time = current_time
                logger.info("Reset all cache metrics")

    def cleanup_expired_caches(self) -> None:
        """Clean up expired cache entries."""
        current_time = time.time()

        # Only run cleanup if enough time has passed
        if current_time - self._last_cleanup < self._cleanup_interval:
            return

        with self._lock:
            for name, cache in self._caches.items():
                # TTL caches handle expiration automatically
                if isinstance(cache, TTLCache):
                    # No manual cleanup needed for TTLCache
                    continue
                if isinstance(cache, LRUCache):
                    # LRU cache doesn't have built-in expiration
                    # Could implement size-based cleanup if needed
                    pass

            self._last_cleanup = current_time

    def clear_cache(self, cache_name: str) -> None:
        """Clear a specific cache."""
        with self._lock:
            if cache_name in self._caches:
                cache = self._caches[cache_name]
                if hasattr(cache, "clear"):
                    cache.clear()
                logger.info(f"Cleared cache '{cache_name}'")

    def clear_all_caches(self) -> None:
        """Clear all caches."""
        with self._lock:
            for name, cache in self._metrics.items():
                if hasattr(cache, "clear"):
                    cache.clear()
                logger.info(f"Cleared cache '{name}'")

            logger.info("Cleared all caches")

    def get_cache_info(self) -> dict[str, Any]:
        """Get information about all caches."""
        with self._lock:
            info = {
                "total_caches": len(self._metrics),
                "global_metrics": self.get_metrics(),
                "cache_details": {},
            }

            for name, cache in self._caches.items():
                cache_info = {
                    "type": type(cache).__name__,
                    "size": len(cache) if hasattr(cache, "__len__") else "unknown",
                    "max_size": getattr(cache, "maxsize", "unknown"),
                    "ttl": getattr(cache, "ttl", "unknown"),
                }

                if name in self._metrics:
                    cache_info["metrics"] = self.get_metrics(name)

                info["cache_details"][name] = cache_info

            return info


# Global cache manager instance
cache_manager = CacheManager()


def create_ttl_cache(name: str, max_size: int = 1000, ttl: int = 3600) -> TTLCache:
    """Convenience function to create a TTL cache."""
    config = CacheConfig(max_size=max_size, ttl=ttl)
    return cache_manager.create_ttl_cache(name, config)


def create_lru_cache(name: str, max_size: int = 1000) -> LRUCache:
    """Convenience function to create an LRU cache."""
    config = CacheConfig(max_size=max_size)
    return cache_manager.create_lru_cache(name, config)


def get_cache_metrics(cache_name: str | None = None) -> dict[str, Any]:
    """Convenience function to get cache metrics."""
    return cache_manager.get_metrics(cache_name)


def reset_cache_metrics(cache_name: str | None = None) -> None:
    """Convenience function to reset cache metrics."""
    cache_manager.reset_metrics(cache_name)


def clear_cache(cache_name: str) -> None:
    """Convenience function to clear a cache."""
    cache_manager.clear_cache(cache_name)


def clear_all_caches() -> None:
    """Convenience function to clear all caches."""
    cache_manager.clear_all_caches()


# Cache decorator factory
def cached(ttl: int = 3600, max_size: int = 1000, cache_name: str | None = None):
    """Decorator factory for caching function results."""

    def decorator(func):
        cache_name = cache_name or f"function_{func.__name__}"
        cache = create_ttl_cache(cache_name, max_size=max_size, ttl=ttl)

        def wrapper(*args, **kwargs):
            # Create cache key from args and kwargs
            try:
                # Simple key generation - in production, use a more robust method
                key = str(hash((args, tuple(sorted(kwargs.items())))))
            except TypeError:
                # Fallback for unhashable arguments
                key = str(args) + str(sorted(kwargs.items()))

            # Check cache
            try:
                result = cache[key]
                cache_manager.record_hit(cache_name)
                return result
            except KeyError:
                cache_manager.record_miss(cache_name)
                result = func(*args, **kwargs)
                cache[key] = result
                return result

        wrapper.cache = cache
        wrapper.cache_name = cache_name
        wrapper.cache_manager = cache_manager
        return wrapper

    return decorator
