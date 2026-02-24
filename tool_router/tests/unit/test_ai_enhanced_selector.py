"""Unit tests for tool_router/ai/enhanced_selector.py module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tool_router.ai.enhanced_selector import (
    AIModel,
    AIProvider,
    BaseAISelector,
    CostTracker,
    EnhancedAISelector,
    OllamaSelector,
)


def test_ai_provider_enum() -> None:
    """Test AIProvider enum values."""
    assert AIProvider.OLLAMA.value == "ollama"
    assert AIProvider.OPENAI.value == "openai"
    assert AIProvider.ANTHROPIC.value == "anthropic"


def test_ai_model_enum() -> None:
    """Test AIModel enum values."""
    assert AIModel.LLAMA32_3B.value == "llama3.2:3b"
    assert AIModel.LLAMA32_1B.value == "llama3.2:1b"
    assert AIModel.QWEN_2_5_3B.value == "qwen2.5:3b"


def test_ai_model_get_hardware_requirements() -> None:
    """Test AIModel hardware requirements method."""
    reqs = AIModel.get_hardware_requirements("llama3.2:3b")
    assert reqs["ram_gb"] == 4
    assert reqs["tokens_per_sec"] == 10
    assert reqs["hardware_tier"] == "n100_optimal"


def test_ai_model_get_cost_per_million_tokens() -> None:
    """Test AIModel cost calculation method."""
    costs = AIModel.get_cost_per_million_tokens("llama3.2:3b")
    assert costs["input"] == 0.0
    assert costs["output"] == 0.0


def test_ai_model_is_local_model() -> None:
    """Test AIModel local model detection."""
    assert AIModel.is_local_model("llama3.2:3b") is True
    assert AIModel.is_local_model("gpt-4") is False


def test_ai_model_get_model_tier() -> None:
    """Test AIModel tier classification."""
    assert AIModel.get_model_tier("llama3.2:1b") == "fast"
    assert AIModel.get_model_tier("llama3.2:3b") == "balanced"
    assert AIModel.get_model_tier("unknown") == "unknown"


def test_base_ai_selector_abstract() -> None:
    """Test BaseAISelector is abstract."""
    with pytest.raises(TypeError):
        BaseAISelector()


def test_ollama_selector_select_tool_success() -> None:
    """Test successful tool selection."""
    selector = OllamaSelector(
        endpoint="http://localhost:11434",
        model="llama3.2:3b",
        timeout=1000,
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "response": '{"tool_name": "search", "confidence": 0.8, "reasoning": "Matches search task"}'
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response
        result = selector.select_tool("search web", [{"name": "search", "description": "Search web"}])

    assert result["tool_name"] == "search"
    assert result["confidence"] == 0.8


def test_ollama_selector_select_tool_low_confidence() -> None:
    """Test tool selection with low confidence."""
    selector = OllamaSelector(
        endpoint="http://localhost:11434",
        model="llama3.2:3b",
        min_confidence=0.7,
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "response": '{"tool_name": "search", "confidence": 0.5}'
    }

    with patch("httpx.post", return_value=mock_response):
        result = selector.select_tool("search web", [{"name": "search", "description": "Search web"}])

    assert result is None


def test_ollama_selector_select_tool_invalid_response() -> None:
    """Test tool selection with invalid response."""
    selector = OllamaSelector(
        endpoint="http://localhost:11434",
        model="llama3.2:3b",
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "invalid json"}

    with patch("httpx.post", return_value=mock_response):
        result = selector.select_tool("search web", [{"name": "search", "description": "Search web"}])

    assert result is None


def test_ollama_selector_select_tool_http_error() -> None:
    """Test tool selection with HTTP error."""
    selector = OllamaSelector(
        endpoint="http://localhost:11434",
        model="llama3.2:3b",
    )

    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch("httpx.post", return_value=mock_response):
        result = selector.select_tool("search web", [{"name": "search", "description": "Search web"}])

    assert result is None


def test_enhanced_ai_selector_initialization() -> None:
    """Test EnhancedAISelector initialization."""
    ollama_selector = OllamaSelector(
        endpoint="http://localhost:11434",
        model="llama3.2:3b",
        timeout=5000,
        min_confidence=0.3,
    )

    selector = EnhancedAISelector(
        providers=[ollama_selector],
        primary_weight=0.7,
        fallback_weight=0.3,
        timeout=5000,
        min_confidence=0.3,
    )
    assert len(selector.providers) == 1
    assert selector.primary_weight == 0.7
    assert selector.fallback_weight == 0.3
    assert selector.timeout_ms == 5000
    assert selector.min_confidence == 0.3


def test_enhanced_ai_selector_select_tool() -> None:
    """Test EnhancedAISelector tool selection."""
    ollama_selector = OllamaSelector(
        endpoint="http://localhost:11434",
        model="llama3.2:3b",
        timeout=1000,
    )

    selector = EnhancedAISelector(providers=[ollama_selector])

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "response": '{"tool_name": "search", "confidence": 0.8, "reasoning": "Matches search task"}'
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response
        result = selector.select_tool("search web", [{"name": "search", "description": "Search web"}])

    assert result["tool_name"] == "search"
    assert result["confidence"] == 0.8


def test_cost_tracker_initialization() -> None:
    """Test CostTracker initialization."""
    tracker = CostTracker()
    assert tracker.total_requests == 0
    assert tracker.total_cost_saved == 0.0
    assert tracker.average_response_time == 0.0
    assert tracker.model_usage_stats == {}


def test_cost_tracker_track_selection() -> None:
    """Test CostTracker selection tracking."""
    tracker = CostTracker()
    tracker.track_selection(
        model="llama3.2:3b",
        task_complexity="simple",
        estimated_tokens={"total": 100, "input": 80, "output": 20}
    )

    assert tracker.total_requests == 1
    assert tracker.model_usage_stats["llama3.2:3b"]["usage_count"] == 1
    assert tracker.model_usage_stats["llama3.2:3b"]["total_tokens"] == 100


def test_cost_tracker_multiple_selections() -> None:
    """Test CostTracker with multiple selections."""
    tracker = CostTracker()
    tracker.track_selection(
        model="llama3.2:3b",
        task_complexity="simple",
        estimated_tokens={"total": 100, "input": 80, "output": 20}
    )
    tracker.track_selection(
        model="llama3.2:3b",
        task_complexity="complex",
        estimated_tokens={"total": 200, "input": 150, "output": 50}
    )

    assert tracker.total_requests == 2
    assert tracker.model_usage_stats["llama3.2:3b"]["usage_count"] == 2
    assert tracker.model_usage_stats["llama3.2:3b"]["total_tokens"] == 300
