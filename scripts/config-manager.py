#!/usr/bin/env python3
"""
Configuration Backup and Restore Utility for MCP Gateway

This script provides functionality to backup and restore IDE configurations,
making it easy to manage multiple IDE setups and share configurations.
"""

import json
import os
import sys
import argparse
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class ConfigManager:
    """Manages IDE configuration backup and restore operations."""

    def __init__(self, backup_dir: str = "config/backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        self.ide_configs = {
            'cursor': {
                'config_path': Path.home() / '.cursor' / 'mcp.json',
                'backup_name': 'cursor-mcp.json'
            },
            'windsurf': {
                'config_path': Path.home() / '.codeium' / 'windsurf' / 'mcp_config.json',
                'backup_name': 'windsurf-mcp-config.json'
            },
            'vscode': {
                'config_path': Path.home() / '.vscode' / 'mcp.json',
                'backup_name': 'vscode-mcp.json'
            },
            'claude': {
                'config_path': Path.home() / 'Library' / 'Application Support' / 'Claude' / 'claude_desktop_config.json',
                'backup_name': 'claude-desktop-config.json'
            }
        }

    def backup_config(self, ide: str, include_timestamp: bool = True) -> str:
        """Backup IDE configuration to backup directory."""
        if ide not in self.ide_configs:
            raise ValueError(f"Unsupported IDE: {ide}")

        config_info = self.ide_configs[ide]
        config_path = config_info['config_path']

        if not config_path.exists():
            print(f"⚠️  Configuration file not found: {config_path}")
            return ""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") if include_timestamp else ""
        backup_name = f"{timestamp}_{config_info['backup_name']}" if timestamp else config_info['backup_name']
        backup_path = self.backup_dir / backup_name

        try:
            shutil.copy2(config_path, backup_path)
            print(f"✅ Backed up {ide} configuration to {backup_path}")
            return str(backup_path)
        except Exception as e:
            print(f"❌ Failed to backup {ide} configuration: {e}")
            return ""

    def restore_config(self, ide: str, backup_file: Optional[str] = None) -> bool:
        """Restore IDE configuration from backup."""
        if ide not in self.ide_configs:
            raise ValueError(f"Unsupported IDE: {ide}")

        config_info = self.ide_configs[ide]
        config_path = config_info['config_path']

        # Find backup file if not specified
        if backup_file is None:
            backup_pattern = f"*_{config_info['backup_name']}"
            backup_files = list(self.backup_dir.glob(backup_pattern))

            if not backup_files:
                print(f"❌ No backup found for {ide}")
                return False

            # Use the most recent backup
            backup_file = str(max(backup_files, key=os.path.getctime))

        backup_path = Path(backup_file)

        if not backup_path.exists():
            print(f"❌ Backup file not found: {backup_path}")
            return False

        # Create parent directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            shutil.copy2(backup_path, config_path)
            print(f"✅ Restored {ide} configuration from {backup_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to restore {ide} configuration: {e}")
            return False

    def list_backups(self, ide: Optional[str] = None) -> List[Dict]:
        """List available backups."""
        backups = []

        for backup_file in self.backup_dir.glob("*.json"):
            backup_info = {
                'file': backup_file.name,
                'path': str(backup_file),
                'size': backup_file.stat().st_size,
                'modified': datetime.fromtimestamp(backup_file.stat().st_mtime)
            }

            # Determine which IDE this backup belongs to
            for ide_name, config_info in self.ide_configs.items():
                if backup_file.name.endswith(config_info['backup_name']):
                    backup_info['ide'] = ide_name
                    break
            else:
                backup_info['ide'] = 'unknown'

            # Filter by IDE if specified
            if ide is None or backup_info['ide'] == ide:
                backups.append(backup_info)

        return sorted(backups, key=lambda x: x['modified'], reverse=True)

    def generate_config(self, ide: str, server_url: str, gateway_url: str = "http://localhost:4444") -> Dict:
        """Generate IDE configuration for MCP gateway."""
        base_config = {
            "mcpServers": {
                "forge-mcp-gateway": {
                    "command": "npx -y @forge-mcp-gateway/client",
                    "args": ["--url", server_url],
                    "env": {
                        "GATEWAY_URL": gateway_url
                    }
                }
            }
        }

        # IDE-specific modifications
        if ide == 'claude':
            # Claude Desktop uses slightly different format
            base_config["mcpServers"]["forge-mcp-gateway"] = {
                "command": "npx -y @forge-mcp-gateway/client",
                "args": ["--url", server_url]
            }

        return base_config

    def install_config(self, ide: str, server_url: str, gateway_url: str = "http://localhost:4444") -> bool:
        """Generate and install IDE configuration."""
        if ide not in self.ide_configs:
            raise ValueError(f"Unsupported IDE: {ide}")

        config_info = self.ide_configs[ide]
        config_path = config_info['config_path']

        # Generate configuration
        config = self.generate_config(ide, server_url, gateway_url)

        # Create parent directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Backup existing configuration if it exists
            if config_path.exists():
                self.backup_config(ide, include_timestamp=True)

            # Write new configuration
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)

            print(f"✅ Installed {ide} configuration to {config_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to install {ide} configuration: {e}")
            return False

    def cleanup_backups(self, keep_count: int = 5) -> int:
        """Clean up old backups, keeping only the most recent ones."""
        cleaned = 0

        for ide_name in self.ide_configs.keys():
            backup_pattern = f"*_{self.ide_configs[ide_name]['backup_name']}"
            backup_files = list(self.backup_dir.glob(backup_pattern))

            if len(backup_files) <= keep_count:
                continue

            # Sort by modification time and remove oldest
            backup_files.sort(key=lambda x: x.stat().st_mtime)
            for old_backup in backup_files[:-keep_count]:
                try:
                    old_backup.unlink()
                    cleaned += 1
                    print(f"🗑️  Removed old backup: {old_backup.name}")
                except Exception as e:
                    print(f"⚠️  Failed to remove {old_backup.name}: {e}")

        return cleaned

