#!/usr/bin/env python3
"""
Toggle virtual server enabled status in YAML configuration.
Updates the virtual-servers-enhanced.yml file to enable or disable servers.
"""
import os
import sys
import yaml
from pathlib import Path
from typing import Dict, Any

# Get script directory — all paths are derived from this trusted constant.
SCRIPT_DIR = Path(__file__).parent.parent
REPO_ROOT = SCRIPT_DIR.parent
CONFIG_DIR = REPO_ROOT / "config"
VIRTUAL_SERVERS_FILE = CONFIG_DIR / "virtual-servers-enhanced.yml"

def load_config() -> Dict[str, Any]:
    """Load the virtual server configuration from YAML file."""
    if not VIRTUAL_SERVERS_FILE.exists():
        print(f"Error: {VIRTUAL_SERVERS_FILE} not found", file=sys.stderr)
        print("Create it first with: make register-enhanced", file=sys.stderr)
        sys.exit(1)

    try:
        with open(VIRTUAL_SERVERS_FILE, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Error loading configuration: {e}", file=sys.stderr)
        sys.exit(1)

def save_config(config: Dict[str, Any]) -> None:
    """Save the virtual server configuration to YAML file."""
    try:
        with open(VIRTUAL_SERVERS_FILE, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        print(f"Configuration saved to {VIRTUAL_SERVERS_FILE}")
    except Exception as e:
        print(f"Error saving configuration: {e}", file=sys.stderr)
        sys.exit(1)

def list_servers(config: Dict[str, Any]) -> None:
    """List all virtual servers and their enabled status."""
    virtual_servers = config.get('virtual_servers', {})

    if not virtual_servers:
        print("No virtual servers configured")
        return

    print("\nVirtual Server Status:")
    print("=" * 60)
    print(f"{'Server Name':<30} {'Status':<10} {'Gateways':<20}")
    print("-" * 60)

    for name, server_config in virtual_servers.items():
        enabled = server_config.get('enabled', True)
        gateways = server_config.get('gateways', [])
        gateway_count = len(gateways) if isinstance(gateways, list) else 1 if gateways else 0

        status = "✓ Enabled" if enabled else "○ Disabled"
        gateway_text = f"{gateway_count} gateway{'s' if gateway_count != 1 else ''}"

        print(f"{name:<30} {status:<10} {gateway_text:<20}")

    print("-" * 60)
    print(f"Total: {len(virtual_servers)} servers")

def toggle_server(config: Dict[str, Any], server_name: str, enabled: bool) -> bool:
    """Toggle a virtual server's enabled status."""
    virtual_servers = config.get('virtual_servers', {})

    if server_name not in virtual_servers:
        print(f"Error: Virtual server '{server_name}' not found", file=sys.stderr)
        print("Available servers:")
        for name in virtual_servers.keys():
            print(f"  - {name}")
        return False

    old_status = virtual_servers[server_name].get('enabled', True)
    virtual_servers[server_name]['enabled'] = enabled

    action = "enabled" if enabled else "disabled"
    old_action = "enabled" if old_status else "disabled"

    if old_status == enabled:
        print(f"Virtual server '{server_name}' was already {old_action}")
    else:
        print(f"Virtual server '{server_name}' {action} (was {old_action})")

    return True

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 toggle-server.py list                    # List all servers")
        print("  python3 toggle-server.py enable <server-name>    # Enable a server")
        print("  python3 toggle-server.py disable <server-name>   # Disable a server")
        sys.exit(1)

    command = sys.argv[1].lower()

    # Load configuration
    config = load_config()

    if command == "list":
        list_servers(config)
    elif command == "enable":
        if len(sys.argv) < 3:
            print("Error: Server name required", file=sys.stderr)
            print("Usage: python3 toggle-server.py enable <server-name>", file=sys.stderr)
            sys.exit(1)

        server_name = sys.argv[2]
        if toggle_server(config, server_name, True):
            save_config(config)
            print(f"\nRun 'make register-enhanced' to apply changes")
        else:
            sys.exit(1)

    elif command == "disable":
        if len(sys.argv) < 3:
            print("Error: Server name required", file=sys.stderr)
            print("Usage: python3 toggle-server.py disable <server-name>", file=sys.stderr)
            sys.exit(1)

        server_name = sys.argv[2]
        if toggle_server(config, server_name, False):
            save_config(config)
            print(f"\nRun 'make register-enhanced' to apply changes")
        else:
            sys.exit(1)

    else:
        print(f"Error: Unknown command '{command}'", file=sys.stderr)
        print("Available commands: list, enable, disable", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
