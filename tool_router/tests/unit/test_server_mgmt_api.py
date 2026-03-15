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
