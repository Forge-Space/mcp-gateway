"""Tests for scripts/ide-setup.py"""

import os
import importlib.util
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Load module from hyphenated filename (not importable via normal import)
_spec = importlib.util.spec_from_file_location(
    "ide_setup",
    Path(__file__).parent.parent / "ide-setup.py",
)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]
IDEManager = _mod.IDEManager


@pytest.fixture()
def temp_repo_root():
    """Create a temporary repository root with necessary directories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)

        # Create necessary directories
        (repo_root / "scripts").mkdir()
        (repo_root / "data").mkdir()
        (repo_root / "config").mkdir()

        # Create virtual servers config
        servers_config = repo_root / "config" / "virtual-servers.txt"
        servers_config.write_text("""# Virtual servers: Name|enabled|gateways|description
cursor-default|true|sequential-thinking,filesystem,tavily|Default cursor server
cursor-disabled|false|playwright,chrome-devtools|Disabled browser server
legacy-server|tool-router,github
""")

        # Create cursor-mcp-url file
        url_file = repo_root / "data" / ".cursor-mcp-url"
        url_file.write_text("http://localhost:4444/servers/123e4567-e89b-12d3-a456-426614174000/mcp")

        yield repo_root


class TestIDEDetection:
    def test_detect_cursor_installed(self, temp_repo_root):
        """Test detection of Cursor IDE."""
        manager = IDEManager(temp_repo_root)

        # Mock Cursor app existence
        with patch('pathlib.Path.exists', return_value=True):
            detected = manager.detect_installed_ides()
            assert "cursor" in detected

    def test_detect_vscode_installed(self, temp_repo_root):
        """Test detection of VSCode IDE."""
        manager = IDEManager(temp_repo_root)

        # Mock VSCode app existence
        with patch('pathlib.Path.exists', return_value=True):
            detected = manager.detect_installed_ides()
            assert "vscode" in detected

    def test_detect_no_ides(self, temp_repo_root):
        """Test when no IDEs are installed."""
        manager = IDEManager(temp_repo_root)

        with patch('pathlib.Path.exists', return_value=False):
            detected = manager.detect_installed_ides()
            assert detected == []


class TestVirtualServers:
    def test_get_available_servers(self, temp_repo_root):
        """Test loading virtual servers from config."""
        manager = IDEManager(temp_repo_root)
        servers = manager.get_available_servers()

        assert len(servers) == 2  # cursor-default and legacy-server (cursor-disabled is filtered out)
        assert servers[0]['name'] == 'cursor-default'
        assert servers[0]['enabled'] is True
        assert servers[0]['description'] == 'Default cursor server'
        assert servers[1]['name'] == 'legacy-server'
        assert servers[1]['enabled'] is True

    def test_get_available_servers_no_config(self, temp_repo_root):
        """Test when virtual servers config doesn't exist."""
        manager = IDEManager(temp_repo_root)

        # Remove config file
        (temp_repo_root / "config" / "virtual-servers.txt").unlink()

        servers = manager.get_available_servers()
        assert servers == []

    def test_get_server_url(self, temp_repo_root):
        """Test getting server URL from data file."""
        manager = IDEManager(temp_repo_root)
        url = manager.get_server_url("cursor-default")

        assert url == "http://localhost:4444/servers/123e4567-e89b-12d3-a456-426614174000/mcp"

    def test_get_server_url_no_file(self, temp_repo_root):
        """Test when URL file doesn't exist."""
        manager = IDEManager(temp_repo_root)

        # Remove URL file
        (temp_repo_root / "data" / ".cursor-mcp-url").unlink()

        url = manager.get_server_url("cursor-default")
        assert url is None


