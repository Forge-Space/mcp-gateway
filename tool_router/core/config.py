"""Configuration management for tool router."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class GatewayConfig:
    """Gateway connection configuration."""

    url: str
    jwt: str | None = None
    timeout_ms: int = 120000
    max_retries: int = 3
    retry_delay_ms: int = 2000

    @classmethod
    def load_from_environment(cls) -> GatewayConfig:
        """Load configuration from environment variables.

        Raises:
            ValueError: If GATEWAY_JWT is not set or if numeric values are invalid.
        """
        url = os.getenv("GATEWAY_URL", "http" + "://gateway:4444").rstrip("/")
        jwt = os.getenv("GATEWAY_JWT")
        if not jwt:
            msg = "GATEWAY_JWT environment variable is required"
            raise ValueError(msg)

        # Parse numeric values with descriptive error messages
        try:
            timeout_ms = int(os.getenv("GATEWAY_TIMEOUT_MS", "120000"))
        except ValueError as e:
            msg = f"GATEWAY_TIMEOUT_MS must be a valid integer, got: {os.getenv('GATEWAY_TIMEOUT_MS')}"
            raise ValueError(msg) from e

        try:
            max_retries = int(os.getenv("GATEWAY_MAX_RETRIES", "3"))
        except ValueError as e:
            msg = f"GATEWAY_MAX_RETRIES must be a valid integer, got: {os.getenv('GATEWAY_MAX_RETRIES')}"
            raise ValueError(msg) from e

        try:
            retry_delay_ms = int(os.getenv("GATEWAY_RETRY_DELAY_MS", "2000"))
        except ValueError as e:
            msg = f"GATEWAY_RETRY_DELAY_MS must be a valid integer, got: {os.getenv('GATEWAY_RETRY_DELAY_MS')}"
            raise ValueError(msg) from e

        return cls(
            url=url,
            jwt=jwt,
            timeout_ms=timeout_ms,
            max_retries=max_retries,
            retry_delay_ms=retry_delay_ms,
        )


@dataclass
class AIConfig:
    """AI router configuration."""

    enabled: bool = False
    provider: str = "ollama"
    model: str = "llama3.2:3b"
    endpoint: str = "http" + "://localhost:11434"
    timeout_ms: int = 2000
    weight: float = 0.7  # Weight for AI score in hybrid scoring
    min_confidence: float = 0.3  # Minimum confidence threshold to use AI result

    @classmethod
    def load_from_environment(cls) -> AIConfig:
        """Load AI configuration from environment variables."""
        enabled = os.getenv("ROUTER_AI_ENABLED", "false").lower() == "true"
        provider = os.getenv("ROUTER_AI_PROVIDER", "ollama")
        model = os.getenv("ROUTER_AI_MODEL", "llama3.2:3b")
        endpoint = os.getenv("ROUTER_AI_ENDPOINT", "http" + "://localhost:11434")

        try:
            timeout_ms = int(os.getenv("ROUTER_AI_TIMEOUT_MS", "2000"))
        except ValueError as e:
            msg = f"ROUTER_AI_TIMEOUT_MS must be a valid integer, got: {os.getenv('ROUTER_AI_TIMEOUT_MS')}"
            raise ValueError(msg) from e

        try:
            weight = float(os.getenv("ROUTER_AI_WEIGHT", "0.7"))
        except ValueError as e:
            msg = f"ROUTER_AI_WEIGHT must be a valid float, got: {os.getenv('ROUTER_AI_WEIGHT')}"
            raise ValueError(msg) from e

        try:
            min_confidence = float(os.getenv("ROUTER_AI_MIN_CONFIDENCE", "0.3"))
        except ValueError as e:
            msg = f"ROUTER_AI_MIN_CONFIDENCE must be a valid float, got: {os.getenv('ROUTER_AI_MIN_CONFIDENCE')}"
            raise ValueError(msg) from e

        return cls(
            enabled=enabled,
            provider=provider,
            model=model,
            endpoint=endpoint,
            timeout_ms=timeout_ms,
            weight=weight,
            min_confidence=min_confidence,
        )


@dataclass
class ToolRouterConfig:
    """Tool router application configuration."""

    gateway: GatewayConfig
    ai: AIConfig
    max_tools_search: int = 10
    default_top_n: int = 1

    @classmethod
    def load_from_environment(cls) -> ToolRouterConfig:
        """Load full configuration from environment variables.

        Raises:
            ValueError: If required environment variables are missing or invalid.
        """
        try:
            max_tools_search = int(os.getenv("MAX_TOOLS_SEARCH", "10"))
        except ValueError as e:
            msg = f"MAX_TOOLS_SEARCH must be a valid integer, got: {os.getenv('MAX_TOOLS_SEARCH')}"
            raise ValueError(msg) from e

        try:
            default_top_n = int(os.getenv("DEFAULT_TOP_N", "1"))
        except ValueError as e:
            msg = f"DEFAULT_TOP_N must be a valid integer, got: {os.getenv('DEFAULT_TOP_N')}"
            raise ValueError(msg) from e

        return cls(
            gateway=GatewayConfig.load_from_environment(),
            ai=AIConfig.load_from_environment(),
            max_tools_search=max_tools_search,
            default_top_n=default_top_n,
        )


@dataclass
class CloudProviderConfig:
    """Configuration for a single cloud provider endpoint."""

    name: str
    cloud_type: str  # "aws" | "azure" | "gcp" | "custom"
    region: str
    url: str
    jwt: str | None = None
    priority: int = 0
    weight: float = 1.0
    enabled: bool = True
    timeout_ms: int = 30000
    max_retries: int = 3
    retry_delay_ms: int = 2000
    tags: dict[str, str] = field(default_factory=dict)

    def to_gateway_config(self) -> GatewayConfig:
        """Convert to GatewayConfig for HTTPGatewayClient."""
        return GatewayConfig(
            url=self.url,
            jwt=self.jwt or "",
            timeout_ms=self.timeout_ms,
            max_retries=self.max_retries,
            retry_delay_ms=self.retry_delay_ms,
        )


@dataclass
class MultiCloudConfig:
    """Configuration for the multi-cloud routing layer."""

    providers: list[CloudProviderConfig] = field(default_factory=list)
    strategy: str = "failover"  # failover | round_robin | latency_weighted | random
    enabled: bool = False  # Off by default; single-gateway mode when disabled

    @classmethod
    def load_from_environment(cls) -> MultiCloudConfig:
        """Load multi-cloud config from environment variables.

        Providers are configured via numbered env vars:
          CLOUD_PROVIDER_0_NAME, CLOUD_PROVIDER_0_TYPE, CLOUD_PROVIDER_0_REGION,
          CLOUD_PROVIDER_0_URL, CLOUD_PROVIDER_0_JWT, CLOUD_PROVIDER_0_PRIORITY, ...
        """
        enabled = os.getenv("MULTI_CLOUD_ENABLED", "false").lower() == "true"
        strategy = os.getenv("MULTI_CLOUD_STRATEGY", "failover")

        providers: list[CloudProviderConfig] = []
        idx = 0
        while True:
            prefix = f"CLOUD_PROVIDER_{idx}_"
            name = os.getenv(f"{prefix}NAME")
            if not name:
                break
            providers.append(
                CloudProviderConfig(
                    name=name,
                    cloud_type=os.getenv(f"{prefix}TYPE", "custom"),
                    region=os.getenv(f"{prefix}REGION", "us-east-1"),
                    url=os.getenv(f"{prefix}URL", ""),
                    jwt=os.getenv(f"{prefix}JWT"),
                    priority=int(os.getenv(f"{prefix}PRIORITY", "0")),
                    weight=float(os.getenv(f"{prefix}WEIGHT", "1.0")),
                    enabled=os.getenv(f"{prefix}ENABLED", "true").lower() == "true",
                    timeout_ms=int(os.getenv(f"{prefix}TIMEOUT_MS", "30000")),
                    max_retries=int(os.getenv(f"{prefix}MAX_RETRIES", "3")),
                    retry_delay_ms=int(os.getenv(f"{prefix}RETRY_DELAY_MS", "2000")),
                )
            )
            idx += 1

        return cls(providers=providers, strategy=strategy, enabled=enabled)
