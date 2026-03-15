"""Tests for scripts/utils/manage-servers.py

Phase 1 virtual server lifecycle management (FR-2).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Load manage-servers module
# ---------------------------------------------------------------------------

SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "utils" / "manage-servers.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("manage_servers", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["manage_servers"] = mod
    spec.loader.exec_module(mod)
    return mod


_mod = _load_module()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_CONFIG = """\
# Virtual servers: Name|enabled|gateways|description
cursor-default|true|filesystem,tavily|Default Cursor server
cursor-search|true|tavily|Search-only server
cursor-disabled|false|filesystem|A disabled server
legacy-server|filesystem|Legacy format (2 fields)
"""


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    f = tmp_path / "virtual-servers.txt"
    f.write_text(SAMPLE_CONFIG)
    return f


@pytest.fixture(autouse=True)
def patch_config(config_file: Path, monkeypatch):
    monkeypatch.setattr(_mod, "CONFIG_FILE", config_file)


# ---------------------------------------------------------------------------
# Tests: _parse_servers
# ---------------------------------------------------------------------------


class TestParseServers:
    def test_parses_4_field_format(self, config_file):
        servers = _mod._parse_servers(config_file.read_text())
        names = [s["name"] for s in servers]
        assert "cursor-default" in names
        assert "cursor-disabled" in names

    def test_skips_comments_and_blank_lines(self, config_file):
        servers = _mod._parse_servers(config_file.read_text())
        for s in servers:
            assert not s["name"].startswith("#")

    def test_parses_disabled_flag(self, config_file):
        servers = _mod._parse_servers(config_file.read_text())
        disabled = next(s for s in servers if s["name"] == "cursor-disabled")
        assert _mod._is_enabled(disabled["enabled"]) is False

    def test_legacy_format_defaults_enabled(self, config_file):
        servers = _mod._parse_servers(config_file.read_text())
        legacy = next(s for s in servers if s["name"] == "legacy-server")
        assert _mod._is_enabled(legacy["enabled"]) is True


# ---------------------------------------------------------------------------
# Tests: _is_enabled
# ---------------------------------------------------------------------------


class TestIsEnabled:
    @pytest.mark.parametrize("value", ["true", "True", "TRUE", "1", "yes", "Yes"])
    def test_truthy_values(self, value):
        assert _mod._is_enabled(value) is True

    @pytest.mark.parametrize("value", ["false", "False", "FALSE", "0", "no", "No"])
    def test_falsy_values(self, value):
        assert _mod._is_enabled(value) is False


# ---------------------------------------------------------------------------
# Tests: cmd_list
# ---------------------------------------------------------------------------


class TestCmdList:
    def test_returns_zero(self, capsys):
        rc = _mod.cmd_list()
        assert rc == 0

    def test_shows_enabled_and_disabled(self, capsys):
        _mod.cmd_list()
        out = capsys.readouterr().out
        assert "cursor-default" in out
        assert "cursor-disabled" in out

    def test_shows_count_summary(self, capsys):
        _mod.cmd_list()
        out = capsys.readouterr().out
        assert "enabled" in out
        assert "disabled" in out

    def test_empty_config_returns_error(self, config_file, capsys):
        config_file.write_text("# only comments\n")
        rc = _mod.cmd_list()
        assert rc == 1


# ---------------------------------------------------------------------------
# Tests: cmd_enable
# ---------------------------------------------------------------------------


class TestCmdEnable:
    def test_enables_disabled_server(self, config_file):
        rc = _mod.cmd_enable("cursor-disabled")
        assert rc == 0
        text = config_file.read_text()
        assert "cursor-disabled|true|" in text

    def test_already_enabled_no_op(self, config_file, capsys):
        rc = _mod.cmd_enable("cursor-default")
        assert rc == 0
        out = capsys.readouterr().out
        assert "already enabled" in out

    def test_unknown_server_returns_error(self, capsys):
        rc = _mod.cmd_enable("nonexistent-server")
        assert rc == 1
        out = capsys.readouterr().out
        assert "not found" in out

    def test_preserves_other_servers(self, config_file):
        original = config_file.read_text()
        _mod.cmd_enable("cursor-disabled")
        new = config_file.read_text()
        # Other servers unchanged
        assert "cursor-default|true|" in new
        assert "cursor-search|true|" in new


# ---------------------------------------------------------------------------
# Tests: cmd_disable
# ---------------------------------------------------------------------------


class TestCmdDisable:
    def test_disables_enabled_server(self, config_file):
        rc = _mod.cmd_disable("cursor-search")
        assert rc == 0
        text = config_file.read_text()
        assert "cursor-search|false|" in text

    def test_already_disabled_no_op(self, config_file, capsys):
        rc = _mod.cmd_disable("cursor-disabled")
        assert rc == 0
        out = capsys.readouterr().out
        assert "already disabled" in out

    def test_unknown_server_returns_error(self, capsys):
        rc = _mod.cmd_disable("nonexistent-server")
        assert rc == 1

    def test_preserves_other_servers(self, config_file):
        _mod.cmd_disable("cursor-search")
        text = config_file.read_text()
        assert "cursor-default|true|" in text

    def test_roundtrip_enable_disable(self, config_file):
        """disable then re-enable should restore original state."""
        _mod.cmd_disable("cursor-search")
        _mod.cmd_enable("cursor-search")
        text = config_file.read_text()
        assert "cursor-search|true|" in text


# ---------------------------------------------------------------------------
# Tests: cmd_status
# ---------------------------------------------------------------------------


class TestCmdStatus:
    def test_shows_enabled_status(self, capsys):
        rc = _mod.cmd_status("cursor-default")
        assert rc == 0
        out = capsys.readouterr().out
        assert "enabled" in out

    def test_shows_disabled_status(self, capsys):
        rc = _mod.cmd_status("cursor-disabled")
        assert rc == 0
        out = capsys.readouterr().out
        assert "disabled" in out

    def test_unknown_server(self, capsys):
        rc = _mod.cmd_status("nonexistent")
        assert rc == 1


# ---------------------------------------------------------------------------
# Tests: main CLI dispatch
# ---------------------------------------------------------------------------


class TestMainDispatch:
    def test_list_command(self, capsys):
        sys.argv = ["manage-servers.py", "list"]
        rc = _mod.main()
        assert rc == 0

    def test_enable_command(self, config_file, capsys):
        sys.argv = ["manage-servers.py", "enable", "cursor-disabled"]
        rc = _mod.main()
        assert rc == 0

    def test_disable_command(self, config_file, capsys):
        sys.argv = ["manage-servers.py", "disable", "cursor-search"]
        rc = _mod.main()
        assert rc == 0

    def test_status_command(self, capsys):
        sys.argv = ["manage-servers.py", "status", "cursor-default"]
        rc = _mod.main()
        assert rc == 0

    def test_unknown_command(self, capsys):
        sys.argv = ["manage-servers.py", "frobnicate"]
        rc = _mod.main()
        assert rc == 1

    def test_no_args(self, capsys):
        sys.argv = ["manage-servers.py"]
        rc = _mod.main()
        assert rc == 1

    def test_enable_missing_name(self, capsys):
        sys.argv = ["manage-servers.py", "enable"]
        rc = _mod.main()
        assert rc == 1
