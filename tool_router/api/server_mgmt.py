"""Virtual server management and IDE detection API endpoints.

Phase 2 remainder:
  GET   /servers              — list all virtual servers with enabled status
  GET   /servers/{name}       — get a single server by name
  PATCH /servers/{name}/enabled — toggle server enabled/disabled
  GET   /ide/detect           — detect installed IDEs on the host system
"""

from __future__ import annotations

import logging
import os
import platform
import re
import shutil
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Path as FastAPIPath
from pydantic import BaseModel

from tool_router.security.authorization import Permission, RBACEvaluator, Role
from tool_router.security.security_middleware import SecurityContext

from .dependencies import get_security_context


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/servers", tags=["Server Management"])
ide_router = APIRouter(prefix="/ide", tags=["IDE Detection"])

_rbac = RBACEvaluator()

_CONFIG_FILE = Path(__file__).parent.parent.parent / "config" / "virtual-servers.txt"


# ── Auth dependency ───────────────────────────────────────────────────────────


def _require_system_admin(
    ctx: Annotated[SecurityContext, Depends(get_security_context)],
) -> SecurityContext:
    """Require SYSTEM_ADMIN permission (admin role only)."""
    role: Role = _rbac.resolve_role(ctx.user_role)
    if not _rbac.check_permission(role, Permission.SYSTEM_ADMIN):
        raise HTTPException(
            status_code=403,
            detail=f"Role '{role.value}' does not have system admin permission.",
        )
    return ctx


# ── Models ────────────────────────────────────────────────────────────────────


class VirtualServer(BaseModel):
    name: str
    enabled: bool
    gateways: list[str]
    description: str


class ServerEnabledPatch(BaseModel):
    enabled: bool


class IDEInfo(BaseModel):
    id: str
    name: str
    detected: bool
    config_path: str | None = None


class IDEDetectResponse(BaseModel):
    system: str
    detected: list[IDEInfo]


# ── Config helpers ────────────────────────────────────────────────────────────


def _is_enabled(flag: str) -> bool:
    return flag.strip().lower() in ("true", "1", "yes")


def _parse_servers(text: str) -> list[VirtualServer]:
    servers: list[VirtualServer] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split("|")
        name = parts[0]
        if len(parts) >= 4:
            enabled_raw, gateways_raw, description = parts[1], parts[2], parts[3]
        elif len(parts) >= 2:
            enabled_raw = "true"
            gateways_raw = parts[1]
            description = parts[2] if len(parts) >= 3 else ""
        else:
            continue
        servers.append(
            VirtualServer(
                name=name,
                enabled=_is_enabled(enabled_raw),
                gateways=[g.strip() for g in gateways_raw.split(",") if g.strip()],
                description=description,
            )
        )
    return servers


def _read_servers() -> list[VirtualServer]:
    if not _CONFIG_FILE.exists():
        return []
    return _parse_servers(_CONFIG_FILE.read_text())


def _set_server_enabled(name: str, enabled: bool) -> bool:
    """Toggle enabled flag in config/virtual-servers.txt. Returns True when file changed."""
    if not _CONFIG_FILE.exists():
        return False
    text = _CONFIG_FILE.read_text()
    if not re.search(r"^" + re.escape(name) + r"\|", text, re.MULTILINE):
        return False

    new_value = "true" if enabled else "false"
    old_pattern = "false|0|no" if enabled else "true|1|yes"

    new_text = re.sub(
        r"^(" + re.escape(name) + r"\|)(" + old_pattern + r")(\|)",
        rf"\g<1>{new_value}\g<3>",
        text,
        flags=re.MULTILINE | re.IGNORECASE,
    )
    if new_text == text:
        return False
    _CONFIG_FILE.write_text(new_text)
    return True


# ── IDE detection helpers ─────────────────────────────────────────────────────


