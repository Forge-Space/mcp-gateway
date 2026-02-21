"""Unit tests for configuration management."""

import pytest

from tool_router.core.config import AIConfig, GatewayConfig, ToolRouterConfig


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

    def test_invalid_timeout_ms(self, monkeypatch) -> None:
        """Test that invalid timeout_ms raises ValueError."""
        monkeypatch.setenv("GATEWAY_JWT", "token")
        monkeypatch.setenv("GATEWAY_TIMEOUT_MS", "invalid")

        with pytest.raises(ValueError, match="GATEWAY_TIMEOUT_MS must be a valid integer"):
            GatewayConfig.load_from_environment()

    def test_invalid_max_retries(self, monkeypatch) -> None:
        """Test that invalid max_retries raises ValueError."""
        monkeypatch.setenv("GATEWAY_JWT", "token")
        monkeypatch.setenv("GATEWAY_MAX_RETRIES", "invalid")

        with pytest.raises(ValueError, match="GATEWAY_MAX_RETRIES must be a valid integer"):
            GatewayConfig.load_from_environment()

    def test_invalid_retry_delay_ms(self, monkeypatch) -> None:
        """Test that invalid retry_delay_ms raises ValueError."""
        monkeypatch.setenv("GATEWAY_JWT", "token")
        monkeypatch.setenv("GATEWAY_RETRY_DELAY_MS", "invalid")

        with pytest.raises(ValueError, match="GATEWAY_RETRY_DELAY_MS must be a valid integer"):
            GatewayConfig.load_from_environment()


