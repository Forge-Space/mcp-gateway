"""Integration tests for virtual server lifecycle."""

from __future__ import annotations

from tool_router.api.lifecycle import (
    disable_server,
    enable_server,
    get_server_status,
    list_virtual_servers,
)


class TestVirtualServerLifecycle:
    """Integration tests for virtual server lifecycle management."""

    def test_server_enable_disable_cycle(self, mocker, tmp_path):
        """Test complete enable/disable cycle."""
        config_file = tmp_path / "virtual-servers.txt"
        config_file.write_text("test-server|gateway1,gateway2|false\n")

        mocker.patch("tool_router.api.lifecycle.get_virtual_servers_file", return_value=config_file)

        # Initial state: disabled
        status = get_server_status("test-server")
        assert status["found"] is True
        assert status["enabled"] is False

        # Enable server
        result = enable_server("test-server")
        assert result["success"] is True

        # Verify enabled
        status = get_server_status("test-server")
        assert status["enabled"] is True

        # Disable server
        result = disable_server("test-server")
        assert result["success"] is True

        # Verify disabled
        status = get_server_status("test-server")
        assert status["enabled"] is False

    def test_list_servers_summary(self, mocker, tmp_path):
        """Test server list includes correct summary."""
        config_file = tmp_path / "virtual-servers.txt"
        config_file.write_text(
            "server1|gateway1|true\n"
            "server2|gateway2|false\n"
            "server3|gateway3|true\n"
        )

        mocker.patch("tool_router.api.lifecycle.get_virtual_servers_file", return_value=config_file)

        result = list_virtual_servers()

        assert result["summary"]["total"] == 3
        assert result["summary"]["enabled"] == 2
        assert result["summary"]["disabled"] == 1
