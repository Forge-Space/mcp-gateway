#!/usr/bin/env python3
"""Virtual server management utility.

Phase 1: Virtual Server Lifecycle (FR-2)

Commands:
  list               Show all servers with enabled/disabled status
  enable <name>      Enable a server (sets enabled=true)
  disable <name>     Disable a server (sets enabled=false)
  status <name>      Show status of a specific server

The config/virtual-servers.txt format:
  name|enabled|gateways|description

The enabled field supports: true/false, 1/0, yes/no (case-insensitive).
After enabling or disabling a server run 'make register' to apply changes.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


CONFIG_FILE = Path(__file__).parent.parent.parent / "config" / "virtual-servers.txt"


def _is_enabled(flag: str) -> bool:
    return flag.strip().lower() in ("true", "1", "yes")


def _parse_servers(text: str) -> list[dict]:
    servers = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split("|")
        name = parts[0]
        if len(parts) >= 4:
            enabled = parts[1]
            gateways = parts[2]
            description = parts[3]
        elif len(parts) >= 2:
            # Legacy format: name|gateways
            enabled = "true"
            gateways = parts[1]
            description = parts[2] if len(parts) >= 3 else ""
        else:
            continue
        servers.append(
            {
                "name": name,
                "enabled": enabled,
                "gateways": gateways,
                "description": description,
            }
        )
    return servers


def cmd_list() -> int:
    """List all servers with their status."""
    text = CONFIG_FILE.read_text()
    servers = _parse_servers(text)
    if not servers:
        print("No servers found in", CONFIG_FILE)
        return 1

    enabled_count = sum(1 for s in servers if _is_enabled(s["enabled"]))
    disabled_count = len(servers) - enabled_count

    print(f"Virtual servers ({CONFIG_FILE.name}):\n")
    for s in servers:
        icon = "✅" if _is_enabled(s["enabled"]) else "❌"
        suffix = " (disabled)" if not _is_enabled(s["enabled"]) else ""
        print(f"  {icon} {s['name']:<30} {s['description']}{suffix}")
    print(f"\n  {enabled_count} enabled, {disabled_count} disabled")
    print("\nTo enable:  make enable-server SERVER=<name>")
    print("To disable: make disable-server SERVER=<name>")
    print("To apply:   make register")
    return 0


def cmd_enable(name: str) -> int:
    """Enable a server by name."""
    text = CONFIG_FILE.read_text()
    if not re.search(r"^" + re.escape(name) + r"\|", text, re.MULTILINE):
        print(f"❌ Server '{name}' not found in {CONFIG_FILE.name}")
        print("Run 'make list-servers' to see available servers.")
        return 1

    new_text = re.sub(
        r"^(" + re.escape(name) + r"\|)(false|0|no)(\|)",
        r"\1true\3",
        text,
        flags=re.MULTILINE | re.IGNORECASE,
    )
    if new_text == text:
        print(f"ℹ️  Server '{name}' is already enabled.")
        return 0

    CONFIG_FILE.write_text(new_text)
    print(f"✅ Enabled '{name}'. Run 'make register' to apply changes.")
    return 0


def cmd_disable(name: str) -> int:
    """Disable a server by name."""
    text = CONFIG_FILE.read_text()
    if not re.search(r"^" + re.escape(name) + r"\|", text, re.MULTILINE):
        print(f"❌ Server '{name}' not found in {CONFIG_FILE.name}")
        print("Run 'make list-servers' to see available servers.")
        return 1

    new_text = re.sub(
        r"^(" + re.escape(name) + r"\|)(true|1|yes)(\|)",
        r"\1false\3",
        text,
        flags=re.MULTILINE | re.IGNORECASE,
    )
    if new_text == text:
        print(f"ℹ️  Server '{name}' is already disabled.")
        return 0

    CONFIG_FILE.write_text(new_text)
    print(f"✅ Disabled '{name}'. Run 'make register' to apply changes.")
    return 0


def cmd_status(name: str) -> int:
    """Show status of a specific server."""
    text = CONFIG_FILE.read_text()
    servers = _parse_servers(text)
    for s in servers:
        if s["name"] == name:
            status = "enabled" if _is_enabled(s["enabled"]) else "disabled"
            icon = "✅" if _is_enabled(s["enabled"]) else "❌"
            print(f"{icon} {s['name']}: {status}")
            print(f"   Gateways:    {s['gateways']}")
            print(f"   Description: {s['description']}")
            return 0
    print(f"❌ Server '{name}' not found.")
    return 1


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1

    command = args[0].lower()
    if command == "list":
        return cmd_list()
    if command == "enable":
        if len(args) < 2:
            print("Usage: manage-servers.py enable <name>")
            return 1
        return cmd_enable(args[1])
    if command == "disable":
        if len(args) < 2:
            print("Usage: manage-servers.py disable <name>")
            return 1
        return cmd_disable(args[1])
    if command == "status":
        if len(args) < 2:
            print("Usage: manage-servers.py status <name>")
            return 1
        return cmd_status(args[1])

    print(f"Unknown command: {command}")
    print("Available commands: list, enable, disable, status")
    return 1


if __name__ == "__main__":
    sys.exit(main())