class TestAIConfig:
    """Tests for AIConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default AI configuration values."""
        config = AIConfig()

        assert config.enabled is False
        assert config.provider == "ollama"
        assert config.model == "llama3.2:3b"
        assert config.endpoint == "http://localhost:11434"
        assert config.timeout_ms == 2000
        assert config.weight == 0.7
        assert config.min_confidence == 0.3

    def test_custom_values(self) -> None:
        """Test custom AI configuration values."""
        config = AIConfig(
            enabled=True,
            provider="openai",
            model="gpt-4",
            endpoint="https://api.openai.com",
            timeout_ms=5000,
            weight=0.8,
            min_confidence=0.5,
        )

        assert config.enabled is True
        assert config.provider == "openai"
        assert config.model == "gpt-4"
        assert config.endpoint == "https://api.openai.com"
        assert config.timeout_ms == 5000
        assert config.weight == 0.8
        assert config.min_confidence == 0.5

    def test_from_env_success(self, monkeypatch) -> None:
        """Test loading AI configuration from environment variables."""
        monkeypatch.setenv("ROUTER_AI_ENABLED", "true")
        monkeypatch.setenv("ROUTER_AI_PROVIDER", "openai")
        monkeypatch.setenv("ROUTER_AI_MODEL", "gpt-4")
        monkeypatch.setenv("ROUTER_AI_ENDPOINT", "https://api.openai.com")
        monkeypatch.setenv("ROUTER_AI_TIMEOUT_MS", "5000")
        monkeypatch.setenv("ROUTER_AI_WEIGHT", "0.8")
        monkeypatch.setenv("ROUTER_AI_MIN_CONFIDENCE", "0.5")

        config = AIConfig.load_from_environment()

        assert config.enabled is True
        assert config.provider == "openai"
        assert config.model == "gpt-4"
        assert config.endpoint == "https://api.openai.com"
        assert config.timeout_ms == 5000
        assert config.weight == 0.8
        assert config.min_confidence == 0.5

    def test_from_env_defaults(self, monkeypatch) -> None:
        """Test default values when AI env vars not set."""
        # Don't set any AI env vars
        config = AIConfig.load_from_environment()

        assert config.enabled is False
        assert config.provider == "ollama"
        assert config.model == "llama3.2:3b"
        assert config.endpoint == "http://localhost:11434"
        assert config.timeout_ms == 2000
        assert config.weight == 0.7
        assert config.min_confidence == 0.3

    def test_enabled_parsing(self, monkeypatch) -> None:
        """Test boolean parsing for enabled flag."""
        test_cases = [
            ("true", True),
            ("false", False),
            ("TRUE", True),
            ("FALSE", False),
            ("1", False),  # Should be False since not "true"
            ("0", False),  # Should be False since not "true"
            ("", False),   # Empty string defaults to False
        ]

        for env_value, expected in test_cases:
            monkeypatch.setenv("ROUTER_AI_ENABLED", env_value)
            config = AIConfig.load_from_environment()
            assert config.enabled is expected, f"Failed for env value: {env_value}"

    def test_invalid_timeout_ms(self, monkeypatch) -> None:
        """Test that invalid timeout_ms raises ValueError."""
        monkeypatch.setenv("ROUTER_AI_TIMEOUT_MS", "invalid")

        with pytest.raises(ValueError, match="ROUTER_AI_TIMEOUT_MS must be a valid integer"):
            AIConfig.load_from_environment()

    def test_invalid_weight(self, monkeypatch) -> None:
        """Test that invalid weight raises ValueError."""
        monkeypatch.setenv("ROUTER_AI_WEIGHT", "invalid")

        with pytest.raises(ValueError, match="ROUTER_AI_WEIGHT must be a valid float"):
            AIConfig.load_from_environment()

    def test_invalid_min_confidence(self, monkeypatch) -> None:
        """Test that invalid min_confidence raises ValueError."""
        monkeypatch.setenv("ROUTER_AI_MIN_CONFIDENCE", "invalid")

        with pytest.raises(ValueError, match="ROUTER_AI_MIN_CONFIDENCE must be a valid float"):
            AIConfig.load_from_environment()


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

    def test_ai_config_integration(self, monkeypatch) -> None:
        """Test that ToolRouterConfig properly loads AIConfig."""
        monkeypatch.setenv("GATEWAY_JWT", "token")
        monkeypatch.setenv("ROUTER_AI_ENABLED", "true")
        monkeypatch.setenv("ROUTER_AI_PROVIDER", "openai")
        monkeypatch.setenv("ROUTER_AI_MODEL", "gpt-4")

        config = ToolRouterConfig.load_from_environment()

        assert config.ai.enabled is True
        assert config.ai.provider == "openai"
        assert config.ai.model == "gpt-4"

    def test_invalid_max_tools_search(self, monkeypatch) -> None:
        """Test that invalid max_tools_search raises ValueError."""
        monkeypatch.setenv("GATEWAY_JWT", "token")
        monkeypatch.setenv("MAX_TOOLS_SEARCH", "invalid")

        with pytest.raises(ValueError, match="MAX_TOOLS_SEARCH must be a valid integer"):
            ToolRouterConfig.load_from_environment()

    def test_invalid_default_top_n(self, monkeypatch) -> None:
        """Test that invalid default_top_n raises ValueError."""
        monkeypatch.setenv("GATEWAY_JWT", "token")
        monkeypatch.setenv("DEFAULT_TOP_N", "invalid")

        with pytest.raises(ValueError, match="DEFAULT_TOP_N must be a valid integer"):
            ToolRouterConfig.load_from_environment()

    def test_direct_instantiation(self) -> None:
        """Test direct instantiation with GatewayConfig and AIConfig."""
        gateway_config = GatewayConfig(url="http://test:4444", jwt="token")
        ai_config = AIConfig()
        config = ToolRouterConfig(gateway=gateway_config, ai=ai_config, max_tools_search=15, default_top_n=2)

        assert config.gateway == gateway_config
        assert config.ai == ai_config
        assert config.max_tools_search == 15
        assert config.default_top_n == 2


class TestGatewayConfigAdvanced:
    """Advanced tests for GatewayConfig."""
    
    def test_url_trimming(self, monkeypatch) -> None:
        """Test that URL trailing slash is trimmed."""
        monkeypatch.setenv("GATEWAY_URL", "http://gateway:4444/")
        monkeypatch.setenv("GATEWAY_JWT", "token")
        
        config = GatewayConfig.load_from_environment()
        assert config.url == "http://gateway:4444"
    
    def test_missing_jwt_error(self, monkeypatch) -> None:
        """Test that missing JWT raises ValueError."""
        monkeypatch.delenv("GATEWAY_JWT", raising=False)
        
        with pytest.raises(ValueError, match="GATEWAY_JWT environment variable is required"):
            GatewayConfig.load_from_environment()
    
    def test_invalid_timeout_ms_error(self, monkeypatch) -> None:
        """Test that invalid timeout_ms raises ValueError."""
        monkeypatch.setenv("GATEWAY_JWT", "token")
        monkeypatch.setenv("GATEWAY_TIMEOUT_MS", "invalid")
        
        with pytest.raises(ValueError, match="GATEWAY_TIMEOUT_MS must be a valid integer"):
            GatewayConfig.load_from_environment()


