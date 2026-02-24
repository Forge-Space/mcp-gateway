"""Comprehensive unit tests for infrastructure components."""

import os
import unittest
from unittest.mock import Mock, patch

import pytest

from tool_router.args.builder import COMMON_TASK_PARAMETER_NAMES, build_arguments
from tool_router.core.config import GatewayConfig
from tool_router.gateway.client import HTTPGatewayClient


class TestGatewayConfig:
    """Test GatewayConfig class."""

    def test_gateway_config_creation(self):
        """Test GatewayConfig creation with all parameters."""
        config = GatewayConfig(
            url="https://api.example.com",
            jwt="test-jwt-token",
            timeout_ms=5000,
            max_retries=3,
            retry_delay_ms=1000,
        )

        assert config.url == "https://api.example.com"
        assert config.jwt == "test-jwt-token"
        assert config.timeout_ms == 5000
        assert config.max_retries == 3
        assert config.retry_delay_ms == 1000

    def test_gateway_config_defaults(self):
        """Test GatewayConfig with default values."""
        config = GatewayConfig(url="https://api.example.com", jwt="test-token")

        assert config.url == "https://api.example.com"
        assert config.jwt == "test-token"
        assert config.timeout_ms == 10000  # Default value
        assert config.max_retries == 3  # Default value
        assert config.retry_delay_ms == 1000  # Default value

    def test_load_from_environment(self):
        """Test loading config from environment variables."""
        with patch.dict(
            os.environ,
            {
                "GATEWAY_URL": "https://env-api.example.com",
                "GATEWAY_JWT": "env-jwt-token",
                "GATEWAY_TIMEOUT_MS": "8000",
                "GATEWAY_MAX_RETRIES": "5",
                "GATEWAY_RETRY_DELAY_MS": "500",
            },
        ):
            config = GatewayConfig.load_from_environment()

            assert config.url == "https://env-api.example.com"
            assert config.jwt == "env-jwt-token"
            assert config.timeout_ms == 8000
            assert config.max_retries == 5
            assert config.retry_delay_ms == 500

    def test_load_from_environment_missing_required(self):
        """Test loading config when required env vars are missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ValueError, match="GATEWAY_URL environment variable is required"
            ):
                GatewayConfig.load_from_environment()

    def test_load_from_environment_missing_optional(self):
        """Test loading config when optional env vars are missing."""
        with patch.dict(
            os.environ,
            {"GATEWAY_URL": "https://api.example.com", "GATEWAY_JWT": "test-token"},
            clear=True,
        ):
            config = GatewayConfig.load_from_environment()

            assert config.url == "https://api.example.com"
            assert config.jwt == "test-token"
            assert config.timeout_ms == 10000  # Default
            assert config.max_retries == 3  # Default
            assert config.retry_delay_ms == 1000  # Default

    def test_load_from_environment_invalid_values(self):
        """Test loading config with invalid environment values."""
        with patch.dict(
            os.environ,
            {
                "GATEWAY_URL": "https://api.example.com",
                "GATEWAY_JWT": "test-token",
                "GATEWAY_TIMEOUT_MS": "invalid",
                "GATEWAY_MAX_RETRIES": "not_a_number",
            },
        ):
            with pytest.raises(ValueError, match="Invalid GATEWAY_TIMEOUT_MS"):
                GatewayConfig.load_from_environment()

    def test_gateway_config_validation(self):
        """Test GatewayConfig validation."""
        # Valid URL
        config = GatewayConfig(url="https://api.example.com", jwt="token")
        assert config.url == "https://api.example.com"

        # Invalid URL should still work (validation is minimal)
        config = GatewayConfig(url="invalid-url", jwt="token")
        assert config.url == "invalid-url"

    def test_gateway_config_equality(self):
        """Test GatewayConfig equality comparison."""
        config1 = GatewayConfig(url="https://api.example.com", jwt="token")
        config2 = GatewayConfig(url="https://api.example.com", jwt="token")
        config3 = GatewayConfig(url="https://api.example.com", jwt="different")

        assert config1 == config2
        assert config1 != config3

    def test_gateway_config_repr(self):
        """Test GatewayConfig string representation."""
        config = GatewayConfig(url="https://api.example.com", jwt="token")
        repr_str = repr(config)

        assert "GatewayConfig" in repr_str
        assert "https://api.example.com" in repr_str
        assert "token" not in repr_str  # JWT should not be exposed in repr


class TestHTTPGatewayClient:
    """Test HTTPGatewayClient class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = GatewayConfig(
            url="https://api.example.com",
            jwt="test-jwt-token",
            timeout_ms=5000,
            max_retries=3,
            retry_delay_ms=1000,
        )

    def test_initialization(self):
        """Test HTTPGatewayClient initialization."""
        client = HTTPGatewayClient(self.config)

        assert client.config == self.config
        assert client._timeout_seconds == 5.0  # 5000ms / 1000
        assert client._retry_delay_seconds == 1.0  # 1000ms / 1000

    def test_headers(self):
        """Test building request headers."""
        client = HTTPGatewayClient(self.config)

        headers = client._headers()

        assert "Authorization" in headers
        assert headers["Authorization"] == f"Bearer {self.config.jwt}"
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"

    def test_make_request_success(self):
        """Test successful request making."""
        client = HTTPGatewayClient(self.config)

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = Mock()
            mock_response.read.return_value = b'{"result": "success"}'
            mock_urlopen.return_value.__enter__.return_value = mock_response

            result = client._make_request("https://api.example.com/test")

            assert result == {"result": "success"}
            mock_urlopen.assert_called_once()

    def test_make_request_with_data(self):
        """Test request making with data."""
        client = HTTPGatewayClient(self.config)
        test_data = {"key": "value"}

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = Mock()
            mock_response.read.return_value = b'{"id": 123}'
            mock_urlopen.return_value.__enter__.return_value = mock_response

            result = client._make_request(
                "https://api.example.com/test", method="POST", data=b'{"key": "value"}'
            )

            assert result == {"id": 123}
            mock_urlopen.assert_called_once()

    def test_make_request_http_error_4xx(self):
        """Test request making with 4xx HTTP error."""
        client = HTTPGatewayClient(self.config)

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_error = Mock()
            mock_error.code = 404
            mock_error.read.return_value = b"Not Found"
            mock_urlopen.side_effect = Exception("Gateway HTTP error 404: Not Found")

            with pytest.raises(ValueError, match="Gateway HTTP error 404: Not Found"):
                client._make_request("https://api.example.com/test")

    def test_make_request_http_error_5xx_with_retry(self):
        """Test request making with 5xx HTTP error and retry."""
        client = HTTPGatewayClient(self.config)

        with (
            patch("urllib.request.urlopen") as mock_urlopen,
            patch("time.sleep") as mock_sleep,
        ):
            # First call fails with 500, second succeeds
            mock_error = Mock()
            mock_error.code = 500
            mock_urlopen.side_effect = [
                Exception("Gateway server error (HTTP 500)"),
                Mock(
                    __enter__=Mock(
                        return_value=Mock(
                            read=Mock(return_value=b'{"result": "success"}')
                        )
                    )
                ),
            ]

            result = client._make_request("https://api.example.com/test")

            assert result == {"result": "success"}
            assert mock_urlopen.call_count == 2
            assert mock_sleep.call_count == 1

    def test_make_request_max_retries_exceeded(self):
        """Test request making when max retries exceeded."""
        client = HTTPGatewayClient(self.config)

        with (
            patch("urllib.request.urlopen") as mock_urlopen,
            patch("time.sleep") as mock_sleep,
        ):
            # All calls fail with 500
            mock_urlopen.side_effect = Exception("Gateway server error (HTTP 500)")

            with pytest.raises(ConnectionError, match="Failed after 3 attempts"):
                client._make_request("https://api.example.com/test")

            assert mock_urlopen.call_count == 3  # max_retries + 1
            assert mock_sleep.call_count == 2

    def test_make_request_network_error_with_retry(self):
        """Test request making with network error and retry."""
        client = HTTPGatewayClient(self.config)

        with (
            patch("urllib.request.urlopen") as mock_urlopen,
            patch("time.sleep") as mock_sleep,
        ):
            mock_urlopen.side_effect = [
                Exception("Network error: Connection refused"),
                Mock(
                    __enter__=Mock(
                        return_value=Mock(
                            read=Mock(return_value=b'{"result": "success"}')
                        )
                    )
                ),
            ]

            result = client._make_request("https://api.example.com/test")

            assert result == {"result": "success"}
            assert mock_urlopen.call_count == 2
            assert mock_sleep.call_count == 1

    def test_make_request_timeout_with_retry(self):
        """Test request making with timeout and retry."""
        client = HTTPGatewayClient(self.config)

        with (
            patch("urllib.request.urlopen") as mock_urlopen,
            patch("time.sleep") as mock_sleep,
        ):
            mock_urlopen.side_effect = [
                TimeoutError("Request timeout after 5.0s"),
                Mock(
                    __enter__=Mock(
                        return_value=Mock(
                            read=Mock(return_value=b'{"result": "success"}')
                        )
                    )
                ),
            ]

            result = client._make_request("https://api.example.com/test")

            assert result == {"result": "success"}
            assert mock_urlopen.call_count == 2
            assert mock_sleep.call_count == 1

    def test_make_request_json_decode_error(self):
        """Test request making with JSON decode error."""
        client = HTTPGatewayClient(self.config)

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = Mock()
            mock_response.read.return_value = b"invalid json"
            mock_urlopen.return_value.__enter__.return_value = mock_response

            with pytest.raises(ValueError, match="Invalid JSON response"):
                client._make_request("https://api.example.com/test")

    def test_get_tools_success_list_response(self):
        """Test getting tools successfully with list response."""
        client = HTTPGatewayClient(self.config)

        with patch.object(client, "_make_request") as mock_request:
            mock_tools = [
                {"name": "tool1", "description": "Test tool 1"},
                {"name": "tool2", "description": "Test tool 2"},
            ]
            mock_request.return_value = mock_tools

            tools = client.get_tools()

            assert tools == mock_tools
            mock_request.assert_called_once()

    def test_get_tools_success_dict_response(self):
        """Test getting tools successfully with dict response."""
        client = HTTPGatewayClient(self.config)

        with patch.object(client, "_make_request") as mock_request:
            mock_response = {"tools": [{"name": "tool1", "description": "Test tool 1"}]}
            mock_request.return_value = mock_response

            tools = client.get_tools()

            assert tools == [{"name": "tool1", "description": "Test tool 1"}]

    def test_get_tools_json_decode_error(self):
        """Test getting tools with JSON decode error."""
        client = HTTPGatewayClient(self.config)

        with patch.object(client, "_make_request") as mock_request:
            mock_request.side_effect = ValueError("Invalid JSON response")

            tools = client.get_tools()

            assert tools == []  # Should handle gracefully

    def test_get_tools_connection_error(self):
        """Test getting tools with connection error."""
        client = HTTPGatewayClient(self.config)

        with patch.object(client, "_make_request") as mock_request:
            mock_request.side_effect = ConnectionError("Failed after 3 attempts")

            tools = client.get_tools()

            assert tools == []  # Should handle gracefully

    def test_get_tools_value_error(self):
        """Test getting tools with ValueError."""
        client = HTTPGatewayClient(self.config)

        with patch.object(client, "_make_request") as mock_request:
            mock_request.side_effect = ValueError("Gateway HTTP error 404: Not Found")

            with pytest.raises(
                ValueError,
                match="Failed to fetch tools: Gateway HTTP error 404: Not Found",
            ):
                client.get_tools()

    def test_call_tool_success(self):
        """Test calling tool successfully."""
        client = HTTPGatewayClient(self.config)
        tool_name = "test_tool"
        arguments = {"param1": "value1"}

        with patch.object(client, "_make_request") as mock_request:
            mock_response = {
                "result": {"content": [{"text": "Tool executed successfully"}]}
            }
            mock_request.return_value = mock_response

            result = client.call_tool(tool_name, arguments)

            assert result == "Tool executed successfully"
            mock_request.assert_called_once()

    def test_call_tool_success_no_content(self):
        """Test calling tool successfully with no content."""
        client = HTTPGatewayClient(self.config)

        with patch.object(client, "_make_request") as mock_request:
            mock_response = {"result": {}}
            mock_request.return_value = mock_response

            result = client.call_tool("test_tool", {})

            assert result == "{}"  # JSON string of empty dict

    def test_call_tool_with_error(self):
        """Test calling tool with error response."""
        client = HTTPGatewayClient(self.config)

        with patch.object(client, "_make_request") as mock_request:
            mock_response = {"error": "Tool execution failed"}
            mock_request.return_value = mock_response

            result = client.call_tool("test_tool", {})

            assert result == "Gateway error: Tool execution failed"

    def test_call_tool_request_error(self):
        """Test calling tool with request error."""
        client = HTTPGatewayClient(self.config)

        with patch.object(client, "_make_request") as mock_request:
            mock_request.side_effect = ValueError("Request failed")

            result = client.call_tool("test_tool", {})

            assert result == "Failed to call tool: Request failed"

    def test_call_tool_connection_error(self):
        """Test calling tool with connection error."""
        client = HTTPGatewayClient(self.config)

        with patch.object(client, "_make_request") as mock_request:
            mock_request.side_effect = ConnectionError("Connection failed")

            result = client.call_tool("test_tool", {})

            assert result == "Failed to call tool: Connection failed"

    def test_backward_compatibility_get_tools(self):
        """Test backward compatibility get_tools function."""
        with (
            patch(
                "tool_router.gateway.client.GatewayConfig.load_from_environment"
            ) as mock_load,
            patch("tool_router.gateway.client.HTTPGatewayClient") as mock_client_class,
        ):
            mock_config = GatewayConfig(url="https://test.com", jwt="token")
            mock_load.return_value = mock_config

            mock_client = Mock()
            mock_client.get_tools.return_value = [{"name": "tool1"}]
            mock_client_class.return_value = mock_client

            from tool_router.gateway.client import get_tools

            tools = get_tools()

            assert tools == [{"name": "tool1"}]
            mock_load.assert_called_once()
            mock_client_class.assert_called_once_with(mock_config)
            mock_client.get_tools.assert_called_once()

    def test_backward_compatibility_call_tool(self):
        """Test backward compatibility call_tool function."""
        with (
            patch(
                "tool_router.gateway.client.GatewayConfig.load_from_environment"
            ) as mock_load,
            patch("tool_router.gateway.client.HTTPGatewayClient") as mock_client_class,
        ):
            mock_config = GatewayConfig(url="https://test.com", jwt="token")
            mock_load.return_value = mock_config

            mock_client = Mock()
            mock_client.call_tool.return_value = "Tool result"
            mock_client_class.return_value = mock_client

            from tool_router.gateway.client import call_tool

            result = call_tool("test_tool", {"param": "value"})

            assert result == "Tool result"
            mock_load.assert_called_once()
            mock_client_class.assert_called_once_with(mock_config)
            mock_client.call_tool.assert_called_once_with(
                "test_tool", {"param": "value"}
            )


