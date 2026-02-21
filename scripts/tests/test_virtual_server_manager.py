"""Tests for scripts/virtual-server-manager.py"""

import importlib.util
import textwrap
from pathlib import Path

import pytest

# Load module from hyphenated filename (not importable via normal import)
_spec = importlib.util.spec_from_file_location(
    "virtual_server_manager",
    Path(__file__).parent.parent / "virtual-server-manager.py",
)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]
VirtualServer = _mod.VirtualServer
VirtualServerManager = _mod.VirtualServerManager


@pytest.fixture()
def config_4field(tmp_path: Path) -> Path:
    """Config file in 4-field format (name|enabled|gateways|description)."""
    content = textwrap.dedent("""\
        # Virtual servers: Name|enabled|gateways|description
        cursor-default|true|sequential-thinking,filesystem,tavily|Default cursor server
        cursor-router|true|tool-router|Router only
        cursor-disabled|false|playwright,chrome-devtools|Disabled browser server
        legacy-server|tool-router,github
    """)
    cfg = tmp_path / "virtual-servers.txt"
    cfg.write_text(content)
    return cfg


@pytest.fixture()
def manager(config_4field: Path) -> VirtualServerManager:
    return VirtualServerManager(str(config_4field))


class TestLoad:
    def test_loads_all_entries(self, manager: VirtualServerManager) -> None:
        assert len(manager.servers) == 4  # 3 four-field + 1 two-field legacy

    def test_enabled_flag_true(self, manager: VirtualServerManager) -> None:
        assert manager.servers["cursor-default"].enabled is True

    def test_enabled_flag_false(self, manager: VirtualServerManager) -> None:
        assert manager.servers["cursor-disabled"].enabled is False

    def test_gateways_parsed(self, manager: VirtualServerManager) -> None:
        assert manager.servers["cursor-default"].gateways == [
            "sequential-thinking", "filesystem", "tavily"
        ]

    def test_description_parsed(self, manager: VirtualServerManager) -> None:
        assert manager.servers["cursor-default"].description == "Default cursor server"

    def test_legacy_2field_enabled_by_default(self, manager: VirtualServerManager) -> None:
        assert manager.servers["legacy-server"].enabled is True

    def test_legacy_2field_gateways(self, manager: VirtualServerManager) -> None:
        assert manager.servers["legacy-server"].gateways == ["tool-router", "github"]

    def test_skips_blank_lines_and_comments(self, manager: VirtualServerManager) -> None:
        assert "#" not in manager.servers
        assert "" not in manager.servers


class TestGetEnabledServers:
    def test_returns_only_enabled(self, manager: VirtualServerManager) -> None:
        enabled = manager.get_enabled_servers()
        names = {s.name for s in enabled}
        assert "cursor-disabled" not in names
        assert "cursor-default" in names
        assert "cursor-router" in names
        assert "legacy-server" in names

    def test_count(self, manager: VirtualServerManager) -> None:
        assert len(manager.get_enabled_servers()) == 3  # cursor-default, cursor-router, legacy-server


class TestEnableDisable:
    def test_disable_enabled_server(self, manager: VirtualServerManager) -> None:
        result = manager.disable_server("cursor-default")
        assert result is True
        assert manager.servers["cursor-default"].enabled is False

    def test_enable_disabled_server(self, manager: VirtualServerManager) -> None:
        result = manager.enable_server("cursor-disabled")
        assert result is True
        assert manager.servers["cursor-disabled"].enabled is True

    def test_enable_already_enabled(self, manager: VirtualServerManager, capsys) -> None:
        result = manager.enable_server("cursor-router")
        assert result is True
        captured = capsys.readouterr()
        assert "already enabled" in captured.out

    def test_disable_already_disabled(self, manager: VirtualServerManager, capsys) -> None:
        result = manager.disable_server("cursor-disabled")
        assert result is True
        captured = capsys.readouterr()
        assert "already disabled" in captured.out

    def test_enable_nonexistent(self, manager: VirtualServerManager) -> None:
        result = manager.enable_server("does-not-exist")
        assert result is False

    def test_disable_nonexistent(self, manager: VirtualServerManager) -> None:
        result = manager.disable_server("does-not-exist")
        assert result is False


class TestPersistence:
    def test_save_and_reload(self, manager: VirtualServerManager, config_4field: Path) -> None:
        manager.disable_server("cursor-default")
        reloaded = VirtualServerManager(str(config_4field))
        assert reloaded.servers["cursor-default"].enabled is False

    def test_backup_created_on_save(self, manager: VirtualServerManager, config_4field: Path) -> None:
        manager.disable_server("cursor-default")
        backup = config_4field.with_suffix(".backup")
        assert backup.exists()

    def test_roundtrip_preserves_all_servers(self, manager: VirtualServerManager, config_4field: Path) -> None:
        manager.save_servers()
        reloaded = VirtualServerManager(str(config_4field))
        assert set(reloaded.servers.keys()) == set(manager.servers.keys())


class TestValidate:
    def test_no_warnings_for_valid_config(self, manager: VirtualServerManager) -> None:
        warnings = manager.validate_servers()
        empty_gateway_warnings = [w for w in warnings if "no gateways" in w]
        assert empty_gateway_warnings == []

    def test_warns_on_empty_gateways(self, tmp_path: Path) -> None:
        cfg = tmp_path / "vs.txt"
        cfg.write_text("empty-server|true||No gateways here\n")
        m = VirtualServerManager(str(cfg))
        warnings = m.validate_servers()
        assert any("no gateways" in w for w in warnings)


class TestMissingConfigFile:
    def test_loads_gracefully_when_file_missing(self, tmp_path: Path) -> None:
        m = VirtualServerManager(str(tmp_path / "nonexistent.txt"))
        assert m.servers == {}
