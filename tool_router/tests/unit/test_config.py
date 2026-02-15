"""Unit tests for configuration management."""

from __future__ import annotations

import pytest

from tool_router.core.config import GatewayConfig, ToolRouterConfig


class TestGatewayConfig:
    """Tests for GatewayConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = GatewayConfig(url="http://test:4444", jwt="token")

        assert config.url == "http://test:4444"
        assert config.jwt == "token"
        assert config.timeout_ms == 120000
        assert config.max_retries == 3
        assert config.retry_delay_ms == 2000

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = GatewayConfig(
            url="http://custom:8080",
            jwt="custom-token",
            timeout_ms=5000,
            max_retries=5,
            retry_delay_ms=1000,
        )

        assert config.url == "http://custom:8080"
        assert config.jwt == "custom-token"
        assert config.timeout_ms == 5000
        assert config.max_retries == 5
        assert config.retry_delay_ms == 1000

    def test_from_env_success(self, monkeypatch) -> None:
        """Test loading configuration from environment variables."""
        monkeypatch.setenv("GATEWAY_URL", "http://env-gateway:4444")
        monkeypatch.setenv("GATEWAY_JWT", "env-token")
        monkeypatch.setenv("GATEWAY_TIMEOUT_MS", "30000")
        monkeypatch.setenv("GATEWAY_MAX_RETRIES", "5")
        monkeypatch.setenv("GATEWAY_RETRY_DELAY_MS", "1500")

        config = GatewayConfig.load_from_environment()

        assert config.url == "http://env-gateway:4444"
        assert config.jwt == "env-token"
        assert config.timeout_ms == 30000
        assert config.max_retries == 5
        assert config.retry_delay_ms == 1500

    def test_from_env_missing_jwt(self, monkeypatch) -> None:
        """Test that missing JWT raises ValueError."""
        monkeypatch.delenv("GATEWAY_JWT", raising=False)

        with pytest.raises(ValueError, match="GATEWAY_JWT environment variable"):
            GatewayConfig.load_from_environment()

    def test_from_env_defaults(self, monkeypatch) -> None:
        """Test default values when env vars not set."""
        monkeypatch.setenv("GATEWAY_JWT", "token")
        monkeypatch.delenv("GATEWAY_URL", raising=False)
        monkeypatch.delenv("GATEWAY_TIMEOUT_MS", raising=False)
        monkeypatch.delenv("GATEWAY_MAX_RETRIES", raising=False)
        monkeypatch.delenv("GATEWAY_RETRY_DELAY_MS", raising=False)

        config = GatewayConfig.load_from_environment()

        assert config.url == "http://gateway:4444"
        assert config.timeout_ms == 120000
        assert config.max_retries == 3
        assert config.retry_delay_ms == 2000

    def test_url_trailing_slash_stripped(self, monkeypatch) -> None:
        """Test that trailing slashes are removed from URL."""
        monkeypatch.setenv("GATEWAY_URL", "http://gateway:4444/")
        monkeypatch.setenv("GATEWAY_JWT", "token")

        config = GatewayConfig.load_from_environment()

        assert config.url == "http://gateway:4444"
        assert not config.url.endswith("/")


class TestToolRouterConfig:
    """Tests for ToolRouterConfig dataclass."""

    def test_default_values(self, monkeypatch) -> None:
        """Test default configuration values."""
        monkeypatch.setenv("GATEWAY_JWT", "token")

        config = ToolRouterConfig.load_from_environment()

        assert config.max_tools_search == 10
        assert config.default_top_n == 1
        assert isinstance(config.gateway, GatewayConfig)

    def test_custom_values(self, monkeypatch) -> None:
        """Test custom configuration values."""
        monkeypatch.setenv("GATEWAY_JWT", "token")
        monkeypatch.setenv("MAX_TOOLS_SEARCH", "20")
        monkeypatch.setenv("DEFAULT_TOP_N", "3")

        config = ToolRouterConfig.load_from_environment()

        assert config.max_tools_search == 20
        assert config.default_top_n == 3

    def test_gateway_config_integration(self, monkeypatch) -> None:
        """Test that ToolRouterConfig properly loads GatewayConfig."""
        monkeypatch.setenv("GATEWAY_URL", "http://test:4444")
        monkeypatch.setenv("GATEWAY_JWT", "test-token")
        monkeypatch.setenv("GATEWAY_TIMEOUT_MS", "10000")

        config = ToolRouterConfig.load_from_environment()

        assert config.gateway.url == "http://test:4444"
        assert config.gateway.jwt == "test-token"
        assert config.gateway.timeout_ms == 10000

    def test_from_env_propagates_gateway_error(self, monkeypatch) -> None:
        """Test that GatewayConfig errors propagate correctly."""
        monkeypatch.delenv("GATEWAY_JWT", raising=False)

        with pytest.raises(ValueError, match="GATEWAY_JWT"):
            ToolRouterConfig.load_from_environment()

    def test_direct_instantiation(self) -> None:
        """Test direct instantiation with GatewayConfig."""
        gateway_config = GatewayConfig(url="http://test:4444", jwt="token")
        config = ToolRouterConfig(gateway=gateway_config, max_tools_search=15, default_top_n=2)

        assert config.gateway == gateway_config
        assert config.max_tools_search == 15
        assert config.default_top_n == 2
