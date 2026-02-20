"""Cache management module for MCP Gateway."""

from .cache_manager import (
    CacheManager,
    CacheConfig,
    CacheMetrics,
    cache_manager,
    create_ttl_cache,
    create_lru_cache,
    get_cache_metrics,
    reset_cache_metrics,
    clear_cache,
    clear_all_caches,
    cached,
)

from .redis_cache import (
    RedisCache,
    RedisConfig,
    create_redis_cache,
)

from .invalidation import (
    TagInvalidationManager,
    EventInvalidationManager,
    DependencyInvalidationManager,
    AdvancedInvalidationManager,
    InvalidationStrategy,
    invalidate_by_tags,
    invalidate_by_event,
    invalidate_by_dependency,
    get_advanced_invalidation_manager,
)

from .config import (
    CacheBackendConfig,
    get_cache_backend_config,
    is_redis_enabled,
    get_redis_url,
    validate_cache_config,
)

from .dashboard import (
    CachePerformanceDashboard,
    CachePerformanceCollector,
    CacheAlertManager,
    get_cache_performance_dashboard,
    start_dashboard_collection,
    stop_dashboard_collection,
    get_dashboard_data,
    get_dashboard_trends,
    get_alert_summary,
)

__all__ = [
    "CacheManager",
    "CacheConfig",
    "CacheMetrics",
    "cache_manager",
    "create_ttl_cache",
    "create_lru_cache",
    "get_cache_metrics",
    "reset_cache_metrics",
    "clear_cache",
    "clear_all_caches",
    "cached",
    "RedisCache",
    "RedisConfig",
    "create_redis_cache",
    "TagInvalidationManager",
    "EventInvalidationManager",
    "DependencyInvalidationManager",
    "AdvancedInvalidationManager",
    "InvalidationStrategy",
    "invalidate_by_tags",
    "invalidate_by_event",
    "invalidate_by_dependency",
    "get_advanced_invalidation_manager",
    "CacheBackendConfig",
    "get_cache_backend_config",
    "is_redis_enabled",
    "get_redis_url",
    "validate_cache_config",
    "CachePerformanceDashboard",
    "CachePerformanceCollector",
    "CacheAlertManager",
    "get_cache_performance_dashboard",
    "start_dashboard_collection",
    "stop_dashboard_collection",
    "get_dashboard_data",
    "get_dashboard_trends",
    "get_alert_summary",
]
