"""Unit tests for IDE configuration generator."""

from __future__ import annotations

import pytest

from tool_router.api.ide_config import generate_ide_config, get_ide_config_paths


class TestGenerateIDEConfig:
    """Tests for generate_ide_config function."""

    def test_generate_ide_config_windsurf_success(self) -> None:
        """Test successful Windsurf configuration generation."""
        result = generate_ide_config(
            ide="windsurf",
            server_name="test-server",
            server_uuid="abc-123",
            gateway_url="http://localhost:4444"
        )

        assert "mcpServers" in result
        assert "test-server" in result["mcpServers"]
        assert result["mcpServers"]["test-server"]["command"] == "npx"
        assert "-y" in result["mcpServers"]["test-server"]["args"]
        assert "@mcp-gateway/client" in result["mcpServers"]["test-server"]["args"]
        assert "--url=http://localhost:4444/servers/abc-123/mcp" in result["mcpServers"]["test-server"]["args"]

    def test_generate_ide_config_cursor_success(self) -> None:
        """Test successful Cursor configuration generation."""
        result = generate_ide_config(
            ide="cursor",
            server_name="cursor-server",
            server_uuid="def-456",
            gateway_url="https://gateway.example.com"
        )

        assert "mcpServers" in result
        assert "cursor-server" in result["mcpServers"]
        assert result["mcpServers"]["cursor-server"]["command"] == "npx"
        assert "--url=https://gateway.example.com/servers/def-456/mcp" in result["mcpServers"]["cursor-server"]["args"]

    def test_generate_ide_config_with_jwt_token(self) -> None:
        """Test configuration generation with JWT token."""
        result = generate_ide_config(
            ide="windsurf",
            server_name="secure-server",
            server_uuid="ghi-789",
            gateway_url="http://localhost:4444",
            jwt_token="jwt-token-123"
        )

        assert "--token=jwt-token-123" in result["mcpServers"]["secure-server"]["args"]

    def test_generate_ide_config_invalid_ide(self) -> None:
        """Test error handling for invalid IDE parameter."""
        with pytest.raises(ValueError, match="ide must be 'windsurf' or 'cursor'"):
            generate_ide_config(
                ide="invalid-ide",
                server_name="test-server",
                server_uuid="abc-123"
            )

    def test_generate_ide_config_empty_server_name(self) -> None:
        """Test error handling for empty server name."""
        with pytest.raises(ValueError, match="server_name must be a non-empty string"):
            generate_ide_config(
                ide="windsurf",
                server_name="",
                server_uuid="abc-123"
            )

    def test_generate_ide_config_empty_server_uuid(self) -> None:
        """Test error handling for empty server UUID."""
        with pytest.raises(ValueError, match="server_uuid must be a non-empty string"):
            generate_ide_config(
                ide="windsurf",
                server_name="test-server",
                server_uuid=""
            )

    def test_generate_ide_config_empty_gateway_url(self) -> None:
        """Test error handling for empty gateway URL."""
        with pytest.raises(ValueError, match="gateway_url must be a non-empty string"):
            generate_ide_config(
                ide="windsurf",
                server_name="test-server",
                server_uuid="abc-123",
                gateway_url=""
            )

    def test_generate_ide_config_empty_jwt_token(self) -> None:
        """Test error handling for empty JWT token (should be None or non-empty)."""
        with pytest.raises(ValueError, match="jwt_token must be None or a non-empty string"):
            generate_ide_config(
                ide="windsurf",
                server_name="test-server",
                server_uuid="abc-123",
                jwt_token=""
            )

    def test_generate_ide_config_none_jwt_token(self) -> None:
        """Test that None JWT token is accepted."""
        result = generate_ide_config(
            ide="windsurf",
            server_name="test-server",
            server_uuid="abc-123",
            jwt_token=None
        )

        assert "mcpServers" in result
        assert "--token" not in str(result)  # No token argument should be present


class TestGetIDEConfigPaths:
    """Tests for get_ide_config_paths function."""

    def test_get_ide_config_paths(self) -> None:
        """Test getting IDE configuration file paths."""
        result = get_ide_config_paths()

        assert isinstance(result, dict)
        assert "windsurf" in result
        assert "cursor" in result
        assert result["windsurf"] == ".windsurf/mcp.json"
        assert result["cursor"] == "~/.cursor/mcp.json"

    def test_get_ide_config_paths_structure(self) -> None:
        """Test that paths have expected structure."""
        result = get_ide_config_paths()

        # Check that paths are strings
        for ide, path in result.items():
            assert isinstance(ide, str)
            assert isinstance(path, str)
            assert len(path) > 0
            assert "/" in path  # Should contain directory separator