def _detect_ides() -> IDEDetectResponse:
    system = platform.system()

    def _any_exists(*paths: Path | str) -> bool:
        return any(Path(p).exists() for p in paths)

    # Cursor
    cursor_paths = [
        Path("/Applications/Cursor.app"),
        Path("~/Applications/Cursor.app").expanduser(),
        Path("~/.cursor").expanduser(),
    ]
    if system == "Windows":
        cursor_paths.append(Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "cursor" / "Cursor.exe")
    elif system == "Linux":
        cursor_paths.append(Path("/usr/bin/cursor"))
    cursor_detected = _any_exists(*cursor_paths) or bool(shutil.which("cursor"))

    # VSCode
    vscode_paths = [
        Path("/Applications/Visual Studio Code.app"),
        Path("/Applications/VSCode.app"),
    ]
    if system == "Windows":
        vscode_paths.append(Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Microsoft VS Code" / "Code.exe")
    vscode_detected = _any_exists(*vscode_paths) or bool(shutil.which("code")) or bool(shutil.which("code-insiders"))

    # Windsurf
    windsurf_paths = [
        Path("/Applications/Windsurf.app"),
        Path("~/Applications/Windsurf.app").expanduser(),
        Path("~/.windsurf").expanduser(),
    ]
    windsurf_detected = _any_exists(*windsurf_paths) or bool(shutil.which("windsurf"))

    # Claude Desktop
    if system == "Darwin":
        claude_cfg_dir = Path("~/Library/Application Support/Claude").expanduser()
    elif system == "Windows":
        claude_cfg_dir = Path(os.environ.get("APPDATA", "")) / "Claude"
    else:
        claude_cfg_dir = Path("~/.config/claude").expanduser()
    claude_detected = claude_cfg_dir.exists()

    # Zed
    zed_paths = [
        Path("/Applications/Zed.app"),
        Path("~/Applications/Zed.app").expanduser(),
        Path("~/.config/zed").expanduser(),
    ]
    zed_detected = _any_exists(*zed_paths) or bool(shutil.which("zed"))

    ides = [
        IDEInfo(
            id="cursor",
            name="Cursor",
            detected=cursor_detected,
            config_path=str(Path("~/.cursor/mcp.json").expanduser()) if cursor_detected else None,
        ),
        IDEInfo(id="vscode", name="VSCode", detected=vscode_detected),
        IDEInfo(
            id="windsurf",
            name="Windsurf",
            detected=windsurf_detected,
            config_path=str(Path("~/.windsurf/mcp.json").expanduser()) if windsurf_detected else None,
        ),
        IDEInfo(
            id="claude",
            name="Claude Desktop",
            detected=claude_detected,
            config_path=str(claude_cfg_dir / "claude_desktop_config.json") if claude_detected else None,
        ),
        IDEInfo(
            id="zed",
            name="Zed",
            detected=zed_detected,
            config_path=str(Path("~/.config/zed/settings.json").expanduser()) if zed_detected else None,
        ),
    ]
    return IDEDetectResponse(system=system, detected=ides)


# ── Routes ────────────────────────────────────────────────────────────────────


@router.get("", response_model=list[VirtualServer], summary="List virtual servers")
async def list_servers(
    _ctx: Annotated[SecurityContext, Depends(_require_system_admin)],
) -> list[VirtualServer]:
    """Return all virtual servers with their enabled status and gateway assignments."""
    return _read_servers()


@router.get(
    "/{name}",
    response_model=VirtualServer,
    summary="Get a virtual server by name",
)
async def get_server(
    name: Annotated[str, FastAPIPath(description="Server name")],
    _ctx: Annotated[SecurityContext, Depends(_require_system_admin)],
) -> VirtualServer:
    """Return a single virtual server configuration."""
    servers = _read_servers()
    for server in servers:
        if server.name == name:
            return server
    raise HTTPException(status_code=404, detail=f"Server '{name}' not found")


@router.patch(
    "/{name}/enabled",
    response_model=VirtualServer,
    summary="Enable or disable a virtual server",
)
async def patch_server_enabled(
    name: Annotated[str, FastAPIPath(description="Server name")],
    body: ServerEnabledPatch,
    _ctx: Annotated[SecurityContext, Depends(_require_system_admin)],
) -> VirtualServer:
    """Toggle the enabled flag for a virtual server in config/virtual-servers.txt.

    After enabling or disabling, run ``make register`` to apply changes to the gateway.
    """
    servers = _read_servers()
    target = next((s for s in servers if s.name == name), None)
    if target is None:
        raise HTTPException(status_code=404, detail=f"Server '{name}' not found")

    if target.enabled == body.enabled:
        return target

    changed = _set_server_enabled(name, body.enabled)
    if not changed:
        raise HTTPException(status_code=500, detail="Failed to update server config")

    logger.info("server_enabled_changed server=%s enabled=%s", name, body.enabled)
    return VirtualServer(
        name=target.name,
        enabled=body.enabled,
        gateways=target.gateways,
        description=target.description,
    )


@ide_router.get("/detect", response_model=IDEDetectResponse, summary="Detect installed IDEs")
async def detect_ides(
    _ctx: Annotated[SecurityContext, Depends(_require_system_admin)],
) -> IDEDetectResponse:
    """Detect which IDEs are installed on the host system and return their config paths."""
    return _detect_ides()
