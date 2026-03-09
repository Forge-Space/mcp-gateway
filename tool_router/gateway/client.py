from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol

from tool_router.core.config import GatewayConfig
from tool_router.gateway.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitOpenError,
)


@dataclass
class SecurityMetadata:
    """Security context propagated to spoke MCP servers."""

    user_id: str | None = None
    role: str | None = None
    permissions: list[str] | None = None
    request_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            k: v
            for k, v in {
                "user_id": self.user_id,
                "role": self.role,
                "permissions": self.permissions,
                "request_id": self.request_id,
            }.items()
            if v is not None
        }


class GatewayClient(Protocol):
    """Protocol for gateway client implementations."""

    def get_tools(self) -> list[dict[str, Any]]:
        """Fetch available tools from the gateway."""
        ...

    def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """Execute a tool via the gateway."""
        ...


class HTTPGatewayClient:
    """HTTP-based gateway client with retry logic and configurable timeouts."""

    def __init__(
        self,
        config: GatewayConfig,
        circuit_breaker: CircuitBreaker | None = None,
    ) -> None:
        self.config = config
        self._timeout_seconds = config.timeout_ms / 1000
        self._retry_delay_seconds = config.retry_delay_ms / 1000
        self._breaker = circuit_breaker or CircuitBreaker(CircuitBreakerConfig())

    def _headers(self) -> dict[str, str]:
        """Build request headers with authentication."""
        return {
            "Authorization": f"Bearer {self.config.jwt}",
            "Content-Type": "application/json",
        }

    def _make_request(self, url: str, method: str = "GET", data: bytes | None = None) -> dict[str, Any]:
        endpoint = self.config.url
        return self._breaker.call(endpoint, self._make_request_inner, url, method, data)

    def _should_retry(self, attempt: int) -> bool:
        return attempt < self.config.max_retries - 1

    def _sleep_before_retry(self, attempt: int) -> None:
        time.sleep(self._retry_delay_seconds * (2**attempt))

    def _handle_http_error(self, error: urllib.error.HTTPError, attempt: int) -> str:
        if error.code >= 500:
            if self._should_retry(attempt):
                self._sleep_before_retry(attempt)
            return f"Gateway server error (HTTP {error.code})"

        try:
            error_body = error.read().decode("utf-8")
        except (OSError, UnicodeDecodeError):
            error_body = "<unable to read response body>"
        msg = f"Gateway HTTP error {error.code}: {error_body}"
        raise ValueError(msg)

    def _handle_network_error(self, error: urllib.error.URLError, attempt: int) -> str:
        if self._should_retry(attempt):
            self._sleep_before_retry(attempt)
        return f"Network error: {error.reason}"

    def _handle_timeout_error(self, attempt: int) -> str:
        if self._should_retry(attempt):
            self._sleep_before_retry(attempt)
        return f"Request timeout after {self._timeout_seconds}s"

    def _make_request_inner(self, url: str, method: str = "GET", data: bytes | None = None) -> dict[str, Any]:
        req = urllib.request.Request(url, headers=self._headers(), method=method)
        if data:
            req.data = data

        last_error: str | None = None
        for attempt in range(self.config.max_retries):
            try:
                with urllib.request.urlopen(req, timeout=self._timeout_seconds) as resp:
                    return json.loads(resp.read().decode())
            except urllib.error.HTTPError as error:
                last_error = self._handle_http_error(error, attempt)
            except urllib.error.URLError as error:
                last_error = self._handle_network_error(error, attempt)
            except TimeoutError:
                last_error = self._handle_timeout_error(attempt)
            except json.JSONDecodeError:
                msg = "Invalid JSON response"
                raise ValueError(msg)

            if self._should_retry(attempt):
                continue

        msg = f"Failed after {self.config.max_retries} attempts. Last error: {last_error}"
        raise ConnectionError(msg)

    def get_tools(self) -> list[dict[str, Any]]:
        """Fetch available tools from the gateway.

        Returns:
            List of tool definitions, or empty list if gateway is unavailable

        Note:
            Returns empty list gracefully on errors to allow system to continue functioning
        """
        url = f"{self.config.url}/tools?limit=0&include_pagination=false"

        try:
            response_data = self._make_request(url, method="GET")
        except ValueError as error:
            # Business logic: handle JSON parsing errors gracefully
            # This allows the system to continue functioning even with malformed responses
            if "Invalid JSON response" in str(error):
                return []
            # Re-raise other ValueErrors (like HTTP errors) with original message format
            msg = f"Failed to fetch tools: {error}"
            raise ValueError(msg) from error
        except (ConnectionError, CircuitOpenError) as error:
            # Business logic: Convert connection errors from HTTP retries to ValueError
            # This maintains backward compatibility with existing error handling
            if "Failed after" in str(error) and "attempts" in str(error):
                msg = f"Failed to fetch tools: {error}"
                raise ValueError(msg) from error
            # Handle other connection errors gracefully
            return []

        if isinstance(response_data, list):
            return response_data
        if isinstance(response_data, dict) and "tools" in response_data:
            return response_data["tools"]
        return []

    def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
        security: SecurityMetadata | None = None,
    ) -> str:
        """Execute a tool via the gateway.

        Args:
            name: Tool name to execute
            arguments: Tool arguments
            security: Optional security context for spoke propagation

        Returns:
            Tool execution result as string
        """
        url = f"{self.config.url}/rpc"
        params: dict[str, Any] = {"name": name, "arguments": arguments}
        if security:
            params["_metadata"] = {"security": security.to_dict()}
        body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": params,
        }

        try:
            json_rpc_response = self._make_request(url, method="POST", data=json.dumps(body).encode())
        except (ValueError, ConnectionError, CircuitOpenError) as error:
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
