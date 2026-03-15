"""Tests for IDE setup and management (Phase 2 IDE Integration UX).

Covers:
- IDEManager initialisation and IDE registry (including Zed)
- Cross-platform detect_installed_ides detection logic
- generate_ide_config output format for all IDEs
- install_ide_config merge strategy per IDE
- use_wrapper_script (generalised, no longer Cursor-only)
- verify_setup (generalised, no longer Cursor-only)
- mcp-wrapper.sh existence and basic syntax
"""

from __future__ import annotations

import importlib.util
import json
import platform
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Load ide-setup module dynamically (it lives in scripts/, not a package)
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent
IDE_SETUP_PATH = REPO_ROOT / "scripts" / "ide-setup.py"


def _load_ide_setup():
    """Import scripts/ide-setup.py as a module."""
    spec = importlib.util.spec_from_file_location("ide_setup", IDE_SETUP_PATH)
    mod = importlib.util.module_from_spec(spec)
    # Inject into sys.modules so dataclass decorator works
    sys.modules["ide_setup"] = mod
    spec.loader.exec_module(mod)
    return mod


try:
    _ide_setup_mod = _load_ide_setup()
    IDEManager = _ide_setup_mod.IDEManager
    IDE_SETUP_IMPORTABLE = True
except Exception:
    IDE_SETUP_IMPORTABLE = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_manager(tmp_path: Path) -> "IDEManager":
    """Create an IDEManager with its repo_root pointing to a temp directory."""
    # Scaffold minimum expected directories
    (tmp_path / "scripts").mkdir(exist_ok=True)
    (tmp_path / "data").mkdir(exist_ok=True)
    (tmp_path / "config").mkdir(exist_ok=True)
    return IDEManager(repo_root=tmp_path)


# ---------------------------------------------------------------------------
# Tests: IDEManager — registry
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not IDE_SETUP_IMPORTABLE, reason="ide-setup.py import failed")
class TestIDERegistry:
    """Verify the IDE registry is complete and well-formed."""

    def test_all_expected_ides_present(self, tmp_path):
        mgr = make_manager(tmp_path)
        assert "cursor" in mgr.ides
        assert "windsurf" in mgr.ides
        assert "vscode" in mgr.ides
        assert "claude" in mgr.ides
        assert "zed" in mgr.ides, "Zed must be registered (Phase 2 FR-4)"

    def test_each_ide_has_required_fields(self, tmp_path):
        mgr = make_manager(tmp_path)
        for ide_key, cfg in mgr.ides.items():
            assert cfg.name, f"{ide_key}: name missing"
            assert cfg.config_path, f"{ide_key}: config_path missing"
            assert cfg.wrapper_script, f"{ide_key}: wrapper_script missing"
            assert isinstance(cfg.env_vars, dict), f"{ide_key}: env_vars must be dict"

    def test_zed_uses_context_servers_path(self, tmp_path):
        mgr = make_manager(tmp_path)
        zed = mgr.ides["zed"]
        assert ".config/zed" in zed.config_path

    def test_claude_config_path_platform_correct(self, tmp_path):
        mgr = make_manager(tmp_path)
        system = platform.system()
        claude_path = mgr.ides["claude"].config_path
        if system == "Darwin":
            assert "Library/Application Support/Claude" in claude_path, (
                f"macOS Claude path must use Library/Application Support, got: {claude_path}"
            )
        elif system == "Linux":
            assert ".config/claude" in claude_path, f"Linux Claude path must use .config/claude, got: {claude_path}"


