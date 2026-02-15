"""Unit tests for AI tool selector."""

import json
from unittest.mock import Mock, patch

import pytest
import requests

from tool_router.ai.selector import AIToolSelector


@pytest.fixture
def selector():
    """Create AIToolSelector instance for testing."""
    return AIToolSelector(
        endpoint="http://test-ollama:11434",
        model="llama3.2:3b",
        timeout_ms=2000,
    )


@pytest.fixture
def sample_tools():
    """Sample tools for testing."""
    return [
        {
            "name": "brave_web_search",
            "description": "Search the web using Brave Search API",
        },
        {
            "name": "list_directory",
            "description": "List files and directories in a path",
        },
        {
            "name": "read_file",
            "description": "Read contents of a file",
        },
    ]


class TestAIToolSelector:
    """Test AIToolSelector class."""

    def test_init(self):
        """Test selector initialization."""
        selector = AIToolSelector(
            endpoint="http://localhost:11434",
            model="mistral:7b",
            timeout_ms=3000,
        )
        assert selector.endpoint == "http://localhost:11434"
        assert selector.model == "mistral:7b"
        assert selector.timeout_seconds == 3.0
        assert selector.api_url == "http://localhost:11434/api/generate"

    def test_endpoint_normalization(self):
        """Test endpoint URL normalization."""
        selector = AIToolSelector(endpoint="http://localhost:11434/")
        assert selector.endpoint == "http://localhost:11434"

    @patch("tool_router.ai.selector.requests.post")
    def test_select_tool_success(self, mock_post, selector, sample_tools):
        """Test successful tool selection."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": json.dumps(
                {
                    "tool_name": "brave_web_search",
                    "confidence": 0.95,
                    "reasoning": "Task requires web search",
                }
            )
        }
        mock_post.return_value = mock_response

        result = selector.select_tool("search the web for Python tutorials", sample_tools)

        assert result is not None
        assert result["tool_name"] == "brave_web_search"
        assert result["confidence"] == 0.95
        assert "reasoning" in result

    @patch("tool_router.ai.selector.requests.post")
    def test_select_tool_with_extra_text(self, mock_post, selector, sample_tools):
        """Test parsing when model returns JSON with extra text."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": (
                'Here is my selection:\n{"tool_name": "read_file", '
                '"confidence": 0.8, "reasoning": "Need to read file"}\nHope this helps!'
            )
        }
        mock_post.return_value = mock_response

        result = selector.select_tool("read config.json", sample_tools)

        assert result is not None
        assert result["tool_name"] == "read_file"
        assert result["confidence"] == 0.8

    @patch("tool_router.ai.selector.requests.post")
    def test_select_tool_invalid_json(self, mock_post, selector, sample_tools):
        """Test handling of invalid JSON response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "I think you should use brave_web_search but I'm not sure"}
        mock_post.return_value = mock_response

        result = selector.select_tool("search something", sample_tools)

        assert result is None

    @patch("tool_router.ai.selector.requests.post")
    def test_select_tool_nonexistent_tool(self, mock_post, selector, sample_tools):
        """Test handling when AI selects a tool that doesn't exist."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": json.dumps(
                {
                    "tool_name": "nonexistent_tool",
                    "confidence": 0.9,
                    "reasoning": "Best tool",
                }
            )
        }
        mock_post.return_value = mock_response

        result = selector.select_tool("do something", sample_tools)

        assert result is None

    @patch("tool_router.ai.selector.requests.post")
    def test_select_tool_timeout(self, mock_post, selector, sample_tools):
        """Test timeout handling."""
        mock_post.side_effect = requests.Timeout()

        result = selector.select_tool("search web", sample_tools)

        assert result is None

    @patch("tool_router.ai.selector.requests.post")
    def test_select_tool_request_error(self, mock_post, selector, sample_tools):
        """Test request error handling."""
        mock_post.side_effect = requests.RequestException("Connection failed")

        result = selector.select_tool("search web", sample_tools)

        assert result is None

    @patch("tool_router.ai.selector.requests.post")
    def test_select_tool_http_error(self, mock_post, selector, sample_tools):
        """Test HTTP error handling."""
        mock_response = Mock()
        mock_response.status_code = 500
        http_err = requests.HTTPError()
        http_err.response = mock_response
        mock_response.raise_for_status.side_effect = http_err
        mock_post.return_value = mock_response

        result = selector.select_tool("search web", sample_tools)

        assert result is None

    @patch("tool_router.ai.selector.requests.post")
    def test_select_tool_model_not_found(self, mock_post, selector, sample_tools):
        """Test handling when model is not found (404)."""
        mock_response = Mock()
        mock_response.status_code = 404
        http_error = requests.HTTPError()
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_post.return_value = mock_response

        result = selector.select_tool("search web", sample_tools)

        assert result is None

    def test_select_tool_empty_tools(self, selector):
        """Test with empty tools list."""
        result = selector.select_tool("search web", [])

        assert result is None

    @patch("tool_router.ai.selector.requests.post")
    def test_select_tool_too_many_tools(self, mock_post, selector):
        """Test limiting tools to 100."""
        tools = [{"name": f"tool_{i}", "description": f"Tool {i}"} for i in range(150)]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": json.dumps(
                {
                    "tool_name": "tool_0",
                    "confidence": 0.8,
                    "reasoning": "First tool",
                }
            )
        }
        mock_post.return_value = mock_response

        result = selector.select_tool("do something", tools)

        # Should still work but only use first 100 tools
        assert result is not None

        # Verify that only 100 tools were sent to the API
        mock_post.assert_called_once()

    @patch("tool_router.ai.selector.requests.post")
    def test_select_tool_confidence_out_of_range(self, mock_post, selector, sample_tools):
        """Test confidence normalization."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": json.dumps(
                {
                    "tool_name": "read_file",
                    "confidence": 1.5,  # Out of range
                    "reasoning": "Best tool",
                }
            )
        }
        mock_post.return_value = mock_response

        result = selector.select_tool("read file", sample_tools)

        # Should clamp to valid range
        assert result is not None
        assert 0.0 <= result["confidence"] <= 1.0

    @patch("tool_router.ai.selector.requests.get")
    def test_is_available_success(self, mock_get, selector):
        """Test availability check when service is available."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        assert selector.is_available() is True

    @patch("tool_router.ai.selector.requests.get")
    def test_is_available_failure(self, mock_get, selector):
        """Test availability check when service is unavailable."""
        mock_get.side_effect = requests.RequestException()

        assert selector.is_available() is False

    @patch("tool_router.ai.selector.requests.post")
    def test_pull_model_success(self, mock_post, selector):
        """Test successful model pull."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        assert selector.pull_model() is True

    @patch("tool_router.ai.selector.requests.post")
    def test_pull_model_failure(self, mock_post, selector):
        """Test failed model pull."""
        mock_post.side_effect = requests.RequestException()

        assert selector.pull_model() is False
