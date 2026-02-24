"""Tests for AI-powered tool selection using Ollama."""

from __future__ import annotations

from unittest.mock import Mock, patch

import httpx

from tool_router.ai.selector import OllamaSelector


class TestOllamaSelector:
    """Test cases for OllamaSelector class."""

    def test_init(self) -> None:
        """Test OllamaSelector initialization."""
        selector = OllamaSelector("http://localhost:11434", "llama3.2:3b", 2000)

        assert selector.endpoint == "http://localhost:11434"
        assert selector.model == "llama3.2:3b"
        assert selector.timeout_ms == 2000
        assert selector.timeout_s == 2.0

    def test_init_trailing_endpoint(self) -> None:
        """Test initialization with trailing slash in endpoint."""
        selector = OllamaSelector("http://localhost:11434/", "llama3.2:3b", 2000)

        assert selector.endpoint == "http://localhost:11434"

    @patch("tool_router.ai.selector.httpx.Client")
    def test_select_tool_success(self, mock_client_class: Mock) -> None:
        """Test successful tool selection."""
        # Mock HTTP client
        mock_client = Mock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "response": '{\n  "tool_name": "search_web",\n  "confidence": 0.85,\n  "reasoning": "The user wants to search the web"\n}'
        }
        mock_client.post.return_value = mock_response

        selector = OllamaSelector("http://localhost:11434", "llama3.2:3b", 2000)

        tools = [
            {"name": "search_web", "description": "Search the web for information"},
            {"name": "list_files", "description": "List files in a directory"},
        ]

        result = selector.select_tool("search for information about AI", tools)

        assert result is not None
        assert result["tool_name"] == "search_web"
        assert result["confidence"] == 0.85
        assert "reasoning" in result

        # Verify the API call
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "http://localhost:11434/api/generate"
        assert call_args[1]["json"]["model"] == "llama3.2:3b"
        assert "search for information about AI" in call_args[1]["json"]["prompt"]

    @patch("tool_router.ai.selector.httpx.Client")
    def test_select_tool_timeout(self, mock_client_class: Mock) -> None:
        """Test tool selection with timeout."""
        mock_client = Mock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client.post.side_effect = httpx.TimeoutException("Timeout")

        selector = OllamaSelector("http://localhost:11434", "llama3.2:3b", 1000)

        tools = [{"name": "search_web", "description": "Search the web"}]

        result = selector.select_tool("search for something", tools)

        assert result is None

    @patch("tool_router.ai.selector.httpx.Client")
    def test_select_tool_http_error(self, mock_client_class: Mock) -> None:
        """Test tool selection with HTTP error."""
        mock_client = Mock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client.post.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=Mock(), response=Mock()
        )

        selector = OllamaSelector("http://localhost:11434", "llama3.2:3b", 2000)

        tools = [{"name": "search_web", "description": "Search the web"}]

        result = selector.select_tool("search for something", tools)

        assert result is None

    @patch("tool_router.ai.selector.httpx.Client")
    def test_select_tool_invalid_json(self, mock_client_class: Mock) -> None:
        """Test tool selection with invalid JSON response."""
        mock_client = Mock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"response": "invalid json response"}
        mock_client.post.return_value = mock_response

        selector = OllamaSelector("http://localhost:11434", "llama3.2:3b", 2000)

        tools = [{"name": "search_web", "description": "Search the web"}]

        result = selector.select_tool("search for something", tools)

        assert result is None

    @patch("tool_router.ai.selector.httpx.Client")
    def test_select_tool_missing_fields(self, mock_client_class: Mock) -> None:
        """Test tool selection with missing required fields."""
        mock_client = Mock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "response": '{\n  "tool_name": "search_web",\n  "confidence": 0.85\n}'  # Missing reasoning
        }
        mock_client.post.return_value = mock_response

        selector = OllamaSelector("http://localhost:11434", "llama3.2:3b", 2000)

        tools = [{"name": "search_web", "description": "Search the web"}]

        result = selector.select_tool("search for something", tools)

        assert result is None

    @patch("tool_router.ai.selector.httpx.Client")
    def test_select_tool_invalid_confidence(self, mock_client_class: Mock) -> None:
        """Test tool selection with invalid confidence value."""
        mock_client = Mock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "response": '{\n  "tool_name": "search_web",\n  "confidence": 1.5,\n  "reasoning": "Invalid confidence"\n}'
        }
        mock_client.post.return_value = mock_response

        selector = OllamaSelector("http://localhost:11434", "llama3.2:3b", 2000)

        tools = [{"name": "search_web", "description": "Search the web"}]

        result = selector.select_tool("search for something", tools)

        assert result is None

    @patch("tool_router.ai.selector.httpx.Client")
    def test_select_tool_json_with_extra_text(self, mock_client_class: Mock) -> None:
        """Test tool selection when JSON is embedded in extra text."""
        mock_client = Mock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "response": 'I think the best tool is: {\n  "tool_name": "search_web",\n  "confidence": 0.9,\n  "reasoning": "This matches the user\'s intent"\n} based on the query.'
        }
        mock_client.post.return_value = mock_response

        selector = OllamaSelector("http://localhost:11434", "llama3.2:3b", 2000)

        tools = [{"name": "search_web", "description": "Search the web"}]

        result = selector.select_tool("search for something", tools)

        assert result is not None
        assert result["tool_name"] == "search_web"
        assert result["confidence"] == 0.9

    def test_create_prompt(self) -> None:
        """Test prompt creation."""
        selector = OllamaSelector("http://localhost:11434", "llama3.2:3b", 2000)

        task = "search for information about AI"
        tool_list = "- search_web: Search the web for information\n- list_files: List files in a directory"

        prompt = selector._create_prompt(task, tool_list)

        assert "search for information about AI" in prompt
        assert "search_web: Search the web for information" in prompt
        assert "list_files: List files in a directory" in prompt
        assert '"tool_name":' in prompt
        assert '"confidence":' in prompt
        assert '"reasoning":' in prompt

    def test_parse_response_success(self) -> None:
        """Test successful response parsing."""
        selector = OllamaSelector("http://localhost:11434", "llama3.2:3b", 2000)

        response = '{\n  "tool_name": "search_web",\n  "confidence": 0.85,\n  "reasoning": "Good match"\n}'

        result = selector._parse_response(response)

        assert result is not None
        assert result["tool_name"] == "search_web"
        assert result["confidence"] == 0.85
        assert result["reasoning"] == "Good match"

    def test_parse_response_no_json(self) -> None:
        """Test response parsing with no JSON found."""
        selector = OllamaSelector("http://localhost:11434", "llama3.2:3b", 2000)

        response = "This is not a JSON response"

        result = selector._parse_response(response)

        assert result is None

    def test_parse_response_invalid_json(self) -> None:
        """Test response parsing with invalid JSON."""
        selector = OllamaSelector("http://localhost:11434", "llama3.2:3b", 2000)

        response = "{invalid json}"

        result = selector._parse_response(response)

        assert result is None

    def test_select_tool_empty_tools_list(self) -> None:
        """Test tool selection with empty tools list."""
        selector = OllamaSelector("http://localhost:11434", "llama3.2:3b", 2000)

        result = selector.select_tool("search for something", [])

        assert result is None

    @patch("tool_router.ai.selector.httpx.Client")
    def test_select_tool_generic_exception(self, mock_client_class: Mock) -> None:
        """Test tool selection with generic exception."""
        mock_client = Mock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        mock_client.post.side_effect = Exception("Generic error")

        selector = OllamaSelector("http://localhost:11434", "llama3.2:3b", 2000)

        tools = [{"name": "search_web", "description": "Search the web"}]

        result = selector.select_tool("search for something", tools)

        assert result is None
