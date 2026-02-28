"""Tests for tool_router.ai.enhanced_selector module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tool_router.ai.enhanced_selector import (
    AIModel,
    AIProvider,
    BaseAISelector,
    OllamaSelector,
)


class TestAIProvider:
    """Test cases for AIProvider enum."""

    def test_ai_provider_values(self):
        """Test that AIProvider has expected values."""
        assert AIProvider.OLLAMA.value == "ollama"
        assert AIProvider.OPENAI.value == "openai"
        assert AIProvider.ANTHROPIC.value == "anthropic"

    def test_ai_provider_count(self):
        """Test number of AI providers."""
        assert len(AIProvider) == 3


class TestAIModel:
    """Test cases for AIModel enum."""

    def test_ai_model_values(self):
        """Test that AIModel has expected values."""
        assert AIModel.LLAMA32_3B.value == "llama3.2:3b"
        assert AIModel.LLAMA32_1B.value == "llama3.2:1b"
        assert AIModel.GPT4O_MINI.value == "gpt-4o-mini"
        assert AIModel.CLAUDE_SONNET.value == "claude-3-5-sonnet-20241022"

    def test_get_hardware_requirements(self):
        """Test hardware requirements for different models."""
        # Test local models
        llama3b_req = AIModel.get_hardware_requirements(AIModel.LLAMA32_3B.value)
        assert llama3b_req["ram_gb"] == 4
        assert llama3b_req["tokens_per_sec"] == 10
        assert llama3b_req["hardware_tier"] == "n100_optimal"

        tinyllama_req = AIModel.get_hardware_requirements(AIModel.TINYLLAMA.value)
        assert tinyllama_req["ram_gb"] == 1.5
        assert tinyllama_req["tokens_per_sec"] == 20
        assert tinyllama_req["hardware_tier"] == "n100_ultra_fast"

        # Test enterprise models
        gpt4_req = AIModel.get_hardware_requirements(AIModel.GPT4O.value)
        assert gpt4_req["ram_gb"] == 8
        assert gpt4_req["tokens_per_sec"] == 5
        assert gpt4_req["hardware_tier"] == "unknown"

        # Test unknown model
        unknown_req = AIModel.get_hardware_requirements("unknown-model")
        assert unknown_req["ram_gb"] == 8
        assert unknown_req["tokens_per_sec"] == 5
        assert unknown_req["hardware_tier"] == "unknown"

    def test_get_cost_per_million_tokens(self):
        """Test cost per million tokens for different models."""
        # Test OpenAI models
        gpt4o_mini_cost = AIModel.get_cost_per_million_tokens(AIModel.GPT4O_MINI.value)
        assert gpt4o_mini_cost["input"] == 0.15
        assert gpt4o_mini_cost["output"] == 0.60

        # Test Anthropic models
        claude_sonnet_cost = AIModel.get_cost_per_million_tokens(AIModel.CLAUDE_SONNET.value)
        assert claude_sonnet_cost["input"] == 3.00
        assert claude_sonnet_cost["output"] == 15.00

        # Test Google models
        gemini_flash_cost = AIModel.get_cost_per_million_tokens(AIModel.GEMINI_FLASH.value)
        assert gemini_flash_cost["input"] == 0.075
        assert gemini_flash_cost["output"] == 0.30

        # Test local models (free)
        llama_cost = AIModel.get_cost_per_million_tokens(AIModel.LLAMA32_3B.value)
        assert llama_cost["input"] == 0.0
        assert llama_cost["output"] == 0.0

        # Test unknown model
        unknown_cost = AIModel.get_cost_per_million_tokens("unknown-model")
        assert unknown_cost["input"] == 0.0
        assert unknown_cost["output"] == 0.0

    def test_is_local_model(self):
        """Test local model detection."""
        # Test local models
        assert AIModel.is_local_model(AIModel.LLAMA32_3B.value) is True
        assert AIModel.is_local_model(AIModel.LLAMA32_1B.value) is True
        assert AIModel.is_local_model(AIModel.QWEN_2_5_3B.value) is True
        assert AIModel.is_local_model(AIModel.GEMMA2_2B.value) is True
        assert AIModel.is_local_model(AIModel.PHI_3_MINI.value) is True
        assert AIModel.is_local_model(AIModel.TINYLLAMA.value) is True

        # Test enterprise models
        assert AIModel.is_local_model(AIModel.GPT4O_MINI.value) is False
        assert AIModel.is_local_model(AIModel.CLAUDE_SONNET.value) is False
        assert AIModel.is_local_model(AIModel.GEMINI_PRO.value) is False

        # Test unknown model
        assert AIModel.is_local_model("unknown-model") is False

    def test_get_model_tier(self):
        """Test model tier classification."""
        # Test ultra-fast models
        assert AIModel.get_model_tier(AIModel.TINYLLAMA.value) == "ultra_fast"
        assert AIModel.get_model_tier(AIModel.GEMMA2_2B.value) == "ultra_fast"

        # Test fast models
        assert AIModel.get_model_tier(AIModel.LLAMA32_1B.value) == "fast"
        assert AIModel.get_model_tier(AIModel.PHI_3_MINI.value) == "fast"

        # Test balanced models
        assert AIModel.get_model_tier(AIModel.LLAMA32_3B.value) == "balanced"
        assert AIModel.get_model_tier(AIModel.QWEN_2_5_3B.value) == "balanced"

        # Test premium models
        assert AIModel.get_model_tier(AIModel.GPT4O_MINI.value) == "premium"
        assert AIModel.get_model_tier(AIModel.CLAUDE_HAIKU.value) == "premium"
        assert AIModel.get_model_tier(AIModel.GEMINI_FLASH.value) == "premium"

        # Test enterprise models
        assert AIModel.get_model_tier(AIModel.GPT4O.value) == "enterprise"
        assert AIModel.get_model_tier(AIModel.GPT35_TURBO.value) == "enterprise"
        assert AIModel.get_model_tier(AIModel.CLAUDE_SONNET.value) == "enterprise"
        assert AIModel.get_model_tier(AIModel.GEMINI_PRO.value) == "enterprise"
        assert AIModel.get_model_tier(AIModel.GROK_MINI.value) == "enterprise"

        # Test unknown model
        assert AIModel.get_model_tier("unknown-model") == "unknown"


class _TestSelector(BaseAISelector):
    """Test implementation of BaseAISelector for testing."""

    __test__ = False

    def select_tool(
        self,
        task: str,
        tools: list[dict[str, any]],
        context: str = "",
        similar_tools: list[str] | None = None,
    ) -> dict[str, any] | None:
        """Test implementation."""
        return {"tool_name": "test", "confidence": 0.8, "reasoning": "test"}

    def select_tools_multi(
        self,
        task: str,
        tools: list[dict[str, any]],
        context: str = "",
        max_tools: int = 3,
    ) -> dict[str, any] | None:
        """Test implementation."""
        return {"tools": ["tool1", "tool2"], "confidence": 0.7, "reasoning": "test"}


class TestBaseAISelector:
    """Test cases for BaseAISelector abstract class."""

    def test_initialization(self):
        """Test BaseAISelector initialization."""
        selector = _TestSelector(AIModel.LLAMA32_3B.value)
        assert selector.model == AIModel.LLAMA32_3B.value
        assert selector.timeout_ms == 2000
        assert selector.timeout_s == 2.0
        assert selector.min_confidence == 0.3

        selector = _TestSelector(model=AIModel.GPT4O_MINI.value, timeout=5000, min_confidence=0.5)
        assert selector.model == AIModel.GPT4O_MINI.value
        assert selector.timeout_ms == 5000
        assert selector.timeout_s == 5.0
        assert selector.min_confidence == 0.5

    def test_abstract_methods(self):
        """Test that abstract methods raise NotImplementedError."""
        selector = _TestSelector(AIModel.LLAMA32_3B.value)

        # Since _TestSelector implements the abstract methods, we need to test
        # the abstract base class directly
        with pytest.raises(TypeError):
            BaseAISelector(AIModel.LLAMA32_3B.value)


class TestOllamaSelector:
    """Test cases for OllamaSelector."""

    def test_initialization(self):
        """Test OllamaSelector initialization."""
        # Test with default model
        selector = OllamaSelector("http://localhost:11434")
        assert selector.endpoint == "http://localhost:11434"
        assert selector.model == AIModel.LLAMA32_3B.value
        assert selector.timeout_ms == 2000
        assert selector.min_confidence == 0.3

        # Test with custom model and parameters
        selector = OllamaSelector(
            endpoint="http://localhost:11434",
            model=AIModel.TINYLLAMA.value,
            timeout=3000,
            min_confidence=0.4,
        )
        assert selector.endpoint == "http://localhost:11434"
        assert selector.model == AIModel.TINYLLAMA.value
        assert selector.timeout_ms == 3000
        assert selector.min_confidence == 0.4

    def test_endpoint_trailing_slash_removal(self):
        """Test that trailing slash is removed from endpoint."""
        selector = OllamaSelector("http://localhost:11434/")
        assert selector.endpoint == "http://localhost:11434"

        # Test with double slash - both should be removed by rstrip
        selector = OllamaSelector("http://localhost:11434//")
        assert selector.endpoint == "http://localhost:11434"

    @patch("tool_router.ai.enhanced_selector.OllamaSelector._call_ollama")
    @patch("tool_router.ai.enhanced_selector.OllamaSelector._parse_response")
    def test_select_tool_success(self, mock_parse, mock_call):
        """Test successful tool selection."""
        # Setup mocks
        mock_call.return_value = "test response"
        mock_parse.return_value = {
            "tool_name": "test_tool",
            "confidence": 0.8,
            "reasoning": "test",
        }

        selector = OllamaSelector("http://localhost:11434")
        tools = [
            {"name": "tool1", "description": "Test tool 1"},
            {"name": "tool2", "description": "Test tool 2"},
        ]

        result = selector.select_tool("test task", tools)

        # Verify result
        assert result == {
            "tool_name": "test_tool",
            "confidence": 0.8,
            "reasoning": "test",
        }

        # Verify mocks were called
        mock_call.assert_called_once()
        mock_parse.assert_called_once_with("test response")

    def test_select_tool_no_tools(self):
        """Test tool selection with empty tools list."""
        selector = OllamaSelector("http://localhost:11434")

        result = selector.select_tool("test task", [])

        assert result is None

    @patch("tool_router.ai.enhanced_selector.OllamaSelector._call_ollama")
    def test_select_tool_no_response(self, mock_call):
        """Test tool selection when no response from Ollama."""
        mock_call.return_value = None

        selector = OllamaSelector("http://localhost:11434")
        tools = [{"name": "tool1", "description": "Test tool"}]

        result = selector.select_tool("test task", tools)

        assert result is None

    @patch("tool_router.ai.enhanced_selector.OllamaSelector._call_ollama")
    @patch("tool_router.ai.enhanced_selector.OllamaSelector._parse_response")
    def test_select_tool_parse_failure(self, mock_parse, mock_call):
        """Test tool selection when response parsing fails."""
        mock_call.return_value = "test response"
        mock_parse.return_value = None

        selector = OllamaSelector("http://localhost:11434")
        tools = [{"name": "tool1", "description": "Test tool"}]

        result = selector.select_tool("test task", tools)

        assert result is None

    @patch("tool_router.ai.enhanced_selector.OllamaSelector._call_ollama")
    @patch("tool_router.ai.enhanced_selector.OllamaSelector._parse_response")
    def test_select_tool_with_context(self, mock_parse, mock_call):
        """Test tool selection with context and similar tools."""
        mock_call.return_value = "test response"
        mock_parse.return_value = {
            "tool_name": "test_tool",
            "confidence": 0.8,
            "reasoning": "test",
        }

        selector = OllamaSelector("http://localhost:11434")
        tools = [{"name": "tool1", "description": "Test tool"}]

        result = selector.select_tool(
            task="test task",
            tools=tools,
            context="test context",
            similar_tools=["similar_tool1", "similar_tool2"],
        )

        assert result == {
            "tool_name": "test_tool",
            "confidence": 0.8,
            "reasoning": "test",
        }

    @patch("httpx.Client")
    def test_call_ollama_success(self, mock_client_class):
        """Test successful Ollama API call."""
        # Setup mock response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"response": "test response"}
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__enter__.return_value = mock_client

        selector = OllamaSelector("http://localhost:11434")

        result = selector._call_ollama("test prompt")

        assert result == "test response"
        mock_client.post.assert_called_once_with(
            "http://localhost:11434/api/generate",
            json={
                "model": selector.model,
                "prompt": "test prompt",
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 200,
                },
            },
        )

    @patch("httpx.Client")
    def test_call_ollama_http_error(self, mock_client_class):
        """Test Ollama API call with HTTP error."""
        import httpx

        mock_client = MagicMock()
        mock_client.post.side_effect = httpx.HTTPStatusError("HTTP Error", request=MagicMock(), response=MagicMock())
        mock_client_class.return_value.__enter__.return_value = mock_client

        selector = OllamaSelector("http://localhost:11434")

        result = selector._call_ollama("test prompt")

        assert result is None

    @patch("httpx.Client")
    def test_call_ollama_timeout(self, mock_client_class):
        """Test Ollama API call timeout."""
        import httpx

        mock_client = MagicMock()
        mock_client.post.side_effect = httpx.TimeoutException("Timeout")
        mock_client_class.return_value.__enter__.return_value = mock_client

        selector = OllamaSelector("http://localhost:11434")

        result = selector._call_ollama("test prompt")

        assert result is None

    def test_parse_response_valid_json(self):
        """Test parsing valid JSON response."""
        selector = OllamaSelector("http://localhost:11434")

        # Test with JSON response - using correct field names
        response = '{"tool_name": "test_tool", "confidence": 0.8, "reasoning": "test"}'
        result = selector._parse_response(response)

        assert result == {
            "tool_name": "test_tool",
            "confidence": 0.8,
            "reasoning": "test",
        }

    def test_parse_response_invalid_json(self):
        """Test parsing invalid JSON response."""
        selector = OllamaSelector("http://localhost:11434")

        # Test with invalid JSON
        response = "invalid json response"
        result = selector._parse_response(response)

        assert result is None

    def test_parse_response_empty(self):
        """Test parsing empty response."""
        selector = OllamaSelector("http://localhost:11434")

        result = selector._parse_response("")

        assert result is None

    def test_parse_response_no_confidence(self):
        """Test parsing response without confidence."""
        selector = OllamaSelector("http://localhost:11434")

        # Test with response but no confidence
        response = '{"tool_name": "test_tool", "reasoning": "test"}'
        result = selector._parse_response(response)

        assert result is None

    def test_parse_response_low_confidence(self):
        """Test parsing response with low confidence."""
        selector = OllamaSelector("http://localhost:11434", min_confidence=0.5)

        # Test with low confidence
        response = '{"tool_name": "test_tool", "confidence": 0.3, "reasoning": "test"}'
        result = selector._parse_response(response)

        # Should still return the result, confidence check is done elsewhere
        assert result == {
            "tool_name": "test_tool",
            "confidence": 0.3,
            "reasoning": "test",
        }

    def test_parse_response_high_confidence(self):
        """Test parsing response with high confidence."""
        selector = OllamaSelector("http://localhost:11434", min_confidence=0.5)

        # Test with high confidence
        response = '{"tool_name": "test_tool", "confidence": 0.8, "reasoning": "test"}'
        result = selector._parse_response(response)

        assert result == {
            "tool_name": "test_tool",
            "confidence": 0.8,
            "reasoning": "test",
        }

    def test_parse_response_invalid_confidence_range(self):
        """Test parsing response with invalid confidence range."""
        selector = OllamaSelector("http://localhost:11434")

        # Test with confidence > 1
        response = '{"tool_name": "test_tool", "confidence": 1.5, "reasoning": "test"}'
        result = selector._parse_response(response)

        assert result is None

        # Test with confidence < 0
        response = '{"tool_name": "test_tool", "confidence": -0.1, "reasoning": "test"}'
        result = selector._parse_response(response)

        assert result is None

    def test_parse_response_with_extra_text(self):
        """Test parsing response with extra text around JSON."""
        selector = OllamaSelector("http://localhost:11434")

        # Test with extra text
        response = 'Some text before {"tool_name": "test_tool", "confidence": 0.8, "reasoning": "test"} and after'
        result = selector._parse_response(response)

        assert result == {
            "tool_name": "test_tool",
            "confidence": 0.8,
            "reasoning": "test",
        }
