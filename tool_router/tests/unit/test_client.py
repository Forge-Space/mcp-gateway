from __future__ import annotations

import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from tool_router.core.config import GatewayConfig
from tool_router.gateway.client import (
    GatewayClient,
    HTTPGatewayClient,
    call_tool,
    get_tools,
)


class TestHTTPGatewayClient:
    """Tests for HTTPGatewayClient class."""

    def test_initialization(self) -> None:
        """Test client initialization with config."""
        config = GatewayConfig(
            url="http://test:4444",
            jwt="token",
            timeout_ms=5000,
            max_retries=3,
            retry_delay_ms=1000,
        )
        client = HTTPGatewayClient(config)

        assert client.config == config
        assert client._timeout_seconds == 5.0
        assert client._retry_delay_seconds == 1.0

    def test_headers_includes_auth_and_content_type(self) -> None:
        """Test that headers include proper authentication and content type."""
        config = GatewayConfig(url="http://test:4444", jwt="test-token")
        client = HTTPGatewayClient(config)

        headers = client._headers()

        assert headers["Authorization"] == "Bearer test-token"
        assert headers["Content-Type"] == "application/json"

    def test_make_request_success(self) -> None:
        """Test successful request without retries."""
        config = GatewayConfig(url="http://test:4444", jwt="token")
        client = HTTPGatewayClient(config)

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"result": "success"}'

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = client._make_request("http://test:4444/test")

        assert result == {"result": "success"}

    def test_make_request_with_data(self) -> None:
        """Test request with POST data."""
        config = GatewayConfig(url="http://test:4444", jwt="token")
        client = HTTPGatewayClient(config)

        mock_response = MagicMock()
        mock_response.read.return_value = b'{"result": "success"}'

        with patch(
            "urllib.request.urlopen", return_value=mock_response
        ) as mock_urlopen:
            client._make_request(
                "http://test:4444/test", method="POST", data=b'{"test": "data"}'
            )

        # Verify the request was created with data
        assert mock_urlopen.called
        request_arg = mock_urlopen.call_args[0][0]
        assert request_arg.data == b'{"test": "data"}'
        assert request_arg.method == "POST"

    def test_make_request_retry_on_server_error(self) -> None:
        """Test retry logic on HTTP 5xx errors."""
        config = GatewayConfig(
            url="http://test:4444", jwt="token", max_retries=3, retry_delay_ms=100
        )
        client = HTTPGatewayClient(config)

        # First call fails with 500, second succeeds
        server_error = MagicMock()
        server_error.code = 500
        server_error.read.return_value = b"Server Error"

        success_response = MagicMock()
        success_response.read.return_value = b'{"result": "success"}'

        with patch("urllib.request.urlopen") as mock_urlopen:
            with patch("time.sleep"):  # Mock sleep to speed up test
                mock_urlopen.side_effect = [
                    urllib.error.HTTPError(url="", msg="", hdrs="", fp=server_error),
                    success_response,
                ]

                result = client._make_request("http://test:4444/test")

        assert result == {"result": "success"}
        assert mock_urlopen.call_count == 2

    def test_make_request_retry_on_network_error(self) -> None:
        """Test retry logic on network errors."""
        config = GatewayConfig(
            url="http://test:4444", jwt="token", max_retries=2, retry_delay_ms=50
        )
        client = HTTPGatewayClient(config)

        success_response = MagicMock()
        success_response.read.return_value = b'{"result": "success"}'

        with patch("urllib.request.urlopen") as mock_urlopen:
            with patch("time.sleep"):
                mock_urlopen.side_effect = [
                    urllib.error.URLError("Network unreachable"),
                    success_response,
                ]

                result = client._make_request("http://test:4444/test")

        assert result == {"result": "success"}
        assert mock_urlopen.call_count == 2

    def test_make_request_retry_on_timeout(self) -> None:
        """Test retry logic on timeout."""
        config = GatewayConfig(
            url="http://test:4444", jwt="token", max_retries=2, retry_delay_ms=50
        )
        client = HTTPGatewayClient(config)

        success_response = MagicMock()
        success_response.read.return_value = b'{"result": "success"}'

        with patch("urllib.request.urlopen") as mock_urlopen:
            with patch("time.sleep"):
                mock_urlopen.side_effect = [
                    TimeoutError("Request timed out"),
                    success_response,
                ]

                result = client._make_request("http://test:4444/test")

        assert result == {"result": "success"}
        assert mock_urlopen.call_count == 2

    def test_make_request_exponential_backoff(self) -> None:
        """Test that retry delay increases exponentially."""
        config = GatewayConfig(
            url="http://test:4444", jwt="token", max_retries=3, retry_delay_ms=100
        )
        client = HTTPGatewayClient(config)

        server_error = MagicMock()
        server_error.code = 500
        server_error.read.return_value = b"Server Error"

        success_response = MagicMock()
        success_response.read.return_value = b'{"result": "success"}'

        with patch("urllib.request.urlopen") as mock_urlopen:
            with patch("time.sleep") as mock_sleep:
                mock_urlopen.side_effect = [
                    urllib.error.HTTPError(url="", msg="", hdrs="", fp=server_error),
                    urllib.error.HTTPError(url="", msg="", hdrs="", fp=server_error),
                    success_response,
                ]

                client._make_request("http://test:4444/test")

        # Verify exponential backoff: 100ms, 200ms
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(0.1)  # 100ms
        mock_sleep.assert_any_call(0.2)  # 200ms

    def test_make_request_fails_after_max_retries(self) -> None:
        """Test failure after exhausting max retries."""
        config = GatewayConfig(
            url="http://test:4444", jwt="token", max_retries=2, retry_delay_ms=50
        )
        client = HTTPGatewayClient(config)

        server_error = MagicMock()
        server_error.code = 500
        server_error.read.return_value = b"Server Error"

        with patch("urllib.request.urlopen") as mock_urlopen:
            with patch("time.sleep"):
                mock_urlopen.side_effect = urllib.error.HTTPError(
                    url="", msg="", hdrs="", fp=server_error
                )

                with pytest.raises(ConnectionError, match="Failed after 2 attempts"):
                    client._make_request("http://test:4444/test")

        assert mock_urlopen.call_count == 2

    def test_make_request_client_error_no_retry(self) -> None:
        """Test that 4xx errors don't trigger retries."""
        config = GatewayConfig(url="http://test:4444", jwt="token", max_retries=3)
        client = HTTPGatewayClient(config)

        client_error = MagicMock()
        client_error.code = 404
        client_error.read.return_value = b"Not Found"

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.HTTPError(
                url="", msg="", hdrs="", fp=client_error
            )

            with pytest.raises(ValueError, match="Gateway HTTP error 404"):
                client._make_request("http://test:4444/test")

        # Should not retry on client errors
        assert mock_urlopen.call_count == 1

    def test_make_request_invalid_json_response(self) -> None:
        """Test handling of invalid JSON responses."""
        config = GatewayConfig(url="http://test:4444", jwt="token")
        client = HTTPGatewayClient(config)

        mock_response = MagicMock()
        mock_response.read.return_value = b"invalid json"

        with patch("urllib.request.urlopen", return_value=mock_response):
            with pytest.raises(ValueError, match="Invalid JSON response"):
                client._make_request("http://test:4444/test")

    def test_get_tools_success(self) -> None:
        """Test successful tools fetch."""
        config = GatewayConfig(url="http://test:4444", jwt="token")
        client = HTTPGatewayClient(config)

        mock_response_data = [
            {"name": "tool1", "description": "Test tool 1"},
            {"name": "tool2", "description": "Test tool 2"},
        ]

        with patch.object(client, "_make_request", return_value=mock_response_data):
            result = client.get_tools()

        assert result == mock_response_data
        assert len(result) == 2

    def test_get_tools_wrapped_response(self) -> None:
        """Test tools fetch with wrapped response format."""
        config = GatewayConfig(url="http://test:4444", jwt="token")
        client = HTTPGatewayClient(config)

        mock_response_data = {"tools": [{"name": "tool1", "description": "Test tool"}]}

        with patch.object(client, "_make_request", return_value=mock_response_data):
            result = client.get_tools()

        assert result == [{"name": "tool1", "description": "Test tool"}]

    def test_get_tools_empty_response(self) -> None:
        """Test tools fetch with empty/invalid response."""
        config = GatewayConfig(url="http://test:4444", jwt="token")
        client = HTTPGatewayClient(config)

        with patch.object(client, "_make_request", return_value={}):
            result = client.get_tools()

        assert result == []

    def test_get_tools_propagates_errors(self) -> None:
        """Test that get_tools properly propagates errors."""
        config = GatewayConfig(url="http://test:4444", jwt="token")
        client = HTTPGatewayClient(config)

        with patch.object(
            client, "_make_request", side_effect=ValueError("Network error")
        ):
            with pytest.raises(
                ValueError, match="Failed to fetch tools: Network error"
            ):
                client.get_tools()

    def test_call_tool_success(self) -> None:
        """Test successful tool call."""
        config = GatewayConfig(url="http://test:4444", jwt="token")
        client = HTTPGatewayClient(config)

        mock_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "content": [
                    {"type": "text", "text": "Tool executed successfully"},
                    {"type": "text", "text": "Additional output"},
                ]
            },
        }

        with patch.object(client, "_make_request", return_value=mock_response):
            result = client.call_tool("test_tool", {"arg": "value"})

        assert result == "Tool executed successfully\nAdditional output"

    def test_call_tool_with_non_text_content(self) -> None:
        """Test tool call with non-text content fallback."""
        config = GatewayConfig(url="http://test:4444", jwt="token")
        client = HTTPGatewayClient(config)

        mock_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"data": "some_binary_data", "metadata": {}},
        }

        with patch.object(client, "_make_request", return_value=mock_response):
            result = client.call_tool("test_tool", {"arg": "value"})

        assert result == '{"data": "some_binary_data", "metadata": {}}'

    def test_call_tool_with_error_response(self) -> None:
        """Test tool call with error response."""
        config = GatewayConfig(url="http://test:4444", jwt="token")
        client = HTTPGatewayClient(config)

        mock_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"code": -32601, "message": "Method not found"},
        }

        with patch.object(client, "_make_request", return_value=mock_response):
            result = client.call_tool("unknown_tool", {})

        assert (
            result == "Gateway error: {'code': -32601, 'message': 'Method not found'}"
        )

    def test_call_tool_propagates_errors_as_string(self) -> None:
        """Test that call_tool returns errors as string rather than raising."""
        config = GatewayConfig(url="http://test:4444", jwt="token")
        client = HTTPGatewayClient(config)

        with patch.object(
            client, "_make_request", side_effect=ValueError("Connection failed")
        ):
            result = client.call_tool("test_tool", {})

        assert result == "Failed to call tool: Connection failed"

    def test_call_tool_request_format(self) -> None:
        """Test that tool call uses correct JSON-RPC format."""
        config = GatewayConfig(url="http://test:4444", jwt="token")
        client = HTTPGatewayClient(config)

        mock_response = {"jsonrpc": "2.0", "id": 1, "result": {"content": []}}

        with patch.object(
            client, "_make_request", return_value=mock_response
        ) as mock_request:
            client.call_tool("test_tool", {"arg1": "value1", "arg2": "value2"})

        # Verify the request was made with correct data
        call_args = mock_request.call_args
        assert call_args[0][0] == f"{config.url}/rpc"
        assert call_args[1]["method"] == "POST"

        # Parse the request data
        request_data = json.loads(call_args[1]["data"].decode())
        expected_body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "test_tool",
                "arguments": {"arg1": "value1", "arg2": "value2"},
            },
        }
        assert request_data == expected_body


