"""Enhanced unit tests for gateway client to improve coverage."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch

from tool_router.gateway.client import (
    HTTPGatewayClient,
    RedirectHandler,
    _validate_url_security,
    GatewayConfig,
)


class TestValidateUrlSecurity:
    """Tests for URL security validation function."""

    def test_validate_url_security_invalid_scheme(self) -> None:
        """Test rejection of invalid URL schemes."""
        with pytest.raises(ValueError, match="Invalid URL scheme: ftp"):
            _validate_url_security("ftp://example.com")

    def test_validate_url_security_no_hostname(self) -> None:
        """Test rejection of URLs without hostname."""
        with pytest.raises(ValueError, match="Invalid URL: no hostname"):
            _validate_url_security("http:///path")

    def test_validate_url_security_private_ip(self) -> None:
        """Test rejection of private IP addresses."""
        with pytest.raises(ValueError, match="Private IP address not allowed"):
            _validate_url_security("http://192.168.1.1")

    def test_validate_url_security_loopback(self) -> None:
        """Test rejection of loopback addresses."""
        with pytest.raises(ValueError, match="Loopback address not allowed"):
            _validate_url_security("http://127.0.0.1")

    def test_validate_url_security_link_local(self) -> None:
        """Test rejection of link-local addresses."""
        with pytest.raises(ValueError, match="Link-local address not allowed"):
            _validate_url_security("http://169.254.169.254")

    def test_validate_url_security_valid_public_ip(self) -> None:
        """Test acceptance of valid public IP addresses."""
        # Should not raise any exception
        _validate_url_security("http://8.8.8.8")

    def test_validate_url_security_valid_domain(self) -> None:
        """Test acceptance of valid domain names."""
        # Should not raise any exception
        _validate_url_security("https://api.example.com")


class TestRedirectHandler:
    """Tests for RedirectHandler class."""

    def test_http_error_302_within_limit(self) -> None:
        """Test 302 redirect handling within limit."""
        handler = RedirectHandler(max_redirects=5)
        handler.redirect_count = 2

        # Mock the parent method
        with patch.object(handler.__class__.__bases__[0], 'http_error_302', return_value="handled"):
            result = handler.http_error_302(None, None, 302, "Found", {})
            assert result == "handled"
            assert handler.redirect_count == 3

    def test_http_error_302_exceeds_limit(self) -> None:
        """Test 302 redirect handling when limit exceeded."""
        handler = RedirectHandler(max_redirects=2)
        handler.redirect_count = 2

        with pytest.raises(ValueError, match="Too many redirects: 3"):
            handler.http_error_302(None, None, 302, "Found", {})

    def test_http_error_301_within_limit(self) -> None:
        """Test 301 redirect handling within limit."""
        handler = RedirectHandler(max_redirects=5)
        handler.redirect_count = 1

        # Mock the parent method
        with patch.object(handler.__class__.__bases__[0], 'http_error_301', return_value="handled"):
            result = handler.http_error_301(None, None, 301, "Moved Permanently", {})
            assert result == "handled"
            assert handler.redirect_count == 2

    def test_http_error_301_exceeds_limit(self) -> None:
        """Test 301 redirect handling when limit exceeded."""
        handler = RedirectHandler(max_redirects=1)
        handler.redirect_count = 1

        with pytest.raises(ValueError, match="Too many redirects: 2"):
            handler.http_error_301(None, None, 301, "Moved Permanently", {})


class TestHTTPGatewayClientEnhanced:
    """Enhanced tests for HTTPGatewayClient."""

    def test_init_with_custom_config(self) -> None:
        """Test HTTPGatewayClient initialization with custom config."""
        config = GatewayConfig(
            url="https://custom.example.com",
            jwt="custom-token",
            timeout_ms=5000
        )

        client = HTTPGatewayClient(config)

        assert client.config.url == "https://custom.example.com"
        assert client.config.jwt == "custom-token"
        assert client.config.timeout_ms == 5000

    def test_init_with_default_config(self) -> None:
        """Test HTTPGatewayClient initialization with default config."""
        config = GatewayConfig(
            url="http://localhost:4444",
            jwt="test-token"
        )

        client = HTTPGatewayClient(config)

        assert client.config.url == "http://localhost:4444"
        assert client.config.jwt == "test-token"
        assert client.config.timeout_ms == 120000  # Default value

    def test_make_request_with_authentication_headers(self, mocker) -> None:
        """Test _make_request includes authentication headers."""
        config = GatewayConfig(
            url="http://localhost:4444",
            jwt="test-jwt-token"
        )
        client = HTTPGatewayClient(config)

        mock_urlopen = mocker.patch("urllib.request.urlopen")
        mock_response = Mock()
        mock_response.read.return_value = b'{"result": "success"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        client._make_request("http://localhost:4444/test", method="GET")

        # Verify the request was made with proper headers
        call_args = mock_urlopen.call_args
        request = call_args[0][0]

        assert "Authorization" in request.headers
        assert request.headers["Authorization"] == "Bearer test-jwt-token"

    def test_make_request_without_authentication(self, mocker) -> None:
        """Test _make_request without JWT token."""
        config = GatewayConfig(
            url="http://localhost:4444"
            # No jwt
        )
        client = HTTPGatewayClient(config)

        mock_urlopen = mocker.patch("urllib.request.urlopen")
        mock_response = Mock()
        mock_response.read.return_value = b'{"result": "success"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        client._make_request("http://localhost:4444/test", method="GET")

        # Verify the request was made without auth header
        call_args = mock_urlopen.call_args
        request = call_args[0][0]

        assert "Authorization" not in request.headers

    def test_make_request_with_custom_headers(self, mocker) -> None:
        """Test _make_request with custom headers."""
        config = GatewayConfig(
            url="http://localhost:4444",
            jwt="test-token"
        )
        client = HTTPGatewayClient(config)

        mock_urlopen = mocker.patch("urllib.request.urlopen")
        mock_response = Mock()
        mock_response.read.return_value = b'{"result": "success"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        client._make_request(
            "http://localhost:4444/test",
            method="POST",
            headers={"X-Custom": "value"}
        )

        # Verify custom headers were included
        call_args = mock_urlopen.call_args
        request = call_args[0][0]

        assert request.headers["X-Custom"] == "value"

    def test_make_request_with_post_data(self, mocker) -> None:
        """Test _make_request with POST data."""
        config = GatewayConfig(url="http://localhost:4444")
        client = HTTPGatewayClient(config)

        mock_urlopen = mocker.patch("urllib.request.urlopen")
        mock_response = Mock()
        mock_response.read.return_value = b'{"result": "success"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        test_data = {"key": "value"}
        client._make_request(
            "http://localhost:4444/test",
            method="POST",
            data=test_data
        )

        # Verify the request was made with POST data
        call_args = mock_urlopen.call_args
        request = call_args[0][0]

        assert request.data == b'{"key": "value"}'

    def test_make_request_timeout_handling(self, mocker) -> None:
        """Test _make_request timeout handling."""
        config = GatewayConfig(url="http://localhost:4444", timeout_ms=1000)
        client = HTTPGatewayClient(config)

        mock_urlopen = mocker.patch("urllib.request.urlopen")

        with pytest.raises(ValueError, match="Request timeout"):
            client._make_request("http://localhost:4444/test", method="GET")

    def test_get_tools_with_retry_logic(self, mocker) -> None:
        """Test get_tools with retry logic on temporary failures."""
        config = GatewayConfig(url="http://localhost:4444", jwt="test-token")
        client = HTTPGatewayClient(config)

        # Mock _make_request to fail once then succeed
        mock_make_request = mocker.patch.object(client, '_make_request')
        mock_make_request.side_effect = [
            ValueError("Temporary error"),  # First call fails
            {"tools": []}  # Second call succeeds
        ]

        with patch("time.sleep"):  # Mock sleep to avoid actual delays
            result = client.get_tools()

        assert result == []
        assert mock_make_request.call_count == 2

    def test_call_tool_error_handling(self, mocker) -> None:
        """Test call_tool error handling."""
        config = GatewayConfig(url="http://localhost:4444", jwt="test-token")
        client = HTTPGatewayClient(config)

        # Mock _make_request to return an error response
        mock_make_request = mocker.patch.object(client, '_make_request')
        mock_make_request.return_value = {
            "error": "Tool not found",
            "code": 404
        }

        with pytest.raises(ValueError, match="Tool not found"):
            client.call_tool("nonexistent_tool", {})

    def test_call_tool_success(self, mocker) -> None:
        """Test successful call_tool execution."""
        config = GatewayConfig(url="http://localhost:4444", jwt="test-token")
        client = HTTPGatewayClient(config)

        # Mock _make_request to return success response
        mock_make_request = mocker.patch.object(client, '_make_request')
        mock_make_request.return_value = {
            "result": "Tool executed successfully",
            "content": "Hello, World!"
        }

        result = client.call_tool("test_tool", {"param": "value"})

        assert result == "Hello, World!"
        mock_make_request.assert_called_once()
