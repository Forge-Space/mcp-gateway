"""Unit tests for tool_router/core/config.py module."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from tool_router.core.config import AIConfig, GatewayConfig, ToolRouterConfig


def test_gateway_config_dataclass() -> None:
    """Test GatewayConfig dataclass structure."""
    config = GatewayConfig(
        url="http://localhost:4444",
        jwt="test-token",
        timeout_ms=5000,
        max_retries=2,
        retry_delay_ms=1000,
    )

    assert config.url == "http://localhost:4444"
    assert config.jwt == "test-token"
    assert config.timeout_ms == 5000
    assert config.max_retries == 2
    assert config.retry_delay_ms == 1000


def test_gateway_config_defaults() -> None:
    """Test GatewayConfig default values."""
    config = GatewayConfig(url="http://localhost:4444")

    assert config.jwt is None
    assert config.timeout_ms == 120000
    assert config.max_retries == 3
    assert config.retry_delay_ms == 2000


def test_gateway_config_load_from_environment_success() -> None:
    """Test GatewayConfig.load_from_environment with valid env vars."""
    env_vars = {
        "GATEWAY_URL": "http://test:4444/",
        "GATEWAY_JWT": "test-jwt",
        "GATEWAY_TIMEOUT_MS": "5000",
        "GATEWAY_MAX_RETRIES": "2",
        "GATEWAY_RETRY_DELAY_MS": "1000",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        config = GatewayConfig.load_from_environment()

    assert config.url == "http://test:4444"
    assert config.jwt == "test-jwt"
    assert config.timeout_ms == 5000
    assert config.max_retries == 2
    assert config.retry_delay_ms == 1000


def test_gateway_config_load_from_environment_missing_jwt() -> None:
    """Test GatewayConfig.load_from_environment raises error when JWT missing."""
    env_vars = {
        "GATEWAY_URL": "http://test:4444",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        with pytest.raises(
            ValueError, match="GATEWAY_JWT environment variable is required"
        ):
            GatewayConfig.load_from_environment()


def test_gateway_config_load_from_environment_invalid_timeout() -> None:
    """Test GatewayConfig.load_from_environment raises error for invalid timeout."""
    env_vars = {
        "GATEWAY_URL": "http://test:4444",
        "GATEWAY_JWT": "test-jwt",
        "GATEWAY_TIMEOUT_MS": "invalid",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        with pytest.raises(
            ValueError, match="GATEWAY_TIMEOUT_MS must be a valid integer"
        ):
            GatewayConfig.load_from_environment()


def test_gateway_config_load_from_environment_invalid_max_retries() -> None:
    """Test GatewayConfig.load_from_environment raises error for invalid max_retries."""
    env_vars = {
        "GATEWAY_URL": "http://test:4444",
        "GATEWAY_JWT": "test-jwt",
        "GATEWAY_MAX_RETRIES": "invalid",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        with pytest.raises(
            ValueError, match="GATEWAY_MAX_RETRIES must be a valid integer"
        ):
            GatewayConfig.load_from_environment()


def test_gateway_config_load_from_environment_invalid_retry_delay() -> None:
    """Test GatewayConfig.load_from_environment raises error for invalid retry_delay."""
    env_vars = {
        "GATEWAY_URL": "http://test:4444",
        "GATEWAY_JWT": "test-jwt",
        "GATEWAY_RETRY_DELAY_MS": "invalid",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        with pytest.raises(
            ValueError, match="GATEWAY_RETRY_DELAY_MS must be a valid integer"
        ):
            GatewayConfig.load_from_environment()


def test_gateway_config_load_from_environment_defaults() -> None:
    """Test GatewayConfig.load_from_environment uses defaults when env vars missing."""
    env_vars = {
        "GATEWAY_JWT": "test-jwt",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        config = GatewayConfig.load_from_environment()

    assert config.url == "http://gateway:4444"
    assert config.jwt == "test-jwt"
    assert config.timeout_ms == 120000
    assert config.max_retries == 3
    assert config.retry_delay_ms == 2000


def test_ai_config_dataclass() -> None:
    """Test AIConfig dataclass structure."""
    config = AIConfig(
        enabled=True,
        provider="custom",
        model="custom-model",
        endpoint="http://custom:8080",
        timeout_ms=3000,
        weight=0.8,
        min_confidence=0.4,
    )

    assert config.enabled is True
    assert config.provider == "custom"
    assert config.model == "custom-model"
    assert config.endpoint == "http://custom:8080"
    assert config.timeout_ms == 3000
    assert config.weight == 0.8
    assert config.min_confidence == 0.4


def test_ai_config_defaults() -> None:
    """Test AIConfig default values."""
    config = AIConfig()

    assert config.enabled is False
    assert config.provider == "ollama"
    assert config.model == "llama3.2:3b"
    assert config.endpoint == "http://localhost:11434"
    assert config.timeout_ms == 2000
    assert config.weight == 0.7
    assert config.min_confidence == 0.3


def test_ai_config_load_from_environment_success() -> None:
    """Test AIConfig.load_from_environment with valid env vars."""
    env_vars = {
        "ROUTER_AI_ENABLED": "true",
        "ROUTER_AI_PROVIDER": "custom",
        "ROUTER_AI_MODEL": "custom-model",
        "ROUTER_AI_ENDPOINT": "http://custom:8080",
        "ROUTER_AI_TIMEOUT_MS": "3000",
        "ROUTER_AI_WEIGHT": "0.8",
        "ROUTER_AI_MIN_CONFIDENCE": "0.4",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        config = AIConfig.load_from_environment()

    assert config.enabled is True
    assert config.provider == "custom"
    assert config.model == "custom-model"
    assert config.endpoint == "http://custom:8080"
    assert config.timeout_ms == 3000
    assert config.weight == 0.8
    assert config.min_confidence == 0.4


def test_ai_config_load_from_environment_disabled() -> None:
    """Test AIConfig.load_from_environment with AI disabled."""
    env_vars = {
        "ROUTER_AI_ENABLED": "false",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        config = AIConfig.load_from_environment()

    assert config.enabled is False


def test_ai_config_load_from_environment_invalid_timeout() -> None:
    """Test AIConfig.load_from_environment raises error for invalid timeout."""
    env_vars = {
        "ROUTER_AI_TIMEOUT_MS": "invalid",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        with pytest.raises(
            ValueError, match="ROUTER_AI_TIMEOUT_MS must be a valid integer"
        ):
            AIConfig.load_from_environment()


def test_ai_config_load_from_environment_invalid_weight() -> None:
    """Test AIConfig.load_from_environment raises error for invalid weight."""
    env_vars = {
        "ROUTER_AI_WEIGHT": "invalid",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        with pytest.raises(ValueError, match="ROUTER_AI_WEIGHT must be a valid float"):
            AIConfig.load_from_environment()


def test_ai_config_load_from_environment_invalid_min_confidence() -> None:
    """Test AIConfig.load_from_environment raises error for invalid min_confidence."""
    env_vars = {
        "ROUTER_AI_MIN_CONFIDENCE": "invalid",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        with pytest.raises(
            ValueError, match="ROUTER_AI_MIN_CONFIDENCE must be a valid float"
        ):
            AIConfig.load_from_environment()


def test_ai_config_load_from_environment_defaults() -> None:
    """Test AIConfig.load_from_environment uses defaults when env vars missing."""
    with patch.dict(os.environ, {}, clear=True):
        config = AIConfig.load_from_environment()

    assert config.enabled is False
    assert config.provider == "ollama"
    assert config.model == "llama3.2:3b"
    assert config.endpoint == "http://localhost:11434"
    assert config.timeout_ms == 2000
    assert config.weight == 0.7
    assert config.min_confidence == 0.3


def test_tool_router_config_dataclass() -> None:
    """Test ToolRouterConfig dataclass structure."""
    gateway_config = GatewayConfig(url="http://test:4444", jwt="test")
    ai_config = AIConfig(enabled=True)

    config = ToolRouterConfig(
        gateway=gateway_config,
        ai=ai_config,
        max_tools_search=20,
        default_top_n=5,
    )

    assert config.gateway == gateway_config
    assert config.ai == ai_config
    assert config.max_tools_search == 20
    assert config.default_top_n == 5


def test_tool_router_config_defaults() -> None:
    """Test ToolRouterConfig default values."""
    gateway_config = GatewayConfig(url="http://test:4444", jwt="test")
    ai_config = AIConfig()

    config = ToolRouterConfig(gateway=gateway_config, ai=ai_config)

    assert config.max_tools_search == 10
    assert config.default_top_n == 1


def test_tool_router_config_load_from_environment_success() -> None:
    """Test ToolRouterConfig.load_from_environment with valid env vars."""
    env_vars = {
        "GATEWAY_URL": "http://test:4444",
        "GATEWAY_JWT": "test-jwt",
        "ROUTER_AI_ENABLED": "true",
        "MAX_TOOLS_SEARCH": "20",
        "DEFAULT_TOP_N": "5",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        config = ToolRouterConfig.load_from_environment()

    assert config.gateway.url == "http://test:4444"
    assert config.gateway.jwt == "test-jwt"
    assert config.ai.enabled is True
    assert config.max_tools_search == 20
    assert config.default_top_n == 5


def test_tool_router_config_load_from_environment_invalid_max_tools() -> None:
    """Test ToolRouterConfig.load_from_environment raises error for invalid max_tools."""
    env_vars = {
        "GATEWAY_JWT": "test-jwt",
        "MAX_TOOLS_SEARCH": "invalid",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        with pytest.raises(
            ValueError, match="MAX_TOOLS_SEARCH must be a valid integer"
        ):
            ToolRouterConfig.load_from_environment()


def test_tool_router_config_load_from_environment_invalid_default_top_n() -> None:
    """Test ToolRouterConfig.load_from_environment raises error for invalid default_top_n."""
    env_vars = {
        "GATEWAY_JWT": "test-jwt",
        "DEFAULT_TOP_N": "invalid",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        with pytest.raises(ValueError, match="DEFAULT_TOP_N must be a valid integer"):
            ToolRouterConfig.load_from_environment()


def test_tool_router_config_load_from_environment_defaults() -> None:
    """Test ToolRouterConfig.load_from_environment uses defaults when env vars missing."""
    env_vars = {
        "GATEWAY_JWT": "test-jwt",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        config = ToolRouterConfig.load_from_environment()

    assert config.max_tools_search == 10
    assert config.default_top_n == 1
    assert config.gateway.url == "http://gateway:4444"
    assert config.ai.enabled is False
