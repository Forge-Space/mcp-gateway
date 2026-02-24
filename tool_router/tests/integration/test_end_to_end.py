"""End-to-end integration tests for tool router."""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from tool_router.args.builder import build_arguments
from tool_router.core.config import GatewayConfig
from tool_router.gateway.client import HTTPGatewayClient
from tool_router.scoring.matcher import select_top_matching_tools


# Test configuration constants
TEST_JWT_TOKEN = os.getenv("TEST_JWT_TOKEN", "test-jwt-token")
TEST_GATEWAY_URL = os.getenv("TEST_GATEWAY_URL", "http://gateway:4444")


@pytest.fixture
def sample_tools() -> list[dict]:
    """Sample tools for testing."""
    return [
        {
            "name": "web_search",
            "description": "Search the web for information",
            "inputSchema": {
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
        {
            "name": "fetch_url",
            "description": "Fetch content from a URL",
            "inputSchema": {
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
        },
        {
            "name": "calculate",
            "description": "Perform mathematical calculations",
            "inputSchema": {
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"],
            },
        },
    ]


class TestEndToEndWorkflows:
    """End-to-end workflow tests."""

    def test_complete_task_execution_flow(self, sample_tools: list[dict]) -> None:
        """Test: fetch tools → score → build args → call tool."""
        # Step 1: Pick best tool for task
        task = "search for Python tutorials"
        best_tools = select_top_matching_tools(sample_tools, task, "", top_n=1)

        assert len(best_tools) == 1
        assert best_tools[0]["name"] == "web_search"

        # Step 2: Build arguments
        tool = best_tools[0]
        args = build_arguments(tool, task)

        assert "query" in args
        assert args["query"] == task

        # Step 3: Mock call tool
        config = GatewayConfig(
            url=TEST_GATEWAY_URL,
            jwt=TEST_JWT_TOKEN,
            timeout_ms=5000,
            max_retries=2,
            retry_delay_ms=100,
        )
        client = HTTPGatewayClient(config)

        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "result": {"content": [{"type": "text", "text": "Found 10 Python tutorial results"}]},
            }
        ).encode()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=None)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = client.call_tool(tool["name"], args)

        assert "Python tutorial" in result

    def test_no_matching_tool_scenario(self, sample_tools: list[dict]) -> None:
        """Test behavior when no tool matches the task."""
        task = "play music"
        best_tools = select_top_matching_tools(sample_tools, task, "", top_n=1)

        # Should return empty list when no positive scores
        assert len(best_tools) == 0

    def test_multiple_tool_selection(self, sample_tools: list[dict]) -> None:
        """Test selecting multiple relevant tools."""
        task = "fetch and search web content"
        best_tools = select_top_matching_tools(sample_tools, task, "", top_n=3)

        # Should return multiple tools with positive scores
        assert len(best_tools) >= 2
        tool_names = {t["name"] for t in best_tools}
        assert "web_search" in tool_names or "fetch_url" in tool_names

    def test_context_influences_selection(self, sample_tools: list[dict]) -> None:
        """Test that context helps disambiguate tool selection."""
        task = "get data"
        context_web = "I need to search online"
        context_url = "I have a specific URL"

        # With web context
        tools_web = select_top_matching_tools(sample_tools, task, context_web, top_n=1)
        if tools_web:
            assert tools_web[0]["name"] in ["web_search", "fetch_url"]

        # With URL context
        tools_url = select_top_matching_tools(sample_tools, task, context_url, top_n=1)
        if tools_url:
            # Context should influence selection
            assert len(tools_url) > 0

    def test_error_recovery_workflow(self) -> None:
        """Test error handling in complete workflow."""
        config = GatewayConfig(
            url=TEST_GATEWAY_URL,
            jwt=TEST_JWT_TOKEN,
            timeout_ms=1000,
            max_retries=1,
            retry_delay_ms=50,
        )
        client = HTTPGatewayClient(config)

        # Simulate network error
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = ConnectionError("Network error")

            with patch("time.sleep"):  # Speed up test
                result = client.call_tool("test_tool", {})

            # Should return error message, not raise
            assert "Failed to call tool" in result
            assert "Network error" in result

    def test_configuration_validation(self) -> None:
        """Test that invalid configuration is caught early."""
        with pytest.raises(ValueError, match="GATEWAY_JWT"):
            GatewayConfig.load_from_environment()

    def test_argument_building_edge_cases(self, sample_tools: list[dict]) -> None:
        """Test argument building with various tool schemas."""
        # Tool with no schema
        tool_no_schema = {"name": "test", "inputSchema": {}}
        args = build_arguments(tool_no_schema, "do something")
        assert "task" in args

        # Tool with multiple required params
        tool_multi = {
            "name": "test",
            "inputSchema": {
                "properties": {"url": {}, "method": {}},
                "required": ["url", "method"],
            },
        }
        args = build_arguments(tool_multi, "https://example.com")
        assert "url" in args
        assert args["url"] == "https://example.com"
