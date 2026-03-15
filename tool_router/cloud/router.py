"""Multi-cloud router with pluggable routing strategies.

Strategies:
  FAILOVER         — try providers in priority order; skip unhealthy
  ROUND_ROBIN      — cycle through healthy providers
  LATENCY_WEIGHTED — prefer lowest avg latency among healthy providers
  RANDOM           — uniform random selection (useful for testing)
"""

from __future__ import annotations

import logging
import random
from enum import Enum
from typing import Any

from tool_router.cloud.provider import CloudProvider, CloudProviderStatus
from tool_router.gateway.client import SecurityMetadata
from tool_router.observability.tracing import SpanContext


logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    FAILOVER = "failover"
    ROUND_ROBIN = "round_robin"
    LATENCY_WEIGHTED = "latency_weighted"
    RANDOM = "random"


class NoHealthyProviderError(Exception):
    """Raised when all providers are unhealthy or unavailable."""


class MultiCloudRouter:
    """Routes MCP tool calls across multiple cloud providers.

    Maintains a registry of CloudProvider instances and selects the
    best provider per request based on the configured strategy.
    Automatically falls back to the next available provider on failure.
    """

    def __init__(
        self,
        providers: list[CloudProvider] | None = None,
        strategy: RoutingStrategy = RoutingStrategy.FAILOVER,
    ) -> None:
        self._providers: list[CloudProvider] = providers or []
        self._strategy = strategy
        self._rr_index = 0  # Round-robin cursor

    # ------------------------------------------------------------------
    # Provider registry
    # ------------------------------------------------------------------

    def add_provider(self, provider: CloudProvider) -> None:
        """Register a new cloud provider."""
        if any(p.name == provider.name for p in self._providers):
            msg = f"Provider '{provider.name}' already registered"
            raise ValueError(msg)
        self._providers.append(provider)
        logger.info("Registered cloud provider: %s (%s/%s)", provider.name, provider.cloud_type, provider.region)

    def remove_provider(self, name: str) -> bool:
        """Unregister a provider by name. Returns True if found."""
        before = len(self._providers)
        self._providers = [p for p in self._providers if p.name != name]
        return len(self._providers) < before

    def get_provider(self, name: str) -> CloudProvider | None:
        """Look up a provider by name."""
        return next((p for p in self._providers if p.name == name), None)

    def list_providers(self) -> list[CloudProvider]:
        return list(self._providers)

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    def _healthy_providers(self) -> list[CloudProvider]:
        return [
            p
            for p in self._providers
            if p.enabled and p.status in (CloudProviderStatus.HEALTHY, CloudProviderStatus.UNKNOWN)
        ]

    def _select_provider(self) -> CloudProvider:
        """Select a provider according to the current strategy."""
        healthy = self._healthy_providers()
        if not healthy:
            # Degrade gracefully: try DEGRADED providers before giving up
            degraded = [p for p in self._providers if p.enabled and p.status == CloudProviderStatus.DEGRADED]
            if degraded:
                healthy = degraded
            else:
                raise NoHealthyProviderError("No healthy or degraded cloud providers available")

        if self._strategy == RoutingStrategy.FAILOVER:
            return sorted(healthy, key=lambda p: p.priority)[0]

        if self._strategy == RoutingStrategy.ROUND_ROBIN:
            provider = healthy[self._rr_index % len(healthy)]
            self._rr_index = (self._rr_index + 1) % len(healthy)
            return provider

        if self._strategy == RoutingStrategy.LATENCY_WEIGHTED:
            # Prefer lowest avg latency; treat UNKNOWN (0ms) as neutral
            return min(healthy, key=lambda p: p.metrics.avg_latency_ms or float("inf"))

        if self._strategy == RoutingStrategy.RANDOM:
            return random.choice(healthy)  # noqa: S311

        return healthy[0]

    def get_tools(self) -> list[dict[str, Any]]:
        """Fetch tools, trying providers in strategy order until one succeeds."""
        with SpanContext("cloud.get_tools") as span:
            errors: list[str] = []
            tried: list[str] = []

            for provider in self._ordered_providers():
                tried.append(provider.name)
                try:
                    tools = provider.get_tools()
                    span.set_attribute("cloud.provider", provider.name)
                    span.set_attribute("cloud.type", provider.cloud_type)
                    span.set_attribute("cloud.region", provider.region)
                    logger.debug("get_tools succeeded via %s", provider.name)
                    return tools
                except Exception as exc:
                    errors.append(f"{provider.name}: {exc}")
                    logger.warning("get_tools failed on %s: %s", provider.name, exc)

            span.set_attribute("cloud.all_failed", True)
            msg = f"All providers failed get_tools. Tried: {tried}. Errors: {errors}"
            raise NoHealthyProviderError(msg)

    def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
        security: SecurityMetadata | None = None,
    ) -> str:
        """Execute a tool, trying providers in strategy order until one succeeds."""
        with SpanContext("cloud.call_tool") as span:
            span.set_attribute("tool.name", name)
            errors: list[str] = []
            tried: list[str] = []

            for provider in self._ordered_providers():
                tried.append(provider.name)
                try:
                    result = provider.call_tool(name, arguments, security)
                    span.set_attribute("cloud.provider", provider.name)
                    span.set_attribute("cloud.type", provider.cloud_type)
                    logger.debug("call_tool '%s' succeeded via %s", name, provider.name)
                    return result
                except Exception as exc:
                    errors.append(f"{provider.name}: {exc}")
                    logger.warning("call_tool '%s' failed on %s: %s", name, provider.name, exc)

            span.set_attribute("cloud.all_failed", True)
            msg = f"All providers failed call_tool '{name}'. Tried: {tried}. Errors: {errors}"
            raise NoHealthyProviderError(msg)

    def _ordered_providers(self) -> list[CloudProvider]:
        """Return providers in the order they should be tried for failover."""
        if self._strategy == RoutingStrategy.FAILOVER:
            enabled = [p for p in self._providers if p.enabled]
            return sorted(enabled, key=lambda p: (p.status.value == "unhealthy", p.priority))

        if self._strategy == RoutingStrategy.ROUND_ROBIN:
            healthy = self._healthy_providers()
            if not healthy:
                return [p for p in self._providers if p.enabled]
            # Rotate starting from current index
            start = self._rr_index % len(healthy)
            self._rr_index = (self._rr_index + 1) % len(healthy)
            return healthy[start:] + healthy[:start]

        if self._strategy == RoutingStrategy.LATENCY_WEIGHTED:
            healthy = self._healthy_providers()
            if not healthy:
                return [p for p in self._providers if p.enabled]
            return sorted(healthy, key=lambda p: p.metrics.avg_latency_ms or float("inf"))

        if self._strategy == RoutingStrategy.RANDOM:
            healthy = self._healthy_providers()
            if not healthy:
                return [p for p in self._providers if p.enabled]
            shuffled = list(healthy)
            random.shuffle(shuffled)
            return shuffled

        return [p for p in self._providers if p.enabled]

    # ------------------------------------------------------------------
    # Health + status
    # ------------------------------------------------------------------

    def health_summary(self) -> dict[str, Any]:
        """Return aggregated health across all providers."""
        providers_health = [p.health_check() for p in self._providers]
        healthy_count = sum(1 for p in self._providers if p.status == CloudProviderStatus.HEALTHY)
        degraded_count = sum(1 for p in self._providers if p.status == CloudProviderStatus.DEGRADED)
        unhealthy_count = sum(1 for p in self._providers if p.status == CloudProviderStatus.UNHEALTHY)

        overall = "healthy"
        if healthy_count == 0 and degraded_count == 0:
            overall = "unhealthy"
        elif healthy_count == 0:
            overall = "degraded"

        return {
            "overall": overall,
            "strategy": self._strategy.value,
            "total_providers": len(self._providers),
            "healthy": healthy_count,
            "degraded": degraded_count,
            "unhealthy": unhealthy_count,
            "providers": providers_health,
        }

    def set_strategy(self, strategy: RoutingStrategy) -> None:
        self._strategy = strategy
        self._rr_index = 0
