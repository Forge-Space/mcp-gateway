"""Rate limiting and request throttling for AI agent requests."""

from __future__ import annotations

import time
import threading
from typing import Dict, Optional, Set
from dataclasses import dataclass
from collections import defaultdict, deque
from enum import Enum

import redis
from cachetools import TTLCache


class LimitType(Enum):
    """Types of rate limits."""
    PER_MINUTE = "minute"
    PER_HOUR = "hour"
    PER_DAY = "day"
    BURST = "burst"


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_capacity: int = 10
    penalty_duration: int = 300  # seconds
    adaptive_scaling: bool = True
    penalty_multiplier: float = 2.0


@dataclass
class RateLimitResult:
    """Result of rate limit check."""
    allowed: bool
    remaining: int
    reset_time: int
    retry_after: Optional[int] = None
    penalty_applied: bool = False
    metadata: Dict[str, any] = None


class RateLimiter:
    """Multi-strategy rate limiter with adaptive capabilities."""
    
    def __init__(self, use_redis: bool = False, redis_url: Optional[str] = None):
        self.use_redis = use_redis
        self.redis_client = None
        
        # In-memory storage for development/testing
        self._memory_storage = defaultdict(dict)
        self._penalties = defaultdict(float)
        self._lock = threading.RLock()
        
        # Cache for frequently accessed data
        self._cache = TTLCache(maxsize=10000, ttl=60)
        
        if use_redis and redis_url:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
            except Exception as e:
                print(f"Failed to connect to Redis: {e}. Using in-memory storage.")
                self.use_redis = False
    
    def check_rate_limit(self, identifier: str, config: RateLimitConfig) -> RateLimitResult:
        """Check if request is allowed under rate limits."""
        current_time = int(time.time())
        
        # Check if identifier is currently penalized
        if self._is_penalized(identifier, current_time):
            penalty_end = int(self._penalties[identifier])
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=penalty_end,
                retry_after=penalty_end - current_time,
                penalty_applied=True,
                metadata={'reason': 'penalty_active'}
            )
        
        # Check all rate limits
        limits = [
            (LimitType.PER_MINUTE, config.requests_per_minute, 60),
            (LimitType.PER_HOUR, config.requests_per_hour, 3600),
            (LimitType.PER_DAY, config.requests_per_day, 86400),
        ]
        
        most_restrictive = None
        for limit_type, max_requests, window_seconds in limits:
            result = self._check_window_limit(identifier, limit_type, max_requests, window_seconds, current_time)
            
            if not result.allowed:
                most_restrictive = result
                break
            
            if most_restrictive is None or result.remaining < most_restrictive.remaining:
                most_restrictive = result
        
        # Check burst capacity
        burst_result = self._check_burst_limit(identifier, config.burst_capacity, current_time)
        if not burst_result.allowed:
            most_restrictive = burst_result
        
        # Apply adaptive scaling if enabled
        if config.adaptive_scaling and most_restrictive and most_restrictive.allowed:
            most_restrictive = self._apply_adaptive_scaling(identifier, most_restrictive, config)
        
        # Record the request if allowed
        if most_restrictive and most_restrictive.allowed:
            self._record_request(identifier, current_time)
        
        return most_restrictive or RateLimitResult(
            allowed=True,
            remaining=config.requests_per_minute,
            reset_time=current_time + 60,
            metadata={'window': 'minute'}
        )
    
    def _check_window_limit(self, identifier: str, limit_type: LimitType, max_requests: int, window_seconds: int, current_time: int) -> RateLimitResult:
        """Check rate limit for a specific time window."""
        window_start = current_time - (current_time % window_seconds)
        window_end = window_start + window_seconds
        
        if self.use_redis and self.redis_client:
            return self._check_redis_window_limit(identifier, limit_type, max_requests, window_start, window_end, current_time)
        else:
            return self._check_memory_window_limit(identifier, limit_type, max_requests, window_start, window_end, current_time)
    
    def _check_redis_window_limit(self, identifier: str, limit_type: LimitType, max_requests: int, window_start: int, window_end: int, current_time: int) -> RateLimitResult:
        """Check rate limit using Redis."""
        key = f"rate_limit:{identifier}:{limit_type.value}:{window_start}"
        
        try:
            # Use Redis pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window_end - current_time)
            results = pipe.execute()
            
            current_count = results[0]
            remaining = max(0, max_requests - current_count)
            allowed = current_count <= max_requests
            
            return RateLimitResult(
                allowed=allowed,
                remaining=remaining,
                reset_time=window_end,
                metadata={
                    'window_type': limit_type.value,
                    'current_count': current_count,
                    'max_requests': max_requests
                }
            )
        except Exception as e:
            # Fallback to memory storage on Redis error
            return self._check_memory_window_limit(identifier, limit_type, max_requests, window_start, window_end, current_time)
    
    def _check_memory_window_limit(self, identifier: str, limit_type: LimitType, max_requests: int, window_start: int, window_end: int, current_time: int) -> RateLimitResult:
        """Check rate limit using in-memory storage."""
        with self._lock:
            if identifier not in self._memory_storage:
                self._memory_storage[identifier] = {}
            
            if limit_type.value not in self._memory_storage[identifier]:
                self._memory_storage[identifier][limit_type.value] = deque()
            
            requests = self._memory_storage[identifier][limit_type.value]
            
            # Remove old requests outside the window
            while requests and requests[0] < window_start:
                requests.popleft()
            
            current_count = len(requests)
            remaining = max(0, max_requests - current_count)
            allowed = current_count < max_requests
            
            return RateLimitResult(
                allowed=allowed,
                remaining=remaining,
                reset_time=window_end,
                metadata={
                    'window_type': limit_type.value,
                    'current_count': current_count,
                    'max_requests': max_requests
                }
            )
    
    def _check_burst_limit(self, identifier: str, burst_capacity: int, current_time: int) -> RateLimitResult:
        """Check burst capacity limit."""
        burst_window = 10  # 10-second burst window
        window_start = current_time - burst_window
        
        if self.use_redis and self.redis_client:
            key = f"burst_limit:{identifier}:{window_start}"
            try:
                pipe = self.redis_client.pipeline()
                pipe.incr(key)
                pipe.expire(key, burst_window)
                results = pipe.execute()
                
                current_count = results[0]
                allowed = current_count <= burst_capacity
                
                return RateLimitResult(
                    allowed=allowed,
                    remaining=max(0, burst_capacity - current_count),
                    reset_time=current_time + burst_window,
                    metadata={
                        'window_type': 'burst',
                        'current_count': current_count,
                        'burst_capacity': burst_capacity
                    }
                )
            except Exception:
                pass
        
        # Fallback to memory storage
        with self._lock:
            burst_key = f"burst:{identifier}"
            if burst_key not in self._memory_storage:
                self._memory_storage[identifier][burst_key] = deque()
            
            requests = self._memory_storage[identifier][burst_key]
            
            # Remove old requests
            while requests and requests[0] < window_start:
                requests.popleft()
            
            current_count = len(requests)
            allowed = current_count < burst_capacity
            
            return RateLimitResult(
                allowed=allowed,
                remaining=max(0, burst_capacity - current_count),
                reset_time=current_time + burst_window,
                metadata={
                    'window_type': 'burst',
                    'current_count': current_count,
                    'burst_capacity': burst_capacity
                }
            )
    
    def _apply_adaptive_scaling(self, identifier: str, result: RateLimitResult, config: RateLimitConfig) -> RateLimitResult:
        """Apply adaptive scaling based on usage patterns."""
        # Simple adaptive scaling: reduce remaining requests if usage is high
        if result.remaining < config.requests_per_minute * 0.2:  # Less than 20% remaining
            # Apply penalty multiplier
            adjusted_remaining = int(result.remaining * config.penalty_multiplier)
            result.remaining = max(0, adjusted_remaining)
            result.metadata['adaptive_scaling_applied'] = True
        
        return result
    
    def _record_request(self, identifier: str, current_time: int) -> None:
        """Record a request for rate limiting."""
        if self.use_redis and self.redis_client:
            # Redis handles counting automatically in _check_window_limit
            pass
        else:
            with self._lock:
                if identifier not in self._memory_storage:
                    self._memory_storage[identifier] = {}
                
                # Record for each window type
                for limit_type in [LimitType.PER_MINUTE.value, LimitType.PER_HOUR.value, LimitType.PER_DAY.value]:
                    if limit_type not in self._memory_storage[identifier]:
                        self._memory_storage[identifier][limit_type] = deque()
                    
                    self._memory_storage[identifier][limit_type].append(current_time)
                
                # Record burst
                burst_key = "burst"
                if burst_key not in self._memory_storage[identifier]:
                    self._memory_storage[identifier][burst_key] = deque()
                
                self._memory_storage[identifier][burst_key].append(current_time)
    
    def _is_penalized(self, identifier: str, current_time: int) -> bool:
        """Check if identifier is currently penalized."""
        return current_time < self._penalties[identifier]
    
    def apply_penalty(self, identifier: str, duration: int) -> None:
        """Apply a penalty to an identifier."""
        penalty_end = int(time.time()) + duration
        self._penalties[identifier] = penalty_end
        
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.setex(f"penalty:{identifier}", duration, penalty_end)
            except Exception:
                pass
    
    def clear_penalties(self, identifier: str) -> None:
        """Clear penalties for an identifier."""
        del self._penalties[identifier]
        
        if self.use_redis and self.redis_client:
            try:
                self.redis_client.delete(f"penalty:{identifier}")
            except Exception:
                pass
    
    def get_usage_stats(self, identifier: str) -> Dict[str, any]:
        """Get usage statistics for an identifier."""
        current_time = int(time.time())
        stats = {}
        
        # Check each window type
        for limit_type, window_seconds in [
            (LimitType.PER_MINUTE, 60),
            (LimitType.PER_HOUR, 3600),
            (LimitType.PER_DAY, 86400),
        ]:
            window_start = current_time - (current_time % window_seconds)
            window_end = window_start + window_seconds
            
            if self.use_redis and self.redis_client:
                key = f"rate_limit:{identifier}:{limit_type.value}:{window_start}"
                try:
                    count = int(self.redis_client.get(key) or 0)
                    stats[limit_type.value] = {
                        'count': count,
                        'window_start': window_start,
                        'window_end': window_end
                    }
                except Exception:
                    stats[limit_type.value] = {'count': 0, 'window_start': window_start, 'window_end': window_end}
            else:
                with self._lock:
                    if identifier in self._memory_storage and limit_type.value in self._memory_storage[identifier]:
                        requests = self._memory_storage[identifier][limit_type.value]
                        # Count requests in current window
                        count = sum(1 for req_time in requests if window_start <= req_time < window_end)
                        stats[limit_type.value] = {
                            'count': count,
                            'window_start': window_start,
                            'window_end': window_end
                        }
                    else:
                        stats[limit_type.value] = {'count': 0, 'window_start': window_start, 'window_end': window_end}
        
        # Penalty status
        stats['penalty_active'] = self._is_penalized(identifier, current_time)
        if stats['penalty_active']:
            stats['penalty_end'] = self._penalties[identifier]
        
        return stats
    
    def cleanup_expired_data(self) -> None:
        """Clean up expired rate limit data."""
        current_time = int(time.time())
        
        if not self.use_redis:
            with self._lock:
                for identifier in list(self._memory_storage.keys()):
                    # Clean up old windows
                    for window_type in list(self._memory_storage[identifier].keys()):
                        requests = self._memory_storage[identifier][window_type]
                        
                        # Remove requests older than 24 hours
                        cutoff_time = current_time - 86400
                        while requests and requests[0] < cutoff_time:
                            requests.popleft()
                        
                        # Remove empty windows
                        if not requests:
                            del self._memory_storage[identifier][window_type]
                    
                    # Remove empty identifiers
                    if not self._memory_storage[identifier]:
                        del self._memory_storage[identifier]
        
        # Clean up expired penalties
        expired_penalties = [ident for ident, end_time in self._penalties.items() if current_time >= end_time]
        for ident in expired_penalties:
            del self._penalties[ident]
