"""Unit tests for AI tool selector."""

from __future__ import annotations

import pytest
import requests

from tool_router.ai.selector import AIToolSelector


@pytest.fixture
def selector():
    """Create AIToolSelector instance."""
    return AIToolSelector(endpoint="http://localhost:11434", model="llama3.2:3b", timeout_ms=2000)


@pytest.fixture
def sample_tools():
    """Sample tools."""
    return [
        {"name": "search_web", "description": "Search the web"},
        {"name": "list_files", "description": "List files"},
    ]


class TestAIToolSelector:
    """Tests for AIToolSelector."""

    def test_init_default(self):
        """Test default initialization."""
        sel = AIToolSelector()
        assert sel.endpoint == "http://ollama:11434"
        assert sel.timeout_seconds == 2.0

    def test_select_tool_no_tools(self, selector):
        """Test with no tools."""
        result = selector.select_tool("task", [])
        assert result is None

    def test_select_tool_success(self, selector, sample_tools, mocker):
        """Test successful selection."""
        mocker.patch.object(selector, "_call_ollama", return_value='{"tool": "search_web"}')
        mocker.patch.object(
            selector,
            "_parse_response",
            return_value={"tool_name": "search_web", "confidence": 0.9, "reasoning": "match"},
        )
        result = selector.select_tool("search", sample_tools)
        assert result["tool_name"] == "search_web"

    def test_select_tool_timeout(self, selector, sample_tools, mocker):
        """Test timeout handling."""
        mocker.patch.object(selector, "_call_ollama", side_effect=requests.Timeout())
        result = selector.select_tool("task", sample_tools)
        assert result is None

    def test_call_ollama_success(self, selector, mocker):
        """Test Ollama API call."""
        mock_resp = mocker.Mock()
        mock_resp.json.return_value = {"response": "search_web"}
        mocker.patch("requests.post", return_value=mock_resp)
        result = selector._call_ollama("prompt")
        assert result == "search_web"

    def test_parse_response_valid(self, selector, sample_tools):
        """Test parsing valid response."""
        result = selector._parse_response('{"tool_name": "search_web", "confidence": 0.9, "reasoning": "best"}', sample_tools)
        assert result is not None
        assert result["tool_name"] == "search_web"
        assert result["confidence"] == 0.9
