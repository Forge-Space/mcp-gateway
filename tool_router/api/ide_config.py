"""IDE configuration generator API.

Generates MCP configuration snippets for Windsurf and Cursor IDEs.
"""

from __future__ import annotations

from typing import Literal


def generate_ide_config(
    ide: Literal["windsurf", "cursor"],
    server_name: str,
    server_uuid: str,
    gateway_url: str = "http://localhost:4444",
    jwt_token: str | None = None,
) -> dict[str, dict]:
    """Generate IDE-specific MCP configuration.

    Args:
        ide: Target IDE (windsurf or cursor)
        server_name: Name for the MCP server entry
        server_uuid: UUID of the virtual server
        gateway_url: Gateway base URL
        jwt_token: Optional JWT token for authenticated access

    Returns:
        Dictionary with mcpServers configuration for the IDE

    Example:
        >>> config = generate_ide_config("windsurf", "my-server", "abc-123")
        >>> print(config["mcpServers"]["my-server"]["command"])
        'npx'
    """
    mcp_url = f"{gateway_url}/servers/{server_uuid}/mcp"

    if ide == "windsurf":
        return _generate_windsurf_config(server_name, mcp_url, jwt_token)
    return _generate_cursor_config(server_name, mcp_url, jwt_token)


def _generate_windsurf_config(
    server_name: str,
    mcp_url: str,
    jwt_token: str | None,
) -> dict[str, dict]:
    """Generate Windsurf MCP configuration.

    Windsurf uses standard MCP JSON format with npx client.
    """
    args = ["-y", "@mcp-gateway/client", f"--url={mcp_url}"]
    if jwt_token:
        args.append(f"--token={jwt_token}")

    return {
        "mcpServers": {
            server_name: {
                "command": "npx",
                "args": args,
                "env": {},
            }
        }
    }


def _generate_cursor_config(
    server_name: str,
    mcp_url: str,
    jwt_token: str | None,
) -> dict[str, dict]:
    """Generate Cursor MCP configuration.

    Cursor also uses standard MCP JSON format with npx client.
    Same as Windsurf but kept separate for future customization.
    """
    args = ["-y", "@mcp-gateway/client", f"--url={mcp_url}"]
    if jwt_token:
        args.append(f"--token={jwt_token}")

    return {
        "mcpServers": {
            server_name: {
                "command": "npx",
                "args": args,
                "env": {},
            }
        }
    }


def get_ide_config_paths() -> dict[str, str]:
    """Get default config file paths for supported IDEs.

    Returns:
        Dictionary mapping IDE name to config file path
    """
    return {
        "windsurf": ".windsurf/mcp.json",
        "cursor": "~/.cursor/mcp.json",
    }
