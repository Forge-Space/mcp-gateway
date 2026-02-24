"""Advanced cache invalidation strategies for MCP Gateway."""

from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .cache_manager import CacheManager

logger = logging.getLogger(__name__)


class InvalidationStrategy(Enum):
    """Cache invalidation strategies."""

    TTL = "ttl"  # Time-based expiration
    TAG = "tag"  # Tag-based invalidation
    EVENT = "event"  # Event-driven invalidation
    MANUAL = "manual"  # Manual invalidation
    DEPENDENCY = "dependency"  # Dependency-based invalidation


@dataclass
class CacheTag:
    """Cache tag for grouping related cache entries."""

    name: str
    description: str | None = None
    created_at: float = field(default_factory=time.time)
    cache_keys: set[str] = field(default_factory=set)
    invalidation_count: int = 0


@dataclass
class InvalidationEvent:
    """Cache invalidation event."""

    event_type: str
    cache_keys: set[str]
    tags: set[str]
    timestamp: float = field(default_factory=time.time)
    source: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheDependency:
    """Cache dependency relationship."""

    cache_key: str
    depends_on: set[str]
    strategy: InvalidationStrategy = InvalidationStrategy.DEPENDENCY


class TagInvalidationManager:
    """Manages tag-based cache invalidation."""

    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self._tags: dict[str, CacheTag] = {}
        self._key_to_tags: dict[str, set[str]] = defaultdict(set)
        self._lock = threading.RLock()

    def create_tag(self, name: str, description: str | None = None) -> CacheTag:
        """Create a new cache tag."""
        with self._lock:
            if name in self._tags:
                logger.warning(f"Tag '{name}' already exists")
                return self._tags[name]

            tag = CacheTag(name=name, description=description)
            self._tags[name] = tag
            logger.info(f"Created cache tag: {name}")
            return tag

    def add_to_tag(self, tag_name: str, cache_key: str) -> bool:
        """Add a cache key to a tag."""
        with self._lock:
            if tag_name not in self._tags:
                self.create_tag(tag_name)

            self._tags[tag_name].cache_keys.add(cache_key)
            self._key_to_tags[cache_key].add(tag_name)
            logger.debug(f"Added cache key '{cache_key}' to tag '{tag_name}'")
            return True

    def invalidate_tag(self, tag_name: str, reason: str | None = None) -> int:
        """Invalidate all cache entries associated with a tag."""
        with self._lock:
            if tag_name not in self._tags:
                logger.warning(f"Tag '{tag_name}' not found for invalidation")
                return 0

            tag = self._tags[tag_name]
            invalidated_count = 0

            for cache_key in list(tag.cache_keys):
                cache = self.cache_manager.get_cache(
                    self._extract_cache_name(cache_key)
                )
                if cache and hasattr(cache, "delete"):
                    try:
                        cache.delete(cache_key)
                        invalidated_count += 1

                        # Remove from other tags
                        for other_tag in self._key_to_tags[cache_key]:
                            if other_tag != tag_name:
                                self._tags[other_tag].cache_keys.discard(cache_key)

                        # Clean up tracking
                        self._key_to_tags.pop(cache_key, None)

                    except Exception as e:
                        logger.error(
                            f"Failed to invalidate cache key '{cache_key}': {e}"
                        )

            tag.cache_keys.clear()
            tag.invalidation_count += 1

            logger.info(
                f"Invalidated tag '{tag_name}': {invalidated_count} cache entries"
            )
            if reason:
                logger.info(f"Invalidation reason: {reason}")

            return invalidated_count

    def invalidate_multiple_tags(
        self, tag_names: list[str], reason: str | None = None
    ) -> int:
        """Invalidate multiple tags."""
        total_invalidated = 0
        for tag_name in tag_names:
            total_invalidated += self.invalidate_tag(tag_name, reason)
        return total_invalidated

    def get_tag_info(self, tag_name: str) -> CacheTag | None:
        """Get information about a tag."""
        return self._tags.get(tag_name)

    def list_tags(self) -> list[CacheTag]:
        """List all tags."""
        return list(self._tags.values())

    def get_tags_for_key(self, cache_key: str) -> set[str]:
        """Get all tags associated with a cache key."""
        return self._key_to_tags.get(cache_key, set())

    def _extract_cache_name(self, cache_key: str) -> str:
        """Extract cache name from cache key."""
        # Simple extraction - assumes format like "cache_name:key"
        if ":" in cache_key:
            return cache_key.split(":", 1)[0]
        return "default"


