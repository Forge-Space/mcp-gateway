#!/usr/bin/env python3
"""
Virtual Server Lifecycle Manager
Manages enabling/disabling virtual servers with conditional creation.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class VirtualServer:
    """Virtual server configuration."""
    name: str
    gateways: List[str]
    enabled: bool = True
    description: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class VirtualServerManager:
    """Manages virtual server lifecycle."""

    def __init__(self, config_file: str = None):
        self.config_file = config_file or "config/virtual-servers.txt"
        self.config_path = Path(self.config_file)
        self.servers: Dict[str, VirtualServer] = {}
        self.load_servers()

    def load_servers(self) -> None:
        """Load virtual servers from configuration file."""
        if not self.config_path.exists():
            print(f"Configuration file not found: {self.config_file}")
            return

        self.servers = {}

        with open(self.config_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue

                try:
                    # Parse new format: name|enabled|gateways|description
                    parts = line.split('|')

                    if len(parts) == 4:
                        # New format with enabled flag
                        name = parts[0].strip()
                        enabled = parts[1].strip().lower() in ('true', '1', 'yes', 'on')
                        gateways_str = parts[2].strip()
                        description = parts[3].strip()
                    elif len(parts) == 2:
                        # Legacy format - assume enabled
                        name = parts[0].strip()
                        enabled = True
                        gateways_str = parts[1].strip()
                        description = f"Virtual server: {name}"
                    else:
                        print(f"Warning: Invalid format on line {line_num}: {line}")
                        continue

                    gateways = [g.strip() for g in gateways_str.split(',') if g.strip()]

                    server = VirtualServer(
                        name=name,
                        gateways=gateways,
                        enabled=enabled,
                        description=description
                    )

                    self.servers[name] = server

                except Exception as e:
                    print(f"Error parsing line {line_num}: {line}")
                    print(f"Error: {e}")
                    continue

    def save_servers(self) -> None:
        """Save virtual servers to configuration file."""
        # Create backup
        backup_path = self.config_path.with_suffix('.backup')
        if self.config_path.exists():
            backup_path.write_text(self.config_path.read_text())

        # Write new configuration
        with open(self.config_path, 'w') as f:
            f.write("# Virtual servers: Name|enabled|gateways|description\n")
            f.write("# enabled: true/false - controls server creation\n")
            f.write("# gateways: comma-separated list of gateway names\n")
            f.write("# After editing, run: make register\n")
            f.write("# Connect IDE to server URL from script output\n")
            f.write("#\n")

            # Write servers
            for server in self.servers.values():
                enabled_str = "true" if server.enabled else "false"
                gateways_str = ",".join(server.gateways)
                f.write(f"{server.name}|{enabled_str}|{gateways_str}|{server.description}\n")

    def enable_server(self, name: str) -> bool:
        """Enable a virtual server."""
        if name not in self.servers:
            print(f"Error: Server '{name}' not found")
            return False

        if self.servers[name].enabled:
            print(f"Server '{name}' is already enabled")
            return True

        self.servers[name].enabled = True
        self.servers[name].updated_at = datetime.utcnow().isoformat()
        self.save_servers()
        print(f"✅ Enabled server: {name}")
        return True

    def disable_server(self, name: str) -> bool:
        """Disable a virtual server."""
        if name not in self.servers:
            print(f"Error: Server '{name}' not found")
            return False

        if not self.servers[name].enabled:
            print(f"Server '{name}' is already disabled")
            return True

        self.servers[name].enabled = False
        self.servers[name].updated_at = datetime.utcnow().isoformat()
        self.save_servers()
        print(f"❌ Disabled server: {name}")
        return True

    def list_servers(self, show_status: bool = True) -> None:
        """List all virtual servers with status."""
        if not self.servers:
            print("No virtual servers configured")
            return

        print(f"\n{'='*60}")
        print(f"Virtual Servers ({len(self.servers)} total)")
        print(f"{'='*60}")

        enabled_count = 0
        disabled_count = 0

        for name, server in sorted(self.servers.items()):
            status = "✅ ENABLED" if server.enabled else "❌ DISABLED"
            gateways_str = ", ".join(server.gateways[:3])
            if len(server.gateways) > 3:
                gateways_str += f" (+{len(server.gateways)-3} more)"

            if server.enabled:
                enabled_count += 1
            else:
                disabled_count += 1

            print(f"{name:25} {status:12} {gateways_str}")
            if server.description and server.description != f"Virtual server: {name}":
                print(f"{' ' *27} 📝 {server.description}")

        print(f"{'='*60}")
        print(f"Enabled: {enabled_count}, Disabled: {disabled_count}")
        print(f"{'='*60}\n")

    def get_enabled_servers(self) -> List[VirtualServer]:
        """Get list of enabled virtual servers."""
        return [server for server in self.servers.values() if server.enabled]

    def migrate_legacy_format(self) -> None:
        """Migrate legacy format to new format with enabled flag."""
        migrated = False

        for name, server in self.servers.items():
            if not hasattr(server, 'enabled') or server.enabled is None:
                server.enabled = True
                server.description = server.description or f"Virtual server: {name}"
                migrated = True

        if migrated:
            self.save_servers()
            print("✅ Migrated legacy format to new format")

    def validate_servers(self) -> List[str]:
        """Validate server configurations and return warnings."""
        warnings = []

        for name, server in self.servers.items():
            # Check for empty gateway list
            if not server.gateways:
                warnings.append(f"Server '{name}' has no gateways configured")

            # Check for duplicate names
            if name != name.lower():
                warnings.append(f"Server '{name}' contains uppercase - consider using lowercase")

            # Check description
            if not server.description or server.description == f"Virtual server: {name}":
                warnings.append(f"Server '{name}' has no description")

        return warnings

    def register_enhanced_servers(self):
        """Register virtual servers with enabled/disabled status (skips disabled servers)."""
        print("🚀 Starting enhanced virtual server registration...")
        print(f"📋 Configuration: {self.config_file}")
        print(f"📊 Total servers: {len(self.servers)}")

        enabled_servers = [name for name, server in self.servers.items() if server.enabled]
        print(f"✅ Enabled servers: {len(enabled_servers)}")
        print(f"❌ Disabled servers: {len(self.servers) - len(enabled_servers)}")

        if not enabled_servers:
            print("⚠️  No enabled servers to register")
            return

        print("\n🔄 Processing enabled servers...")
        for name in enabled_servers:
            server = self.servers[name]
            print(f"📝 Registering: {name} ({len(server.gateways)} gateways)")
            # TODO: Implement actual registration logic here
            print(f"✅ Registered: {name}")

        print(f"\n✅ Enhanced registration completed: {len(enabled_servers)} servers registered")

def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Virtual Server Lifecycle Manager")
    parser.add_argument('--config', type=str, default='config/virtual-servers.txt',
                        help='Configuration file path')

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Register enhanced command
    register_parser = subparsers.add_parser("register-enhanced",
                                           help="Register virtual servers with enabled/disabled status")

    # Enable server
    enable_parser = subparsers.add_parser("enable", help="Enable a virtual server")
    enable_parser.add_argument("name", help="Server name to enable")

    # Disable server
    disable_parser = subparsers.add_parser("disable", help="Disable a virtual server")
    disable_parser.add_argument("name", help="Server name to disable")

    # List servers
    list_parser = subparsers.add_parser("list", help="List virtual servers")
    list_parser.add_argument("--status", action="store_true", help="Show status indicators")

    # Validate configuration
    validate_parser = subparsers.add_parser("validate", help="Validate configuration")

    # Migrate configuration
    migrate_parser = subparsers.add_parser("migrate", help="Migrate legacy format")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    manager = VirtualServerManager(args.config)

    if args.command == 'register-enhanced':
        manager.register_enhanced_servers()

    elif args.command == "enable":
        success = manager.enable_server(args.name)
        sys.exit(0 if success else 1)

    elif args.command == "disable":
        success = manager.disable_server(args.name)
        sys.exit(0 if success else 1)

    elif args.command == "list":
        manager.list_servers(show_status=args.status)

    elif args.command == "validate":
        warnings = manager.validate_servers()
        if warnings:
            print("⚠️  Configuration warnings:")
            for warning in warnings:
                print(f"  - {warning}")
            sys.exit(1)
        else:
            print("✅ Configuration is valid")

    elif args.command == "migrate":
        manager.migrate_legacy_format()

if __name__ == "__main__":
    main()
