"""Configuration management for caching backends."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from .redis_cache import RedisConfig
from .types import CacheConfig, DataClassification


logger = logging.getLogger(__name__)


@dataclass
class CacheBackendConfig:
    """Configuration for cache backend selection and settings."""

    backend_type: str = "memory"  # "memory", "redis", "hybrid"
    redis_config: RedisConfig | None = None
    fallback_config: CacheConfig | None = None

    @classmethod
    def from_environment(cls) -> CacheBackendConfig:
        """Create configuration from environment variables."""
        backend_type = os.getenv("CACHE_BACKEND", "memory").lower()

        # Redis configuration from environment
        redis_config = None
        if backend_type in ("redis", "hybrid"):
            redis_config = RedisConfig(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                db=int(os.getenv("REDIS_DB", "0")),
                password=os.getenv("REDIS_PASSWORD"),
                socket_timeout=int(os.getenv("REDIS_SOCKET_TIMEOUT", "5")),
                socket_connect_timeout=int(os.getenv("REDIS_CONNECT_TIMEOUT", "5")),
                retry_on_timeout=os.getenv("REDIS_RETRY_ON_TIMEOUT", "true").lower()
                == "true",
                health_check_interval=int(
                    os.getenv("REDIS_HEALTH_CHECK_INTERVAL", "30")
                ),
                max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "10")),
            )

        # Fallback cache configuration
        fallback_config = CacheConfig(
            max_size=int(os.getenv("CACHE_FALLBACK_MAX_SIZE", "1000")),
            ttl=int(os.getenv("CACHE_FALLBACK_TTL", "3600")),
            cleanup_interval=int(os.getenv("CACHE_CLEANUP_INTERVAL", "300")),
            enable_metrics=os.getenv("CACHE_ENABLE_METRICS", "true").lower() == "true",
        )

        return cls(
            backend_type=backend_type,
            redis_config=redis_config,
            fallback_config=fallback_config,
        )


def get_cache_backend_config() -> CacheBackendConfig:
    """Get cache backend configuration from environment."""
    config = CacheBackendConfig.from_environment()

    logger.info(f"Cache backend: {config.backend_type}")
    if config.redis_config:
        logger.info(
            f"Redis configured: {config.redis_config.host}:{config.redis_config.port}"
        )
    if config.fallback_config:
        logger.info(
            f"Fallback cache: max_size={config.fallback_config.max_size}, ttl={config.fallback_config.ttl}s"
        )

    return config


def is_redis_enabled() -> bool:
    """Check if Redis caching is enabled."""
    backend = os.getenv("CACHE_BACKEND", "memory").lower()
    return backend in ("redis", "hybrid")


def get_redis_url() -> str:
    """Get Redis URL from environment variables."""
    host = os.getenv("REDIS_HOST", "localhost")
    port = os.getenv("REDIS_PORT", "6379")
    db = os.getenv("REDIS_DB", "0")
    password = os.getenv("REDIS_PASSWORD")

    if password:
        return f"redis://:{password}@{host}:{port}/{db}"
    return f"redis://{host}:{port}/{db}"


def load_config_from_env() -> CacheConfig:
    """Load CacheConfig from environment variables."""
    # Load retention days from environment
    retention_days = {}
    for classification in ["PUBLIC", "INTERNAL", "SENSITIVE", "CONFIDENTIAL"]:
        env_key = f"CACHE_RETENTION_DAYS_{classification}"
        days_str = os.getenv(env_key)
        if days_str:
            try:
                retention_days[DataClassification(classification.lower())] = int(
                    days_str
                )
            except ValueError:
                logger.warning(
                    f"Invalid retention days for {classification}: {days_str}"
                )

    return CacheConfig(
        max_size=int(os.getenv("CACHE_MAX_SIZE", "1000")),
        ttl=int(os.getenv("CACHE_TTL", "3600")),
        cleanup_interval=int(os.getenv("CACHE_CLEANUP_INTERVAL", "300")),
        enable_metrics=os.getenv("CACHE_ENABLE_METRICS", "true").lower() == "true",
        # Security settings
        encryption_enabled=os.getenv("CACHE_ENCRYPTION_ENABLED", "true").lower()
        == "true",
        audit_enabled=os.getenv("CACHE_AUDIT_ENABLED", "true").lower() == "true",
        access_control_enabled=os.getenv("CACHE_ACCESS_CONTROL_ENABLED", "true").lower()
        == "true",
        gdpr_compliance_enabled=os.getenv(
            "CACHE_GDPR_COMPLIANCE_ENABLED", "true"
        ).lower()
        == "true",
        retention_enabled=os.getenv("CACHE_RETENTION_ENABLED", "true").lower()
        == "true",
        encryption_key=os.getenv("CACHE_ENCRYPTION_KEY"),
        audit_max_entries=int(os.getenv("CACHE_AUDIT_MAX_ENTRIES", "10000")),
        audit_retention_days=int(os.getenv("CACHE_AUDIT_RETENTION_DAYS", "90")),
        retention_days=retention_days if retention_days else None,
    )


def validate_cache_config() -> bool:
    """Validate cache configuration."""
    backend = os.getenv("CACHE_BACKEND", "memory").lower()

    if backend not in ("memory", "redis", "hybrid"):
        logger.error(
            f"Invalid cache backend: {backend}. Must be 'memory', 'redis', or 'hybrid'"
        )
        return False

    if backend in ("redis", "hybrid"):
        # Check Redis configuration
        if not os.getenv("REDIS_HOST"):
            logger.warning("REDIS_HOST not set, using default 'localhost'")

        try:
            port = int(os.getenv("REDIS_PORT", "6379"))
            if port < 1 or port > 65535:
                logger.error(f"Invalid Redis port: {port}")
                return False
        except ValueError:
            logger.error(f"Invalid Redis port format: {os.getenv('REDIS_PORT')}")
            return False

        try:
            db = int(os.getenv("REDIS_DB", "0"))
            if db < 0 or db > 15:
                logger.error(f"Invalid Redis DB: {db}. Must be 0-15")
                return False
        except ValueError:
            logger.error(f"Invalid Redis DB format: {os.getenv('REDIS_DB')}")
            return False

    # Validate cache sizes and TTLs
    try:
        max_size = int(os.getenv("CACHE_FALLBACK_MAX_SIZE", "1000"))
        if max_size < 1:
            logger.error(f"Invalid cache max_size: {max_size}")
            return False
    except ValueError:
        logger.error(
            f"Invalid cache max_size format: {os.getenv('CACHE_FALLBACK_MAX_SIZE')}"
        )
        return False

    try:
        ttl = int(os.getenv("CACHE_FALLBACK_TTL", "3600"))
        if ttl < 1:
            logger.error(f"Invalid cache TTL: {ttl}")
            return False
    except ValueError:
        logger.error(f"Invalid cache TTL format: {os.getenv('CACHE_FALLBACK_TTL')}")
        return False

    logger.info("Cache configuration validation passed")
    return True