class TestGatewayClientProtocol:
    """Tests for GatewayClient protocol compliance."""

    def test_http_gateway_client_implements_protocol(self) -> None:
        """Test that HTTPGatewayClient implements GatewayClient protocol."""
        config = GatewayConfig(url="http://test:4444", jwt="token")
        client = HTTPGatewayClient(config)

        # Should be able to assign to GatewayClient type
        gateway_client: GatewayClient = client
        assert isinstance(gateway_client, GatewayClient)
        assert hasattr(gateway_client, "get_tools")
        assert hasattr(gateway_client, "call_tool")


# Existing tests for module-level functions


def test_get_tools_raises_when_gateway_jwt_unset() -> None:
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError, match="GATEWAY_JWT"):
            get_tools()


def test_get_tools_returns_list_from_list_response() -> None:
    data = [{"name": "t1", "description": "d1"}]
    resp = MagicMock()
    resp.read.return_value = json.dumps(data).encode()
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=None)

    with patch.dict(
        "os.environ", {"GATEWAY_JWT": "token", "GATEWAY_URL": "http://localhost:4444"}
    ):
        with patch("urllib.request.urlopen", return_value=resp):
            result = get_tools()
    assert result == data


def test_get_tools_returns_tools_from_wrapped_response() -> None:
    data = {"tools": [{"name": "t1"}]}
    resp = MagicMock()
    resp.read.return_value = json.dumps(data).encode()
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=None)

    with patch.dict(
        "os.environ", {"GATEWAY_JWT": "token", "GATEWAY_URL": "http://localhost:4444"}
    ):
        with patch("urllib.request.urlopen", return_value=resp):
            result = get_tools()
    assert result == [{"name": "t1"}]


