# Gateway Client Patterns

## Purpose
Guides editing of the HTTP gateway client that connects to upstream MCP servers.

## Key Files
- `tool_router/gateway/client.py` — `HTTPGatewayClient` class + `GatewayClient` Protocol
- `tool_router/core/config.py` — `GatewayConfig` dataclass

## Architecture
`GatewayClient` Protocol defines the interface:
- `get_tools() → list[dict]` — fetch available tools
- `call_tool(name, arguments) → str` — execute a tool

`HTTPGatewayClient` implements HTTP communication:
- JWT Bearer auth via `GatewayConfig.jwt`
- Configurable timeouts via `GatewayConfig.timeout_ms`
- Exponential backoff retry: `retry_delay_ms * (2^attempt)` up to `max_retries`
- GET `/tools?limit=0&include_pagination=false` for tool list
- POST `/rpc` with JSON-RPC 2.0 for tool calls

Error handling:
- HTTP 5xx → retry with backoff
- HTTP 4xx → raise ValueError immediately
- Network/timeout → retry with backoff
- Invalid JSON → raise ValueError
- All retries exhausted → raise ConnectionError

Module-level backward-compat functions: `get_tools()`, `call_tool()` load config from environment.

## Critical Constraints
- Uses stdlib `urllib.request` only (no requests/httpx dependency)
- JWT auth required for all requests
- Response parsing handles both list and `{"tools": [...]}` formats
