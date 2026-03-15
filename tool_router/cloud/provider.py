"""Cloud provider abstraction for multi-cloud MCP Gateway routing.

Each CloudProvider wraps an HTTPGatewayClient and tracks health metrics
(latency, error rate, availability) used by the MultiCloudRouter.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from tool_router.core.config import GatewayConfig
from tool_router.gateway.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitOpenError
from tool_router.gateway.client import HTTPGatewayClient, SecurityMetadata


class CloudProviderStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class CloudProviderMetrics:
    """Rolling health metrics for a cloud provider."""

    total_requests: int = 0
    total_failures: int = 0
    total_latency_ms: float = 0.0
    last_success_time: float = 0.0
    last_failure_time: float = 0.0
    consecutive_failures: int = 0
    consecutive_successes: int = 0

    @property
    def error_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_failures / self.total_requests

    @property
    def avg_latency_ms(self) -> float:
        successful = self.total_requests - self.total_failures
        if successful == 0:
            return 0.0
        return self.total_latency_ms / successful

    def record_success(self, latency_ms: float) -> None:
        self.total_requests += 1
        self.total_latency_ms += latency_ms
        self.last_success_time = time.monotonic()
        self.consecutive_failures = 0
        self.consecutive_successes += 1

    def record_failure(self) -> None:
        self.total_requests += 1
        self.total_failures += 1
        self.last_failure_time = time.monotonic()
        self.consecutive_failures += 1
        self.consecutive_successes = 0


@dataclass
class CloudProvider:
    """A single cloud provider endpoint with health tracking.

    Wraps an HTTPGatewayClient and maintains rolling metrics for
    routing decisions (latency-weighted, failover, round-robin).
    """

    name: str
    cloud_type: str  # "aws" | "azure" | "gcp" | "custom"
    region: str
    config: GatewayConfig
    priority: int = 0  # Lower = higher priority for failover
    weight: float = 1.0  # For weighted round-robin
    enabled: bool = True
    tags: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._client = HTTPGatewayClient(
            self.config,
            circuit_breaker=CircuitBreaker(CircuitBreakerConfig()),
        )
        self._metrics = CloudProviderMetrics()

    @property
    def metrics(self) -> CloudProviderMetrics:
        return self._metrics

    @property
    def status(self) -> CloudProviderStatus:
        if not self.enabled:
            return CloudProviderStatus.UNHEALTHY
        if self._metrics.total_requests == 0:
            return CloudProviderStatus.UNKNOWN
        if self._metrics.consecutive_failures >= 3:
            return CloudProviderStatus.UNHEALTHY
        if self._metrics.error_rate > 0.5:
            return CloudProviderStatus.UNHEALTHY
        if self._metrics.error_rate > 0.1 or self._metrics.consecutive_failures >= 1:
            return CloudProviderStatus.DEGRADED
        return CloudProviderStatus.HEALTHY

    def get_tools(self) -> list[dict[str, Any]]:
        """Fetch tools from this provider, tracking latency and errors."""
        start = time.monotonic()
        try:
            result = self._client.get_tools()
            latency_ms = (time.monotonic() - start) * 1000
            self._metrics.record_success(latency_ms)
            return result
        except (ValueError, ConnectionError, CircuitOpenError):
            self._metrics.record_failure()
            raise

    def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
        security: SecurityMetadata | None = None,
    ) -> str:
        """Execute a tool via this provider, tracking latency and errors."""
        start = time.monotonic()
        try:
            result = self._client.call_tool(name, arguments, security)
            latency_ms = (time.monotonic() - start) * 1000
            self._metrics.record_success(latency_ms)
            return result
        except (ValueError, ConnectionError, CircuitOpenError):
            self._metrics.record_failure()
            raise

    def health_check(self) -> dict[str, Any]:
        """Return current health snapshot for this provider."""
        return {
            "name": self.name,
            "cloud_type": self.cloud_type,
            "region": self.region,
            "enabled": self.enabled,
            "status": self.status.value,
            "priority": self.priority,
            "weight": self.weight,
            "metrics": {
                "total_requests": self._metrics.total_requests,
                "total_failures": self._metrics.total_failures,
                "error_rate": round(self._metrics.error_rate, 4),
                "avg_latency_ms": round(self._metrics.avg_latency_ms, 2),
                "consecutive_failures": self._metrics.consecutive_failures,
                "consecutive_successes": self._metrics.consecutive_successes,
            },
            "tags": self.tags,
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize provider config (no secrets)."""
        return {
            "name": self.name,
            "cloud_type": self.cloud_type,
            "region": self.region,
            "url": self.config.url,
            "enabled": self.enabled,
            "priority": self.priority,
            "weight": self.weight,
            "status": self.status.value,
            "tags": self.tags,
        }
