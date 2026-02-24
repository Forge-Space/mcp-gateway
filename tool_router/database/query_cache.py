"""Database query caching utilities for MCP Gateway."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass
from typing import Any

from ..cache import cache_manager, create_ttl_cache, get_cache_metrics

logger = logging.getLogger(__name__)


@dataclass
class QueryCacheConfig:
    """Configuration for database query caching."""

    enabled: bool = True
    default_ttl: int = 300  # 5 minutes
    max_size: int = 1000
    cache_reads: bool = True
    cache_writes: bool = False  # Don't cache write operations by default
    cache_key_prefix: str = "db_query"


class DatabaseQueryCache:
    """Cache for frequently accessed database queries."""

    def __init__(self, config: QueryCacheConfig | None = None):
        self.config = config or QueryCacheConfig()
        self._cache = None

        if self.config.enabled:
            self._cache = create_ttl_cache(
                f"{self.config.cache_key_prefix}_cache",
                max_size=self.config.max_size,
                ttl=self.config.default_ttl,
            )
            logger.info(
                f"Database query cache enabled with TTL={self.config.default_ttl}s, max_size={self.config.max_size}"
            )
        else:
            logger.info("Database query cache disabled")

    def _generate_cache_key(self, query: str, params: tuple | None = None, table: str | None = None) -> str:
        """Generate a cache key for a database query."""
        # Create a deterministic key from query and parameters
        key_data = {
            "query": query.strip().lower(),
            "params": params if params else (),
            "table": table if table else None,
        }

        # Use JSON serialization for consistent key generation
        key_json = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.sha256(key_json.encode()).hexdigest()

        return f"{self.config.cache_key_prefix}:{key_hash}"

    def get(self, query: str, params: tuple | None = None, table: str | None = None) -> Any | None:
        """Get cached query result."""
        if not self.config.enabled or not self.config.cache_reads or not self._cache:
            return None

        cache_key = self._generate_cache_key(query, params, table)

        try:
            result = self._cache[cache_key]
            cache_manager.record_hit(f"{self.config.cache_key_prefix}_cache")
            logger.debug(f"Cache hit for query: {query[:50]}...")
            return result
        except KeyError:
            cache_manager.record_miss(f"{self.config.cache_key_prefix}_cache")
            logger.debug(f"Cache miss for query: {query[:50]}...")
            return None

    def set(
        self,
        query: str,
        result: Any,
        params: tuple | None = None,
        table: str | None = None,
        ttl: int | None = None,
    ) -> None:
        """Cache a query result."""
        if not self.config.enabled or not self.config.cache_reads or not self._cache:
            return

        # Don't cache None results or empty lists
        if result is None or (isinstance(result, list) and len(result) == 0):
            return

        cache_key = self._generate_cache_key(query, params, table)

        try:
            self._cache[cache_key] = result
            logger.debug(f"Cached result for query: {query[:50]}...")
        except Exception as e:
            logger.warning(f"Failed to cache query result: {e}")

    def invalidate(self, query: str, params: tuple | None = None, table: str | None = None) -> None:
        """Invalidate a specific cached query."""
        if not self.config.enabled or not self._cache:
            return

        cache_key = self._generate_cache_key(query, params, table)
        self._cache.pop(cache_key, None)
        logger.debug(f"Invalidated cache for query: {query[:50]}...")

    def invalidate_table(self, table: str) -> None:
        """Invalidate all cached queries for a specific table."""
        if not self.config.enabled or not self._cache:
            return

        # This is a simple implementation - in production, you might want to track
        # cache keys by table for more efficient invalidation
        keys_to_remove = []
        for key in self._cache.keys():
            if key.startswith(f"{self.config.cache_key_prefix}:"):
                # For now, we'll clear all cache entries when a table is invalidated
                # In a more sophisticated implementation, we could track table dependencies
                keys_to_remove.append(key)

        for key in keys_to_remove:
            self._cache.pop(key, None)

        if keys_to_remove:
            logger.info(f"Invalidated {len(keys_to_remove)} cache entries for table: {table}")

    def invalidate_all(self) -> None:
        """Invalidate all cached queries."""
        if not self.config.enabled or not self._cache:
            return

        cache_size = len(self._cache)
        self._cache.clear()
        logger.info(f"Invalidated {cache_size} cache entries")

    def get_metrics(self) -> dict[str, Any]:
        """Get cache performance metrics."""
        if not self.config.enabled:
            return {"enabled": False}

        cache_metrics = get_cache_metrics(f"{self.config.cache_key_prefix}_cache")

        return {
            "enabled": True,
            "config": asdict(self.config),
            "cache_size": len(self._cache) if self._cache else 0,
            "metrics": cache_metrics,
        }

    def cleanup(self) -> None:
        """Clean up expired cache entries."""
        if self._cache and hasattr(self._cache, "expire"):
            # TTLCache handles expiration automatically
            pass


# Global query cache instance
query_cache = DatabaseQueryCache()


def get_query_cache() -> DatabaseQueryCache:
    """Get the global query cache instance."""
    return query_cache


def cached_query(ttl: int | None = None, table: str | None = None):
    """Decorator for caching database query functions."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract query and params from function arguments
            # This is a simple implementation - in production, you might want
            # more sophisticated argument parsing
            query = kwargs.get("query") or (args[0] if args else None)
            params = kwargs.get("params") or (args[1] if len(args) > 1 else None)

            if not query:
                return func(*args, **kwargs)

            # Try to get from cache
            cached_result = query_cache.get(query, params, table)
            if cached_result is not None:
                return cached_result

            # Execute the query
            result = func(*args, **kwargs)

            # Cache the result
            query_cache.set(query, result, params, table, ttl)

            return result

        wrapper.cache = query_cache
        return wrapper

    return decorator


class QueryCacheMiddleware:
    """Middleware for automatic query caching in database operations."""

    def __init__(self, cache: DatabaseQueryCache | None = None):
        self.cache = cache or query_cache

    def before_execute(self, query: str, params: tuple | None = None) -> Any | None:
        """Called before query execution - check cache."""
        return self.cache.get(query, params)

    def after_execute(
        self,
        query: str,
        result: Any,
        params: tuple | None = None,
        ttl: int | None = None,
    ) -> None:
        """Called after query execution - cache result."""
        self.cache.set(query, result, params, ttl=ttl)

    def on_write_operation(self, table: str) -> None:
        """Called on write operations - invalidate relevant cache entries."""
        self.cache.invalidate_table(table)
