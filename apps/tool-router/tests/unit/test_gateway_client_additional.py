"""Additional unit tests for gateway client to cover remaining missing lines."""

from __future__ import annotations

import json
import pytest
from unittest.mock import Mock, patch
import urllib.error

from tool_router.gateway.client import HTTPGatewayClient, GatewayConfig


class TestHTTPGatewayClientAdditional:
    """Additional tests for HTTPGatewayClient to improve coverage."""

    def test_validate_url_security_private_ip(self) -> None:
        """Test _validate_url_security blocks private IP addresses."""
        from tool_router.gateway.client import _validate_url_security

        # Test various private IP ranges
        private_ips = [
            "http://192.168.1.1",
            "http://10.0.0.1",
            "http://172.16.0.1",
            "http://169.254.169.254",  # This is actually link-local, should be caught by link-local check
        ]

        for ip_url in private_ips[:3]:  # Skip the last one as it's link-local
            with pytest.raises(ValueError, match="Private IP address not allowed"):
                _validate_url_security(ip_url)

    def test_validate_url_security_link_local(self) -> None:
        """Test _validate_url_security blocks link-local addresses."""
        from tool_router.gateway.client import _validate_url_security

        with pytest.raises(ValueError, match="Link-local address not allowed"):
            _validate_url_security("http://169.254.169.254")

    def test_validate_url_security_loopback(self) -> None:
        """Test _validate_url_security blocks loopback addresses."""
        from tool_router.gateway.client import _validate_url_security

        loopback_ips = [
            "http://127.0.0.1",
            "http://localhost",
            "http://0.0.0.0"
        ]

        for ip_url in loopback_ips:
            with pytest.raises(ValueError, match="Loopback address not allowed"):
                _validate_url_security(ip_url)

    def test_make_request_server_error_retry_logic(self, mocker) -> None:
        """Test _make_request retry logic for server errors (5xx)."""
        config = GatewayConfig(url="http://localhost:4444", max_retries=3, retry_delay_ms=100)
        client = HTTPGatewayClient(config)

        mock_urlopen = mocker.patch("urllib.request.urlopen")
        mock_sleep = mocker.patch("time.sleep")

        # First two calls return 500, third succeeds
        server_error = urllib.error.HTTPError(
            url="http://localhost:4444/test",
            code=500,
            msg="Internal Server Error",
            hdrs={},
            fp=None
        )

        mock_response = Mock()
        mock_response.read.return_value = b'{"result": "success"}'

        mock_urlopen.side_effect = [
            server_error,  # First attempt fails
            server_error,  # Second attempt fails
            mock_response  # Third succeeds
        ]

        result = client._make_request("http://localhost:4444/test", method="GET")

        assert result == {"result": "success"}
        assert mock_urlopen.call_count == 3
        assert mock_sleep.call_count == 2

    def test_make_request_server_error_exhaust_retries(self, mocker) -> None:
        """Test _make_request exhausts retries for server errors."""
        config = GatewayConfig(url="http://localhost:4444", max_retries=2, retry_delay_ms=100)
        client = HTTPGatewayClient(config)

        mock_urlopen = mocker.patch("urllib.request.urlopen")
        mock_sleep = mocker.patch("time.sleep")

        # All calls return 500
        server_error = urllib.error.HTTPError(
            url="http://localhost:4444/test",
            code=500,
            msg="Internal Server Error",
            hdrs={},
            fp=None
        )
        mock_urlopen.side_effect = server_error

        with pytest.raises(ValueError, match="Gateway server error \\(HTTP 500\\)"):
            client._make_request("http://localhost:4444/test", method="GET")

        assert mock_urlopen.call_count == 2
        assert mock_sleep.call_count == 1

    def test_make_request_client_error_no_retry(self, mocker) -> None:
        """Test _make_request doesn't retry client errors (4xx)."""
        config = GatewayConfig(url="http://localhost:4444", max_retries=3)
        client = HTTPGatewayClient(config)

        mock_urlopen = mocker.patch("urllib.request.urlopen")

        # Return 400 error
        client_error = urllib.error.HTTPError(
            url="http://localhost:4444/test",
            code=400,
            msg="Bad Request",
            hdrs={},
            fp=None
        )
        mock_urlopen.side_effect = client_error

        with pytest.raises(ValueError, match="Gateway HTTP error 400"):
            client._make_request("http://localhost:4444/test", method="GET")

        # Should not retry
        assert mock_urlopen.call_count == 1

    def test_make_request_client_error_with_body(self, mocker) -> None:
        """Test _make_request includes error body for client errors."""
        config = GatewayConfig(url="http://localhost:4444")
        client = HTTPGatewayClient(config)

        mock_urlopen = mocker.patch("urllib.request.urlopen")

        # Return 400 error with body
        error_body = Mock()
        error_body.read.return_value = b'{"error": "Invalid request"}'
        error_body.decode.return_value = '{"error": "Invalid request"}'

        client_error = urllib.error.HTTPError(
            url="http://localhost:4444/test",
            code=400,
            msg="Bad Request",
            hdrs={},
            fp=error_body
        )
        mock_urlopen.side_effect = client_error

        with pytest.raises(ValueError, match='Gateway HTTP error 400: {"error": "Invalid request"}'):
            client._make_request("http://localhost:4444/test", method="GET")

    def test_make_request_client_error_unreadable_body(self, mocker) -> None:
        """Test _make_request handles unreadable error body."""
        config = GatewayConfig(url="http://localhost:4444")
        client = HTTPGatewayClient(config)

        mock_urlopen = mocker.patch("urllib.request.urlopen")

        # Return 400 error with unreadable body
        error_body = Mock()
        error_body.read.side_effect = OSError("Read error")

        client_error = urllib.error.HTTPError(
            url="http://localhost:4444/test",
            code=400,
            msg="Bad Request",
            hdrs={},
            fp=error_body
        )
        mock_urlopen.side_effect = client_error

        with pytest.raises(ValueError, match="Gateway HTTP error 400: <unable to read response body>"):
            client._make_request("http://localhost:4444/test", method="GET")

    def test_make_request_network_error_retry_logic(self, mocker) -> None:
        """Test _make_request retry logic for network errors."""
        config = GatewayConfig(url="http://localhost:4444", max_retries=2, retry_delay_ms=100)
        client = HTTPGatewayClient(config)

        mock_urlopen = mocker.patch("urllib.request.urlopen")
        mock_sleep = mocker.patch("time.sleep")

        # First call fails with network error, second succeeds
        network_error = urllib.error.URLError("Connection refused")

        mock_response = Mock()
        mock_response.read.return_value = b'{"result": "success"}'

        mock_urlopen.side_effect = [
            network_error,
            mock_response
        ]

        result = client._make_request("http://localhost:4444/test", method="GET")

        assert result == {"result": "success"}
        assert mock_urlopen.call_count == 2
        assert mock_sleep.call_count == 1

    def test_make_request_network_error_exhaust_retries(self, mocker) -> None:
        """Test _make_request exhausts retries for network errors."""
        config = GatewayConfig(url="http://localhost:4444", max_retries=2)
        client = HTTPGatewayClient(config)

        mock_urlopen = mocker.patch("urllib.request.urlopen")
        mock_sleep = mocker.patch("time.sleep")

        # All calls fail with network error
        network_error = urllib.error.URLError("Connection refused")
        mock_urlopen.side_effect = network_error

        with pytest.raises(ValueError, match="Network error: Connection refused"):
            client._make_request("http://localhost:4444/test", method="GET")

        assert mock_urlopen.call_count == 2
        assert mock_sleep.call_count == 1

    def test_make_request_with_json_data(self, mocker) -> None:
        """Test _make_request with JSON data encoding."""
        config = GatewayConfig(url="http://localhost:4444")
        client = HTTPGatewayClient(config)

        mock_urlopen = mocker.patch("urllib.request.urlopen")
        mock_response = Mock()
        mock_response.read.return_value = b'{"result": "success"}'
        mock_urlopen.return_value = mock_response

        test_data = {"key": "value", "number": 123}
        client._make_request(
            "http://localhost:4444/test",
            method="POST",
            data=test_data
        )

        # Verify the request was made with properly encoded JSON data
        call_args = mock_urlopen.call_args
        request = call_args[0][0]

        assert request.data == b'{"key": "value", "number": 123}'

    def test_make_request_timeout_conversion(self, mocker) -> None:
        """Test _make_request converts timeout_ms to seconds."""
        config = GatewayConfig(url="http://localhost:4444", timeout_ms=5000)
        client = HTTPGatewayClient(config)

        mock_urlopen = mocker.patch("urllib.request.urlopen")
        mock_response = Mock()
        mock_response.read.return_value = b'{"result": "success"}'
        mock_urlopen.return_value = mock_response

        client._make_request("http://localhost:4444/test", method="GET")

        # Verify timeout was converted to seconds (5.0)
        call_args = mock_urlopen.call_args
        assert call_args[1]["timeout"] == 5.0

    def test_make_request_retry_delay_conversion(self, mocker) -> None:
        """Test retry delay conversion from milliseconds to seconds."""
        config = GatewayConfig(url="http://localhost:4444", max_retries=2, retry_delay_ms=2000)
        client = HTTPGatewayClient(config)

        mock_urlopen = mocker.patch("urllib.request.urlopen")
        mock_sleep = mocker.patch("time.sleep")

        # First call fails, second succeeds
        network_error = urllib.error.URLError("Connection refused")
        mock_response = Mock()
        mock_response.read.return_value = b'{"result": "success"}'

        mock_urlopen.side_effect = [
            network_error,
            mock_response
        ]

        client._make_request("http://localhost:4444/test", method="GET")

        # Verify sleep was called with correct delay (2.0 seconds)
        mock_sleep.assert_called_once_with(2.0)
