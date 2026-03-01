#!/usr/bin/env python3
"""
Unified IDE Setup and Management for MCP Gateway

Phase 2: IDE Integration UX
Eliminates manual UUID copying, supports all IDEs with one-click setup.

Supported IDEs:
- Cursor (mcp.json)
- Windsurf (mcp.json)
- VSCode (settings.json)
- Claude Desktop (claude_desktop_config.json)
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class IDEConfig:
    """IDE configuration metadata."""

    name: str
    config_path: str
    config_format: str  # json, toml, etc.
    wrapper_script: str
    env_vars: dict[str, str]
    example_profiles: list[str]


class IDEManager:
    """Manages IDE detection, configuration, and operations."""

    def __init__(self, repo_root: Path | None = None):
        self.repo_root = repo_root or Path(__file__).parent.parent
        self.scripts_dir = self.repo_root / "scripts"
        self.data_dir = self.repo_root / "data"
        self.config_dir = self.repo_root / "config"

        # IDE configurations
        self.ides = {
            "cursor": IDEConfig(
                name="Cursor",
                config_path="~/.cursor/mcp.json",
                config_format="json",
                wrapper_script="cursor-mcp-wrapper.sh",
                env_vars={
                    "GITHUB_PERSONAL_ACCESS_TOKEN": "GitHub token (repo scope)",
                    "SNYK_TOKEN": "Snyk API token",
                    "TAVILY_API_KEY": "Tavily API key",
                    "FIGMA_TOKEN": "Figma personal access token",
                },
                example_profiles=["cursor-default", "cursor-router", "nodejs-typescript", "react-nextjs"],
            ),
            "windsurf": IDEConfig(
                name="Windsurf",
                config_path="~/.windsurf/mcp.json",
                config_format="json",
                wrapper_script="cursor-mcp-wrapper.sh",
                env_vars={
                    "GITHUB_PERSONAL_ACCESS_TOKEN": "GitHub token (repo scope)",
                    "SNYK_TOKEN": "Snyk API token",
                    "TAVILY_API_KEY": "Tavily API key",
                },
                example_profiles=["windsurf-default", "windsurf-router", "python-dev"],
            ),
            "vscode": IDEConfig(
                name="VSCode",
                config_path=".vscode/settings.json",  # workspace relative
                config_format="json",
                wrapper_script="cursor-mcp-wrapper.sh",
                env_vars={
                    "GITHUB_PERSONAL_ACCESS_TOKEN": "GitHub token (repo scope)",
                    "SNYK_TOKEN": "Snyk API token",
                    "TAVILY_API_KEY": "Tavily API key",
                },
                example_profiles=["vscode-default", "vscode-router", "web-dev"],
            ),
            "claude": IDEConfig(
                name="Claude Desktop",
                config_path="~/Library/Application Support/Claude/claude_desktop_config.json",
                config_format="json",
                wrapper_script="cursor-mcp-wrapper.sh",
                env_vars={
                    "GITHUB_PERSONAL_ACCESS_TOKEN": "GitHub token (repo scope)",
                    "SNYK_TOKEN": "Snyk API token",
                    "TAVILY_API_KEY": "Tavily API key",
                },
                example_profiles=["claude-default", "claude-router", "research"],
            ),
        }

    def detect_installed_ides(self) -> list[str]:
        """Auto-detect which IDEs are installed on the system."""
        detected = []

        # Check for Cursor
        if Path("/Applications/Cursor.app").exists() or Path("~/Applications/Cursor.app").expanduser().exists():
            detected.append("cursor")

        # Check for VSCode
        if (
            Path("/Applications/Visual Studio Code.app").exists()
            or Path("/Applications/VSCode.app").exists()
            or shutil.which("code")
        ):
            detected.append("vscode")

        # Check for Windsurf (often installed via npm)
        try:
            subprocess.run(["windsurf", "--version"], capture_output=True, check=False)
            detected.append("windsurf")
        except (FileNotFoundError, subprocess.SubprocessError):
            pass

        # Check for Claude Desktop
        if Path("~/Library/Application Support/Claude").expanduser().exists():
            detected.append("claude")

        return detected

    def get_available_servers(self) -> list[dict]:
        """Get list of available virtual servers from config."""
        servers_file = self.config_dir / "virtual-servers.txt"
        servers = []

        if not servers_file.exists():
            print(f"❌ Virtual servers config not found: {servers_file}")
            return servers

        with open(servers_file) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "|" not in line:
                    continue

                parts = line.split("|")
                if len(parts) >= 1:
                    name = parts[0].strip()
                    if len(parts) >= 4:
                        enabled = parts[1].strip().lower() in ["true", "1", "yes"]
                        description = parts[3].strip()
                    elif len(parts) >= 2:
                        enabled = True  # Legacy format defaults to enabled
                        description = parts[2].strip() if len(parts) >= 3 else ""
                    else:
                        enabled = True  # Legacy format defaults to enabled
                        description = ""

                    if enabled:
                        servers.append({"name": name, "enabled": enabled, "description": description})

        return servers

    def get_server_url(self, server_name: str) -> str | None:
        """Get the MCP URL for a specific server."""
        url_file = self.data_dir / ".cursor-mcp-url"
        if not url_file.exists():
            return None

        # For now, return the first URL found
        # TODO: Implement server-specific URL mapping
        with open(url_file) as f:
            return f.read().strip()

    def generate_ide_config(self, ide: str, server_name: str, profile: str | None = None) -> dict:
        """Generate IDE configuration for a specific server."""
        if ide not in self.ides:
            raise ValueError(f"Unsupported IDE: {ide}")

        ide_config = self.ides[ide]
        wrapper_path = self.scripts_dir / ide_config.wrapper_script
        server_url = self.get_server_url(server_name)

        if not server_url:
            raise ValueError(f"No URL found for server: {server_name}")

        # Extract server UUID from URL
        if "/servers/" in server_url and "/mcp" in server_url:
            server_uuid = server_url.split("/servers/")[1].split("/mcp")[0]
        else:
            raise ValueError(f"Invalid server URL format: {server_url}")

        # Build configuration
        if ide == "vscode":
            config = {
                "mcp.servers": {
                    server_name: {
                        "command": str(wrapper_path.absolute()),
                        "args": ["--server-name", server_name],
                        "env": {
                            "GATEWAY_URL": server_url.replace(f"/servers/{server_uuid}/mcp", ""),
                            "SERVER_ID": server_uuid,
                        },
                    }
                }
            }
        else:
            config = {
                "mcpServers": {
                    server_name: {
                        "command": str(wrapper_path.absolute()),
                        "args": ["--server-name", server_name],
                        "env": {
                            "GATEWAY_URL": server_url.replace(f"/servers/{server_uuid}/mcp", ""),
                            "SERVER_ID": server_uuid,
                        },
                    }
                }
            }

        # Add environment variables if available
        env_vars = {}
        for var_name, description in ide_config.env_vars.items():
            env_value = os.environ.get(var_name)
            if env_value:
                env_vars[var_name] = env_value

        if env_vars:
            if ide == "vscode":
                config["mcp.servers"][server_name]["env"].update(env_vars)
            else:
                config["mcpServers"][server_name]["env"].update(env_vars)

        return config

    def install_ide_config(self, ide: str, server_name: str, profile: str | None = None) -> bool:
        """Install IDE configuration for a specific server."""
        try:
            config = self.generate_ide_config(ide, server_name, profile)
            ide_config = self.ides[ide]

            # Expand config path
            config_path = Path(ide_config.config_path).expanduser()

            # Create directory if needed
            config_path.parent.mkdir(parents=True, exist_ok=True)

            # Load existing config if exists
            existing_config = {}
            if config_path.exists():
                try:
                    with open(config_path) as f:
                        existing_config = json.load(f)
                except json.JSONDecodeError:
                    print(f"⚠️  Invalid JSON in {config_path}, creating new config")
                    existing_config = {}

            # Merge configurations
            if ide == "vscode":
                if "mcp.servers" in existing_config:
                    existing_config["mcp.servers"].update(config["mcp.servers"])
                else:
                    existing_config.update(config)
            elif "mcpServers" in existing_config:
                existing_config["mcpServers"].update(config["mcpServers"])
            else:
                existing_config.update(config)

            # Write configuration
            with open(config_path, "w") as f:
                json.dump(existing_config, f, indent=2)

            print(f"✅ Installed {ide_config.name} configuration for server '{server_name}'")
            print(f"   Config file: {config_path}")
            return True

        except Exception as e:
            print(f"❌ Failed to install {ide} configuration: {e}")
            return False

    def backup_ide_config(self, ide: str) -> bool:
        """Backup IDE configuration."""
        try:
            ide_config = self.ides[ide]
            config_path = Path(ide_config.config_path).expanduser()

            if not config_path.exists():
                print(f"⚠️  No {ide_config.name} configuration found to backup")
                return False

            # Create backup directory
            backup_dir = self.data_dir / "ide-backups"
            backup_dir.mkdir(exist_ok=True)

            # Create backup filename with timestamp
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"{ide}_config_{timestamp}.json"

            # Copy configuration
            shutil.copy2(config_path, backup_file)
            print(f"✅ Backed up {ide_config.name} configuration to {backup_file}")
            return True

        except Exception as e:
            print(f"❌ Failed to backup {ide} configuration: {e}")
            return False

    def restore_ide_config(self, ide: str, backup_file: str | None = None) -> bool:
        """Restore IDE configuration from backup."""
        try:
            ide_config = self.ides[ide]
            config_path = Path(ide_config.config_path).expanduser()
            backup_dir = self.data_dir / "ide-backups"

            if not backup_file:
                # Find latest backup
                backups = list(backup_dir.glob(f"{ide}_config_*.json"))
                if not backups:
                    print(f"❌ No {ide_config.name} backups found")
                    return False
                backup_file = max(backups, key=lambda p: p.stat().st_mtime)

            backup_path = Path(backup_file)
            if not backup_path.exists():
                print(f"❌ Backup file not found: {backup_file}")
                return False

            # Create directory if needed
            config_path.parent.mkdir(parents=True, exist_ok=True)

            # Restore configuration
            shutil.copy2(backup_path, config_path)
            print(f"✅ Restored {ide_config.name} configuration from {backup_path}")
            return True

        except Exception as e:
            print(f"❌ Failed to restore {ide} configuration: {e}")
            return False

    def get_ide_status(self, ide: str) -> dict:
        """Get status of IDE configuration."""
        ide_config = self.ides[ide]
        config_path = Path(ide_config.config_path).expanduser()

        status = {
            "ide": ide_config.name,
            "config_exists": config_path.exists(),
            "config_path": str(config_path),
            "servers_configured": [],
            "last_modified": None,
        }

        if config_path.exists():
            try:
                with open(config_path) as f:
                    config_data = json.load(f)

                servers = config_data.get("mcpServers", {})
                status["servers_configured"] = list(servers.keys())
                status["last_modified"] = datetime.fromtimestamp(config_path.stat().st_mtime, UTC).isoformat()

            except (json.JSONDecodeError, Exception) as e:
                status["error"] = str(e)

        return status

    def refresh_jwt_token(self, ide: str) -> bool:
        """Refresh JWT token for IDE configuration."""
        if ide != "cursor":
            print(f"JWT refresh is only supported for Cursor, not {ide}")
            return False

        config_path = Path.home() / ".cursor" / "mcp.json"
        if not config_path.exists():
            print(f"❌ {config_path} not found")
            return False

        try:
            # Generate new JWT token
            jwt_result = subprocess.run(["make", "jwt"], cwd=self.repo_root, capture_output=True, text=True, timeout=10)

            if jwt_result.returncode != 0:
                print("❌ Failed to generate JWT token")
                return False

            # Extract JWT from output
            jwt_line = None
            for line in jwt_result.stdout.split("\n"):
                if line.startswith("eyJ") and line.endswith("=="):
                    jwt_line = line
                    break

            if not jwt_line:
                print("❌ Could not extract JWT token from output")
                return False

            # Update configuration
            with open(config_path) as f:
                config = json.load(f)

            # Find context-forge key
            context_forge_key = None
            for key in config.keys():
                if "context-forge" in key.lower():
                    context_forge_key = key
                    break

            if not context_forge_key:
                print("❌ context-forge entry not found in configuration")
                return False

            # Update JWT token
            if "mcpServers" in config and context_forge_key in config["mcpServers"]:
                config["mcpServers"][context_forge_key]["headers"] = {"Authorization": f"Bearer {jwt_line}"}
            elif context_forge_key in config:
                config[context_forge_key]["headers"] = {"Authorization": f"Bearer {jwt_line}"}

            # Backup and update
            backup_path = config_path.with_suffix(".json.bak")
            shutil.copy2(config_path, backup_path)

            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)

            print(f"✅ Updated JWT token for '{context_forge_key}' in {config_path}")
            print(f"   Backup saved to {backup_path}")
            print("   Restart Cursor to use the new token")
            return True

        except Exception as e:
            print(f"❌ Failed to refresh JWT token: {e}")
            return False

    def use_wrapper_script(self, ide: str) -> bool:
        """Configure IDE to use wrapper script."""
        if ide != "cursor":
            print(f"Wrapper script is only supported for Cursor, not {ide}")
            return False

        config_path = Path.home() / ".cursor" / "mcp.json"
        wrapper_path = self.repo_root / "scripts" / "cursor-mcp-wrapper.sh"

        if not config_path.exists():
            print(f"❌ {config_path} not found")
            return False

        if not wrapper_path.exists():
            print(f"❌ {wrapper_path} not found")
            return False

        try:
            # Check for URL file
            url_file = self.data_dir / ".cursor-mcp-url"
            if not url_file.exists() or url_file.stat().st_size == 0:
                print("❌ Run 'make register' first so data/.cursor-mcp-url exists")
                return False

            # Load configuration
            with open(config_path) as f:
                config = json.load(f)

            # Find or create context-forge key
            context_forge_key = None
            for key in config.keys():
                if "context-forge" in key.lower():
                    context_forge_key = key
                    break

            if not context_forge_key:
                context_forge_key = "context-forge"

            # Configure wrapper
            wrapper_config = {
                "command": str(wrapper_path),
                "timeout": 120000,  # 2 minutes
            }

            if "mcpServers" in config:
                config["mcpServers"][context_forge_key] = wrapper_config
            else:
                config[context_forge_key] = wrapper_config

            # Backup and update
            backup_path = config_path.with_suffix(".json.bak")
            shutil.copy2(config_path, backup_path)

            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)

            print(f"✅ Set '{context_forge_key}' to use wrapper script in {config_path}")
            print(f"   Backup saved to {backup_path}")
            print("   Fully quit Cursor (Cmd+Q / Alt+F4) and reopen to use automatic JWT")
            return True

        except Exception as e:
            print(f"❌ Failed to configure wrapper script: {e}")
            return False

    def verify_setup(self, ide: str) -> bool:
        """Verify IDE setup and configuration."""
        if ide != "cursor":
            print(f"Setup verification is only supported for Cursor, not {ide}")
            return False

        print("🔍 Verifying Cursor setup...")

        # Check gateway reachability
        try:
            result = subprocess.run(
                [
                    "curl",
                    "-s",
                    "-o",
                    "/dev/null",
                    "-w",
                    "%{http_code}",
                    "--connect-timeout",
                    "3",
                    "http://localhost:8080/health",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0 and result.stdout == "200":
                print("✅ Gateway reachable at http://localhost:8080")
            else:
                print("❌ Gateway not reachable. Run 'make start'")
                return False
        except Exception:
            print("❌ Gateway not reachable. Run 'make start'")
            return False

        # Check URL file
        url_file = self.data_dir / ".cursor-mcp-url"
        if not url_file.exists() or url_file.stat().st_size == 0:
            print("❌ data/.cursor-mcp-url missing or empty (run: make register)")
            return False

        with open(url_file) as f:
            mcp_url = f.read().strip()

        print(f"✅ data/.cursor-mcp-url exists: {mcp_url}")

        # Check URL format
        import re

        if not re.search(r"/servers/([a-f0-9-]+)/mcp", mcp_url):
            print("❌ URL does not look like .../servers/UUID/mcp")
            return False

        # Check configuration file
        config_path = Path.home() / ".cursor" / "mcp.json"
        if not config_path.exists():
            print(f"❌ {config_path} not found")
            return False

        try:
            with open(config_path) as f:
                config = json.load(f)

            # Find context-forge entry
            context_forge_key = None
            for key in config.keys():
                if "context-forge" in key.lower():
                    context_forge_key = key
                    break

            if not context_forge_key:
                print("❌ context-forge entry not found in configuration")
                return False

            print(f"✅ Found context-forge entry: {context_forge_key}")

            # Check if using wrapper or direct connection
            if "mcpServers" in config and context_forge_key in config["mcpServers"]:
                entry = config["mcpServers"][context_forge_key]
            else:
                entry = config[context_forge_key]

            if "command" in entry:
                print("✅ Configured to use wrapper script")
                wrapper_path = entry["command"]
                if Path(wrapper_path).exists():
                    print(f"✅ Wrapper script exists: {wrapper_path}")
                else:
                    print(f"❌ Wrapper script not found: {wrapper_path}")
                    return False
            else:
                print("✅ Configured for direct connection")
                if "headers" in entry and "Authorization" in entry["headers"]:
                    print("✅ JWT token configured")
                else:
                    print("⚠️  No JWT token found - run 'make ide-setup IDE=cursor ACTION=refresh-jwt'")

            print("✅ Cursor setup verification completed successfully")
            return True

        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in {config_path}")
            return False
        except Exception as e:
            print(f"❌ Error checking configuration: {e}")
            return False

    def setup_ide(
        self, ide: str, action: str = "install", server_name: str | None = None, profile: str | None = None
    ) -> bool:
        """Main setup function for IDE operations."""
        if ide == "all":
            # Apply to all detected IDEs
            detected = self.detect_installed_ides()
            if not detected:
                print("⚠️  No supported IDEs detected")
                return False

            print(f"Detected IDEs: {', '.join(detected)}")
            success = True
            for detected_ide in detected:
                if not self.setup_ide(detected_ide, action, server_name, profile):
                    success = False
            return success

        if ide not in self.ides:
            print(f"❌ Unsupported IDE: {ide}")
            print(f"Supported IDEs: {', '.join(self.ides.keys())}")
            return False

        if action == "install":
            if not server_name:
                # Show available servers and prompt
                servers = self.get_available_servers()
                if not servers:
                    print("❌ No enabled virtual servers found")
                    return False

                print("Available virtual servers:")
                for i, server in enumerate(servers, 1):
                    print(f"  {i}. {server['name']} - {server.get('description', 'No description')}")

                # For now, use the first server
                server_name = servers[0]["name"]
                print(f"Using server: {server_name}")

            return self.install_ide_config(ide, server_name, profile)

        if action == "backup":
            return self.backup_ide_config(ide)

        if action == "restore":
            return self.restore_ide_config(ide)

        if action == "status":
            try:
                status = self.get_ide_status(ide)
                print(f"\n{status['ide']} Status:")
                print(f"  Config exists: {'✅' if status['config_exists'] else '❌'}")
                print(f"  Config path: {status['config_path']}")
                if status["servers_configured"]:
                    print(f"  Configured servers: {', '.join(status['servers_configured'])}")
                if status.get("error"):
                    print(f"  Error: {status['error']}")
                if status["last_modified"]:
                    print(f"  Last modified: {status['last_modified']}")
                return True
            except Exception as e:
                print(f"❌ Failed to get {ide} status: {e}")
                return False

        elif action == "refresh-jwt":
            return self.refresh_jwt_token(ide)

        elif action == "use-wrapper":
            return self.use_wrapper_script(ide)

        elif action == "verify":
            return self.verify_setup(ide)

        else:
            print(f"❌ Unknown action: {action}")
            print("Supported actions: install, backup, restore, status, refresh-jwt, use-wrapper, verify")
            return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Unified IDE Setup and Management for MCP Gateway",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s setup cursor                    # Install Cursor config
  %(prog)s setup all                       # Install all detected IDE configs
  %(prog)s setup windsurf --action backup   # Backup Windsurf config
  %(prog)s setup vscode --action status     # Check VSCode status
  %(prog)s setup claude --server-name cursor-default  # Install specific server
        """,
    )

    parser.add_argument("command", choices=["setup", "detect", "list-servers"], help="Command to execute")

    parser.add_argument("ide", nargs="?", help="IDE name (cursor, windsurf, vscode, claude, all)")

    parser.add_argument(
        "--action",
        choices=["install", "backup", "restore", "status"],
        default="install",
        help="Action for setup command (default: install)",
    )

    parser.add_argument("--server-name", help="Specific server name to configure")

    parser.add_argument("--profile", help="Configuration profile to use")

    args = parser.parse_args()

    manager = IDEManager()

    try:
        if args.command == "detect":
            detected = manager.detect_installed_ides()
            if detected:
                print(f"Detected IDEs: {', '.join(detected)}")
            else:
                print("No supported IDEs detected")

        elif args.command == "list-servers":
            servers = manager.get_available_servers()
            if servers:
                print("Available virtual servers:")
                for server in servers:
                    status = "✅" if server["enabled"] else "❌"
                    print(f"  {status} {server['name']} - {server.get('description', 'No description')}")
            else:
                print("No enabled virtual servers found")

        elif args.command == "setup":
            if not args.ide:
                print("❌ IDE name required for setup command")
                print("Supported IDEs: cursor, windsurf, vscode, claude, all")
                sys.exit(1)

            success = manager.setup_ide(args.ide, args.action, args.server_name, args.profile)

            sys.exit(0 if success else 1)

        else:
            print(f"❌ Unknown command: {args.command}")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n❌ Operation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
