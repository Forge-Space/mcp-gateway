"""Server lifecycle management API endpoints."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any


# Cross-platform file locking
try:
    import fcntl
    from typing import IO

    def lock_file(file_obj: IO[bytes], timeout: float = 5.0) -> bool:
        """Acquire exclusive lock with timeout (Unix)."""
        start_time = time.time()
        while True:
            try:
                fcntl.flock(file_obj.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
            except OSError:
                if time.time() - start_time >= timeout:
                    return False
                time.sleep(0.1)

    def unlock_file(file_obj: IO[bytes]) -> None:
        """Release file lock (Unix)."""
        fcntl.flock(file_obj.fileno(), fcntl.LOCK_UN)

except ImportError:
    # Windows fallback using msvcrt
    if sys.platform == "win32":
        import msvcrt

        def lock_file(file_obj: IO[bytes], timeout: float = 5.0) -> bool:
            """Acquire exclusive lock with timeout (Windows)."""
            start_time = time.time()
            while True:
                try:
                    msvcrt.locking(file_obj.fileno(), msvcrt.LK_NBLCK, 1)
                    return True
                except OSError:
                    if time.time() - start_time >= timeout:
                        return False
                    time.sleep(0.1)

        def unlock_file(file_obj: IO[bytes]) -> None:
            """Release file lock (Windows)."""
            msvcrt.locking(file_obj.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        # No locking available
        def lock_file(file_obj: IO[bytes], timeout: float = 5.0) -> bool:  # noqa: ARG001
            """No-op lock for unsupported platforms."""
            return True

        def unlock_file(file_obj: IO[bytes]) -> None:
            """No-op unlock for unsupported platforms."""


def get_virtual_servers_file() -> Path:
    """Get path to virtual-servers.txt configuration file."""
    repo_root = Path(__file__).parent.parent.parent
    config_dir_str = os.environ.get("CONFIG_DIR", str(repo_root / "config"))
    config_dir = Path(config_dir_str)
    return config_dir / "virtual-servers.txt"


def parse_server_line(line: str) -> dict[str, Any] | None:
    """Parse a line from virtual-servers.txt.

    Format: Name|gateways|enabled

    Args:
        line: A line from the configuration file in format "Name|gateways|enabled"

    Returns:
        Dictionary with keys "name" (str), "gateways" (list[str]), and "enabled" (bool),
        or None if the line is invalid, empty, or a comment.
    """
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    parts = line.split("|")
    if len(parts) < 2:
        return None

    name = parts[0].strip()
    gateways = [g.strip() for g in parts[1].split(",")]

    # Parse enabled flag (default true)
    enabled = True
    if len(parts) >= 3:
        enabled_flag = parts[2].strip().lower()
        enabled = enabled_flag != "false"

    return {
        "name": name,
        "gateways": gateways,
        "enabled": enabled,
    }


def list_virtual_servers() -> dict[str, Any]:
    """List all virtual servers with their status.

    Returns:
        Dict with servers list and summary statistics.
    """
    config_file = get_virtual_servers_file()

    if not config_file.exists():
        return {
            "servers": [],
            "summary": {
                "total": 0,
                "enabled": 0,
                "disabled": 0,
            },
            "error": f"Configuration file not found: {config_file}",
        }

    servers = []
    enabled_count = 0
    disabled_count = 0

    with config_file.open() as f:
        for line in f:
            server = parse_server_line(line)
            if server:
                servers.append(server)
                if server["enabled"]:
                    enabled_count += 1
                else:
                    disabled_count += 1

    return {
        "servers": servers,
        "summary": {
            "total": len(servers),
            "enabled": enabled_count,
            "disabled": disabled_count,
        },
    }


def get_server_status(server_name: str) -> dict[str, Any]:
    """Get status of a specific virtual server.

    Args:
        server_name: Name of the server to check.

    Returns:
        Dict with server details or error.
    """
    config_file = get_virtual_servers_file()

    if not config_file.exists():
        return {
            "error": f"Configuration file not found: {config_file}",
        }

    with config_file.open() as f:
        for line in f:
            server = parse_server_line(line)
            if server and server["name"] == server_name:
                return {
                    "name": server["name"],
                    "gateways": server["gateways"],
                    "enabled": server["enabled"],
                    "found": True,
                }

    return {
        "error": f"Server '{server_name}' not found",
        "found": False,
    }


def update_server_status(server_name: str, enabled: bool) -> dict[str, Any]:
    """Update the enabled status of a virtual server.

    Args:
        server_name: Name of the server to update.
        enabled: True to enable, False to disable.

    Returns:
        Dict with success status and message.
    """
    config_file = get_virtual_servers_file()

    if not config_file.exists():
        return {
            "success": False,
            "error": f"Configuration file not found: {config_file}",
        }

    # Use file locking for concurrent safety
    with config_file.open("r+") as f:
        # Acquire exclusive lock with timeout
        if not lock_file(f, timeout=5.0):
            return {
                "success": False,
                "error": "Failed to acquire lock on config file (timeout after 5s)",
            }

        try:
            # Read original content for backup
            original_lines = f.readlines()

            # Create backup of original content before any modifications
            backup_file = config_file.with_suffix(".txt.bak")
            if backup_file.exists():
                backup_file.unlink()

            with backup_file.open("w") as backup_f:
                backup_f.writelines(original_lines)

            # Now modify the lines
            lines = original_lines.copy()
            server_found = False
            for i, line in enumerate(lines):
                server = parse_server_line(line)
                if server and server["name"] == server_name:
                    server_found = True
                    # Update enabled status
                    parts = line.strip().split("|")
                    if len(parts) >= 3:
                        parts[2] = str(enabled).lower()
                    else:
                        parts.append(str(enabled).lower())
                    lines[i] = "|".join(parts) + "\n"
                    break

            if not server_found:
                return {
                    "success": False,
                    "error": f"Server '{server_name}' not found",
                }

            # Atomic write: truncate and write updated content
            f.seek(0)
            f.truncate()
            f.writelines(lines)
            f.flush()
            os.fsync(f.fileno())

        finally:
            # Release lock
            unlock_file(f)

    action = "enabled" if enabled else "disabled"
    return {
        "success": True,
        "message": f"Server '{server_name}' {action}",
        "server_name": server_name,
        "enabled": enabled,
    }


def enable_server(server_name: str) -> dict[str, Any]:
    """Enable a virtual server.

    Args:
        server_name: Name of the server to enable.

    Returns:
        Dict with success status and message.
    """
    return update_server_status(server_name, enabled=True)


def disable_server(server_name: str) -> dict[str, Any]:
    """Disable a virtual server.

    Args:
        server_name: Name of the server to disable.

    Returns:
        Dict with success status and message.
    """
    return update_server_status(server_name, enabled=False)
