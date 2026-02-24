"""Unit tests for tool_router/ai/selector.py module."""

from __future__ import annotations

from unittest.mock import patch

from tool_router.ai.selector import OllamaSelector


def test_ollama_selector_initialization() -> None:
    """Test OllamaSelector can be initialized."""
    selector = OllamaSelector(
        endpoint="http://localhost:11434",
        model="llama3.2:3b",
        timeout=2000,
        min_confidence=0.3,
    )

    assert selector.endpoint == "http://localhost:11434"
    assert selector.model == "llama3.2:3b"
    assert selector.timeout_ms == 2000
    assert selector.timeout_s == 2.0
    assert selector.min_confidence == 0.3


def test_ollama_selector_initialization_with_trailing_slash() -> None:
    """Test OllamaSelector removes trailing slash from endpoint."""
    selector = OllamaSelector(
        endpoint="http://localhost:11434/",
        model="llama3.2:3b",
    )

    assert selector.endpoint == "http://localhost:11434"


def test_ollama_selector_initialization_defaults() -> None:
    """Test OllamaSelector uses default values."""
    selector = OllamaSelector(
        endpoint="http://localhost:11434",
        model="llama3.2:3b",
    )

    assert selector.timeout_ms == 2000
    assert selector.timeout_s == 2.0
    assert selector.min_confidence == 0.3


def test_select_tool_empty_tools_list() -> None:
    """Test select_tool returns None for empty tools list."""
    selector = OllamaSelector(
        endpoint="http://localhost:11434",
        model="llama3.2:3b",
    )

    result = selector.select_tool("search", [])
    assert result is None


def test_select_tool_with_valid_response() -> None:
    """Test select_tool with valid AI response."""
    selector = OllamaSelector(
        endpoint="http://localhost:11434",
        model="llama3.2:3b",
        min_confidence=0.5,
    )

    tools = [{"name": "search", "description": "Search the web"}]
    mock_response = '{"tool_name": "search", "confidence": 0.8, "reasoning": "Matches search intent"}'

    with patch.object(selector, "_call_ollama", return_value=mock_response):
        result = selector.select_tool("search the web", tools)

    assert result is not None
    assert result["tool_name"] == "search"
    assert result["confidence"] == 0.8
    assert result["reasoning"] == "Matches search intent"


def test_select_tool_with_low_confidence() -> None:
    """Test select_tool returns None when confidence is below threshold."""
    selector = OllamaSelector(
        endpoint="http://localhost:11434",
        model="llama3.2:3b",
        min_confidence=0.8,
    )

    tools = [{"name": "search", "description": "Search the web"}]
    mock_response = '{"tool_name": "search", "confidence": 0.5, "reasoning": "Low confidence"}'

    with patch.object(selector, "_call_ollama", return_value=mock_response):
        result = selector.select_tool("search the web", tools)

    assert result is None


def test_select_tool_with_invalid_response() -> None:
    """Test select_tool returns None for invalid AI response."""
    selector = OllamaSelector(
        endpoint="http://localhost:11434",
        model="llama3.2:3b",
    )

    tools = [{"name": "search", "description": "Search the web"}]
    mock_response = '{"invalid": "response"}'

    with patch.object(selector, "_call_ollama", return_value=mock_response):
        result = selector.select_tool("search the web", tools)

    assert result is None


def test_select_tool_with_no_response() -> None:
    """Test select_tool returns None when AI call fails."""
    selector = OllamaSelector(
        endpoint="http://localhost:11434",
        model="llama3.2:3b",
    )

    tools = [{"name": "search", "description": "Search the web"}]

    with patch.object(selector, "_call_ollama", return_value=None):
        result = selector.select_tool("search the web", tools)

    assert result is None


def test_select_tool_with_context_and_similar_tools() -> None:
    """Test select_tool with context and similar tools."""
    selector = OllamaSelector(
        endpoint="http://localhost:11434",
        model="llama3.2:3b",
    )

    tools = [{"name": "search", "description": "Search the web"}]
    context = "Looking for recent news"
    similar_tools = ["web_search"]
    mock_response = '{"tool_name": "search", "confidence": 0.9, "reasoning": "Good match"}'

    with patch.object(selector, "_call_ollama", return_value=mock_response):
        result = selector.select_tool("search the web", tools, context=context, similar_tools=similar_tools)

    assert result is not None
    assert result["tool_name"] == "search"


def test_select_tools_multi_empty_tools_list() -> None:
    """Test select_tools_multi returns None for empty tools list."""
    selector = OllamaSelector(
        endpoint="http://localhost:11434",
        model="llama3.2:3b",
    )

    result = selector.select_tools_multi("search", [])
    assert result is None


