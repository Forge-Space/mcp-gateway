"""Cache performance dashboard API endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel

from tool_router.cache.dashboard import (
    get_alert_summary,
    get_cache_performance_dashboard,
    get_dashboard_data,
    get_dashboard_trends,
    start_dashboard_collection,
    stop_dashboard_collection,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cache/dashboard", tags=["cache-dashboard"])


# Pydantic models for API responses
class CacheMetricsResponse(BaseModel):
    """Cache metrics response model."""

    timestamp: float
    cache_name: str
    backend_type: str
    hits: int
    misses: int
    evictions: int
    total_requests: int
    hit_rate: float
    current_size: int
    max_size: int
    memory_usage: int
    avg_get_time: float
    avg_set_time: float
    avg_delete_time: float
    redis_connected: bool
    redis_memory_usage: int
    redis_key_count: int
    health_status: str
    last_health_check: float | None = None


class CacheAlertResponse(BaseModel):
    """Cache alert response model."""

    alert_id: str
    alert_type: str
    severity: str
    message: str
    cache_name: str
    timestamp: float
    resolved: bool
    resolved_at: float | None = None


class DashboardSnapshotResponse(BaseModel):
    """Dashboard snapshot response model."""

    timestamp: float
    metrics: dict[str, CacheMetricsResponse]
    alerts: list[CacheAlertResponse]
    summary: dict[str, Any]


class DashboardConfigResponse(BaseModel):
    """Dashboard configuration response model."""

    collection_interval: int
    max_history_hours: int
    alert_retention_hours: int
    running: bool
    cache_count: int
    alert_rules: dict[str, dict[str, Any]]


class PerformanceTrendsResponse(BaseModel):
    """Performance trends response model."""

    cache_name: str
    hit_rate_trend: float
    miss_rate_trend: float
    size_trend: int
    avg_hit_rate: float
    avg_miss_rate: float
    peak_hit_rate: float
    peak_miss_rate: float
    min_hit_rate: float
    min_miss_rate: float
    data_points: int


class AlertSummaryResponse(BaseModel):
    """Alert summary response model."""

    active_alerts: int
    total_alerts: int
    severity_breakdown: dict[str, int]
    most_recent_alert: float | None = None
    alert_types: list[str]


# API endpoints
@router.get("/status", response_model=DashboardConfigResponse)
async def get_dashboard_status():
    """Get dashboard status and configuration."""
    try:
        dashboard = get_cache_performance_dashboard()
        config = dashboard.get_dashboard_config()

        return DashboardConfigResponse(**config)
    except Exception as e:
        logger.error(f"Error getting dashboard status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard status")


@router.post("/start")
async def start_collection(background_tasks: BackgroundTasks, interval: int = Query(default=30, ge=5, le=300)):
    """Start dashboard metrics collection."""
    try:
        dashboard = get_cache_performance_dashboard()

        if dashboard._running:
            return {"message": "Dashboard collection already running", "interval": dashboard._collection_interval}

        # Start collection in background
        background_tasks.add_task(start_dashboard_collection, interval)

        return {"message": "Dashboard collection started", "interval": interval}
    except Exception as e:
        logger.error(f"Error starting dashboard collection: {e}")
        raise HTTPException(status_code=500, detail="Failed to start dashboard collection")


@router.post("/stop")
async def stop_collection():
    """Stop dashboard metrics collection."""
    try:
        dashboard = get_cache_performance_dashboard()

        if not dashboard._running:
            return {"message": "Dashboard collection not running"}

        stop_dashboard_collection()

        return {"message": "Dashboard collection stopped"}
    except Exception as e:
        logger.error(f"Error stopping dashboard collection: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop dashboard collection")


@router.get("/snapshot", response_model=DashboardSnapshotResponse)
async def get_current_snapshot():
    """Get current dashboard snapshot."""
    try:
        snapshot = get_dashboard_data()

        if not snapshot:
            raise HTTPException(status_code=404, detail="No snapshot data available")

        # Convert metrics to response models
        metrics_response = {}
        for cache_name, metrics in snapshot.metrics.items():
            metrics_response[cache_name] = CacheMetricsResponse(
                timestamp=metrics.timestamp,
                cache_name=metrics.cache_name,
                backend_type=metrics.backend_type,
                hits=metrics.hits,
                misses=metrics.misses,
                evictions=metrics.evictions,
                total_requests=metrics.total_requests,
                hit_rate=metrics.hit_rate,
                current_size=metrics.current_size,
                max_size=metrics.max_size,
                memory_usage=metrics.memory_usage,
                avg_get_time=metrics.avg_get_time,
                avg_set_time=metrics.avg_set_time,
                avg_delete_time=metrics.avg_delete_time,
                redis_connected=metrics.redis_connected,
                redis_memory_usage=metrics.redis_memory_usage,
                redis_key_count=metrics.redis_key_count,
                health_status=metrics.health_status,
                last_health_check=metrics.last_health_check,
            )

        # Convert alerts to response models
        alerts_response = [
            CacheAlertResponse(
                alert_id=alert.alert_id,
                alert_type=alert.alert_type,
                severity=alert.severity,
                message=alert.message,
                cache_name=alert.cache_name,
                timestamp=alert.timestamp,
                resolved=alert.resolved,
                resolved_at=alert.resolved_at,
            )
            for alert in snapshot.alerts
        ]

        return DashboardSnapshotResponse(
            timestamp=snapshot.timestamp, metrics=metrics_response, alerts=alerts_response, summary=snapshot.summary
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dashboard snapshot: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard snapshot")


@router.get("/history")
async def get_historical_data(hours: int = Query(default=24, ge=1, le=168)):
    """Get historical dashboard data."""
    try:
        dashboard = get_cache_performance_dashboard()
        snapshots = dashboard.get_historical_data(hours)

        if not snapshots:
            return {"message": "No historical data available", "snapshots": []}

        # Convert snapshots to response format
        snapshots_response = []
        for snapshot in snapshots:
            metrics_response = {}
            for cache_name, metrics in snapshot.metrics.items():
                metrics_response[cache_name] = CacheMetricsResponse(
                    timestamp=metrics.timestamp,
                    cache_name=metrics.cache_name,
                    backend_type=metrics.backend_type,
                    hits=metrics.hits,
                    misses=metrics.misses,
                    evictions=metrics.evictions,
                    total_requests=metrics.total_requests,
                    hit_rate=metrics.hit_rate,
                    current_size=metrics.current_size,
                    max_size=metrics.max_size,
                    memory_usage=metrics.memory_usage,
                    avg_get_time=metrics.avg_get_time,
                    avg_set_time=metrics.avg_set_time,
                    avg_delete_time=metrics.avg_delete_time,
                    redis_connected=metrics.redis_connected,
                    redis_memory_usage=metrics.redis_memory_usage,
                    redis_key_count=metrics.redis_key_count,
                    health_status=metrics.health_status,
                    last_health_check=metrics.last_health_check,
                )

            snapshots_response.append(
                {"timestamp": snapshot.timestamp, "metrics": metrics_response, "summary": snapshot.summary}
            )

        return {"hours": hours, "snapshot_count": len(snapshots_response), "snapshots": snapshots_response}
    except Exception as e:
        logger.error(f"Error getting historical data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get historical data")


@router.get("/trends")
async def get_performance_trends_api(hours: int = Query(default=24, ge=1, le=168)):
    """Get performance trend analysis."""
    try:
        trends = get_dashboard_trends(hours)

        if not trends:
            return {"message": "No trend data available", "trends": {}}

        # Convert trends to response models
        trends_response = []
        for cache_name, trend_data in trends.items():
            trends_response.append(
                PerformanceTrendsResponse(
                    cache_name=cache_name,
                    hit_rate_trend=trend_data["hit_rate_trend"],
                    miss_rate_trend=trend_data["miss_rate_trend"],
                    size_trend=trend_data["size_trend"],
                    avg_hit_rate=trend_data["avg_hit_rate"],
                    avg_miss_rate=trend_data["avg_miss_rate"],
                    peak_hit_rate=trend_data["peak_hit_rate"],
                    peak_miss_rate=trend_data["peak_miss_rate"],
                    min_hit_rate=trend_data["min_hit_rate"],
                    min_miss_rate=trend_data["min_miss_rate"],
                    data_points=trend_data["data_points"],
                )
            )

        return {"hours": hours, "cache_count": len(trends_response), "trends": trends_response}
    except Exception as e:
        logger.error(f"Error getting performance trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance trends")


@router.get("/alerts", response_model=AlertSummaryResponse)
async def get_alerts_summary():
    """Get alert summary statistics."""
    try:
        summary = get_alert_summary()

        return AlertSummaryResponse(**summary)
    except Exception as e:
        logger.error(f"Error getting alert summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alert summary")


@router.get("/alerts/history")
async def get_alerts_history(limit: int = Query(default=100, ge=1, le=1000)):
    """Get alert history."""
    try:
        dashboard = get_cache_performance_dashboard()
        alerts = dashboard.alert_manager.get_alert_history(limit)

        # Convert alerts to response models
        alerts_response = [
            CacheAlertResponse(
                alert_id=alert.alert_id,
                alert_type=alert.alert_type,
                severity=alert.severity,
                message=alert.message,
                cache_name=alert.cache_name,
                timestamp=alert.timestamp,
                resolved=alert.resolved,
                resolved_at=alert.resolved_at,
            )
            for alert in alerts
        ]

        return {"limit": limit, "total_alerts": len(alerts_response), "alerts": alerts_response}
    except Exception as e:
        logger.error(f"Error getting alert history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alert history")


@router.get("/alerts/active")
async def get_active_alerts():
    """Get active alerts."""
    try:
        dashboard = get_cache_performance_dashboard()
        alerts = dashboard.alert_manager.get_active_alerts()

        # Convert alerts to response models
        alerts_response = [
            CacheAlertResponse(
                alert_id=alert.alert_id,
                alert_type=alert.alert_type,
                severity=alert.severity,
                message=alert.message,
                cache_name=alert.cache_name,
                timestamp=alert.timestamp,
                resolved=alert.resolved,
                resolved_at=alert.resolved_at,
            )
            for alert in alerts
        ]

        return {"active_alerts": len(alerts_response), "alerts": alerts_response}
    except Exception as e:
        logger.error(f"Error getting active alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get active alerts")


@router.get("/health")
async def get_cache_health():
    """Get health status for all caches."""
    try:
        dashboard = get_cache_performance_dashboard()
        health_status = dashboard.get_cache_health_status()

        return {
            "timestamp": dashboard.get_current_snapshot().timestamp if dashboard.get_current_snapshot() else None,
            "cache_health": health_status,
            "healthy_count": sum(1 for status in health_status.values() if status == "healthy"),
            "total_count": len(health_status),
        }
    except Exception as e:
        logger.error(f"Error getting cache health: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cache health")


@router.get("/export")
async def export_metrics(format: str = Query(default="json", regex="^(json|csv)$")):
    """Export metrics data."""
    try:
        dashboard = get_cache_performance_dashboard()

        if format == "json":
            data = dashboard.export_metrics("json")
            return {"format": "json", "data": data}
        if format == "csv":
            data = dashboard.export_metrics("csv")
            return {"format": "csv", "data": data}
        raise HTTPException(status_code=400, detail="Unsupported format")
    except Exception as e:
        logger.error(f"Error exporting metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to export metrics")


@router.post("/collect")
async def trigger_collection():
    """Trigger immediate metrics collection."""
    try:
        dashboard = get_cache_performance_dashboard()
        snapshot = dashboard.collect_snapshot()

        return {
            "message": "Collection triggered successfully",
            "timestamp": snapshot.timestamp,
            "cache_count": len(snapshot.metrics),
            "alert_count": len(snapshot.alerts),
        }
    except Exception as e:
        logger.error(f"Error triggering collection: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger collection")


@router.get("/cache/{cache_name}")
async def get_cache_metrics(cache_name: str):
    """Get metrics for a specific cache."""
    try:
        dashboard = get_cache_performance_dashboard()
        snapshot = dashboard.get_current_snapshot()

        if not snapshot:
            raise HTTPException(status_code=404, detail="No snapshot data available")

        if cache_name not in snapshot.metrics:
            raise HTTPException(status_code=404, detail=f"Cache '{cache_name}' not found")

        metrics = snapshot.metrics[cache_name]

        return CacheMetricsResponse(
            timestamp=metrics.timestamp,
            cache_name=metrics.cache_name,
            backend_type=metrics.backend_type,
            hits=metrics.hits,
            misses=metrics.misses,
            evictions=metrics.evictions,
            total_requests=metrics.total_requests,
            hit_rate=metrics.hit_rate,
            current_size=metrics.current_size,
            max_size=metrics.max_size,
            memory_usage=metrics.memory_usage,
            avg_get_time=metrics.avg_get_time,
            avg_set_time=metrics.avg_set_time,
            avg_delete_time=metrics.avg_delete_time,
            redis_connected=metrics.redis_connected,
            redis_memory_usage=metrics.redis_memory_usage,
            redis_key_count=metrics.redis_key_count,
            health_status=metrics.health_status,
            last_health_check=metrics.last_health_check,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cache metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cache metrics")
