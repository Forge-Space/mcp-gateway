"""Cache performance dashboard for MCP Gateway."""

from __future__ import annotations

import logging
import time
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque
from datetime import datetime, timedelta

from .cache_manager import CacheManager
from .redis_cache import RedisCache
from .invalidation import AdvancedInvalidationManager
from .types import CacheMetrics

logger = logging.getLogger(__name__)


@dataclass
class CachePerformanceMetrics:
    """Real-time cache performance metrics."""
    timestamp: float
    cache_name: str
    backend_type: str  # "memory", "redis", "hybrid"
    
    # Basic metrics
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_requests: int = 0
    hit_rate: float = 0.0
    
    # Size and capacity
    current_size: int = 0
    max_size: int = 0
    memory_usage: int = 0  # bytes
    
    # Performance timing
    avg_get_time: float = 0.0  # milliseconds
    avg_set_time: float = 0.0  # milliseconds
    avg_delete_time: float = 0.0  # milliseconds
    
    # Redis-specific metrics
    redis_connected: bool = False
    redis_memory_usage: int = 0  # bytes
    redis_key_count: int = 0
    
    # Invalidation metrics
    invalidations_count: int = 0
    last_invalidation_time: Optional[float] = None
    
    # Health metrics
    health_status: str = "healthy"  # "healthy", "degraded", "unhealthy"
    last_health_check: Optional[float] = None


@dataclass
class CacheAlert:
    """Cache performance alert."""
    alert_id: str
    alert_type: str  # "high_miss_rate", "low_hit_rate", "memory_usage", "connection_error"
    severity: str  # "info", "warning", "error", "critical"
    message: str
    cache_name: str
    timestamp: float
    resolved: bool = False
    resolved_at: Optional[float] = None


@dataclass
class CachePerformanceSnapshot:
    """Snapshot of cache performance at a point in time."""
    timestamp: float
    metrics: Dict[str, CachePerformanceMetrics]
    alerts: List[CacheAlert]
    summary: Dict[str, Any]


