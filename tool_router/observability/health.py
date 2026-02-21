"""Health check functionality for tool router service."""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

from tool_router.core.config import GatewayConfig
from tool_router.gateway.client import HTTPGatewayClient


class HealthStatus(Enum):
    """Health check status values."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    """Health status of a single component."""

    name: str
    status: HealthStatus
    message: str | None = None
    latency_ms: float | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class HealthCheckResult:
    """Overall health check result."""

    status: HealthStatus
    components: list[ComponentHealth]
    timestamp: float
    version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "status": self.status.value,
            "timestamp": self.timestamp,
            "version": self.version,
            "components": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "message": c.message,
                    "latency_ms": c.latency_ms,
                    "metadata": c.metadata,
                }
                for c in self.components
            ],
        }


class HealthCheck:
    """Health check coordinator for tool router service."""

    def __init__(self, config: GatewayConfig | None = None) -> None:
        """Initialize health checker.

        Args:
            config: Gateway configuration (uses default from env if None)
        """
        if config is None:
            try:
                self.config = GatewayConfig.load_from_environment()
            except ValueError:
                # If env vars not set, use minimal config for testing
                self.config = GatewayConfig(url="http://localhost:4444", jwt="")
        else:
            self.config = config

    def check_gateway_connection(self) -> ComponentHealth:
        """Check gateway API connectivity and response time."""
        check_start_time = time.perf_counter()
        try:
            client = HTTPGatewayClient(self.config)
            tools = client.get_tools()
            latency_milliseconds = (time.perf_counter() - check_start_time) * 1000

            if not tools:
                return ComponentHealth(
                    name="gateway",
                    status=HealthStatus.DEGRADED,
                    message="Gateway reachable but no tools available",
                    latency_ms=latency_milliseconds,
                    metadata={"tool_count": 0},
                )

            return ComponentHealth(
                name="gateway",
                status=HealthStatus.HEALTHY,
                message="Gateway connection successful",
                latency_ms=latency_milliseconds,
                metadata={"tool_count": len(tools)},
            )

        except ValueError as error:
            latency_milliseconds = (time.perf_counter() - check_start_time) * 1000
            return ComponentHealth(
                name="gateway",
                status=HealthStatus.UNHEALTHY,
                message=f"Gateway error: {error}",
                latency_ms=latency_milliseconds,
            )
        except (OSError, RuntimeError) as unexpected_error:
            latency_milliseconds = (time.perf_counter() - check_start_time) * 1000
            return ComponentHealth(
                name="gateway",
                status=HealthStatus.UNHEALTHY,
                message=f"Unexpected error: {type(unexpected_error).__name__}: {unexpected_error}",
                latency_ms=latency_milliseconds,
            )

    def check_configuration(self) -> ComponentHealth:
        """Validate configuration is properly set."""
        try:
            if not self.config.url:
                return ComponentHealth(
                    name="configuration",
                    status=HealthStatus.UNHEALTHY,
                    message="Gateway URL not configured",
                )

            if not self.config.jwt:
                return ComponentHealth(
                    name="configuration",
                    status=HealthStatus.UNHEALTHY,
                    message="JWT token not configured",
                )

            # Check timeout values are reasonable
            if self.config.timeout_ms < 1000 or self.config.timeout_ms > 300000:
                return ComponentHealth(
                    name="configuration",
                    status=HealthStatus.DEGRADED,
                    message=f"Timeout {self.config.timeout_ms}ms outside recommended range (1000-300000)",
                    metadata={
                        "timeout_ms": self.config.timeout_ms,
                        "max_retries": self.config.max_retries,
                    },
                )

            return ComponentHealth(
                name="configuration",
                status=HealthStatus.HEALTHY,
                message="Configuration valid",
                metadata={
                    "url": self.config.url,
                    "timeout_ms": self.config.timeout_ms,
                    "max_retries": self.config.max_retries,
                },
            )

        except (ValueError, AttributeError, TypeError) as error:
            return ComponentHealth(
                name="configuration",
                status=HealthStatus.UNHEALTHY,
                message=f"Configuration error: {error}",
            )

    def check_all(self) -> HealthCheckResult:
        """Run all health checks and return aggregated result."""
        components = [
            self.check_configuration(),
            self.check_gateway_connection(),
        ]

        # Determine overall status
        if any(c.status == HealthStatus.UNHEALTHY for c in components):
            overall_status = HealthStatus.UNHEALTHY
        elif any(c.status == HealthStatus.DEGRADED for c in components):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        return HealthCheckResult(
            status=overall_status,
            components=components,
            timestamp=time.time(),
        )

    def check_readiness(self) -> bool:
        """Quick readiness check - returns True if service can handle requests."""
        result = self.check_all()
        return result.status != HealthStatus.UNHEALTHY

    def check_liveness(self) -> bool:
        """Quick liveness check - returns True if service is running."""
        # For now, if we can check config, we're alive
        config_health = self.check_configuration()
        return config_health.status != HealthStatus.UNHEALTHY