class TestArgsBuilder:
    """Test ArgsBuilder functions."""

    def test_build_arguments_with_common_parameter(self):
        """Test building arguments with common parameter name."""
        tool = {
            "inputSchema": {
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer"},
                },
                "required": ["query"],
            }
        }
        task = "search for something"

        result = build_arguments(tool, task)

        assert result == {"query": task}

    def test_build_arguments_with_first_required_parameter(self):
        """Test building arguments with first required parameter."""
        tool = {
            "inputSchema": {
                "properties": {
                    "custom_param": {"type": "string"},
                    "limit": {"type": "integer"},
                },
                "required": ["custom_param"],
            }
        }
        task = "perform action"

        result = build_arguments(tool, task)

        assert result == {"custom_param": task}

    def test_build_arguments_with_first_required_non_string(self):
        """Test building arguments when first required param is not string."""
        tool = {
            "inputSchema": {
                "properties": {
                    "count": {"type": "integer"},
                    "name": {"type": "string"},
                },
                "required": ["count", "name"],
            }
        }
        task = "test task"

        result = build_arguments(tool, task)

        # Should use name (second required) since count is not string
        assert result == {"name": task}

    def test_build_arguments_fallback_to_task(self):
        """Test building arguments fallback to 'task' parameter."""
        tool = {
            "inputSchema": {
                "properties": {"limit": {"type": "integer"}},
                "required": [],
            }
        }
        task = "fallback task"

        result = build_arguments(tool, task)

        assert result == {"task": task}

    def test_build_arguments_no_schema(self):
        """Test building arguments with no schema."""
        tool = {}
        task = "no schema task"

        result = build_arguments(tool, task)

        assert result == {"task": task}

    def test_build_arguments_empty_schema(self):
        """Test building arguments with empty schema."""
        tool = {"inputSchema": {}}
        task = "empty schema task"

        result = build_arguments(tool, task)

        assert result == {"task": task}

    def test_build_arguments_no_properties(self):
        """Test building arguments with schema but no properties."""
        tool = {"inputSchema": {"required": ["param1"]}}
        task = "no properties task"

        result = build_arguments(tool, task)

        assert result == {"task": task}

    def test_build_arguments_input_schema_alternative(self):
        """Test building arguments with input_schema (alternative field name)."""
        tool = {
            "input_schema": {
                "properties": {"prompt": {"type": "string"}},
                "required": ["prompt"],
            }
        }
        task = "test prompt"

        result = build_arguments(tool, task)

        assert result == {"prompt": task}

    def test_common_task_parameter_names(self):
        """Test common task parameter names list."""
        expected_names = [
            "query",
            "q",
            "search",
            "task",
            "prompt",
            "question",
            "input",
            "text",
            "message",
            "command",
        ]

        assert expected_names == COMMON_TASK_PARAMETER_NAMES

    def test_build_arguments_priority_order(self):
        """Test that parameter names are tried in priority order."""
        tool = {
            "inputSchema": {
                "properties": {
                    "command": {"type": "string"},
                    "query": {"type": "string"},
                },
                "required": [],
            }
        }
        task = "test command"

        result = build_arguments(tool, task)

        # Should use "command" (first in priority list that exists)
        assert result == {"command": task}

    def test_build_arguments_with_type_inference(self):
        """Test building arguments with type inference."""
        tool = {
            "inputSchema": {
                "properties": {"text_param": {}},  # No type specified
                "required": ["text_param"],
            }
        }
        task = "type inference test"

        result = build_arguments(tool, task)

        # Should work even without explicit type
        assert result == {"text_param": task}


