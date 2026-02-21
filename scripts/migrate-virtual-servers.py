#!/usr/bin/env python3
"""
Migration script to convert virtual-servers.txt to new format with enabled flags.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from virtual_server_manager import VirtualServerManager

def main():
    """Migrate virtual servers to new format."""
    config_file = "config/virtual-servers.txt"
    config_path = Path(config_file)

    if not config_path.exists():
        print(f"Error: Configuration file not found: {config_file}")
        sys.exit(1)

    print("🔄 Migrating virtual servers to new format with enabled flags...")

    # Create backup
    backup_path = config_path.with_suffix('.backup')
    print(f"📋 Creating backup: {backup_path}")
    backup_path.write_text(config_path.read_text())

    # Load and migrate
    manager = VirtualServerManager(config_file)

    if not manager.servers:
        print("❌ No servers found to migrate")
        sys.exit(1)

    # Migrate each server
    migrated_count = 0
    for name, server in manager.servers.items():
        if not hasattr(server, 'enabled') or server.enabled is None:
            server.enabled = True
            server.description = server.description or f"Virtual server: {name}"
            server.updated_at = None  # Will be set on save
            migrated_count += 1

    if migrated_count > 0:
        manager.save_servers()
        print(f"✅ Successfully migrated {migrated_count} servers")
        print(f"📁 Configuration updated: {config_file}")

        # Show summary
        enabled_count = len([s for s in manager.servers.values() if s.enabled])
        print(f"📊 Summary: {len(manager.servers)} total servers, {enabled_count} enabled")

        print("\n🔧 Next steps:")
        print("1. Review the migrated configuration")
        print("2. Use 'python scripts/virtual-server-manager.py list' to verify")
        print("3. Use 'python scripts/virtual-server-manager.py disable <name>' to disable servers")
        print("4. Run 'make register' to apply changes")
    else:
        print("ℹ️  Configuration already in new format")

if __name__ == "__main__":
    main()
