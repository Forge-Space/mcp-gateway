"""Configuration management for tool router."""

from __future__ import annotations

import os
from dataclasses import dataclass


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
        url = os.getenv("GATEWAY_URL", "http://gateway:4444").rstrip("/")
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
class AIRouterConfig:
    """AI-powered tool selection configuration."""

    enabled: bool = True
    provider: str = "ollama"
    model: str = "llama3.2:3b"
    endpoint: str = "http://ollama:11434"
    timeout_ms: int = 5000  # Increased for Ollama model cold starts; use OLLAMA_KEEP_ALIVE to prevent unloading
    weight: float = 0.7  # Weight for AI score in hybrid scoring (0.0-1.0)
    min_confidence: float = 0.3  # Minimum AI confidence threshold for using AI selection

    @classmethod
    def load_from_environment(cls) -> AIRouterConfig:
        """Load AI router configuration from environment variables.

        Args:
            No parameters.

        Returns:
            AIRouterConfig with settings from environment or defaults.

        Raises:
            ValueError: If numeric values are invalid or out of range.
        """
        enabled = os.getenv("ROUTER_AI_ENABLED", "true").lower() in ("true", "1", "yes")
        provider = os.getenv("ROUTER_AI_PROVIDER", "ollama")
        model = os.getenv("ROUTER_AI_MODEL", "llama3.2:3b")
        endpoint = os.getenv("ROUTER_AI_ENDPOINT", "http://ollama:11434").rstrip("/")

        try:
            timeout_ms = int(os.getenv("ROUTER_AI_TIMEOUT_MS", "5000"))
        except ValueError as e:
            msg = f"ROUTER_AI_TIMEOUT_MS must be a valid integer, got: {os.getenv('ROUTER_AI_TIMEOUT_MS')}"
            raise ValueError(msg) from e

        # Parse weight with separate parse and range validation
        try:
            weight = float(os.getenv("ROUTER_AI_WEIGHT", "0.7"))
        except ValueError as e:
            msg = f"ROUTER_AI_WEIGHT must be a valid float, got: {os.getenv('ROUTER_AI_WEIGHT')}"
            raise ValueError(msg) from e

        if not 0.0 <= weight <= 1.0:
            msg = f"ROUTER_AI_WEIGHT must be between 0.0 and 1.0, got: {weight}"
            raise ValueError(msg)

        # Parse min_confidence with separate parse and range validation
        try:
            min_confidence = float(os.getenv("ROUTER_AI_MIN_CONFIDENCE", "0.3"))
        except ValueError as e:
            msg = f"ROUTER_AI_MIN_CONFIDENCE must be a valid float, got: {os.getenv('ROUTER_AI_MIN_CONFIDENCE')}"
            raise ValueError(msg) from e

        if not 0.0 <= min_confidence <= 1.0:
            msg = f"ROUTER_AI_MIN_CONFIDENCE must be between 0.0 and 1.0, got: {min_confidence}"
            raise ValueError(msg)

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
    ai: AIRouterConfig
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
            ai=AIRouterConfig.load_from_environment(),
            max_tools_search=max_tools_search,
            default_top_n=default_top_n,
        )