class TestInfrastructureIntegration:
    """Integration tests for infrastructure components."""

    def test_gateway_client_with_config_integration(self):
        """Test GatewayClient integration with Config."""
        config = GatewayConfig(
            url="https://api.example.com",
            jwt="test-token",
            timeout_ms=3000,
            max_retries=2,
            retry_delay_ms=500,
        )
        client = HTTPGatewayClient(config)

        # Test that client uses config correctly
        assert client.config == config
        assert client._timeout_seconds == 3.0  # 3000ms / 1000
        assert client._retry_delay_seconds == 0.5  # 500ms / 1000

    def test_gateway_client_complete_workflow(self):
        """Test GatewayClient complete workflow simulation."""
        config = GatewayConfig(
            url="https://api.example.com",
            jwt="test-token",
            timeout_ms=5000,
            max_retries=3,
        )
        client = HTTPGatewayClient(config)

        # Simulate getting tools and calling a tool
        with patch.object(client, "_make_request") as mock_request:
            # Mock tools response
            mock_request.side_effect = [
                [{"name": "test_tool", "description": "A test tool"}],  # get_tools
                {  # call_tool
                    "result": {"content": [{"text": "Tool executed successfully"}]}
                },
            ]

            # Get tools
            tools = client.get_tools()
            assert len(tools) == 1
            assert tools[0]["name"] == "test_tool"

            # Call tool
            result = client.call_tool("test_tool", {"param": "value"})
            assert result == "Tool executed successfully"

            assert mock_request.call_count == 2

    def test_args_builder_various_schemas(self):
        """Test ArgsBuilder with various schema formats."""
        test_cases = [
            # Case 1: Common parameter name
            {
                "tool": {
                    "inputSchema": {
                        "properties": {"query": {"type": "string"}},
                        "required": ["query"],
                    }
                },
                "task": "search query",
                "expected": {"query": "search query"},
            },
            # Case 2: First required parameter
            {
                "tool": {
                    "inputSchema": {
                        "properties": {"action": {"type": "string"}},
                        "required": ["action"],
                    }
                },
                "task": "perform action",
                "expected": {"action": "perform action"},
            },
            # Case 3: Fallback to task
            {
                "tool": {"inputSchema": {"properties": {}}},
                "task": "fallback task",
                "expected": {"task": "fallback task"},
            },
        ]

        for case in test_cases:
            result = build_arguments(case["tool"], case["task"])
            assert result == case["expected"], f"Failed for case: {case}"


if __name__ == "__main__":
    unittest.main()
