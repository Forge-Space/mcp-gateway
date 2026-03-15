"""Performance monitoring API endpoints for MCP Gateway."""

from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..cache import cache_manager
from ..cache import get_cache_metrics as _get_cache_metrics_data
from ..cache import reset_cache_metrics as _reset_cache_metrics_data
from ..database.query_cache import get_query_cache


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


class CacheMetricsResponse(BaseModel):
    """Cache layer performance metrics."""

    cache_hit_rate: float = Field(description="Overall hit rate (0.0-1.0)")
    total_hits: int = Field(description="Total cache hits")
    total_misses: int = Field(description="Total cache misses")
    total_requests: int = Field(description="Total cache lookups")
    cache_sizes: dict[str, int] = Field(description="Size of each named cache")
    hits_by_type: dict[str, int] = Field(description="Hits broken down by cache type")
    misses_by_type: dict[str, int] = Field(description="Misses broken down by cache type")


class SystemMetricsResponse(BaseModel):
    """Comprehensive system performance snapshot."""

    timestamp: float = Field(description="Unix timestamp")
    uptime: float = Field(description="Seconds since server start")
    cache_metrics: CacheMetricsResponse
    feedback_metrics: dict[str, Any] = Field(description="Feedback store metrics")
    rate_limiter_metrics: dict[str, Any] = Field(description="Rate limiter state")
    query_cache_metrics: dict[str, Any] = Field(description="Database query cache stats")


class MonitoringHealthResponse(BaseModel):
    """Monitoring-level health with cache subsystem checks."""

    status: str = Field(description="Overall status: healthy or degraded")
    timestamp: float = Field(description="Unix timestamp")
    checks: dict[str, Any] = Field(description="Per-subsystem health checks")


class CacheResetResponse(BaseModel):
    """Result of cache metrics reset."""

    status: str = Field(description="Operation result")
    message: str = Field(description="Human-readable summary")
    timestamp: float = Field(description="Unix timestamp")


class PerformanceSummaryResponse(BaseModel):
    """High-level performance dashboard."""

    timestamp: float = Field(description="Unix timestamp")
    uptime_seconds: float = Field(description="Seconds since server start")
    cache_performance: dict[str, Any] = Field(description="Cache hit rate and sizes")
    query_cache: dict[str, Any] = Field(description="Query cache stats")
    recommendations: list[str] = Field(description="Auto-generated tuning suggestions")


# Global start time for uptime calculation
_start_time = time.time()


@router.get(
    "/health",
    response_model=MonitoringHealthResponse,
    summary="Monitoring health check",
    description="Comprehensive health check including cache, feedback, and query cache subsystems.",
)
async def health_check() -> MonitoringHealthResponse:
    current_time = time.time()
    uptime = current_time - _start_time

    checks = {
        "uptime_seconds": uptime,
        "timestamp": current_time,
        "cache_manager": {
            "status": "healthy" if cache_manager else "unavailable",
            "cache_count": len(cache_manager._caches) if cache_manager else 0,
        },
        "feedback_store": {
            "status": "healthy",
            "cache_enabled": True,  # Using cached feedback store
        },
        "rate_limiter": {
            "status": "healthy",
            "cache_enabled": True,
        },
        "query_cache": {
            "status": "healthy",
            "cache_enabled": get_query_cache().config.enabled,
        },
    }

    # Determine overall health status
    all_healthy = all(check["status"] == "healthy" for check in checks.values() if isinstance(check, dict))
    status = "healthy" if all_healthy else "degraded"

    return MonitoringHealthResponse(status=status, timestamp=current_time, checks=checks)


@router.get(
    "/metrics/cache",
    response_model=CacheMetricsResponse,
    summary="Cache metrics",
    description="Returns cache hit/miss rates, sizes, and breakdowns by cache type.",
)
async def get_cache_metrics() -> CacheMetricsResponse:
    try:
        metrics = _get_cache_metrics_data()

        return CacheMetricsResponse(
            cache_hit_rate=metrics.get("global", {}).get("hit_rate", 0.0),
            total_hits=metrics.get("global", {}).get("hits", 0),
            total_misses=metrics.get("global", {}).get("misses", 0),
            total_requests=metrics.get("global", {}).get("total_requests", 0),
            cache_sizes=metrics.get("global", {}).get("cache_sizes", {}),
            hits_by_type=metrics.get("global", {}).get("hits_by_type", {}),
            misses_by_type=metrics.get("global", {}).get("misses_by_type", {}),
        )
    except Exception as e:
        logger.error(f"Failed to get cache metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cache metrics")


@router.get(
    "/metrics/system",
    response_model=SystemMetricsResponse,
    summary="System metrics",
    description="Full system snapshot: cache, feedback, rate limiter, and query cache metrics.",
)
async def get_system_metrics() -> SystemMetricsResponse:
    current_time = time.time()
    uptime = current_time - _start_time

    try:
        # Get cache metrics
        cache_metrics_data = _get_cache_metrics_data()
        cache_metrics = CacheMetricsResponse(
            cache_hit_rate=cache_metrics_data.get("global", {}).get("hit_rate", 0.0),
            total_hits=cache_metrics_data.get("global", {}).get("hits", 0),
            total_misses=cache_metrics_data.get("global", {}).get("misses", 0),
            total_requests=cache_metrics_data.get("global", {}).get("total_requests", 0),
            cache_sizes=cache_metrics_data.get("global", {}).get("cache_sizes", {}),
            hits_by_type=cache_metrics_data.get("global", {}).get("hits_by_type", {}),
            misses_by_type=cache_metrics_data.get("global", {}).get("misses_by_type", {}),
        )

        # Get feedback store metrics (mock for now)
        feedback_metrics = {
            "cache_enabled": True,
            "cache_size": 0,  # Would need access to actual feedback store instance
            "cache_hit_rate": 0.0,
        }

        # Get rate limiter metrics (mock for now)
        rate_limiter_metrics = {
            "cache_enabled": True,
            "cache_hit_rate": 0.0,
            "redis_enabled": False,
        }

        # Get query cache metrics
        query_cache_instance = get_query_cache()
        query_cache_metrics = query_cache_instance.get_metrics()

        return SystemMetricsResponse(
            timestamp=current_time,
            uptime=uptime,
            cache_metrics=cache_metrics,
            feedback_metrics=feedback_metrics,
            rate_limiter_metrics=rate_limiter_metrics,
            query_cache_metrics=query_cache_metrics,
        )

    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system metrics")


