"""Multi-cloud routing layer for MCP Gateway.

Provides cloud provider abstraction, health monitoring, and intelligent
failover across AWS, Azure, GCP, and custom cloud endpoints.
"""

from tool_router.cloud.provider import CloudProvider, CloudProviderStatus
from tool_router.cloud.router import MultiCloudRouter, RoutingStrategy


__all__ = [
    "CloudProvider",
    "CloudProviderStatus",
    "MultiCloudRouter",
    "RoutingStrategy",
]