class TestIDEConfigGeneration:
    def test_generate_cursor_config(self, temp_repo_root):
        """Test generating Cursor IDE configuration."""
        manager = IDEManager(temp_repo_root)
        config = manager.generate_ide_config("cursor", "cursor-default")

        assert "mcpServers" in config
        assert "cursor-default" in config["mcpServers"]
        server_config = config["mcpServers"]["cursor-default"]

        assert "command" in server_config
        assert "args" in server_config
        assert "env" in server_config
        assert server_config["args"] == ["--server-name", "cursor-default"]
        assert "GATEWAY_URL" in server_config["env"]
        assert "SERVER_ID" in server_config["env"]

    def test_generate_vscode_config(self, temp_repo_root):
        """Test generating VSCode IDE configuration."""
        manager = IDEManager(temp_repo_root)
        config = manager.generate_ide_config("vscode", "cursor-default")

        assert "mcp.servers" in config
        assert "cursor-default" in config["mcp.servers"]

    def test_generate_config_invalid_server(self, temp_repo_root):
        """Test generating config for non-existent server."""
        manager = IDEManager(temp_repo_root)

        # Remove URL file to trigger error
        (temp_repo_root / "data" / ".cursor-mcp-url").unlink()

        with pytest.raises(ValueError, match="No URL found"):
            manager.generate_ide_config("cursor", "cursor-default")

    def test_generate_config_invalid_url(self, temp_repo_root):
        """Test generating config with invalid URL format."""
        manager = IDEManager(temp_repo_root)

        # Create invalid URL file
        (temp_repo_root / "data" / ".cursor-mcp-url").write_text("invalid-url")

        with pytest.raises(ValueError, match="Invalid server URL format"):
            manager.generate_ide_config("cursor", "cursor-default")


class TestIDEOperations:
    def test_install_ide_config_new(self, temp_repo_root):
        """Test installing IDE configuration for new config."""
        manager = IDEManager(temp_repo_root)

        # Mock config path
        config_path = temp_repo_root / "test_cursor_config.json"

        with patch.object(manager.ides['cursor'], 'config_path', str(config_path)):
            result = manager.install_ide_config("cursor", "cursor-default")
            assert result is True
            assert config_path.exists()

            # Verify config content
            with open(config_path, 'r') as f:
                saved_config = json.load(f)
                assert "mcpServers" in saved_config
                assert "cursor-default" in saved_config["mcpServers"]

    def test_install_ide_config_existing(self, temp_repo_root):
        """Test installing IDE configuration when config already exists."""
        manager = IDEManager(temp_repo_root)

        # Create existing config
        config_path = temp_repo_root / "test_cursor_config.json"
        existing_config = {"mcpServers": {"existing-server": {"command": "test"}}}
        with open(config_path, 'w') as f:
            json.dump(existing_config, f)

        with patch.object(manager.ides['cursor'], 'config_path', str(config_path)):
            result = manager.install_ide_config("cursor", "cursor-default")
            assert result is True

            # Verify merged config
            with open(config_path, 'r') as f:
                saved_config = json.load(f)
                assert "existing-server" in saved_config["mcpServers"]
                assert "cursor-default" in saved_config["mcpServers"]

    def test_backup_ide_config(self, temp_repo_root):
        """Test backing up IDE configuration."""
        manager = IDEManager(temp_repo_root)

        # Create existing config
        config_path = temp_repo_root / ".cursor" / "mcp.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text('{"test": "config"}')

        with patch.object(manager.ides['cursor'], 'config_path', str(config_path)):
            result = manager.backup_ide_config("cursor")
            assert result is True

            # Verify backup was created
            backup_dir = temp_repo_root / "data" / "ide-backups"
            backup_files = list(backup_dir.glob("cursor_config_*.json"))
            assert len(backup_files) == 1

    def test_backup_ide_config_no_config(self, temp_repo_root):
        """Test backing up when no config exists."""
        manager = IDEManager(temp_repo_root)

        config_path = temp_repo_root / ".cursor" / "mcp.json"

        with patch.object(manager.ides['cursor'], 'config_path', str(config_path)):
            result = manager.backup_ide_config("cursor")
            assert result is False

    def test_restore_ide_config(self, temp_repo_root):
        """Test restoring IDE configuration from backup."""
        manager = IDEManager(temp_repo_root)

        # Create backup directory and file
        backup_dir = temp_repo_root / "data" / "ide-backups"
        backup_dir.mkdir(exist_ok=True)
        backup_file = backup_dir / "cursor_config_20260101_120000.json"
        backup_file.write_text('{"restored": "config"}')

        config_path = temp_repo_root / ".cursor" / "mcp.json"

        with patch.object(manager.ides['cursor'], 'config_path', str(config_path)):
            result = manager.restore_ide_config("cursor", str(backup_file))
            assert result is True
            assert config_path.exists()

            # Verify restored content
            with open(config_path, 'r') as f:
                restored_config = json.load(f)
                assert restored_config == {"restored": "config"}

    def test_get_ide_status_existing_config(self, temp_repo_root):
        """Test getting IDE status when config exists."""
        manager = IDEManager(temp_repo_root)

        # Create existing config
        config_path = temp_repo_root / ".cursor" / "mcp.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_data = {"mcpServers": {"test-server": {"command": "test"}}}
        with open(config_path, 'w') as f:
            json.dump(config_data, f)

        with patch.object(manager.ides['cursor'], 'config_path', str(config_path)):
            status = manager.get_ide_status("cursor")

            assert status["ide"] == "Cursor"
            assert status["config_exists"] is True
            assert "test-server" in status["servers_configured"]
            assert status["last_modified"] is not None

    def test_get_ide_status_no_config(self, temp_repo_root):
        """Test getting IDE status when no config exists."""
        manager = IDEManager(temp_repo_root)

        config_path = temp_repo_root / ".cursor" / "mcp.json"

        with patch.object(manager.ides['cursor'], 'config_path', str(config_path)):
            status = manager.get_ide_status("cursor")

            assert status["ide"] == "Cursor"
            assert status["config_exists"] is False
            assert status["servers_configured"] == []

    def test_setup_ide_install(self, temp_repo_root):
        """Test main setup function with install action."""
        manager = IDEManager(temp_repo_root)

        config_path = temp_repo_root / "test_cursor_config.json"

        with patch.object(manager, 'install_ide_config', return_value=True) as mock_install:
            with patch.object(manager.ides['cursor'], 'config_path', str(config_path)):
                result = manager.setup_ide("cursor", "install", "cursor-default")
                assert result is True
                mock_install.assert_called_once_with("cursor", "cursor-default", None)

    def test_setup_ide_backup(self, temp_repo_root):
        """Test main setup function with backup action."""
        manager = IDEManager(temp_repo_root)

        with patch.object(manager, 'backup_ide_config', return_value=True) as mock_backup:
            result = manager.setup_ide("cursor", "backup")
            assert result is True
            mock_backup.assert_called_once_with("cursor")

    def test_setup_ide_status(self, temp_repo_root):
        """Test main setup function with status action."""
        manager = IDEManager(temp_repo_root)

        with patch.object(manager, 'get_ide_status', return_value={"test": "status"}) as mock_status:
            with patch('builtins.print') as mock_print:
                result = manager.setup_ide("cursor", "status")
                assert result is True
                mock_status.assert_called_once_with("cursor")
                # Verify print was called with status info

    def test_setup_ide_all(self, temp_repo_root):
        """Test setup function for all detected IDEs."""
        manager = IDEManager(temp_repo_root)

        with patch.object(manager, 'detect_installed_ides', return_value=["cursor", "vscode"]) as mock_detect:
            with patch.object(manager, 'setup_ide', return_value=True) as mock_setup:
                result = manager.setup_ide("all", "install", "cursor-default")
                assert result is True
                assert mock_setup.call_count == 2
                mock_detect.assert_called_once()