class EventInvalidationManager:
    """Manages event-driven cache invalidation."""

    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self._event_handlers: dict[str, list[Callable]] = defaultdict(list)
        self._event_history: list[InvalidationEvent] = []
        self._lock = threading.RLock()
        self._max_history = 1000

    def register_handler(
        self, event_type: str, handler: Callable[[InvalidationEvent], None]
    ) -> None:
        """Register an event handler."""
        with self._lock:
            self._event_handlers[event_type].append(handler)
            logger.info(f"Registered handler for event type: {event_type}")

    def trigger_invalidation(
        self,
        event_type: str,
        cache_keys: set[str],
        tags: set[str] | None = None,
        source: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """Trigger cache invalidation event."""
        event = InvalidationEvent(
            event_type=event_type,
            cache_keys=cache_keys,
            tags=tags or set(),
            source=source,
            metadata=metadata or {},
        )

        with self._lock:
            # Store in history
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)

            # Execute handlers
            invalidated_count = 0
            for handler in self._event_handlers.get(event_type, []):
                try:
                    handler(event)
                    invalidated_count += len(event.cache_keys)
                except Exception as e:
                    logger.error(f"Event handler failed for {event_type}: {e}")

            # Perform actual invalidation
            for cache_key in event.cache_keys:
                cache = self.cache_manager.get_cache(
                    self._extract_cache_name(cache_key)
                )
                if cache and hasattr(cache, "delete"):
                    try:
                        cache.delete(cache_key)
                    except Exception as e:
                        logger.error(
                            f"Failed to invalidate cache key '{cache_key}': {e}"
                        )

            logger.info(
                f"Triggered invalidation event '{event_type}': {len(event.cache_keys)} keys"
            )
            return len(event.cache_keys)

    def get_event_history(
        self, event_type: str | None = None, limit: int = 100
    ) -> list[InvalidationEvent]:
        """Get event history."""
        with self._lock:
            history = self._event_history
            if event_type:
                history = [e for e in history if e.event_type == event_type]
            return history[-limit:]

    def _extract_cache_name(self, cache_key: str) -> str:
        """Extract cache name from cache key."""
        if ":" in cache_key:
            return cache_key.split(":", 1)[0]
        return "default"


class DependencyInvalidationManager:
    """Manages dependency-based cache invalidation."""

    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self._dependencies: dict[str, CacheDependency] = {}
        self._reverse_deps: dict[str, set[str]] = defaultdict(set)
        self._lock = threading.RLock()

    def add_dependency(self, cache_key: str, depends_on: set[str]) -> None:
        """Add cache dependency."""
        with self._lock:
            dependency = CacheDependency(
                cache_key=cache_key, depends_on=set(depends_on)
            )
            self._dependencies[cache_key] = dependency

            # Update reverse dependencies
            for dep_key in depends_on:
                self._reverse_deps[dep_key].add(cache_key)

            logger.debug(f"Added dependency: {cache_key} depends on {depends_on}")

    def invalidate_dependents(self, changed_key: str, reason: str | None = None) -> int:
        """Invalidate all cache entries that depend on the changed key."""
        with self._lock:
            dependents = self._reverse_deps.get(changed_key, set())
            invalidated_count = 0

            for dependent_key in dependents:
                cache = self.cache_manager.get_cache(
                    self._extract_cache_name(dependent_key)
                )
                if cache and hasattr(cache, "delete"):
                    try:
                        cache.delete(dependent_key)
                        invalidated_count += 1
                        logger.debug(
                            f"Invalidated dependent cache key: {dependent_key}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to invalidate dependent '{dependent_key}': {e}"
                        )

            if invalidated_count > 0:
                logger.info(
                    f"Invalidated {invalidated_count} dependents of '{changed_key}'"
                )
                if reason:
                    logger.info(f"Dependency invalidation reason: {reason}")

            return invalidated_count

    def get_dependencies(self, cache_key: str) -> CacheDependency | None:
        """Get dependencies for a cache key."""
        return self._dependencies.get(cache_key)

    def get_dependents(self, cache_key: str) -> set[str]:
        """Get all cache keys that depend on the given key."""
        return self._reverse_deps.get(cache_key, set())

    def _extract_cache_name(self, cache_key: str) -> str:
        """Extract cache name from cache key."""
        if ":" in cache_key:
            return cache_key.split(":", 1)[0]
        return "default"