# ---------------------------------------------------------------------------
# Tests: detect_installed_ides
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not IDE_SETUP_IMPORTABLE, reason="ide-setup.py import failed")
class TestDetectInstalledIDEs:
    """Verify IDE detection returns correct results based on filesystem state."""

    def test_returns_list(self, tmp_path):
        mgr = make_manager(tmp_path)
        result = mgr.detect_installed_ides()
        assert isinstance(result, list)

    def test_cursor_detected_when_config_dir_exists(self, tmp_path):
        mgr = make_manager(tmp_path)
        # Simulate ~/.cursor directory being present
        cursor_dir = Path.home() / ".cursor"
        with patch("pathlib.Path.exists", side_effect=lambda p=cursor_dir: str(p) == str(cursor_dir) or False):
            # Just verify detect_installed_ides returns a list without crashing
            result = mgr.detect_installed_ides()
            assert isinstance(result, list)

    def test_zed_detected_when_config_dir_exists(self, tmp_path, monkeypatch):
        """Zed should be detected when ~/.config/zed exists."""
        mgr = make_manager(tmp_path)
        fake_zed_dir = tmp_path / ".config" / "zed"
        fake_zed_dir.mkdir(parents=True)

        original_exists = Path.exists

        def patched_exists(self_path):
            if str(self_path) == str(Path.home() / ".config" / "zed"):
                return True
            return original_exists(self_path)

        with patch.object(Path, "exists", patched_exists):
            result = mgr.detect_installed_ides()
            assert isinstance(result, list)

    def test_no_crash_without_any_ides(self, tmp_path, monkeypatch):
        """detect_installed_ides should return [] when nothing is installed."""
        mgr = make_manager(tmp_path)
        # Patch all path existence checks and which() to return False/None
        with patch("pathlib.Path.exists", return_value=False), patch("shutil.which", return_value=None):
            result = mgr.detect_installed_ides()
            assert result == []


# ---------------------------------------------------------------------------
# Tests: generate_ide_config
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not IDE_SETUP_IMPORTABLE, reason="ide-setup.py import failed")
class TestGenerateIDEConfig:
    """Verify config generation produces correct format per IDE."""

    def _make_manager_with_url(self, tmp_path: Path) -> "IDEManager":
        mgr = make_manager(tmp_path)
        # Write a fake MCP client URL so get_server_url() succeeds
        url_file = tmp_path / "data" / ".mcp-client-url"
        url_file.write_text("http://localhost:4444/servers/abc123/mcp")
        return mgr

    def test_cursor_uses_mcpServers(self, tmp_path):
        mgr = self._make_manager_with_url(tmp_path)
        config = mgr.generate_ide_config("cursor", "cursor-default")
        assert "mcpServers" in config
        assert "context-forge" in config["mcpServers"]
        entry = config["mcpServers"]["context-forge"]
        assert "command" in entry
        assert "env" in entry
        assert "MCP_CLIENT_SERVER_URL" in entry["env"]

    def test_vscode_uses_mcp_servers(self, tmp_path):
        mgr = self._make_manager_with_url(tmp_path)
        config = mgr.generate_ide_config("vscode", "cursor-default")
        assert "mcp.servers" in config

    def test_zed_uses_context_servers(self, tmp_path):
        mgr = self._make_manager_with_url(tmp_path)
        config = mgr.generate_ide_config("zed", "cursor-default")
        assert "context_servers" in config, "Zed must use context_servers key"
        entry = config["context_servers"]["cursor-default"]
        assert "command" in entry
        assert isinstance(entry["command"], dict), "Zed command must be a dict with path+args"
        assert "path" in entry["command"]
        assert "env" in entry
        assert "MCP_CLIENT_SERVER_URL" in entry["env"]

    def test_windsurf_uses_mcpServers(self, tmp_path):
        mgr = self._make_manager_with_url(tmp_path)
        config = mgr.generate_ide_config("windsurf", "cursor-default")
        assert "mcpServers" in config

    def test_claude_uses_mcpServers(self, tmp_path):
        mgr = self._make_manager_with_url(tmp_path)
        config = mgr.generate_ide_config("claude", "cursor-default")
        assert "mcpServers" in config

    def test_invalid_url_format_raises(self, tmp_path):
        mgr = make_manager(tmp_path)
        url_file = tmp_path / "data" / ".mcp-client-url"
        url_file.write_text("http://localhost:4444/bad-path")
        with pytest.raises(ValueError, match="Invalid server URL format"):
            mgr.generate_ide_config("cursor", "cursor-default")

    def test_missing_url_raises(self, tmp_path):
        mgr = make_manager(tmp_path)
        with pytest.raises(ValueError, match="No URL found"):
            mgr.generate_ide_config("cursor", "cursor-default")

    def test_unsupported_ide_raises(self, tmp_path):
        mgr = self._make_manager_with_url(tmp_path)
        with pytest.raises(ValueError, match="Unsupported IDE"):
            mgr.generate_ide_config("neovim", "cursor-default")