class TestErrorHandling:
    def test_unsupported_ide(self, temp_repo_root):
        """Test handling of unsupported IDE."""
        manager = IDEManager(temp_repo_root)

        result = manager.setup_ide("unsupported-ide", "install")
        assert result is False

    def test_invalid_action(self, temp_repo_root):
        """Test handling of invalid action."""
        manager = IDEManager(temp_repo_root)

        result = manager.setup_ide("cursor", "invalid-action")
        assert result is False


class TestEnvironmentVariables:
    def test_generate_config_with_env_vars(self, temp_repo_root):
        """Test config generation with environment variables."""
        manager = IDEManager(temp_repo_root)

        # Set environment variables
        with patch.dict(os.environ, {
            'GITHUB_PERSONAL_ACCESS_TOKEN': 'test-token',
            'SNYK_TOKEN': 'snyk-token'
        }):
            config = manager.generate_ide_config("cursor", "cursor-default")

            server_config = config["mcpServers"]["cursor-default"]
            assert "GITHUB_PERSONAL_ACCESS_TOKEN" in server_config["env"]
            assert server_config["env"]["GITHUB_PERSONAL_ACCESS_TOKEN"] == "test-token"
            assert "SNYK_TOKEN" in server_config["env"]
            assert server_config["env"]["SNYK_TOKEN"] == "snyk-token"
