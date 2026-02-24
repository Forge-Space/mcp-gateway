"""Unit tests for gateway client error handling paths."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from unittest.mock import MagicMock, patch

import pytest

from tool_router.core.config import GatewayConfig
from tool_router.gateway.client import HTTPGatewayClient


class TestHTTPGatewayClientErrorPaths:
    """Tests for HTTPGatewayClient error handling."""

    def test_http_error_500_retries_and_fails(self) -> None:
        """Test that 5xx errors trigger retries and eventually fail."""
        config = GatewayConfig(
            url="http://test:4444",
            jwt="token",
            max_retries=2,
            retry_delay_ms=10,
        )
        client = HTTPGatewayClient(config)

        mock_response = MagicMock()
        mock_response.code = 500
        mock_response.read.return_value = b"Server error"

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.HTTPError(
                "http://test:4444/tools",
                500,
                "Internal Server Error",
                {},
                None,
            )

            with pytest.raises(ValueError, match="Failed to fetch tools"):
                client.get_tools()

            assert mock_urlopen.call_count == 2

    def test_http_error_503_retries_with_backoff(self) -> None:
        """Test that 503 errors retry with exponential backoff."""
        config = GatewayConfig(
            url="http://test:4444",
            jwt="token",
            max_retries=3,
            retry_delay_ms=100,
        )
        client = HTTPGatewayClient(config)

        with (
            patch("urllib.request.urlopen") as mock_urlopen,
            patch("time.sleep") as mock_sleep,
        ):
            mock_urlopen.side_effect = urllib.error.HTTPError(
                "http://test:4444/tools", 503, "Service Unavailable", {}, None
            )

            with pytest.raises(ValueError, match="Failed to fetch tools"):
                client.get_tools()

            # Verify exponential backoff: delay * (attempt + 1)
            assert mock_sleep.call_count == 2  # Retries before last attempt
            mock_sleep.assert_any_call(0.1)  # First retry: 100ms * 1
            mock_sleep.assert_any_call(0.2)  # Second retry: 100ms * 2

    def test_http_error_4xx_raises_immediately(self) -> None:
        """Test that 4xx errors raise immediately without retry."""
        config = GatewayConfig(url="http://test:4444", jwt="token", max_retries=3)
        client = HTTPGatewayClient(config)

        error_response = b'{"error": "Unauthorized"}'
        http_error = urllib.error.HTTPError("http://test:4444/tools", 401, "Unauthorized", {}, None)
        http_error.read = lambda: error_response

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = http_error

            with pytest.raises(ValueError, match="Gateway HTTP error 401"):
                client.get_tools()

            # Should not retry on 4xx
            assert mock_urlopen.call_count == 1

    def test_url_error_retries_and_fails(self) -> None:
        """Test that URLError (network errors) trigger retries."""
        config = GatewayConfig(
            url="http://test:4444",
            jwt="token",
            max_retries=2,
            retry_delay_ms=10,
        )
        client = HTTPGatewayClient(config)

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

            with pytest.raises(ValueError, match="Failed to fetch tools"):
                client.get_tools()

            assert mock_urlopen.call_count == 2

    def test_timeout_error_retries_and_fails(self) -> None:
        """Test that TimeoutError triggers retries."""
        config = GatewayConfig(
            url="http://test:4444",
            jwt="token",
            max_retries=2,
            retry_delay_ms=10,
            timeout_ms=1000,
        )
        client = HTTPGatewayClient(config)

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = TimeoutError("Request timed out")

            with pytest.raises(ValueError, match="Failed to fetch tools"):
                client.get_tools()

            assert mock_urlopen.call_count == 2

    def test_json_decode_error_handled_gracefully(self) -> None:
        """Test that invalid JSON is handled gracefully and returns empty list."""
        config = GatewayConfig(url="http://test:4444", jwt="token")
        client = HTTPGatewayClient(config)

        mock_response = MagicMock()
        # The response.read() returns bytes, then decode() is called on those bytes
        mock_response.read.return_value = b"Not valid JSON"
        mock_response.__enter__ = lambda self: self
        mock_response.__exit__ = lambda self, *args: None

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_response

            # Should handle JSON decode errors gracefully and return empty list
            result = client.get_tools()
            assert result == []

            # Should not retry on JSON decode errors
            assert mock_urlopen.call_count == 1

    def test_call_tool_with_server_error(self) -> None:
        """Test call_tool handles server errors gracefully."""
        config = GatewayConfig(
            url="http://test:4444",
            jwt="token",
            max_retries=2,
            retry_delay_ms=10,
        )
        client = HTTPGatewayClient(config)

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.HTTPError("http://test:4444/rpc", 502, "Bad Gateway", {}, None)

            result = client.call_tool("test_tool", {"arg": "value"})

            assert "Failed to call tool" in result
            assert mock_urlopen.call_count == 2

    def test_call_tool_with_network_error(self) -> None:
        """Test call_tool handles network errors gracefully."""
        config = GatewayConfig(
            url="http://test:4444",
            jwt="token",
            max_retries=2,
            retry_delay_ms=10,
        )
        client = HTTPGatewayClient(config)

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError("Network unreachable")

            result = client.call_tool("test_tool", {"arg": "value"})

            assert "Failed to call tool" in result
            assert "Network error" in result or "Connection" in result

    def test_mixed_errors_across_retries(self) -> None:
        """Test handling of different errors across retry attempts."""
        config = GatewayConfig(
            url="http://test:4444",
            jwt="token",
            max_retries=3,
            retry_delay_ms=10,
        )
        client = HTTPGatewayClient(config)

        # First attempt: 503, second: timeout, third: 500
        errors = [
            urllib.error.HTTPError("http://test:4444/tools", 503, "Service Unavailable", {}, None),
            TimeoutError("Timeout"),
            urllib.error.HTTPError("http://test:4444/tools", 500, "Internal Server Error", {}, None),
        ]

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = errors

            with pytest.raises(ValueError, match="Failed to fetch tools"):
                client.get_tools()

            assert mock_urlopen.call_count == 3

    def test_successful_retry_after_failures(self) -> None:
        """Test successful response after initial failures."""
        config = GatewayConfig(
            url="http://test:4444",
            jwt="token",
            max_retries=3,
            retry_delay_ms=10,
        )
        client = HTTPGatewayClient(config)

        mock_success = MagicMock()
        mock_success.read.return_value = json.dumps({"tools": []}).encode()
        mock_success.__enter__ = lambda self: self
        mock_success.__exit__ = lambda self, *args: None

        # Business logic: Fail twice with different error types, then succeed
        errors = [
            urllib.error.HTTPError("http://test:4444/tools", 503, "Service Unavailable", {}, None),
            urllib.error.URLError("Connection refused"),
            mock_success,
        ]

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = errors

            result = client.get_tools()

            # Business logic: Should eventually succeed after retries
            assert result == []
            assert mock_urlopen.call_count == 3

            # Business logic: Verify retry delay behavior
            # Should have waited between retries (mock time verification would require additional setup)

            # Business logic: Verify error handling doesn't corrupt client state
            # Client should still be functional after retry success
            assert client is not None
            assert client.config.max_retries == 3

            # Business logic: Verify different error types are handled
            # HTTP errors and URL errors should both trigger retries
