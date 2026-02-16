"""Unit tests for health API."""

from __future__ import annotations

from tool_router.api.health import get_ai_router_health
from tool_router.observability.health import HealthStatus


class TestGetAIRouterHealth:
    """Tests for get_ai_router_health."""

    def test_health_ai_enabled_available(self, mocker):
        """Test health when AI is enabled and Ollama is available."""
        mock_config = mocker.Mock()
        mock_config.ai.enabled = True
        mock_config.ai.provider = "ollama"
        mock_config.ai.model = "llama3.2:3b"
        mock_config.ai.endpoint = "http://localhost:11434"
        mock_config.ai.timeout_ms = 2000
        mock_config.ai.weight = 0.7
        mock_config.ai.min_confidence = 0.6

        mock_selector = mocker.Mock()
        mock_selector.is_available.return_value = True

        result = get_ai_router_health(config=mock_config, ai_selector=mock_selector)

        assert result["status"] == HealthStatus.HEALTHY.value
        assert result["ai_enabled"] is True
        assert result["ollama_available"] is True
        assert len(result["issues"]) == 0

    def test_health_ai_enabled_unavailable(self, mocker):
        """Test health when AI is enabled but Ollama is unavailable."""
        mock_config = mocker.Mock()
        mock_config.ai.enabled = True
        mock_config.ai.provider = "ollama"
        mock_config.ai.model = "llama3.2:3b"
        mock_config.ai.endpoint = "http://localhost:11434"
        mock_config.ai.timeout_ms = 2000
        mock_config.ai.weight = 0.7
        mock_config.ai.min_confidence = 0.6

        mock_selector = mocker.Mock()
        mock_selector.is_available.return_value = False

        result = get_ai_router_health(config=mock_config, ai_selector=mock_selector)

        assert result["status"] == HealthStatus.DEGRADED.value
        assert result["ai_enabled"] is True
        assert result["ollama_available"] is False
        assert len(result["issues"]) > 0
        assert "not available" in result["issues"][0]

    def test_health_ai_disabled(self, mocker):
        """Test health when AI is disabled."""
        mock_config = mocker.Mock()
        mock_config.ai.enabled = False
        mock_config.ai.provider = "ollama"
        mock_config.ai.model = "llama3.2:3b"
        mock_config.ai.endpoint = "http://localhost:11434"
        mock_config.ai.timeout_ms = 2000
        mock_config.ai.weight = 0.7
        mock_config.ai.min_confidence = 0.6

        result = get_ai_router_health(config=mock_config)

        assert result["status"] == HealthStatus.HEALTHY.value
        assert result["ai_enabled"] is False
        assert result["ollama_available"] is None
        assert len(result["issues"]) > 0
        assert "disabled" in result["issues"][0]

    def test_health_creates_selector_when_none(self, mocker):
        """Test that health check creates selector if not provided."""
        mock_config = mocker.Mock()
        mock_config.ai.enabled = True
        mock_config.ai.provider = "ollama"
        mock_config.ai.model = "llama3.2:3b"
        mock_config.ai.endpoint = "http://localhost:11434"
        mock_config.ai.timeout_ms = 2000
        mock_config.ai.weight = 0.7
        mock_config.ai.min_confidence = 0.6

        mock_selector_class = mocker.patch("tool_router.api.health.AIToolSelector")
        mock_selector_instance = mocker.Mock()
        mock_selector_instance.is_available.return_value = True
        mock_selector_class.return_value = mock_selector_instance

        result = get_ai_router_health(config=mock_config, ai_selector=None)

        mock_selector_class.assert_called_once()
        assert result["ollama_available"] is True

    def test_health_configuration_included(self, mocker):
        """Test that configuration is included in response."""
        mock_config = mocker.Mock()
        mock_config.ai.enabled = True
        mock_config.ai.provider = "ollama"
        mock_config.ai.model = "llama3.2:3b"
        mock_config.ai.endpoint = "http://localhost:11434"
        mock_config.ai.timeout_ms = 2000
        mock_config.ai.weight = 0.7
        mock_config.ai.min_confidence = 0.6

        mock_selector = mocker.Mock()
        mock_selector.is_available.return_value = True

        result = get_ai_router_health(config=mock_config, ai_selector=mock_selector)

        assert "configuration" in result
        assert result["configuration"]["provider"] == "ollama"
        assert result["configuration"]["model"] == "llama3.2:3b"
        assert result["configuration"]["weight"] == 0.7