class TestGatewayConfigAdvanced:
    """Advanced tests for GatewayConfig."""
    
    def test_url_trimming(self, monkeypatch) -> None:
        """Test that URL trailing slash is trimmed."""
        monkeypatch.setenv("GATEWAY_URL", "http://gateway:4444/")
        monkeypatch.setenv("GATEWAY_JWT", "token")
        
        config = GatewayConfig.load_from_environment()
        assert config.url == "http://gateway:4444"
    
    def test_url_trimming_multiple_slashes(self, monkeypatch) -> None:
        """Test that multiple trailing slashes are trimmed."""
        monkeypatch.setenv("GATEWAY_URL", "http://gateway:4444///")
        monkeypatch.setenv("GATEWAY_JWT", "token")
        
        config = GatewayConfig.load_from_environment()
        assert config.url == "http://gateway:4444"
    
    def test_missing_jwt_error(self, monkeypatch) -> None:
        """Test that missing JWT raises ValueError."""
        monkeypatch.delenv("GATEWAY_JWT", raising=False)
        
        with pytest.raises(ValueError, match="GATEWAY_JWT environment variable is required"):
            GatewayConfig.load_from_environment()
    
    def test_empty_jwt_error(self, monkeypatch) -> None:
        """Test that empty JWT raises ValueError."""
        monkeypatch.setenv("GATEWAY_JWT", "")
        
        with pytest.raises(ValueError, match="GATEWAY_JWT environment variable is required"):
            GatewayConfig.load_from_environment()
    
    def test_invalid_timeout_ms_error(self, monkeypatch) -> None:
        """Test that invalid timeout_ms raises ValueError."""
        monkeypatch.setenv("GATEWAY_JWT", "token")
        monkeypatch.setenv("GATEWAY_TIMEOUT_MS", "invalid")
        
        with pytest.raises(ValueError, match="GATEWAY_TIMEOUT_MS must be a valid integer"):
            GatewayConfig.load_from_environment()
    
    def test_invalid_max_retries_error(self, monkeypatch) -> None:
        """Test that invalid max_retries raises ValueError."""
        monkeypatch.setenv("GATEWAY_JWT", "token")
        monkeypatch.setenv("GATEWAY_MAX_RETRIES", "not_a_number")
        
        with pytest.raises(ValueError, match="GATEWAY_MAX_RETRIES must be a valid integer"):
            GatewayConfig.load_from_environment()
    
    def test_invalid_retry_delay_ms_error(self, monkeypatch) -> None:
        """Test that invalid retry_delay_ms raises ValueError."""
        monkeypatch.setenv("GATEWAY_JWT", "token")
        monkeypatch.setenv("GATEWAY_RETRY_DELAY_MS", "float_value")
        
        with pytest.raises(ValueError, match="GATEWAY_RETRY_DELAY_MS must be a valid integer"):
            GatewayConfig.load_from_environment()
    
    def test_negative_timeout_ms_error(self, monkeypatch) -> None:
        """Test that negative timeout_ms raises ValueError."""
        monkeypatch.setenv("GATEWAY_JWT", "token")
        monkeypatch.setenv("GATEWAY_TIMEOUT_MS", "-1000")
        
        # This should pass validation (negative values are allowed at parsing level)
        config = GatewayConfig.load_from_environment()
        assert config.timeout_ms == -1000
    
    def test_zero_max_retries(self, monkeypatch) -> None:
        """Test that zero max_retries is allowed."""
        monkeypatch.setenv("GATEWAY_JWT", "token")
        monkeypatch.setenv("GATEWAY_MAX_RETRIES", "0")
        
        config = GatewayConfig.load_from_environment()
        assert config.max_retries == 0
    
    def test_large_numeric_values(self, monkeypatch) -> None:
        """Test handling of large numeric values."""
        monkeypatch.setenv("GATEWAY_JWT", "token")
        monkeypatch.setenv("GATEWAY_TIMEOUT_MS", "999999999")
        monkeypatch.setenv("GATEWAY_MAX_RETRIES", "1000")
        monkeypatch.setenv("GATEWAY_RETRY_DELAY_MS", "60000")
        
        config = GatewayConfig.load_from_environment()
        assert config.timeout_ms == 999999999
        assert config.max_retries == 1000
        assert config.retry_delay_ms == 60000
    
    def test_partial_environment_config(self, monkeypatch) -> None:
        """Test loading with partial environment variables."""
        monkeypatch.setenv("GATEWAY_JWT", "token")
        # Only set JWT, others should use defaults
        
        config = GatewayConfig.load_from_environment()
        assert config.url == "http://gateway:4444"  # Default
        assert config.jwt == "token"
        assert config.timeout_ms == 120000  # Default
        assert config.max_retries == 3  # Default
        assert config.retry_delay_ms == 2000  # Default