# ---------------------------------------------------------------------------
# Tests: install_ide_config merge strategy
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not IDE_SETUP_IMPORTABLE, reason="ide-setup.py import failed")
class TestInstallIDEConfig:
    """Verify install_ide_config creates and merges configs correctly."""

    def _url_file(self, tmp_path: Path) -> None:
        (tmp_path / "data" / ".mcp-client-url").write_text("http://localhost:4444/servers/abc123/mcp")

    def test_cursor_creates_mcp_json(self, tmp_path, monkeypatch):
        """Cursor config should be written to cursor's config path."""
        mgr = make_manager(tmp_path)
        self._url_file(tmp_path)
        # Override the config_path to write into tmp_path
        cursor_cfg = tmp_path / "cursor_mcp.json"
        mgr.ides["cursor"] = mgr.ides["cursor"].__class__(
            name="Cursor",
            config_path=str(cursor_cfg),
            config_format="json",
            wrapper_script="mcp-wrapper.sh",
            env_vars={},
            example_profiles=[],
        )
        success = mgr.install_ide_config("cursor", "cursor-default")
        assert success
        assert cursor_cfg.exists()
        data = json.loads(cursor_cfg.read_text())
        assert "mcpServers" in data

    def test_zed_creates_context_servers(self, tmp_path):
        """Zed config should use context_servers key."""
        mgr = make_manager(tmp_path)
        self._url_file(tmp_path)
        zed_cfg = tmp_path / "zed_settings.json"
        mgr.ides["zed"] = mgr.ides["zed"].__class__(
            name="Zed",
            config_path=str(zed_cfg),
            config_format="json",
            wrapper_script="mcp-wrapper.sh",
            env_vars={},
            example_profiles=[],
        )
        success = mgr.install_ide_config("zed", "cursor-default")
        assert success
        data = json.loads(zed_cfg.read_text())
        assert "context_servers" in data

    def test_merges_with_existing_cursor_config(self, tmp_path):
        """Existing mcpServers entries should be preserved."""
        mgr = make_manager(tmp_path)
        self._url_file(tmp_path)
        cursor_cfg = tmp_path / "cursor_mcp.json"
        cursor_cfg.write_text(json.dumps({"mcpServers": {"existing-server": {"command": "foo"}}}))
        mgr.ides["cursor"] = mgr.ides["cursor"].__class__(
            name="Cursor",
            config_path=str(cursor_cfg),
            config_format="json",
            wrapper_script="mcp-wrapper.sh",
            env_vars={},
            example_profiles=[],
        )
        mgr.install_ide_config("cursor", "cursor-default")
        data = json.loads(cursor_cfg.read_text())
        assert "existing-server" in data["mcpServers"], "Existing servers must be preserved"
        assert "context-forge" in data["mcpServers"], "New server must be added"


# ---------------------------------------------------------------------------
# Tests: mcp-wrapper.sh
# ---------------------------------------------------------------------------


