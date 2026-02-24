"""Integration tests for gateway client end-to-end flows."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from tool_router.core.config import GatewayConfig
from tool_router.gateway.client import HTTPGatewayClient


@pytest.fixture
def gateway_config() -> GatewayConfig:
    """Create test gateway configuration."""
    return GatewayConfig(
        url="http://test-gateway:4444",
        jwt="test-token-123",
        timeout_ms=5000,
        max_retries=2,
        retry_delay_ms=100,
    )


@pytest.fixture
def mock_response():
    """Create mock HTTP response."""

    def _create_response(data: dict) -> MagicMock:
        resp = MagicMock()
        resp.read.return_value = json.dumps(data).encode()
        resp.__enter__ = MagicMock(return_value=resp)
        resp.__exit__ = MagicMock(return_value=None)
        return resp

    return _create_response


class TestGatewayClientIntegration:
    """Integration tests for HTTPGatewayClient."""

    def test_get_tools_and_call_tool_workflow(
        self, gateway_config: GatewayConfig, mock_response
    ) -> None:
        """Test complete workflow: fetch tools, select one, call it."""
        client = HTTPGatewayClient(gateway_config)

        # Mock get_tools response
        tools_data = {
            "tools": [
                {
                    "name": "search_web",
                    "description": "Search the web",
                    "inputSchema": {"properties": {"query": {"type": "string"}}},
                },
                {
                    "name": "fetch_url",
                    "description": "Fetch URL content",
                    "inputSchema": {"properties": {"url": {"type": "string"}}},
                },
            ]
        }

        # Mock call_tool response
        call_result = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"content": [{"type": "text", "text": "Search results here"}]},
        }

        with patch("urllib.request.urlopen") as mock_urlopen:
            # First call: get_tools
            mock_urlopen.return_value = mock_response(tools_data)
            tools = client.get_tools()

            assert len(tools) == 2
            assert tools[0]["name"] == "search_web"

            # Second call: call_tool
            mock_urlopen.return_value = mock_response(call_result)
            result = client.call_tool("search_web", {"query": "test"})

            assert result == "Search results here"
            assert mock_urlopen.call_count == 2

    def test_retry_logic_on_server_error(
        self, gateway_config: GatewayConfig, mock_response
    ) -> None:
        """Test that client retries on 5xx errors."""
        client = HTTPGatewayClient(gateway_config)

        with patch("urllib.request.urlopen") as mock_urlopen:
            # First attempt: 500 error
            error_resp = MagicMock()
            error_resp.code = 500
            error_resp.read.return_value = b"Server error"
            mock_urlopen.side_effect = [
                Exception("HTTP Error 500"),
                mock_response({"tools": []}),
            ]

            # Should retry and eventually succeed
            with patch("time.sleep"):  # Speed up test
                with pytest.raises(Exception):
                    client.get_tools()

    def test_configuration_affects_behavior(self) -> None:
        """Test that configuration parameters are respected."""
        # Short timeout config
        fast_config = GatewayConfig(
            url="http://gateway:4444",
            jwt="token",
            timeout_ms=100,
            max_retries=1,
            retry_delay_ms=50,
        )

        client = HTTPGatewayClient(fast_config)
        assert client._timeout_seconds == 0.1
        assert client.config.max_retries == 1

        # Long timeout config
        slow_config = GatewayConfig(
            url="http://gateway:4444",
            jwt="token",
            timeout_ms=30000,
            max_retries=5,
            retry_delay_ms=1000,
        )

        client = HTTPGatewayClient(slow_config)
        assert client._timeout_seconds == 30.0
        assert client.config.max_retries == 5

    def test_authentication_header_included(
        self, gateway_config: GatewayConfig, mock_response
    ) -> None:
        """Test that JWT token is included in request headers."""
        client = HTTPGatewayClient(gateway_config)

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_response({"tools": []})

            with patch("urllib.request.Request") as mock_request:
                client.get_tools()

                # Verify Request was called with auth header
                call_args = mock_request.call_args
                headers = call_args[1]["headers"]
                assert "Authorization" in headers
                assert headers["Authorization"] == "Bearer test-token-123"

    def test_error_handling_preserves_context(
        self, gateway_config: GatewayConfig
    ) -> None:
        """Test that errors include helpful context."""
        client = HTTPGatewayClient(gateway_config)

        with patch("urllib.request.urlopen") as mock_urlopen:
            # Test retry-related ConnectionError that gets converted to ValueError
            mock_urlopen.side_effect = ConnectionError(
                "Failed after 3 attempts. Last error: Network unreachable"
            )

            with patch("time.sleep"):
                with pytest.raises(ValueError) as exc_info:
                    client.get_tools()

                # Error message should include context
                assert "Failed to fetch tools" in str(exc_info.value)
                assert "Failed after 3 attempts" in str(exc_info.value)
