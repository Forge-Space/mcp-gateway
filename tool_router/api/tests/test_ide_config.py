"""Tests for IDE config generator API."""

from __future__ import annotations

from tool_router.api.ide_config import (
    generate_ide_config,
    get_ide_config_paths,
)


class TestIDEConfigAPI:
    """Test IDE config generator API."""

    def test_generate_windsurf_config_basic(self) -> None:
        """Test basic Windsurf config generation."""
        config = generate_ide_config(
            ide="windsurf",
            server_name="test-server",
            server_uuid="abc-123",
            gateway_url="http://localhost:4444",
        )

        assert "mcpServers" in config
        assert "test-server" in config["mcpServers"]
        server_config = config["mcpServers"]["test-server"]
        assert server_config["command"] == "npx"
        assert "-y" in server_config["args"]
        assert "@mcp-gateway/client" in server_config["args"]
        assert "--url=http://localhost:4444/servers/abc-123/mcp" in server_config["args"]
        assert "env" in server_config

    def test_generate_windsurf_config_with_token(self) -> None:
        """Test Windsurf config with JWT token."""
        config = generate_ide_config(
            ide="windsurf",
            server_name="secure-server",
            server_uuid="xyz-789",
            gateway_url="https://gateway.example.com",
            jwt_token="test-jwt-token",
        )

        server_config = config["mcpServers"]["secure-server"]
        assert "--token=test-jwt-token" in server_config["args"]
        assert "--url=https://gateway.example.com/servers/xyz-789/mcp" in server_config["args"]

    def test_generate_cursor_config_basic(self) -> None:
        """Test basic Cursor config generation."""
        config = generate_ide_config(
            ide="cursor",
            server_name="cursor-test",
            server_uuid="def-456",
            gateway_url="http://localhost:4444",
        )

        assert "mcpServers" in config
        assert "cursor-test" in config["mcpServers"]
        server_config = config["mcpServers"]["cursor-test"]
        assert server_config["command"] == "npx"
        assert "@mcp-gateway/client" in server_config["args"]

    def test_generate_cursor_config_with_token(self) -> None:
        """Test Cursor config with JWT token."""
        config = generate_ide_config(
            ide="cursor",
            server_name="cursor-secure",
            server_uuid="ghi-789",
            gateway_url="https://remote.gateway.com",
            jwt_token="cursor-jwt",
        )

        server_config = config["mcpServers"]["cursor-secure"]
        assert "--token=cursor-jwt" in server_config["args"]

    def test_get_ide_config_paths(self) -> None:
        """Test IDE config path retrieval."""
        paths = get_ide_config_paths()

        assert "windsurf" in paths
        assert "cursor" in paths
        assert paths["windsurf"] == ".windsurf/mcp.json"
        assert paths["cursor"] == "~/.cursor/mcp.json"

    def test_config_structure_consistency(self) -> None:
        """Test that both IDEs generate consistent structure."""
        windsurf_config = generate_ide_config(
            ide="windsurf",
            server_name="test",
            server_uuid="123",
        )
        cursor_config = generate_ide_config(
            ide="cursor",
            server_name="test",
            server_uuid="123",
        )

        # Both should have same structure
        assert windsurf_config.keys() == cursor_config.keys()
        assert windsurf_config["mcpServers"]["test"]["command"] == cursor_config["mcpServers"]["test"]["command"]