def test_select_tools_multi_with_valid_response() -> None:
    """Test select_tools_multi with valid AI response."""
    selector = OllamaSelector(
        endpoint="http://localhost:11434",
        model="llama3.2:3b",
        min_confidence=0.5,
    )

    tools = [
        {"name": "search", "description": "Search the web"},
        {"name": "fetch", "description": "Get URL"},
    ]
    mock_response = '{"tools": ["search", "fetch"], "confidence": 0.8, "reasoning": "Both needed"}'

    with patch.object(selector, "_call_ollama", return_value=mock_response):
        result = selector.select_tools_multi("search and fetch", tools)

    assert result is not None
    assert result["tools"] == ["search", "fetch"]
    assert result["confidence"] == 0.8
    assert result["reasoning"] == "Both needed"


def test_select_tools_multi_with_invalid_tool_names() -> None:
    """Test select_tools_multi filters invalid tool names."""
    selector = OllamaSelector(
        endpoint="http://localhost:11434",
        model="llama3.2:3b",
    )

    tools = [{"name": "search", "description": "Search the web"}]
    mock_response = '{"tools": ["invalid_tool"], "confidence": 0.8, "reasoning": "Invalid"}'

    with patch.object(selector, "_call_ollama", return_value=mock_response):
        result = selector.select_tools_multi("search", tools)

    assert result is None


def test_select_tools_multi_with_low_confidence() -> None:
    """Test select_tools_multi returns None when confidence is below threshold."""
    selector = OllamaSelector(
        endpoint="http://localhost:11434",
        model="llama3.2:3b",
        min_confidence=0.8,
    )

    tools = [{"name": "search", "description": "Search the web"}]
    mock_response = '{"tools": ["search"], "confidence": 0.5, "reasoning": "Low confidence"}'

    with patch.object(selector, "_call_ollama", return_value=mock_response):
        result = selector.select_tools_multi("search", tools)

    assert result is None


def test_create_prompt_backward_compatibility() -> None:
    """Test _create_prompt method for backward compatibility."""
    selector = OllamaSelector(
        endpoint="http://localhost:11434",
        model="llama3.2:3b",
    )

    task = "search the web"
    tool_list = "search: Search the web\nfetch: Get URL"

    prompt = selector._create_prompt(task, tool_list)

    assert task in prompt
    assert tool_list in prompt
    assert "tool_name" in prompt


def test_parse_response_valid_json() -> None:
    """Test _parse_response with valid JSON."""
    selector = OllamaSelector(
        endpoint="http://localhost:11434",
        model="llama3.2:3b",
    )

    response = 'Some text {"tool_name": "search", "confidence": 0.8, "reasoning": "Good"} more text'

    result = selector._parse_response(response)

    assert result is not None
    assert result["tool_name"] == "search"
    assert result["confidence"] == 0.8
    assert result["reasoning"] == "Good"


def test_parse_response_invalid_json() -> None:
    """Test _parse_response with invalid JSON."""
    selector = OllamaSelector(
        endpoint="http://localhost:11434",
        model="llama3.2:3b",
    )

    response = 'Some text {"invalid": "json"} more text'

    result = selector._parse_response(response)

    assert result is None


def test_parse_response_no_json() -> None:
    """Test _parse_response with no JSON found."""
    selector = OllamaSelector(
        endpoint="http://localhost:11434",
        model="llama3.2:3b",
    )

    response = "No JSON here"

    result = selector._parse_response(response)

    assert result is None


def test_parse_response_invalid_confidence() -> None:
    """Test _parse_response with invalid confidence value."""
    selector = OllamaSelector(
        endpoint="http://localhost:11434",
        model="llama3.2:3b",
    )

    response = '{"tool_name": "search", "confidence": 1.5, "reasoning": "Invalid"}'

    result = selector._parse_response(response)

    assert result is None


def test_parse_multi_response_valid_json() -> None:
    """Test _parse_multi_response with valid JSON."""
    selector = OllamaSelector(
        endpoint="http://localhost:11434",
        model="llama3.2:3b",
    )

    available_tools = [{"name": "search"}, {"name": "fetch"}]
    response = 'Some text {"tools": ["search"], "confidence": 0.8, "reasoning": "Good"} more text'

    result = selector._parse_multi_response(response, available_tools)

    assert result is not None
    assert result["tools"] == ["search"]
    assert result["confidence"] == 0.8
    assert result["reasoning"] == "Good"


def test_parse_multi_response_invalid_tool_names() -> None:
    """Test _parse_multi_response with invalid tool names."""
    selector = OllamaSelector(
        endpoint="http://localhost:11434",
        model="llama3.2:3b",
    )

    available_tools = [{"name": "search"}]
    response = '{"tools": ["invalid"], "confidence": 0.8, "reasoning": "Invalid"}'

    result = selector._parse_multi_response(response, available_tools)

    assert result is None


def test_parse_multi_response_empty_tools_list() -> None:
    """Test _parse_multi_response with empty tools list."""
    selector = OllamaSelector(
        endpoint="http://localhost:11434",
        model="llama3.2:3b",
    )

    available_tools = [{"name": "search"}]
    response = '{"tools": [], "confidence": 0.8, "reasoning": "Empty"}'

    result = selector._parse_multi_response(response, available_tools)

    assert result is None