def test_get_tools_returns_empty_for_unknown_shape() -> None:
    """Test graceful handling of unknown response shapes."""
    resp = MagicMock()
    resp.read.return_value = b"{}"
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=None)

    with patch.dict(
        "os.environ", {"GATEWAY_JWT": "token", "GATEWAY_URL": "http://localhost:4444"}
    ):
        with patch("urllib.request.urlopen", return_value=resp):
            result = get_tools()

    # Business logic: unknown/empty response should return empty list
    assert result == []

    # Business logic: test with malformed JSON response
    malformed_resp = MagicMock()
    malformed_resp.read.return_value = b"not valid json"
    malformed_resp.__enter__ = MagicMock(return_value=malformed_resp)
    malformed_resp.__exit__ = MagicMock(return_value=None)

    with patch.dict(
        "os.environ", {"GATEWAY_JWT": "token", "GATEWAY_URL": "http://localhost:4444"}
    ):
        with patch("urllib.request.urlopen", return_value=malformed_resp):
            # Should handle JSON parsing errors gracefully
            result = get_tools()
            assert result == []  # Should default to empty list on JSON error

    # Business logic: test with null response
    null_resp = MagicMock()
    null_resp.read.return_value = b"null"
    null_resp.__enter__ = MagicMock(return_value=null_resp)
    null_resp.__exit__ = MagicMock(return_value=None)

    with patch.dict(
        "os.environ", {"GATEWAY_JWT": "token", "GATEWAY_URL": "http://localhost:4444"}
    ):
        with patch("urllib.request.urlopen", return_value=null_resp):
            result = get_tools()
            assert result == []  # Should handle null response

    # Business logic: verify function doesn't crash with various edge cases
    # This tests the robustness of the response parsing logic


def test_call_tool_raises_when_gateway_jwt_unset() -> None:
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError, match="GATEWAY_JWT"):
            call_tool("foo", {})


def test_call_tool_returns_error_message_on_jsonrpc_error() -> None:
    out = {"jsonrpc": "2.0", "id": 1, "error": {"message": "Tool not found"}}
    resp = MagicMock()
    resp.read.return_value = json.dumps(out).encode()
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=None)

    with patch.dict(
        "os.environ", {"GATEWAY_JWT": "token", "GATEWAY_URL": "http://localhost:4444"}
    ):
        with patch("urllib.request.urlopen", return_value=resp):
            result = call_tool("bad_tool", {})
    assert "Gateway error" in result
    assert "Tool not found" in result


def test_call_tool_returns_text_content() -> None:
    out = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {"content": [{"type": "text", "text": "Hello"}]},
    }
    resp = MagicMock()
    resp.read.return_value = json.dumps(out).encode()
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=None)

    with patch.dict(
        "os.environ", {"GATEWAY_JWT": "token", "GATEWAY_URL": "http://localhost:4444"}
    ):
        with patch("urllib.request.urlopen", return_value=resp):
            result = call_tool("greet", {})
    assert result == "Hello"
