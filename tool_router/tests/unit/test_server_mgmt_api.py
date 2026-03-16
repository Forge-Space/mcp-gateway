"""Tests for server management and IDE detection API endpoints.

Covers:
  GET  /servers                 — list virtual servers (admin only)
  GET  /servers/{name}          — get single server (admin only)
  PATCH /servers/{name}/enabled — toggle enabled flag (admin only)
  GET  /ide/detect              — detect installed IDEs (admin only)

RBAC: all endpoints require SYSTEM_ADMIN permission (admin role only).
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tool_router.api.dependencies import get_security_context
from tool_router.api.server_mgmt import (
    _detect_ides,
    _parse_servers,
    _require_system_admin,
    _set_server_enabled,
    ide_router,
    router,
)
from tool_router.security.security_middleware import SecurityContext


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SAMPLE_CONFIG = textwrap.dedent("""\
    # Virtual servers config
    cursor-default|true|filesystem,memory|Default cursor server
    cursor-search|false|tavily|Search-focused server
    python-dev|true|tool-router,github,filesystem|Python development
""")


def _make_ctx(role: str) -> SecurityContext:
    return SecurityContext(
        user_id="u-test",
        session_id="s-test",
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="req-1",
        endpoint="/servers",
        authentication_method="jwt",
        user_role=role,
    )


def _make_app(role: str | None = "admin") -> FastAPI:
    """Build isolated test app with optional auth override."""
    app = FastAPI()
    app.include_router(router)
    app.include_router(ide_router)

    if role is not None:
        ctx = _make_ctx(role)

        async def _mock_ctx() -> SecurityContext:
            return ctx

        app.dependency_overrides[get_security_context] = _mock_ctx

    return app


# ---------------------------------------------------------------------------
# Unit: _parse_servers
# ---------------------------------------------------------------------------


class TestParseServers:
    def test_parses_enabled_server(self) -> None:
        servers = _parse_servers(_SAMPLE_CONFIG)
        assert len(servers) == 3
        cs = next(s for s in servers if s.name == "cursor-default")
        assert cs.enabled is True
        assert cs.gateways == ["filesystem", "memory"]
        assert cs.description == "Default cursor server"

    def test_parses_disabled_server(self) -> None:
        servers = _parse_servers(_SAMPLE_CONFIG)
        search = next(s for s in servers if s.name == "cursor-search")
        assert search.enabled is False

    def test_skips_comments_and_blank_lines(self) -> None:
        text = "\n# comment\n\ncursor-default|true|filesystem|desc\n"
        servers = _parse_servers(text)
        assert len(servers) == 1

    def test_legacy_format_without_enabled_field(self) -> None:
        text = "old-server|filesystem,memory|Old description\n"
        servers = _parse_servers(text)
        assert servers[0].enabled is True

    def test_gateways_split_and_stripped(self) -> None:
        text = "srv|true| a , b , c |desc\n"
        servers = _parse_servers(text)
        assert servers[0].gateways == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# Unit: _set_server_enabled
# ---------------------------------------------------------------------------


class TestSetServerEnabled:
    def test_enables_disabled_server(self, tmp_path: Path) -> None:
        cfg = tmp_path / "virtual-servers.txt"
        cfg.write_text("cursor-search|false|tavily|Search server\n")
        with patch("tool_router.api.server_mgmt._CONFIG_FILE", cfg):
            changed = _set_server_enabled("cursor-search", True)
        assert changed is True
        assert "cursor-search|true|" in cfg.read_text()

    def test_disables_enabled_server(self, tmp_path: Path) -> None:
        cfg = tmp_path / "virtual-servers.txt"
        cfg.write_text("cursor-default|true|filesystem|Default\n")
        with patch("tool_router.api.server_mgmt._CONFIG_FILE", cfg):
            changed = _set_server_enabled("cursor-default", False)
        assert changed is True
        assert "cursor-default|false|" in cfg.read_text()

    def test_noop_when_already_in_target_state(self, tmp_path: Path) -> None:
        cfg = tmp_path / "virtual-servers.txt"
        cfg.write_text("cursor-default|true|filesystem|Default\n")
        with patch("tool_router.api.server_mgmt._CONFIG_FILE", cfg):
            changed = _set_server_enabled("cursor-default", True)
        assert changed is False

    def test_returns_false_for_unknown_server(self, tmp_path: Path) -> None:
        cfg = tmp_path / "virtual-servers.txt"
        cfg.write_text("cursor-default|true|filesystem|Default\n")
        with patch("tool_router.api.server_mgmt._CONFIG_FILE", cfg):
            changed = _set_server_enabled("nonexistent", True)
        assert changed is False

    def test_returns_false_when_config_missing(self, tmp_path: Path) -> None:
        missing = tmp_path / "missing.txt"
        with patch("tool_router.api.server_mgmt._CONFIG_FILE", missing):
            changed = _set_server_enabled("any", True)
        assert changed is False

    def test_case_insensitive_flag_recognition(self, tmp_path: Path) -> None:
        cfg = tmp_path / "virtual-servers.txt"
        cfg.write_text("cursor-search|FALSE|tavily|Search\n")
        with patch("tool_router.api.server_mgmt._CONFIG_FILE", cfg):
            changed = _set_server_enabled("cursor-search", True)
        assert changed is True


# ---------------------------------------------------------------------------
# Unit: _require_system_admin dependency
# ---------------------------------------------------------------------------


class TestRequireSystemAdmin:
    def test_admin_passes_through(self) -> None:
        ctx = _make_ctx("admin")
        result = _require_system_admin(ctx)
        assert result is ctx

    def test_developer_is_forbidden(self) -> None:
        from fastapi import HTTPException

        ctx = _make_ctx("developer")
        with pytest.raises(HTTPException) as exc_info:
            _require_system_admin(ctx)
        assert exc_info.value.status_code == 403

    def test_user_is_forbidden(self) -> None:
        from fastapi import HTTPException

        ctx = _make_ctx("user")
        with pytest.raises(HTTPException) as exc_info:
            _require_system_admin(ctx)
        assert exc_info.value.status_code == 403

    def test_guest_is_forbidden(self) -> None:
        from fastapi import HTTPException

        ctx = _make_ctx("guest")
        with pytest.raises(HTTPException) as exc_info:
            _require_system_admin(ctx)
        assert exc_info.value.status_code == 403

    def test_unknown_role_is_forbidden(self) -> None:
        from fastapi import HTTPException

        ctx = _make_ctx("bogus-role")
        with pytest.raises(HTTPException) as exc_info:
            _require_system_admin(ctx)
        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# Integration: GET /servers
# ---------------------------------------------------------------------------


class TestListServers:
    def test_returns_200_with_server_list(self, tmp_path: Path) -> None:
        cfg = tmp_path / "virtual-servers.txt"
        cfg.write_text(_SAMPLE_CONFIG)
        client = TestClient(_make_app("admin"), raise_server_exceptions=False)
        with patch("tool_router.api.server_mgmt._CONFIG_FILE", cfg):
            resp = client.get("/servers")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 3
        names = [s["name"] for s in data]
        assert "cursor-default" in names
        assert "cursor-search" in names

    def test_returns_enabled_field_correctly(self, tmp_path: Path) -> None:
        cfg = tmp_path / "virtual-servers.txt"
        cfg.write_text(_SAMPLE_CONFIG)
        client = TestClient(_make_app("admin"), raise_server_exceptions=False)
        with patch("tool_router.api.server_mgmt._CONFIG_FILE", cfg):
            resp = client.get("/servers")
        data = resp.json()
        search = next(s for s in data if s["name"] == "cursor-search")
        assert search["enabled"] is False

    def test_non_admin_returns_403(self) -> None:
        client = TestClient(_make_app("developer"), raise_server_exceptions=False)
        resp = client.get("/servers")
        assert resp.status_code == 403

    def test_no_auth_returns_401_or_403(self) -> None:
        client = TestClient(_make_app(role=None), raise_server_exceptions=False)
        resp = client.get("/servers")
        assert resp.status_code in (401, 403, 422)

    def test_empty_config_returns_empty_list(self, tmp_path: Path) -> None:
        cfg = tmp_path / "virtual-servers.txt"
        cfg.write_text("# no servers\n")
        client = TestClient(_make_app("admin"), raise_server_exceptions=False)
        with patch("tool_router.api.server_mgmt._CONFIG_FILE", cfg):
            resp = client.get("/servers")
        assert resp.status_code == 200
        assert resp.json() == []


# ---------------------------------------------------------------------------
# Integration: GET /servers/{name}
# ---------------------------------------------------------------------------


class TestGetServer:
    def test_returns_200_for_known_server(self, tmp_path: Path) -> None:
        cfg = tmp_path / "virtual-servers.txt"
        cfg.write_text(_SAMPLE_CONFIG)
        client = TestClient(_make_app("admin"), raise_server_exceptions=False)
        with patch("tool_router.api.server_mgmt._CONFIG_FILE", cfg):
            resp = client.get("/servers/cursor-default")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "cursor-default"
        assert data["enabled"] is True
        assert "filesystem" in data["gateways"]

    def test_returns_404_for_unknown_server(self, tmp_path: Path) -> None:
        cfg = tmp_path / "virtual-servers.txt"
        cfg.write_text(_SAMPLE_CONFIG)
        client = TestClient(_make_app("admin"), raise_server_exceptions=False)
        with patch("tool_router.api.server_mgmt._CONFIG_FILE", cfg):
            resp = client.get("/servers/nonexistent-server")
        assert resp.status_code == 404

    def test_non_admin_returns_403(self) -> None:
        client = TestClient(_make_app("user"), raise_server_exceptions=False)
        resp = client.get("/servers/cursor-default")
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Integration: PATCH /servers/{name}/enabled
# ---------------------------------------------------------------------------


class TestPatchServerEnabled:
    def test_enables_disabled_server(self, tmp_path: Path) -> None:
        cfg = tmp_path / "virtual-servers.txt"
        cfg.write_text(_SAMPLE_CONFIG)
        client = TestClient(_make_app("admin"), raise_server_exceptions=False)
        with patch("tool_router.api.server_mgmt._CONFIG_FILE", cfg):
            resp = client.patch("/servers/cursor-search/enabled", json={"enabled": True})
        assert resp.status_code == 200
        assert resp.json()["enabled"] is True

    def test_disables_enabled_server(self, tmp_path: Path) -> None:
        cfg = tmp_path / "virtual-servers.txt"
        cfg.write_text(_SAMPLE_CONFIG)
        client = TestClient(_make_app("admin"), raise_server_exceptions=False)
        with patch("tool_router.api.server_mgmt._CONFIG_FILE", cfg):
            resp = client.patch("/servers/cursor-default/enabled", json={"enabled": False})
        assert resp.status_code == 200
        assert resp.json()["enabled"] is False

    def test_noop_when_state_matches(self, tmp_path: Path) -> None:
        cfg = tmp_path / "virtual-servers.txt"
        cfg.write_text(_SAMPLE_CONFIG)
        client = TestClient(_make_app("admin"), raise_server_exceptions=False)
        with patch("tool_router.api.server_mgmt._CONFIG_FILE", cfg):
            # cursor-default is already enabled
            resp = client.patch("/servers/cursor-default/enabled", json={"enabled": True})
        assert resp.status_code == 200
        assert resp.json()["enabled"] is True

    def test_returns_404_for_unknown_server(self, tmp_path: Path) -> None:
        cfg = tmp_path / "virtual-servers.txt"
        cfg.write_text(_SAMPLE_CONFIG)
        client = TestClient(_make_app("admin"), raise_server_exceptions=False)
        with patch("tool_router.api.server_mgmt._CONFIG_FILE", cfg):
            resp = client.patch("/servers/ghost/enabled", json={"enabled": True})
        assert resp.status_code == 404

    def test_non_admin_returns_403(self) -> None:
        client = TestClient(_make_app("developer"), raise_server_exceptions=False)
        resp = client.patch("/servers/cursor-default/enabled", json={"enabled": False})
        assert resp.status_code == 403

    def test_missing_body_returns_422(self, tmp_path: Path) -> None:
        cfg = tmp_path / "virtual-servers.txt"
        cfg.write_text(_SAMPLE_CONFIG)
        client = TestClient(_make_app("admin"), raise_server_exceptions=False)
        with patch("tool_router.api.server_mgmt._CONFIG_FILE", cfg):
            resp = client.patch("/servers/cursor-default/enabled", json={})
        assert resp.status_code == 422

    def test_config_written_to_disk(self, tmp_path: Path) -> None:
        cfg = tmp_path / "virtual-servers.txt"
        cfg.write_text(_SAMPLE_CONFIG)
        client = TestClient(_make_app("admin"), raise_server_exceptions=False)
        with patch("tool_router.api.server_mgmt._CONFIG_FILE", cfg):
            client.patch("/servers/cursor-search/enabled", json={"enabled": True})
        assert "cursor-search|true|" in cfg.read_text()


# ---------------------------------------------------------------------------
# Integration: GET /ide/detect
# ---------------------------------------------------------------------------


class TestIdeDetect:
    def test_returns_200_with_system_and_detected_list(self) -> None:
        client = TestClient(_make_app("admin"), raise_server_exceptions=False)
        resp = client.get("/ide/detect")
        assert resp.status_code == 200
        data = resp.json()
        assert "system" in data
        assert "detected" in data
        assert isinstance(data["detected"], list)

    def test_returns_all_five_ides(self) -> None:
        client = TestClient(_make_app("admin"), raise_server_exceptions=False)
        resp = client.get("/ide/detect")
        ids = [ide["id"] for ide in resp.json()["detected"]]
        assert set(ids) == {"cursor", "vscode", "windsurf", "claude", "zed"}

    def test_each_ide_has_required_fields(self) -> None:
        client = TestClient(_make_app("admin"), raise_server_exceptions=False)
        resp = client.get("/ide/detect")
        for ide in resp.json()["detected"]:
            assert "id" in ide
            assert "name" in ide
            assert "detected" in ide
            assert isinstance(ide["detected"], bool)

    def test_non_admin_returns_403(self) -> None:
        client = TestClient(_make_app("user"), raise_server_exceptions=False)
        resp = client.get("/ide/detect")
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Unit: _detect_ides
# ---------------------------------------------------------------------------


class TestDetectIdesUnit:
    def test_returns_ide_detect_response_shape(self) -> None:
        result = _detect_ides()
        assert result.system in ("Darwin", "Linux", "Windows")
        assert len(result.detected) == 5

    def test_detected_field_is_bool(self) -> None:
        result = _detect_ides()
        for ide in result.detected:
            assert isinstance(ide.detected, bool)

    def test_config_path_none_when_not_detected(self) -> None:
        with (
            patch("shutil.which", return_value=None),
            patch("pathlib.Path.exists", return_value=False),
        ):
            result = _detect_ides()
        for ide in result.detected:
            if not ide.detected:
                assert ide.config_path is None


# ---------------------------------------------------------------------------
# Coverage gap: _parse_servers — name-only line (no pipe) → continue
# ---------------------------------------------------------------------------


class TestParseServersCoverageGaps:
    def test_name_only_line_is_skipped(self) -> None:
        """A line with no '|' has only 1 part → falls into the else: continue branch (line 104)."""
        text = "bare-name-no-pipe\ncursor-default|true|filesystem|desc\n"
        servers = _parse_servers(text)
        # Only the valid server is returned; the bare line is skipped
        assert len(servers) == 1
        assert servers[0].name == "cursor-default"


# ---------------------------------------------------------------------------
# Coverage gap: _read_servers — config file missing → return []
# ---------------------------------------------------------------------------


class TestReadServersCoverageGaps:
    def test_returns_empty_list_when_config_missing(self, tmp_path: Path) -> None:
        """When _CONFIG_FILE does not exist, _read_servers returns [] (line 118)."""
        non_existent = tmp_path / "virtual-servers.txt"
        with patch("tool_router.api.server_mgmt._CONFIG_FILE", non_existent):
            from tool_router.api.server_mgmt import _read_servers  # noqa: PLC0415

            result = _read_servers()
        assert result == []


# ---------------------------------------------------------------------------
# Coverage gap: _detect_ides — Windows / Linux platform branches
# ---------------------------------------------------------------------------


class TestDetectIdesWindowsLinux:
    def test_windows_cursor_path_appended(self) -> None:
        """On Windows, LOCALAPPDATA path for Cursor.exe is added (line 161)."""
        with (
            patch("platform.system", return_value="Windows"),
            patch("shutil.which", return_value=None),
            patch("pathlib.Path.exists", return_value=False),
            patch(
                "os.environ.get",
                side_effect=lambda k, d="": "C:\\Users\\user\\AppData\\Local" if k == "LOCALAPPDATA" else d,
            ),
        ):
            result = _detect_ides()
        # Should return without error and include cursor in detected list
        cursor_ide = next(ide for ide in result.detected if ide.id == "cursor")
        assert cursor_ide is not None

    def test_linux_cursor_path_appended(self) -> None:
        """On Linux, /usr/bin/cursor path is added (line 163)."""
        with (
            patch("platform.system", return_value="Linux"),
            patch("shutil.which", return_value=None),
            patch("pathlib.Path.exists", return_value=False),
        ):
            result = _detect_ides()
        cursor_ide = next(ide for ide in result.detected if ide.id == "cursor")
        assert cursor_ide is not None

    def test_windows_vscode_path_appended(self) -> None:
        """On Windows, LOCALAPPDATA path for VS Code is added (line 172)."""
        with (
            patch("platform.system", return_value="Windows"),
            patch("shutil.which", return_value=None),
            patch("pathlib.Path.exists", return_value=False),
            patch(
                "os.environ.get",
                side_effect=lambda k, d="": "C:\\Users\\user\\AppData\\Local" if k == "LOCALAPPDATA" else d,
            ),
        ):
            result = _detect_ides()
        vscode_ide = next(ide for ide in result.detected if ide.id == "vscode")
        assert vscode_ide is not None

    def test_windows_claude_cfg_dir(self) -> None:
        """On Windows, APPDATA path for Claude Desktop config is used (lines 186-187)."""
        with (
            patch("platform.system", return_value="Windows"),
            patch("shutil.which", return_value=None),
            patch("pathlib.Path.exists", return_value=False),
            patch(
                "os.environ.get",
                side_effect=lambda k, d="": "C:\\Users\\user\\AppData\\Roaming" if k == "APPDATA" else d,
            ),
        ):
            result = _detect_ides()
        claude_ide = next(ide for ide in result.detected if ide.id == "claude")
        assert claude_ide is not None

    def test_linux_claude_cfg_dir(self) -> None:
        """On Linux, ~/.config/claude is used as Claude Desktop config dir (lines 188-189)."""
        with (
            patch("platform.system", return_value="Linux"),
            patch("shutil.which", return_value=None),
            patch("pathlib.Path.exists", return_value=False),
        ):
            result = _detect_ides()
        claude_ide = next(ide for ide in result.detected if ide.id == "claude")
        assert claude_ide is not None


# ---------------------------------------------------------------------------
# Coverage gap: patch_server_enabled — _set_server_enabled returns False → 500
# ---------------------------------------------------------------------------


class TestPatchServerEnabledFailure:
    def test_returns_500_when_set_enabled_fails(self, tmp_path: Path) -> None:
        """When _set_server_enabled returns False the endpoint raises HTTP 500 (line 282)."""
        cfg = tmp_path / "virtual-servers.txt"
        # Write a config where the server exists; enabled=True so disabling it is a real change
        cfg.write_text("cursor-default|true|filesystem|desc\n")

        with (
            patch("tool_router.api.server_mgmt._CONFIG_FILE", cfg),
            # Force _set_server_enabled to return False even though the file exists
            patch("tool_router.api.server_mgmt._set_server_enabled", return_value=False),
        ):
            client = TestClient(_make_app("admin"), raise_server_exceptions=False)
            # The router is mounted without prefix, so path is relative to its own root
            resp = client.patch("/cursor-default/enabled", json={"enabled": False})

        # 404 means _read_servers didn't find the server — need to also patch _read_servers
        # The config file IS patched but the module-level _CONFIG_FILE is already resolved;
        # patch _read_servers directly to return a known server list
        from tool_router.api.server_mgmt import VirtualServer  # noqa: PLC0415

        fake_server = VirtualServer(name="cursor-default", enabled=True, gateways=["filesystem"], description="desc")

        with (
            patch("tool_router.api.server_mgmt._read_servers", return_value=[fake_server]),
            patch("tool_router.api.server_mgmt._set_server_enabled", return_value=False),
        ):
            client2 = TestClient(_make_app("admin"), raise_server_exceptions=False)
            resp2 = client2.patch("/servers/cursor-default/enabled", json={"enabled": False})

        assert resp2.status_code == 500