class CachePerformanceCollector:
    """Collects cache performance metrics from various sources."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self._lock = threading.RLock()
        self._start_time = time.time()
        
        # Performance tracking
        self._get_times: deque = deque(maxlen=1000)
        self._set_times: deque = deque(maxlen=1000)
        self._delete_times: deque = deque(maxlen=1000)
    
    def collect_metrics(self, cache_name: str) -> CachePerformanceMetrics:
        """Collect metrics for a specific cache."""
        with self._lock:
            cache = self.cache_manager.get_cache(cache_name)
            metrics = self.cache_manager._metrics.get(cache_name, CacheMetrics())
            
            # Basic metrics
            hit_rate = (metrics.hits / max(metrics.total_requests, 1)) * 100
            
            # Determine backend type
            backend_type = "memory"
            if isinstance(cache, RedisCache):
                backend_type = "redis"
                if cache._redis_client:
                    backend_type = "hybrid"
            
            # Size information
            current_size = 0
            max_size = 0
            memory_usage = 0
            
            if hasattr(cache, '__len__'):
                try:
                    current_size = len(cache)
                except:
                    current_size = 0
            
            if hasattr(cache, 'maxsize'):
                max_size = cache.maxsize
            
            # Redis-specific metrics
            redis_connected = False
            redis_memory_usage = 0
            redis_key_count = 0
            
            if isinstance(cache, RedisCache):
                redis_connected = cache._is_healthy
                try:
                    info = cache.get_info()
                    redis_memory_usage = info.get('memory_usage', 0)
                    redis_key_count = info.get('key_count', 0)
                except Exception as e:
                    logger.warning(f"Failed to get Redis info: {e}")
            
            # Calculate average timing
            avg_get_time = sum(self._get_times) / max(len(self._get_times), 1) if self._get_times else 0.0
            avg_set_time = sum(self._set_times) / max(len(self._set_times), 1) if self._set_times else 0.0
            avg_delete_time = sum(self._delete_times) / max(len(self._delete_times), 1) if self._delete_times else 0.0
            
            # Health status
            health_status = "healthy"
            if backend_type == "redis" and not redis_connected:
                health_status = "degraded"
            elif hit_rate < 50 and metrics.total_requests > 100:
                health_status = "degraded"
            elif hit_rate < 20 and metrics.total_requests > 100:
                health_status = "unhealthy"
            
            return CachePerformanceMetrics(
                timestamp=time.time(),
                cache_name=cache_name,
                backend_type=backend_type,
                hits=metrics.hits,
                misses=metrics.misses,
                evictions=metrics.evictions,
                total_requests=metrics.total_requests,
                hit_rate=hit_rate,
                current_size=current_size,
                max_size=max_size,
                memory_usage=memory_usage,
                avg_get_time=avg_get_time,
                avg_set_time=avg_set_time,
                avg_delete_time=avg_delete_time,
                redis_connected=redis_connected,
                redis_memory_usage=redis_memory_usage,
                redis_key_count=redis_key_count,
                health_status=health_status,
                last_health_check=time.time()
            )
    
    def record_get_time(self, duration: float) -> None:
        """Record cache get operation time."""
        with self._lock:
            self._get_times.append(duration)
    
    def record_set_time(self, duration: float) -> None:
        """Record cache set operation time."""
        with self._lock:
            self._set_times.append(duration)
    
    def record_delete_time(self, duration: float) -> None:
        """Record cache delete operation time."""
        with self._lock:
            self._delete_times.append(duration)


class CacheAlertManager:
    """Manages cache performance alerts."""
    
    def __init__(self):
        self._lock = threading.RLock()
        self._alerts: Dict[str, CacheAlert] = {}
        self._alert_rules = {
            "high_miss_rate": {"threshold": 80.0, "severity": "warning"},
            "low_hit_rate": {"threshold": 50.0, "severity": "warning"},
            "memory_usage": {"threshold": 90.0, "severity": "warning"},
            "connection_error": {"threshold": 0.0, "severity": "error"},
            "unhealthy": {"threshold": 0.0, "severity": "critical"},
        }
    
    def check_alerts(self, metrics: CachePerformanceMetrics) -> List[CacheAlert]:
        """Check for alerts based on metrics."""
        alerts = []
        
        with self._lock:
            # Check high miss rate
            miss_rate = (metrics.misses / max(metrics.total_requests, 1)) * 100
            if miss_rate > self._alert_rules["high_miss_rate"]["threshold"]:
                alert_id = f"high_miss_rate_{metrics.cache_name}"
                if alert_id not in self._alerts or not self._alerts[alert_id].resolved:
                    alert = CacheAlert(
                        alert_id=alert_id,
                        alert_type="high_miss_rate",
                        severity=self._alert_rules["high_miss_rate"]["severity"],
                        message=f"High miss rate: {miss_rate:.1f}%",
                        cache_name=metrics.cache_name,
                        timestamp=metrics.timestamp
                    )
                    alerts.append(alert)
                    self._alerts[alert_id] = alert
            
            # Check low hit rate
            if metrics.hit_rate < self._alert_rules["low_hit_rate"]["threshold"]:
                alert_id = f"low_hit_rate_{metrics.cache_name}"
                if alert_id not in self._alerts or not self._alerts[alert_id].resolved:
                    alert = CacheAlert(
                        alert_id=alert_id,
                        alert_type="low_hit_rate",
                        severity=self._alert_rules["low_hit_rate"]["severity"],
                        message=f"Low hit rate: {metrics.hit_rate:.1f}%",
                        cache_name=metrics.cache_name,
                        timestamp=metrics.timestamp
                    )
                    alerts.append(alert)
                    self._alerts[alert_id] = alert
            
            # Check memory usage
            if metrics.max_size > 0:
                usage_percent = (metrics.current_size / metrics.max_size) * 100
                if usage_percent > self._alert_rules["memory_usage"]["threshold"]:
                    alert_id = f"memory_usage_{metrics.cache_name}"
                    if alert_id not in self._alerts or not self._alerts[alert_id].resolved:
                        alert = CacheAlert(
                            alert_id=alert_id,
                            alert_type="memory_usage",
                            severity=self._alert_rules["memory_usage"]["severity"],
                            message=f"High memory usage: {usage_percent:.1f}%",
                            cache_name=cache_name,
                            timestamp=metrics.timestamp
                        )
                        alerts.append(alert)
                        self._alerts[alert_id] = alert
            
            # Check Redis connection
            if metrics.backend_type in ["redis", "hybrid"] and not metrics.redis_connected:
                alert_id = f"connection_error_{metrics.cache_name}"
                if alert_id not in self._alerts or not self._alerts[alert_id].resolved:
                    alert = CacheAlert(
                        alert_id=alert_id,
                        alert_type="connection_error",
                        severity=self._alert_rules["connection_error"]["severity"],
                        message="Redis connection lost",
                        cache_name=metrics.cache_name,
                        timestamp=metrics.timestamp
                    )
                    alerts.append(alert)
                    self._alerts[alert_id] = alert
            
            # Check health status
            if metrics.health_status == "unhealthy":
                alert_id = f"unhealthy_{metrics.cache_name}"
                if alert_id not in self._alerts or not self._alerts[alert_id].resolved:
                    alert = CacheAlert(
                        alert_id=alert_id,
                        alert_type="unhealthy",
                        severity=self._alert_rules["unhealthy"]["severity"],
                        message=f"Cache is {metrics.health_status}",
                        cache_name=metrics.cache_name,
                        timestamp=metrics.timestamp
                    )
                    alerts.append(alert)
                    self._alerts[alert_id] = alert
            
            # Resolve alerts that are no longer active
            for alert_id, alert in list(self._alerts.items()):
                should_resolve = False
                
                if alert.alert_type == "high_miss_rate":
                    miss_rate = (metrics.misses / max(metrics.total_requests, 1)) * 100
                    should_resolve = miss_rate <= self._alert_rules["high_miss_rate"]["threshold"]
                elif alert.alert_type == "low_hit_rate":
                    should_resolve = metrics.hit_rate >= self._alert_rules["low_hit_rate"]["threshold"]
                elif alert.alert_type == "memory_usage":
                    if metrics.max_size > 0:
                        usage_percent = (metrics.current_size / metrics.max_size) * 100
                        should_resolve = usage_percent <= self._alert_rules["memory_usage"]["threshold"]
                elif alert.alert_type == "connection_error":
                    should_resolve = metrics.redis_connected
                elif alert.alert_type == "unhealthy":
                    should_resolve = metrics.health_status != "unhealthy"
                
                if should_resolve:
                    alert.resolved = True
                    alert.resolved_at = metrics.timestamp
        
        return alerts
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        with self._lock:
            return [alert for alert in self._alerts.values() if not alert.resolved]
    
    def get_alert_history(self, limit: int = 100) -> List[CacheAlert]:
        """Get alert history."""
        with self._lock:
            all_alerts = list(self._alerts.values())
            all_alerts.sort(key=lambda a: a.timestamp, reverse=True)
            return all_alerts[:limit]


class CachePerformanceDashboard:
    """Main cache performance dashboard."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.collector = CachePerformanceCollector(cache_manager)
        self.alert_manager = CacheAlertManager()
        
        # History tracking
        self._history: deque = deque(maxlen=1000)
        self._snapshots: deque = deque(maxlen=100)
        
        # Background collection
        self._running = False
        self._collection_thread: Optional[threading.Thread] = None
        self._collection_interval = 30  # seconds
        
        # Dashboard configuration
        self.max_history_hours = 24
        self.alert_retention_hours = 48
    
    def start_collection(self, interval: int = 30) -> None:
        """Start background metrics collection."""
        if self._running:
            logger.warning("Dashboard collection already running")
            return None
        
        self._collection_interval = interval
        self._running = True
        
        def collect_loop():
            while self._running:
                try:
                    self.collect_snapshot()
                    time.sleep(self._collection_interval)
                except Exception as e:
                    logger.error(f"Error in dashboard collection: {e}")
                    time.sleep(self._collection_interval)
        
        self._collection_thread = threading.Thread(target=collect_loop, daemon=True)
        self._collection_thread.start()
        
        logger.info(f"Started cache performance dashboard collection (interval: {interval}s)")
        return self._collection_thread
    
    def stop_collection(self) -> None:
        """Stop background metrics collection."""
        if not self._running:
            return None
        
        self._running = False
        if self._collection_thread:
            self._collection_thread.join(timeout=5)
        
        logger.info("Stopped cache performance dashboard collection")
    
    def collect_snapshot(self) -> CachePerformanceSnapshot:
        """Collect a performance snapshot."""
        # Collect metrics for all caches
        metrics = {}
        for cache_name in self.cache_manager._caches:
            metrics[cache_name] = self.collector.collect_metrics(cache_name)
        
        # Check for alerts
        all_alerts = []
        for cache_metrics in metrics.values():
            alerts = self.alert_manager.check_alerts(cache_metrics)
            all_alerts.extend(alerts)
        
        # Create snapshot
        snapshot = CachePerformanceSnapshot(
            timestamp=time.time(),
            metrics=metrics,
            alerts=all_alerts,
            summary=self._calculate_summary(metrics)
        )
        
        # Store in history
        self._snapshots.append(snapshot)
        self._history.append(snapshot)
        
        # Cleanup old snapshots
        cutoff_time = time.time() - (self.max_history_hours * 3600)
        while self._snapshots and self._snapshots[0].timestamp < cutoff_time:
            self._snapshots.popleft()
        
        return snapshot
    
    def get_current_snapshot(self) -> Optional[CachePerformanceSnapshot]:
        """Get the most recent snapshot."""
        return self._snapshots[-1] if self._snapshots else None
    
    def get_historical_data(self, hours: int = 24) -> List[CachePerformanceSnapshot]:
        """Get historical performance data."""
        cutoff_time = time.time() - (hours * 3600)
        return [s for s in self._snapshots if s.timestamp >= cutoff_time]
    
    def get_performance_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance trend analysis."""
        snapshots = self.get_historical_data(hours)
        
        if len(snapshots) < 2:
            return {}
        
        trends = {}
        
        for cache_name in snapshots[0].metrics.keys():
            # Extract metric series
            hit_rates = [s.metrics[cache_name].hit_rate for s in snapshots]
            miss_rates = [(100 - hr) for hr in hit_rates]
            sizes = [s.metrics[cache_name].current_size for s in snapshots]
            timestamps = [s.timestamp for s in snapshots]
            
            if len(hit_rates) >= 2:
                # Calculate trends
                hit_rate_trend = hit_rates[-1] - hit_rates[0]
                miss_rate_trend = miss_rates[-1] - miss_rates[0]
                size_trend = sizes[-1] - sizes[0]
                
                trends[cache_name] = {
                    "hit_rate_trend": hit_rate_trend,
                    "miss_rate_trend": miss_rate_trend,
                    "size_trend": size_trend,
                    "avg_hit_rate": sum(hit_rates) / len(hit_rates),
                    "avg_miss_rate": sum(miss_rates) / len(miss_rates),
                    "peak_hit_rate": max(hit_rates),
                    "peak_miss_rate": max(miss_rates),
                    "min_hit_rate": min(hit_rates),
                    "min_miss_rate": min(miss_rates),
                    "data_points": len(hit_rates)
                }
        
        return trends
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary statistics."""
        active_alerts = self.alert_manager.get_active_alerts()
        all_alerts = self.alert_manager.get_alert_history()
        
        severity_counts = defaultdict(int)
        for alert in all_alerts:
            severity_counts[alert.severity] += 1
        
        return {
            "active_alerts": len(active_alerts),
            "total_alerts": len(all_alerts),
            "severity_breakdown": dict(severity_counts),
            "most_recent_alert": all_alerts[0].timestamp if all_alerts else None,
            "alert_types": list(set(alert.alert_type for alert in all_alerts))
        }
    
    def get_cache_health_status(self) -> Dict[str, str]:
        """Get health status for all caches."""
        status = {}
        snapshot = self.get_current_snapshot()
        
        if snapshot:
            for cache_name, metrics in snapshot.metrics.items():
                status[cache_name] = metrics.health_status
        
        return status
    
    def _calculate_summary(self, metrics: Dict[str, CachePerformanceMetrics]) -> Dict[str, Any]:
        """Calculate summary statistics."""
        if not metrics:
            return {}
        
        total_hits = sum(m.hits for m in metrics.values())
        total_misses = sum(m.misses for m in metrics.values())
        total_requests = sum(m.total_requests for m in metrics.values())
        total_evictions = sum(m.evictions for m in metrics.values())
        
        overall_hit_rate = (total_hits / max(total_requests, 1)) * 100
        
        backend_counts = defaultdict(int)
        for m in metrics.values():
            backend_counts[m.backend_type] += 1
        
        healthy_count = sum(1 for m in metrics.values() if m.health_status == "healthy")
        
        return {
            "total_caches": len(metrics),
            "healthy_caches": healthy_count,
            "overall_hit_rate": overall_hit_rate,
            "total_hits": total_hits,
            "total_misses": total_misses,
            "total_requests": total_requests,
            "total_evictions": total_evictions,
            "backend_distribution": dict(backend_counts),
            "timestamp": time.time()
        }
    
    def export_metrics(self, format: str = "json") -> str:
        """Export metrics data."""
        snapshot = self.get_current_snapshot()
        
        if format == "json":
            import json
            return json.dumps(snapshot.__dict__, indent=2, default=str)
        elif format == "csv":
            # Simple CSV export
            lines = ["timestamp,cache_name,backend_type,hits,misses,hit_rate,size,health_status"]
            for cache_name, metrics in snapshot.metrics.items():
                lines.append(f"{metrics.timestamp},{cache_name},{metrics.backend_type},{metrics.hits},{metrics.misses},{metrics.hit_rate},{metrics.current_size},{metrics.health_status}")
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def get_dashboard_config(self) -> Dict[str, Any]:
        """Get dashboard configuration."""
        return {
            "collection_interval": self._collection_interval,
            "max_history_hours": self.max_history_hours,
            "alert_retention_hours": self.alert_retention_hours,
            "running": self._running,
            "cache_count": len(self.cache_manager._caches),
            "alert_rules": self.alert_manager._alert_rules
        }


# Global dashboard instance
_cache_performance_dashboard: Optional[CachePerformanceDashboard] = None


def get_cache_performance_dashboard() -> CachePerformanceDashboard:
    """Get the global cache performance dashboard."""
    global _cache_performance_dashboard
    if _cache_performance_dashboard is None:
        from .cache_manager import cache_manager
        _cache_performance_dashboard = CachePerformanceDashboard(cache_manager)
    return _cache_performance_dashboard


def start_dashboard_collection(interval: int = 30) -> None:
    """Start the global dashboard collection."""
    return get_cache_performance_dashboard().start_collection(interval)


def stop_dashboard_collection() -> None:
    """Stop the global dashboard collection."""
    return get_cache_performance_dashboard().stop_collection()


def get_dashboard_data() -> Optional[CachePerformanceSnapshot]:
    """Get current dashboard data."""
    return get_cache_performance_dashboard().get_current_snapshot()


def get_dashboard_trends(hours: int = 24) -> Dict[str, Any]:
    """Get dashboard trend analysis."""
    return get_cache_performance_dashboard().get_performance_trends(hours)


def get_alert_summary() -> Dict[str, Any]:
    """Get alert summary."""
    return get_cache_performance_dashboard().get_alert_summary()
