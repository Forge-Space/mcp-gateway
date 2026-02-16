"""Unit tests for REST API handlers."""

from __future__ import annotations

import pytest

from tool_router.api.rest import (
    handle_get_server,
    handle_list_servers,
    handle_update_server,
)


class TestHandleListServers:
    """Tests for handle_list_servers."""

    def test_list_servers_success(self, mocker):
        """Test successful server listing."""
        mock_result = {"servers": [{"name": "server1", "enabled": True}]}
        mocker.patch("tool_router.api.rest.list_virtual_servers", return_value=mock_result)

        result, status = handle_list_servers()

        assert status == 200
        assert result == mock_result

    def test_list_servers_error(self, mocker):
        """Test error handling."""
        mocker.patch("tool_router.api.rest.list_virtual_servers", side_effect=Exception("DB error"))

        result, status = handle_list_servers()

        assert status == 500
        assert "error" in result


class TestHandleGetServer:
    """Tests for handle_get_server."""

    def test_get_server_found(self, mocker):
        """Test getting existing server."""
        mock_result = {"found": True, "name": "server1", "enabled": True}
        mocker.patch("tool_router.api.rest.get_server_status", return_value=mock_result)

        result, status = handle_get_server("server1")

        assert status == 200
        assert result["found"] is True

    def test_get_server_not_found(self, mocker):
        """Test getting non-existent server."""
        mock_result = {"found": False}
        mocker.patch("tool_router.api.rest.get_server_status", return_value=mock_result)

        result, status = handle_get_server("nonexistent")

        assert status == 404
        assert result["found"] is False

    def test_get_server_error(self, mocker):
        """Test error handling."""
        mocker.patch("tool_router.api.rest.get_server_status", side_effect=Exception("Error"))

        result, status = handle_get_server("server1")

        assert status == 500
        assert "error" in result


class TestHandleUpdateServer:
    """Tests for handle_update_server."""

    def test_update_server_enable(self, mocker):
        """Test enabling a server."""
        mock_result = {"success": True, "message": "Enabled"}
        mocker.patch("tool_router.api.rest.enable_server", return_value=mock_result)

        result, status = handle_update_server("server1", {"enabled": True})

        assert status == 200
        assert result["success"] is True

    def test_update_server_disable(self, mocker):
        """Test disabling a server."""
        mock_result = {"success": True, "message": "Disabled"}
        mocker.patch("tool_router.api.rest.disable_server", return_value=mock_result)

        result, status = handle_update_server("server1", {"enabled": False})

        assert status == 200
        assert result["success"] is True

    def test_update_server_missing_enabled(self, mocker):
        """Test missing enabled field."""
        result, status = handle_update_server("server1", {})

        assert status == 400
        assert "enabled" in result["error"]

    def test_update_server_invalid_enabled_type(self, mocker):
        """Test invalid enabled type."""
        result, status = handle_update_server("server1", {"enabled": "yes"})

        assert status == 400
        assert "boolean" in result["error"]

    def test_update_server_not_found(self, mocker):
        """Test updating non-existent server."""
        mock_result = {"success": False, "error": "Not found"}
        mocker.patch("tool_router.api.rest.enable_server", return_value=mock_result)

        result, status = handle_update_server("nonexistent", {"enabled": True})

        assert status == 404
        assert result["success"] is False

    def test_update_server_error(self, mocker):
        """Test error handling."""
        mocker.patch("tool_router.api.rest.enable_server", side_effect=Exception("Error"))

        result, status = handle_update_server("server1", {"enabled": True})

        assert status == 500
        assert "error" in result