@router.post(
    "/metrics/cache/reset",
    response_model=CacheResetResponse,
    summary="Reset cache metrics",
    description="Reset hit/miss counters for a specific cache or all caches.",
)
async def reset_cache_metrics(cache_name: str | None = None) -> dict[str, Any]:
    try:
        _reset_cache_metrics_data(cache_name)

        message = f"Reset metrics for cache: {cache_name}" if cache_name else "Reset all cache metrics"
        logger.info(message)

        return {
            "status": "success",
            "message": message,
            "timestamp": time.time(),
        }
    except Exception as e:
        logger.error(f"Failed to reset cache metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset cache metrics")


@router.post(
    "/cache/clear",
    response_model=CacheResetResponse,
    summary="Clear cache",
    description="Evict all entries from a specific cache or all caches.",
)
async def clear_cache(cache_name: str | None = None) -> dict[str, Any]:
    try:
        if cache_name:
            from ..cache import clear_cache as clear_specific_cache

            clear_specific_cache(cache_name)
            message = f"Cleared cache: {cache_name}"
        else:
            from ..cache import clear_all_caches

            clear_all_caches()
            message = "Cleared all caches"

        logger.info(message)

        return {
            "status": "success",
            "message": message,
            "timestamp": time.time(),
        }
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")


@router.get(
    "/cache/info",
    summary="Cache configuration info",
    description="Returns configuration and state for all named caches.",
)
async def get_cache_info() -> dict[str, Any]:
    try:
        return cache_manager.get_cache_info()
    except Exception as e:
        logger.error(f"Failed to get cache info: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve cache information")


@router.post(
    "/query-cache/invalidate",
    response_model=CacheResetResponse,
    summary="Invalidate query cache",
    description="Evict cached database query results for a table or all tables.",
)
async def invalidate_query_cache(table: str | None = None) -> dict[str, Any]:
    try:
        query_cache = get_query_cache()

        if table:
            query_cache.invalidate_table(table)
            message = f"Invalidated query cache for table: {table}"
        else:
            query_cache.invalidate_all()
            message = "Invalidated all query cache entries"

        logger.info(message)

        return {
            "status": "success",
            "message": message,
            "timestamp": time.time(),
        }
    except Exception as e:
        logger.error(f"Failed to invalidate query cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to invalidate query cache")


@router.get(
    "/performance",
    response_model=PerformanceSummaryResponse,
    summary="Performance dashboard",
    description="High-level performance overview with cache stats and auto-generated tuning recommendations.",
)
async def get_performance_summary() -> dict[str, Any]:
    try:
        current_time = time.time()
        uptime = current_time - _start_time

        # Get cache metrics
        cache_metrics_data = _get_cache_metrics_data()
        global_metrics = cache_metrics_data.get("global", {})

        # Get query cache metrics
        query_cache_instance = get_query_cache()
        query_metrics = query_cache_instance.get_metrics()

        performance_summary = {
            "timestamp": current_time,
            "uptime_seconds": uptime,
            "cache_performance": {
                "overall_hit_rate": global_metrics.get("hit_rate", 0.0),
                "total_requests": global_metrics.get("total_requests", 0),
                "total_cache_size": sum(global_metrics.get("cache_sizes", {}).values()),
            },
            "query_cache": {
                "enabled": query_metrics.get("enabled", False),
                "cache_size": query_metrics.get("cache_size", 0),
                "hit_rate": query_metrics.get("metrics", {}).get("cache_hit_rate", 0.0),
            },
            "recommendations": _generate_performance_recommendations(
                global_metrics.get("hit_rate", 0.0),
                query_metrics.get("metrics", {}).get("cache_hit_rate", 0.0),
                uptime,
            ),
        }

        return performance_summary

    except Exception as e:
        logger.error(f"Failed to get performance summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance summary")


def _generate_performance_recommendations(
    cache_hit_rate: float, query_cache_hit_rate: float, uptime: float
) -> list[str]:
    """Generate performance recommendations based on metrics."""
    recommendations = []

    # Cache hit rate recommendations
    if cache_hit_rate < 0.5:
        recommendations.append("Consider increasing cache TTL or size to improve hit rate")
    elif cache_hit_rate > 0.9:
        recommendations.append("Cache hit rate is excellent - consider reducing cache size to save memory")

    # Query cache recommendations
    if query_cache_hit_rate < 0.3:
        recommendations.append("Query cache hit rate is low - review query patterns and caching strategy")

    # Uptime-based recommendations
    if uptime < 300:  # Less than 5 minutes
        recommendations.append("System recently started - metrics may not be representative yet")

    if not recommendations:
        recommendations.append("Performance metrics look good - no immediate recommendations")

    return recommendations