class AdvancedInvalidationManager:
    """Advanced cache invalidation manager combining multiple strategies."""

    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.tag_manager = TagInvalidationManager(cache_manager)
        self.event_manager = EventInvalidationManager(cache_manager)
        self.dependency_manager = DependencyInvalidationManager(cache_manager)

        # Register default event handlers
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Register default event handlers."""

        # Tag-based invalidation handler
        def tag_invalidation_handler(event: InvalidationEvent) -> None:
            for tag in event.tags:
                self.tag_manager.invalidate_tag(tag, f"Event: {event.event_type}")

        self.event_manager.register_handler(
            "tag_invalidation", tag_invalidation_handler
        )

        # Dependency invalidation handler
        def dependency_invalidation_handler(event: InvalidationEvent) -> None:
            for cache_key in event.cache_keys:
                self.dependency_manager.invalidate_dependents(
                    cache_key, f"Event: {event.event_type}"
                )

        self.event_manager.register_handler(
            "dependency_invalidation", dependency_invalidation_handler
        )

    def invalidate_by_tags(self, tags: list[str], reason: str | None = None) -> int:
        """Invalidate cache entries by tags."""
        return self.tag_manager.invalidate_multiple_tags(tags, reason)

    def invalidate_by_event(
        self,
        event_type: str,
        cache_keys: set[str],
        tags: set[str] | None = None,
        source: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """Invalidate cache entries by event."""
        return self.event_manager.trigger_invalidation(
            event_type, cache_keys, tags, source, metadata
        )

    def invalidate_by_dependency(
        self, changed_key: str, reason: str | None = None
    ) -> int:
        """Invalidate cache entries by dependency."""
        return self.dependency_manager.invalidate_dependents(changed_key, reason)

    def create_tagged_cache(
        self,
        cache_name: str,
        key: str,
        value: Any,
        tags: set[str],
        ttl: int | None = None,
    ) -> bool:
        """Create a cache entry with tags."""
        cache = self.cache_manager.get_cache(cache_name)
        if not cache:
            logger.error(f"Cache '{cache_name}' not found")
            return False

        # Store in cache
        full_key = f"{cache_name}:{key}"
        if hasattr(cache, "set"):
            cache.set(full_key, value, ttl)

        # Add to tags
        for tag in tags:
            self.tag_manager.add_to_tag(tag, full_key)

        return True

    def add_dependency(self, cache_key: str, depends_on: set[str]) -> None:
        """Add cache dependency."""
        full_key = cache_key if ":" in cache_key else f"default:{cache_key}"
        self.dependency_manager.add_dependency(full_key, depends_on)

    def get_invalidation_summary(self) -> dict[str, Any]:
        """Get summary of invalidation statistics."""
        return {
            "tags": {
                "total": len(self.tag_manager.list_tags()),
                "invalidations": sum(
                    tag.invalidation_count for tag in self.tag_manager.list_tags()
                ),
            },
            "events": {
                "total": len(self.event_manager.get_event_history()),
                "types": list(
                    set(e.event_type for e in self.event_manager.get_event_history())
                ),
            },
            "dependencies": {
                "total": len(self.dependency_manager._dependencies),
                "reverse_deps": len(self.dependency_manager._reverse_deps),
            },
        }


# Global instance
advanced_invalidation_manager: AdvancedInvalidationManager | None = None


def get_advanced_invalidation_manager() -> AdvancedInvalidationManager:
    """Get the global advanced invalidation manager."""
    global advanced_invalidation_manager
    if advanced_invalidation_manager is None:
        from .cache_manager import cache_manager

        advanced_invalidation_manager = AdvancedInvalidationManager(cache_manager)
    return advanced_invalidation_manager


def invalidate_by_tags(tags: list[str], reason: str | None = None) -> int:
    """Convenience function to invalidate by tags."""
    return get_advanced_invalidation_manager().invalidate_by_tags(tags, reason)


def invalidate_by_event(
    event_type: str,
    cache_keys: set[str],
    tags: set[str] | None = None,
    source: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> int:
    """Convenience function to invalidate by event."""
    return get_advanced_invalidation_manager().invalidate_by_event(
        event_type, cache_keys, tags, source, metadata
    )


def invalidate_by_dependency(changed_key: str, reason: str | None = None) -> int:
    """Convenience function to invalidate by dependency."""
    return get_advanced_invalidation_manager().invalidate_by_dependency(
        changed_key, reason
    )