def main():
    parser = argparse.ArgumentParser(description="MCP Gateway Configuration Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Backup IDE configuration")
    backup_parser.add_argument("ide", choices=["cursor", "windsurf", "vscode", "claude", "all"],
                              help="IDE to backup (or 'all' for all)")
    backup_parser.add_argument("--no-timestamp", action="store_true",
                              help="Don't include timestamp in backup filename")

    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore IDE configuration")
    restore_parser.add_argument("ide", choices=["cursor", "windsurf", "vscode", "claude"],
                              help="IDE to restore")
    restore_parser.add_argument("--file", help="Specific backup file to restore")

    # List command
    list_parser = subparsers.add_parser("list", help="List available backups")
    list_parser.add_argument("--ide", choices=["cursor", "windsurf", "vscode", "claude"],
                            help="Filter by IDE")

    # Install command
    install_parser = subparsers.add_parser("install", help="Generate and install IDE configuration")
    install_parser.add_argument("ide", choices=["cursor", "windsurf", "vscode", "claude", "all"],
                               help="IDE to install configuration for")
    install_parser.add_argument("--server-url", default="http://localhost:4444/sse/cursor-default",
                               help="Server URL to use in configuration")
    install_parser.add_argument("--gateway-url", default="http://localhost:4444",
                               help="Gateway URL to use in configuration")

    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old backups")
    cleanup_parser.add_argument("--keep", type=int, default=5,
                               help="Number of recent backups to keep per IDE")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    manager = ConfigManager()

    if args.command == "backup":
        if args.ide == "all":
            for ide in manager.ide_configs.keys():
                manager.backup_config(ide, not args.no_timestamp)
        else:
            manager.backup_config(args.ide, not args.no_timestamp)

    elif args.command == "restore":
        manager.restore_config(args.ide, args.file)

    elif args.command == "list":
        backups = manager.list_backups(args.ide)
        if not backups:
            print("No backups found")
            return

        print(f"\n📋 Available Backups ({len(backups)} total):")
        print("-" * 80)
        for backup in backups:
            size_kb = backup['size'] / 1024
            print(f"{backup['file']:<40} {backup['ide']:<10} {size_kb:>6.1f}KB  {backup['modified'].strftime('%Y-%m-%d %H:%M')}")

    elif args.command == "install":
        if args.ide == "all":
            for ide in manager.ide_configs.keys():
                manager.install_config(ide, args.server_url, args.gateway_url)
        else:
            manager.install_config(args.ide, args.server_url, args.gateway_url)

    elif args.command == "cleanup":
        cleaned = manager.cleanup_backups(args.keep)
        print(f"✅ Cleaned up {cleaned} old backup files")

if __name__ == "__main__":
    main()
