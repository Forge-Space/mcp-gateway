"""Cache management and security module for MCP Gateway.

This module provides comprehensive cache management and security features:
- Basic cache operations with TTL and LRU support
- Redis integration for distributed caching
- Cache invalidation strategies
- Performance monitoring and dashboards
- Security features (encryption, access control, GDPR compliance)
- Retention policy management
- Audit trail functionality
- RESTful API endpoints

Security Components:
- CacheEncryption: Fernet-based encryption for sensitive data
- AccessControlManager: Role-based access control
- GDPRComplianceManager: GDPR compliance features
- RetentionPolicyManager: Data retention and lifecycle
- CacheSecurityManager: Integrated security manager
"""

# Basic cache management
from .cache_manager import (
    CacheConfig,
    CacheManager,
    CacheMetrics,
    cache_manager,
    cached,
    clear_all_caches,
    clear_cache,
    create_lru_cache,
    create_ttl_cache,
    get_cache_metrics,
    reset_cache_metrics,
)

# Configuration and utilities
from .config import (
    CacheBackendConfig,
    get_cache_backend_config,
    get_redis_url,
    is_redis_enabled,
    validate_cache_config,
)

# Performance monitoring
from .dashboard import (
    CacheAlertManager,
    CachePerformanceCollector,
    CachePerformanceDashboard,
    get_alert_summary,
    get_cache_performance_dashboard,
    get_dashboard_data,
    get_dashboard_trends,
    start_dashboard_collection,
    stop_dashboard_collection,
)

# Cache invalidation
from .invalidation import (
    AdvancedInvalidationManager,
    DependencyInvalidationManager,
    EventInvalidationManager,
    InvalidationStrategy,
    TagInvalidationManager,
    get_advanced_invalidation_manager,
    invalidate_by_dependency,
    invalidate_by_event,
    invalidate_by_tags,
)

# Redis cache integration
from .redis_cache import (
    RedisCache,
    RedisConfig,
    create_redis_cache,
)


# Security and compliance features
try:
    from .security import (
        AccessControlManager,
        CacheEncryption,
        CacheSecurityManager,
        GDPRComplianceManager,
        RetentionPolicyManager,
    )

    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False

try:
    from .compliance import (
        ComplianceManager,
        ComplianceReporter,
        GDPRComplianceHandler,
    )

    COMPLIANCE_AVAILABLE = True
except ImportError:
    COMPLIANCE_AVAILABLE = False

try:
    from .retention import (
        LifecycleManager,
        RetentionAuditor,
        RetentionScheduler,
    )
    from .retention import (
        RetentionPolicyManager as RetentionPolicyManagerMain,
    )

    RETENTION_AVAILABLE = True
except ImportError:
    RETENTION_AVAILABLE = False

try:
    from .api import (
        CacheSecurityAPI,
        create_cache_security_api,
        get_cache_security_api,
        shutdown_cache_security_api,
    )

    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False

# Version information
__version__ = "2.4.0"
__author__ = "MCP Gateway Team"
__license__ = "MIT"

# Feature availability flags
__security_features_available__ = SECURITY_AVAILABLE
__compliance_features_available__ = COMPLIANCE_AVAILABLE
__retention_available__ = RETENTION_AVAILABLE
__api_features_available__ = API_AVAILABLE

# Main exports - basic cache management (always available)
__all__ = [
    "AdvancedInvalidationManager",
    "CacheAlertManager",
    "CacheBackendConfig",
    "CacheConfig",
    "CacheManager",
    "CacheMetrics",
    "CachePerformanceCollector",
    "CachePerformanceDashboard",
    "DependencyInvalidationManager",
    "EventInvalidationManager",
    "InvalidationStrategy",
    "RedisCache",
    "RedisConfig",
    "TagInvalidationManager",
    "cache_manager",
    "cached",
    "clear_all_caches",
    "clear_cache",
    "create_lru_cache",
    "create_redis_cache",
    "create_ttl_cache",
    "get_advanced_invalidation_manager",
    "get_alert_summary",
    "get_cache_backend_config",
    "get_cache_metrics",
    "get_cache_performance_dashboard",
    "get_dashboard_data",
    "get_dashboard_trends",
    "get_redis_url",
    "invalidate_by_dependency",
    "invalidate_by_event",
    "invalidate_by_tags",
    "is_redis_enabled",
    "reset_cache_metrics",
    "start_dashboard_collection",
    "stop_dashboard_collection",
    "validate_cache_config",
]

# Security exports (if available)
if SECURITY_AVAILABLE:
    __all__.extend(
        [
            "AccessControlManager",
            "CacheEncryption",
            "CacheSecurityManager",
            "GDPRComplianceManager",
            "RetentionPolicyManager",
        ]
    )

# Compliance exports (if available)
if COMPLIANCE_AVAILABLE:
    __all__.extend(
        [
            "ComplianceManager",
            "ComplianceReporter",
            "GDPRComplianceHandler",
        ]
    )

# Retention exports (if available)
if RETENTION_AVAILABLE:
    __all__.extend(
        [
            "LifecycleManager",
            "RetentionAuditor",
            "RetentionPolicyManagerMain",
            "RetentionScheduler",
        ]
    )

# API exports (if available)
if API_AVAILABLE:
    __all__.extend(
        [
            "CacheSecurityAPI",
            "create_cache_security_api",
            "get_cache_security_api",
            "shutdown_cache_security_api",
        ]
    )


# Convenience functions for feature availability
def has_security_features() -> bool:
    """Check if security features are available."""
    return __security_features_available__


def has_compliance_features() -> bool:
    """Check if compliance features are available."""
    return __compliance_available__


def has_retention_features() -> bool:
    """Check if retention features are available."""
    return __retention_available__


def has_api_features() -> bool:
    """Check if API features are available."""
    return __api_available__


def get_available_features() -> dict:
    """Get dictionary of available features."""
    return {
        "security": __security_features_available,
        "compliance": __compliance_available,
        "retention": __retention_available,
        "api": __api_available,
        "redis": is_redis_enabled(),
    }
