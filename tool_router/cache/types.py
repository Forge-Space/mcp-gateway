"""Cache types and configurations."""

from __future__ import annotations

from typing import Optional
from dataclasses import dataclass


@dataclass
class CacheConfig:
    """Configuration for cache instances."""
    max_size: int = 1000
    ttl: int = 3600  # 1 hour default TTL
    cleanup_interval: int = 300  # 5 minutes
    enable_metrics: bool = True


@dataclass
class CacheMetrics:
    """Cache performance metrics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_requests: int = 0
    hit_rate: float = 0.0
    last_reset_time: float = 0.0
    cache_size: int = 0