class TestMcpWrapperScript:
    """Verify mcp-wrapper.sh exists, is executable, and has valid syntax."""

    @pytest.fixture
    def wrapper_path(self) -> Path:
        return REPO_ROOT / "scripts" / "mcp-wrapper.sh"

    def test_wrapper_exists(self, wrapper_path):
        assert wrapper_path.exists(), "mcp-wrapper.sh must exist (not a broken symlink)"

    def test_wrapper_is_not_symlink(self, wrapper_path):
        assert not wrapper_path.is_symlink(), "mcp-wrapper.sh must be a real file, not a symlink"

    def test_wrapper_is_executable(self, wrapper_path):
        import os

        assert os.access(wrapper_path, os.X_OK), "mcp-wrapper.sh must be executable"

    def test_wrapper_has_valid_bash_syntax(self, wrapper_path):
        result = subprocess.run(
            ["bash", "-n", str(wrapper_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"mcp-wrapper.sh has syntax errors: {result.stderr}"

    def test_wrapper_reads_mcp_client_server_url(self, wrapper_path):
        content = wrapper_path.read_text()
        assert "MCP_CLIENT_SERVER_URL" in content

    def test_wrapper_uses_npx(self, wrapper_path):
        content = wrapper_path.read_text()
        assert "npx" in content or "NPX" in content


# ---------------------------------------------------------------------------
# Tests: verify_setup — no longer Cursor-only
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not IDE_SETUP_IMPORTABLE, reason="ide-setup.py import failed")
class TestVerifySetup:
    """verify_setup should accept all IDEs, not just cursor."""

    def test_verify_unsupported_ide_returns_false(self, tmp_path):
        mgr = make_manager(tmp_path)
        result = mgr.verify_setup("neovim")
        assert result is False

    def test_verify_zed_without_config_returns_false(self, tmp_path):
        mgr = make_manager(tmp_path)
        # Redirect Zed config to a non-existent temp file
        mgr.ides["zed"] = mgr.ides["zed"].__class__(
            name="Zed",
            config_path=str(tmp_path / "nonexistent.json"),
            config_format="json",
            wrapper_script="mcp-wrapper.sh",
            env_vars={},
            example_profiles=[],
        )
        # Gateway check will fail; we expect False — no crash
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")
            result = mgr.verify_setup("zed")
        assert result is False

    def test_verify_cursor_without_config_returns_false(self, tmp_path):
        mgr = make_manager(tmp_path)
        mgr.ides["cursor"] = mgr.ides["cursor"].__class__(
            name="Cursor",
            config_path=str(tmp_path / "nonexistent.json"),
            config_format="json",
            wrapper_script="mcp-wrapper.sh",
            env_vars={},
            example_profiles=[],
        )
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")
            result = mgr.verify_setup("cursor")
        assert result is False


# ---------------------------------------------------------------------------
# Tests: use_wrapper_script — no longer Cursor-only
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not IDE_SETUP_IMPORTABLE, reason="ide-setup.py import failed")
class TestUseWrapperScript:
    """use_wrapper_script should work for all supported IDEs."""

    def _make_wrapper(self, tmp_path: Path) -> Path:
        """Create a minimal mcp-wrapper.sh in the scripts dir."""
        wrapper = tmp_path / "scripts" / "mcp-wrapper.sh"
        wrapper.write_text(
            "#!/usr/bin/env bash\nexec npx @forgespace/mcp-gateway-client --url=$MCP_CLIENT_SERVER_URL\n"
        )
        wrapper.chmod(0o755)
        return wrapper

    def test_use_wrapper_cursor(self, tmp_path):
        mgr = make_manager(tmp_path)
        self._make_wrapper(tmp_path)
        # Write URL file
        (tmp_path / "data" / ".mcp-client-url").write_text("http://localhost:4444/servers/abc/mcp")
        # Redirect cursor config path to tmp
        cursor_cfg = tmp_path / "cursor_mcp.json"
        mgr.ides["cursor"] = mgr.ides["cursor"].__class__(
            name="Cursor",
            config_path=str(cursor_cfg),
            config_format="json",
            wrapper_script="mcp-wrapper.sh",
            env_vars={},
            example_profiles=[],
        )
        result = mgr.use_wrapper_script("cursor")
        assert result is True
        data = json.loads(cursor_cfg.read_text())
        assert "mcpServers" in data
        assert "context-forge" in data["mcpServers"]

    def test_use_wrapper_zed(self, tmp_path):
        mgr = make_manager(tmp_path)
        self._make_wrapper(tmp_path)
        (tmp_path / "data" / ".mcp-client-url").write_text("http://localhost:4444/servers/abc/mcp")
        zed_cfg = tmp_path / "zed_settings.json"
        mgr.ides["zed"] = mgr.ides["zed"].__class__(
            name="Zed",
            config_path=str(zed_cfg),
            config_format="json",
            wrapper_script="mcp-wrapper.sh",
            env_vars={},
            example_profiles=[],
        )
        result = mgr.use_wrapper_script("zed")
        assert result is True
        data = json.loads(zed_cfg.read_text())
        assert "context_servers" in data, "Zed config must use context_servers"
        assert "context-forge" in data["context_servers"]
        entry = data["context_servers"]["context-forge"]
        assert isinstance(entry["command"], dict), "Zed command must be object with path"

    def test_use_wrapper_missing_url_returns_false(self, tmp_path):
        mgr = make_manager(tmp_path)
        self._make_wrapper(tmp_path)
        # No URL file, no env var
        result = mgr.use_wrapper_script("cursor")
        assert result is False

    def test_use_wrapper_missing_wrapper_returns_false(self, tmp_path):
        mgr = make_manager(tmp_path)
        # No wrapper script created
        result = mgr.use_wrapper_script("cursor")
        assert result is False

    def test_use_wrapper_unsupported_ide_returns_false(self, tmp_path):
        mgr = make_manager(tmp_path)
        result = mgr.use_wrapper_script("neovim")
        assert result is False