class TestAIConfigAdvanced:
    """Advanced tests for AIConfig."""
    
    def test_ai_config_with_custom_values(self) -> None:
        """Test AIConfig with custom values."""
        config = AIConfig(
            model_name="custom-model",
            temperature=0.9,
            max_tokens=2048,
            timeout_ms=60000
        )
        
        assert config.model_name == "custom-model"
        assert config.temperature == 0.9
        assert config.max_tokens == 2048
        assert config.timeout_ms == 60000
    
    def test_ai_config_edge_cases(self) -> None:
        """Test AIConfig with edge case values."""
        config = AIConfig(
            model_name="",
            temperature=0.0,
            max_tokens=1,
            timeout_ms=1000
        )
        
        assert config.model_name == ""
        assert config.temperature == 0.0
        assert config.max_tokens == 1
        assert config.timeout_ms == 1000
    
    def test_ai_config_high_values(self) -> None:
        """Test AIConfig with high values."""
        config = AIConfig(
            model_name="large-model",
            temperature=2.0,
            max_tokens=100000,
            timeout_ms=300000
        )
        
        assert config.model_name == "large-model"
        assert config.temperature == 2.0
        assert config.max_tokens == 100000
        assert config.timeout_ms == 300000


class TestToolRouterConfigAdvanced:
    """Advanced tests for ToolRouterConfig."""
    
    def test_tool_router_config_edge_cases(self) -> None:
        """Test ToolRouterConfig with edge case values."""
        gateway_config = GatewayConfig(url="http://test:4444", jwt="token")
        ai_config = AIConfig()
        
        config = ToolRouterConfig(
            gateway=gateway_config,
            ai=ai_config,
            max_tools_search=0,
            default_top_n=0
        )
        
        assert config.max_tools_search == 0
        assert config.default_top_n == 0
    
    def test_tool_router_config_large_values(self) -> None:
        """Test ToolRouterConfig with large values."""
        gateway_config = GatewayConfig(url="http://test:4444", jwt="token")
        ai_config = AIConfig()
        
        config = ToolRouterConfig(
            gateway=gateway_config,
            ai=ai_config,
            max_tools_search=10000,
            default_top_n=1000
        )
        
        assert config.max_tools_search == 10000
        assert config.default_top_n == 1000
    
    def test_tool_router_config_from_env_complex(self, monkeypatch) -> None:
        """Test ToolRouterConfig from environment with complex values."""
        # Set all environment variables
        monkeypatch.setenv("GATEWAY_URL", "https://production.example.com")
        monkeypatch.setenv("GATEWAY_JWT", "production-jwt-token")
        monkeypatch.setenv("GATEWAY_TIMEOUT_MS", "60000")
        monkeypatch.setenv("GATEWAY_MAX_RETRIES", "5")
        monkeypatch.setenv("GATEWAY_RETRY_DELAY_MS", "5000")
        monkeypatch.setenv("AI_MODEL_NAME", "gpt-4-turbo")
        monkeypatch.setenv("AI_TEMPERATURE", "0.7")
        monkeypatch.setenv("AI_MAX_TOKENS", "4096")
        monkeypatch.setenv("AI_TIMEOUT_MS", "120000")
        monkeypatch.setenv("MAX_TOOLS_SEARCH", "50")
        monkeypatch.setenv("DEFAULT_TOP_N", "5")
        
        config = ToolRouterConfig.load_from_environment()
        
        # Verify GatewayConfig
        assert config.gateway.url == "https://production.example.com"
        assert config.gateway.jwt == "production-jwt-token"
        assert config.gateway.timeout_ms == 60000
        assert config.gateway.max_retries == 5
        assert config.gateway.retry_delay_ms == 5000
        
        # Verify AIConfig
        assert config.ai.model_name == "gpt-4-turbo"
        assert config.ai.temperature == 0.7
        assert config.ai.max_tokens == 4096
        assert config.ai.timeout_ms == 120000
        
        # Verify ToolRouterConfig
        assert config.max_tools_search == 50
        assert config.default_top_n == 5
