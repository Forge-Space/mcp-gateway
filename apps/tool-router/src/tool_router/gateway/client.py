from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any, Protocol

from tool_router.core.config import GatewayConfig


class GatewayClient(Protocol):
    """Protocol for gateway client implementations."""

    def get_tools(self) -> list[dict[str, Any]]:
        """Fetch available tools from the gateway."""
        raise NotImplementedError

    def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """Execute a tool via the gateway."""
        raise NotImplementedError


class HTTPGatewayClient:
    """HTTP-based gateway client with retry logic and configurable timeouts."""

    def __init__(self, config: GatewayConfig) -> None:
        """Initialize client with configuration.

        Args:
            config: Gateway connection configuration
        """
        self.config = config
        self._timeout_seconds = config.timeout_ms / 1000
        self._retry_delay_seconds = config.retry_delay_ms / 1000

    def _headers(self) -> dict[str, str]:
        """Build request headers with authentication."""
        return {
            "Authorization": f"Bearer {self.config.jwt}",
            "Content-Type": "application/json",
        }

    def _make_request(self, url: str, method: str = "GET", data: bytes | None = None) -> dict[str, Any]:
        """Make HTTP request with retry logic for transient failures."""
        req = urllib.request.Request(url, headers=self._headers(), method=method)
        if data:
            req.data = data

        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                with urllib.request.urlopen(req, timeout=self._timeout_seconds) as resp:
                    return json.loads(resp.read().decode())
            except urllib.error.HTTPError as http_error:
                if http_error.code >= 500:
                    last_error = f"Gateway server error (HTTP {http_error.code})"
                    if attempt < self.config.max_retries - 1:
                        time.sleep(self._retry_delay_seconds * (2**attempt))
                        continue
                else:
                    # Safely read error response body
                    try:
                        error_body = http_error.read().decode("utf-8")
                    except (OSError, UnicodeDecodeError):
                        error_body = "<unable to read response body>"
                    msg = f"Gateway HTTP error {http_error.code}: {error_body}"
                    raise ValueError(msg)
            except urllib.error.URLError as network_error:
                last_error = f"Network error: {network_error.reason}"
                if attempt < self.config.max_retries - 1:
                    time.sleep(self._retry_delay_seconds * (2**attempt))
                    continue
            except TimeoutError:
                last_error = f"Request timeout after {self._timeout_seconds}s"
                if attempt < self.config.max_retries - 1:
                    time.sleep(self._retry_delay_seconds * (2**attempt))
                    continue
            except json.JSONDecodeError as json_error:
                msg = f"Invalid JSON response from gateway: {json_error}"
                raise ValueError(msg)

        msg = f"Failed after {self.config.max_retries} attempts. Last error: {last_error}"
        raise ConnectionError(msg)

    def get_tools(self) -> list[dict[str, Any]]:
        """Fetch available tools from the gateway.

        Returns:
            List of tool definitions

        Raises:
            ValueError: If the request fails or response is invalid
            ConnectionError: If connection fails after retries
        """
        url = f"{self.config.url}/tools?limit=0&include_pagination=false"

        try:
            response_data = self._make_request(url, method="GET")
        except (ValueError, ConnectionError) as error:
            msg = f"Failed to fetch tools: {error}"
            raise ValueError(msg) from error

        if isinstance(response_data, list):
            return response_data
        if isinstance(response_data, dict) and "tools" in response_data:
            return response_data["tools"]
        return []

    def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """Execute a tool via the gateway.

        Args:
            name: Tool name to execute
            arguments: Tool arguments

        Returns:
            Tool execution result as string
        """
        url = f"{self.config.url}/rpc"
        body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        }

        try:
            json_rpc_response = self._make_request(url, method="POST", data=json.dumps(body).encode())
        except (ValueError, ConnectionError) as error:
            return f"Failed to call tool: {error}"

        if "error" in json_rpc_response:
            return f"Gateway error: {json_rpc_response['error']}"
        content = json_rpc_response.get("result", {}).get("content", [])
        texts = [
            content_item.get("text", "")
            for content_item in content
            if isinstance(content_item, dict) and "text" in content_item
        ]
        return "\n".join(texts) if texts else json.dumps(json_rpc_response.get("result", {}))


# Backward compatibility: module-level functions that use environment config
def get_tools() -> list[dict[str, Any]]:
    """Fetch tools using environment configuration (backward compatibility)."""
    from tool_router.core.config import GatewayConfig

    config = GatewayConfig.load_from_environment()
    client = HTTPGatewayClient(config)
    return client.get_tools()


def call_tool(name: str, arguments: dict[str, Any]) -> str:
    """Call tool using environment configuration (backward compatibility)."""
    from tool_router.core.config import GatewayConfig

    config = GatewayConfig.load_from_environment()
    client = HTTPGatewayClient(config)
    return client.call_tool(name, arguments)
