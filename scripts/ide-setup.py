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
- Zed (settings.json — context_servers)
"""

from __future__ import annotations

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
                wrapper_script="mcp-wrapper.sh",
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
                wrapper_script="mcp-wrapper.sh",
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
                wrapper_script="mcp-wrapper.sh",
                env_vars={
                    "GITHUB_PERSONAL_ACCESS_TOKEN": "GitHub token (repo scope)",
                    "SNYK_TOKEN": "Snyk API token",
                    "TAVILY_API_KEY": "Tavily API key",
                },
                example_profiles=["vscode-default", "vscode-router", "web-dev"],
            ),
            "claude": IDEConfig(
                name="Claude Desktop",
                config_path=self._claude_config_path(),
                config_format="json",
                wrapper_script="mcp-wrapper.sh",
                env_vars={
                    "GITHUB_PERSONAL_ACCESS_TOKEN": "GitHub token (repo scope)",
                    "SNYK_TOKEN": "Snyk API token",
                    "TAVILY_API_KEY": "Tavily API key",
                },
                example_profiles=["claude-default", "claude-router", "research"],
            ),
            "zed": IDEConfig(
                name="Zed",
                config_path="~/.config/zed/settings.json",
                config_format="json",
                wrapper_script="mcp-wrapper.sh",
                env_vars={
                    "GITHUB_PERSONAL_ACCESS_TOKEN": "GitHub token (repo scope)",
                    "SNYK_TOKEN": "Snyk API token",
                    "TAVILY_API_KEY": "Tavily API key",
                },
                example_profiles=["zed-default", "zed-router"],
            ),
        }

    @staticmethod
    def _claude_config_path() -> str:
        """Return platform-correct Claude Desktop config path."""
        import platform

        system = platform.system()
        if system == "Darwin":
            return "~/Library/Application Support/Claude/claude_desktop_config.json"
        if system == "Windows":
            appdata = os.environ.get("APPDATA", "~")
            return str(Path(appdata) / "Claude" / "claude_desktop_config.json")
        # Linux / other
        return "~/.config/claude/claude_desktop_config.json"

    def detect_installed_ides(self) -> list[str]:
        """Auto-detect which IDEs are installed on the system (macOS, Linux, Windows)."""
        import platform

        detected: list[str] = []
        system = platform.system()

        # ── Cursor ──────────────────────────────────────────────────────────
        cursor_paths = [
            Path("/Applications/Cursor.app"),
            Path("~/Applications/Cursor.app").expanduser(),
            Path("~/.cursor").expanduser(),  # config dir present means it ran at least once
        ]
        if system == "Windows":
            cursor_paths += [
                Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "cursor" / "Cursor.exe",
                Path(os.environ.get("APPDATA", "")) / "Cursor",
            ]
        elif system == "Linux":
            cursor_paths += [
                Path("/usr/bin/cursor"),
                Path("~/.local/share/applications/cursor.desktop").expanduser(),
            ]
        if any(p.exists() for p in cursor_paths) or shutil.which("cursor"):
            detected.append("cursor")

        # ── VSCode ──────────────────────────────────────────────────────────
        vscode_paths = [
            Path("/Applications/Visual Studio Code.app"),
            Path("/Applications/VSCode.app"),
        ]
        if system == "Windows":
            vscode_paths += [
                Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Microsoft VS Code" / "Code.exe",
            ]
        elif system == "Linux":
            vscode_paths += [
                Path("/usr/share/applications/code.desktop"),
            ]
        if any(p.exists() for p in vscode_paths) or shutil.which("code") or shutil.which("code-insiders"):
            detected.append("vscode")

        # ── Windsurf ────────────────────────────────────────────────────────
        windsurf_paths = [
            Path("/Applications/Windsurf.app"),
            Path("~/Applications/Windsurf.app").expanduser(),
            Path("~/.windsurf").expanduser(),
        ]
        if system == "Windows":
            windsurf_paths += [
                Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Windsurf" / "Windsurf.exe",
            ]
        elif system == "Linux":
            windsurf_paths += [
                Path("~/.local/share/applications/windsurf.desktop").expanduser(),
            ]
        if any(p.exists() for p in windsurf_paths) or shutil.which("windsurf"):
            detected.append("windsurf")

        # ── Claude Desktop ──────────────────────────────────────────────────
        claude_config = Path(self._claude_config_path()).expanduser().parent
        if claude_config.exists():
            detected.append("claude")

        # ── Zed ─────────────────────────────────────────────────────────────
        zed_paths = [
            Path("/Applications/Zed.app"),
            Path("~/Applications/Zed.app").expanduser(),
            Path("~/.config/zed").expanduser(),
        ]
        if system == "Linux":
            zed_paths += [
                Path("~/.local/share/applications/dev.zed.Zed.desktop").expanduser(),
            ]
        if any(p.exists() for p in zed_paths) or shutil.which("zed"):
            detected.append("zed")

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
        explicit_url = os.environ.get("MCP_CLIENT_SERVER_URL", "").strip()
        if explicit_url:
            return explicit_url

        url_file = self.data_dir / ".mcp-client-url"
        if not url_file.exists():
            return None

        with open(url_file) as f:
            return f.read().strip()

    def generate_ide_config(self, ide: str, server_name: str, profile: str | None = None) -> dict:
        """Generate IDE configuration for a specific server."""
        if ide not in self.ides:
            raise ValueError(f"Unsupported IDE: {ide}")

        ide_config = self.ides[ide]
        wrapper_path = self.scripts_dir / ide_config.wrapper_script
        server_url = self.get_server_url(server_name)
        timeout_ms = int(os.environ.get("CURSOR_MCP_TIMEOUT_MS", "120000"))

        if not server_url:
            raise ValueError(f"No URL found for server: {server_name}")

        if "/servers/" not in server_url or "/mcp" not in server_url:
            raise ValueError(f"Invalid server URL format: {server_url}")

        # Zed uses a different entry schema under "context_servers"
        if ide == "zed":
            zed_entry = {
                "command": {"path": str(wrapper_path.absolute()), "args": []},
                "settings": {},
                "env": {"MCP_CLIENT_SERVER_URL": server_url},
            }
            for var_name in ide_config.env_vars:
                env_value = os.environ.get(var_name)
                if env_value:
                    zed_entry["env"][var_name] = env_value
            return {"context_servers": {server_name: zed_entry}}

        entry = {
            "command": str(wrapper_path.absolute()),
            "env": {"MCP_CLIENT_SERVER_URL": server_url},
            "timeout": timeout_ms,
        }
        config_key = "context-forge" if ide == "cursor" else server_name
        container_key = "mcp.servers" if ide == "vscode" else "mcpServers"
        config = {container_key: {config_key: entry}}

        # Add environment variables if available
        env_vars = {}
        for var_name in ide_config.env_vars:
            env_value = os.environ.get(var_name)
            if env_value:
                env_vars[var_name] = env_value

        if env_vars:
            config[container_key][config_key]["env"].update(env_vars)

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

            # Merge configurations (IDE-specific container keys)
            if ide == "vscode":
                existing_config.setdefault("mcp.servers", {}).update(config.get("mcp.servers", {}))
            elif ide == "zed":
                existing_config.setdefault("context_servers", {}).update(config.get("context_servers", {}))
            else:
                existing_config.setdefault("mcpServers", {}).update(config.get("mcpServers", {}))

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

                # Zed uses context_servers, VSCode uses mcp.servers, others use mcpServers
                if ide == "zed":
                    servers = config_data.get("context_servers", {})
                elif ide == "vscode":
                    servers = config_data.get("mcp.servers", {})
                else:
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
        """Configure IDE to use wrapper script (all supported IDEs)."""
        if ide not in self.ides:
            print(f"❌ Unsupported IDE: {ide}")
            return False

        ide_config = self.ides[ide]
        config_path = Path(ide_config.config_path).expanduser()
        wrapper_path = self.repo_root / "scripts" / "mcp-wrapper.sh"

        if not wrapper_path.exists():
            print(f"❌ {wrapper_path} not found. Run: chmod +x scripts/mcp-wrapper.sh")
            return False

        if not config_path.exists():
            print(f"⚠️  {config_path} not found — creating new config")
            config_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            explicit_url = os.environ.get("MCP_CLIENT_SERVER_URL", "").strip()
            url_file = self.data_dir / ".mcp-client-url"
            file_url = ""
            if url_file.exists() and url_file.stat().st_size > 0:
                with open(url_file) as f:
                    file_url = f.read().strip()
            mcp_url = explicit_url or file_url
            if not mcp_url:
                print("❌ Missing MCP URL. Run 'make register' or set MCP_CLIENT_SERVER_URL")
                return False

            # Load existing config (empty dict if new file)
            config: dict = {}
            if config_path.exists():
                try:
                    with open(config_path) as f:
                        config = json.load(f)
                except json.JSONDecodeError:
                    print(f"⚠️  Invalid JSON in {config_path}, starting fresh")

            # Build the wrapper entry in the IDE-specific format
            timeout_ms = int(os.environ.get("CURSOR_MCP_TIMEOUT_MS", "120000"))
            if ide == "zed":
                entry_key = "context-forge"
                wrapper_entry = {
                    "command": {"path": str(wrapper_path), "args": []},
                    "settings": {},
                    "env": {"MCP_CLIENT_SERVER_URL": mcp_url},
                }
                config.setdefault("context_servers", {})[entry_key] = wrapper_entry
                container_display = "context_servers"
            elif ide == "vscode":
                entry_key = "context-forge"
                wrapper_entry = {
                    "command": str(wrapper_path),
                    "timeout": timeout_ms,
                    "env": {"MCP_CLIENT_SERVER_URL": mcp_url},
                }
                config.setdefault("mcp.servers", {})[entry_key] = wrapper_entry
                container_display = "mcp.servers"
            else:
                # cursor, windsurf, claude — all use mcpServers
                entry_key = "context-forge"
                wrapper_entry = {
                    "command": str(wrapper_path),
                    "timeout": timeout_ms,
                    "env": {"MCP_CLIENT_SERVER_URL": mcp_url},
                }
                config.setdefault("mcpServers", {})[entry_key] = wrapper_entry
                container_display = "mcpServers"

            # Backup and write
            if config_path.exists():
                backup_path = config_path.with_suffix(".json.bak")
                shutil.copy2(config_path, backup_path)
                print(f"   Backup saved to {backup_path}")

            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)

            print(f"✅ Wrote '{entry_key}' under {container_display} in {config_path}")
            print(f"   MCP URL source: {'MCP_CLIENT_SERVER_URL env' if explicit_url else 'data/.mcp-client-url'}")
            print(f"   Restart {ide_config.name} to pick up the change")
            return True

        except Exception as e:
            print(f"❌ Failed to configure wrapper script: {e}")
            return False

    def verify_setup(self, ide: str) -> bool:
        """Verify IDE setup and configuration (all supported IDEs)."""
        if ide not in self.ides:
            print(f"❌ Unsupported IDE: {ide}")
            return False

        ide_config = self.ides[ide]
        print(f"🔍 Verifying {ide_config.name} setup...")
        gateway_base = os.environ.get("GATEWAY_URL", f"http://localhost:{os.environ.get('PORT', '4444')}")
        gateway_base = gateway_base.rstrip("/")
        health_url = f"{gateway_base}/health"

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
                    health_url,
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0 and result.stdout == "200":
                print(f"✅ Gateway reachable at {gateway_base}")
            else:
                print("❌ Gateway not reachable. Run 'make start'")
                return False
        except Exception:
            print("❌ Gateway not reachable. Run 'make start'")
            return False

        # Check configuration file
        config_path = Path(ide_config.config_path).expanduser()
        if not config_path.exists():
            print(f"❌ {config_path} not found — run: python3 scripts/ide-setup.py setup {ide} --action use-wrapper")
            return False

        try:
            import re

            with open(config_path) as f:
                config = json.load(f)

            # Determine the container key for this IDE
            if ide == "zed":
                container_key = "context_servers"
            elif ide == "vscode":
                container_key = "mcp.servers"
            else:
                container_key = "mcpServers"

            servers = config.get(container_key, {})
            if not isinstance(servers, dict):
                print(f"❌ Invalid {ide_config.name} config: {container_key} must be an object")
                return False

            # Find the wrapper entry (search by key name or by command/env)
            def _has_wrapper_url(v: dict) -> bool:
                env = v.get("env", {})
                if isinstance(env, dict) and env.get("MCP_CLIENT_SERVER_URL"):
                    return True
                cmd = v.get("command", {})
                # Zed stores command as {"path": ..., "args": [...]}
                if isinstance(cmd, dict):
                    return str(cmd.get("path", "")).endswith("mcp-wrapper.sh")
                return str(cmd).endswith("mcp-wrapper.sh")

            entry_key = next((k for k in servers if "context-forge" in k.lower()), None)
            if not entry_key:
                entry_key = next((k for k, v in servers.items() if isinstance(v, dict) and _has_wrapper_url(v)), None)
            if not entry_key:
                print(f"❌ No wrapper-style MCP entry found in {container_key}")
                return False

            print(f"✅ Found MCP entry: {entry_key}")
            entry = servers[entry_key]
            if not isinstance(entry, dict):
                print("❌ Invalid MCP entry format")
                return False

            # Resolve the command path (str for most IDEs, dict for Zed)
            cmd = entry.get("command", "")
            wrapper_cmd = cmd.get("path", "") if isinstance(cmd, dict) else cmd
            if not wrapper_cmd:
                print("❌ MCP entry does not specify a command")
                return False
            if not str(wrapper_cmd).endswith("mcp-wrapper.sh"):
                print(f"❌ MCP entry points to unexpected command: {wrapper_cmd}")
                return False
            if Path(str(wrapper_cmd)).exists():
                print(f"✅ Wrapper script exists: {wrapper_cmd}")
            else:
                print(f"❌ Wrapper script not found: {wrapper_cmd}")
                return False

            entry_env = entry.get("env", {})
            if not isinstance(entry_env, dict):
                print("❌ Invalid env configuration in MCP entry")
                return False

            entry_mcp_url = str(entry_env.get("MCP_CLIENT_SERVER_URL", "")).strip()
            url_file = self.data_dir / ".mcp-client-url"
            file_mcp_url = ""
            if url_file.exists() and url_file.stat().st_size > 0:
                with open(url_file) as f:
                    file_mcp_url = f.read().strip()
                print(f"✅ data/.mcp-client-url exists: {file_mcp_url}")
            else:
                print("ℹ️  data/.mcp-client-url is missing; relying on MCP_CLIENT_SERVER_URL in IDE config")

            effective_url = entry_mcp_url or file_mcp_url
            if not effective_url:
                print("❌ No MCP URL source found. Run make register or set MCP_CLIENT_SERVER_URL")
                return False

            if not re.search(r"/servers/([a-f0-9-]+)/mcp", effective_url):
                print(f"❌ URL does not look like .../servers/UUID/mcp: {effective_url}")
                return False

            if entry_mcp_url:
                print("✅ Wrapper config includes MCP_CLIENT_SERVER_URL")

            print(f"✅ {ide_config.name} setup verification completed successfully")
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

    parser.add_argument("ide", nargs="?", help="IDE name (cursor, windsurf, vscode, claude, zed, all)")

    parser.add_argument(
        "--action",
        choices=[
            "install",
            "backup",
            "restore",
            "status",
            "refresh-jwt",
            "use-wrapper",
            "verify",
        ],
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
                print("Supported IDEs: cursor, windsurf, vscode, claude, zed, all")
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
