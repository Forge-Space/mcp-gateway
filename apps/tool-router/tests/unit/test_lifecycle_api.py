"""Unit tests for lifecycle API."""

from __future__ import annotations

from tool_router.api.lifecycle import (
    disable_server,
    enable_server,
    get_server_status,
    list_virtual_servers,
    parse_server_line,
)


class TestParseServerLine:
    """Tests for parse_server_line."""

    def test_parse_valid_line(self):
        """Test parsing valid server line."""
        result = parse_server_line("server1|gateway1,gateway2|true")

        assert result is not None
        assert result["name"] == "server1"
        assert result["gateways"] == ["gateway1", "gateway2"]
        assert result["enabled"] is True

    def test_parse_disabled_server(self):
        """Test parsing disabled server."""
        result = parse_server_line("server2|gateway3|false")

        assert result is not None
        assert result["enabled"] is False

    def test_parse_empty_line(self):
        """Test parsing empty line."""
        result = parse_server_line("")
        assert result is None

    def test_parse_comment_line(self):
        """Test parsing comment line."""
        result = parse_server_line("# This is a comment")
        assert result is None

    def test_parse_invalid_format(self):
        """Test parsing invalid format."""
        result = parse_server_line("invalid")
        assert result is None


class TestListVirtualServers:
    """Tests for list_virtual_servers."""

    def test_list_servers_success(self, mocker, tmp_path):
        """Test listing servers."""
        config_file = tmp_path / "virtual-servers.txt"
        config_file.write_text("server1|gateway1|true\nserver2|gateway2|false\n")

        mocker.patch("tool_router.api.lifecycle.get_virtual_servers_file", return_value=config_file)

        result = list_virtual_servers()

        assert "servers" in result
        assert len(result["servers"]) == 2
        assert result["servers"][0]["name"] == "server1"
        assert result["servers"][0]["enabled"] is True
        assert result["summary"]["total"] == 2
        assert result["summary"]["enabled"] == 1
        assert result["summary"]["disabled"] == 1

    def test_list_servers_file_not_found(self, mocker, tmp_path):
        """Test when config file doesn't exist."""
        config_file = tmp_path / "nonexistent.txt"
        mocker.patch("tool_router.api.lifecycle.get_virtual_servers_file", return_value=config_file)

        result = list_virtual_servers()

        assert result["servers"] == []
        assert "error" in result
        assert result["summary"]["total"] == 0


class TestGetServerStatus:
    """Tests for get_server_status."""

    def test_get_server_found(self, mocker, tmp_path):
        """Test getting existing server."""
        config_file = tmp_path / "virtual-servers.txt"
        config_file.write_text("server1|gateway1|true\n")

        mocker.patch("tool_router.api.lifecycle.get_virtual_servers_file", return_value=config_file)

        result = get_server_status("server1")

        assert result["found"] is True
        assert result["name"] == "server1"
        assert result["enabled"] is True

    def test_get_server_not_found(self, mocker, tmp_path):
        """Test getting non-existent server."""
        config_file = tmp_path / "virtual-servers.txt"
        config_file.write_text("server1|gateway1|true\n")

        mocker.patch("tool_router.api.lifecycle.get_virtual_servers_file", return_value=config_file)

        result = get_server_status("nonexistent")

        assert result["found"] is False


class TestEnableServer:
    """Tests for enable_server."""

    def test_enable_server_success(self, mocker, tmp_path):
        """Test enabling a server."""
        config_file = tmp_path / "virtual-servers.txt"
        config_file.write_text("server1|gateway1|false\n")

        mocker.patch("tool_router.api.lifecycle.get_virtual_servers_file", return_value=config_file)

        result = enable_server("server1")

        assert result["success"] is True
        assert "enabled" in result["message"].lower()

    def test_enable_server_not_found(self, mocker, tmp_path):
        """Test enabling non-existent server."""
        config_file = tmp_path / "virtual-servers.txt"
        config_file.write_text("server1|gateway1|true\n")

        mocker.patch("tool_router.api.lifecycle.get_virtual_servers_file", return_value=config_file)

        result = enable_server("nonexistent")

        assert result["success"] is False
        assert "not found" in result["error"].lower()


class TestDisableServer:
    """Tests for disable_server."""

    def test_disable_server_success(self, mocker, tmp_path):
        """Test disabling a server."""
        config_file = tmp_path / "virtual-servers.txt"
        config_file.write_text("server1|gateway1|true\n")

        mocker.patch("tool_router.api.lifecycle.get_virtual_servers_file", return_value=config_file)

        result = disable_server("server1")

        assert result["success"] is True
        assert "disabled" in result["message"].lower()

    def test_disable_server_not_found(self, mocker, tmp_path):
        """Test disabling non-existent server."""
        config_file = tmp_path / "virtual-servers.txt"
        config_file.write_text("server1|gateway1|true\n")

        mocker.patch("tool_router.api.lifecycle.get_virtual_servers_file", return_value=config_file)

        result = disable_server("nonexistent")

        assert result["success"] is False
        assert "not found" in result["error"].lower()
