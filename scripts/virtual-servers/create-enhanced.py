#!/usr/bin/env python3
"""
Enhanced Virtual Server Creation with Enabled Flag Support
Creates virtual servers from enhanced YAML configuration with conditional creation.
"""
import os
import sys
import json
import subprocess
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Get script directory — all paths are derived from this trusted constant.
SCRIPT_DIR = Path(__file__).parent.parent
REPO_ROOT = SCRIPT_DIR.parent
CONFIG_DIR = REPO_ROOT / "config"
VIRTUAL_SERVERS_FILE = CONFIG_DIR / "virtual-servers-enhanced.yml"
LEGACY_FILE = CONFIG_DIR / "virtual-servers.txt"
GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://localhost:4444")

# Timeout configuration (in seconds)
_timeout_env = os.environ.get("GATEWAY_TIMEOUT", "30")
try:
    DEFAULT_TIMEOUT = int(_timeout_env)
    if DEFAULT_TIMEOUT <= 0:
        raise ValueError("Timeout must be positive")
except ValueError:
    print(f"Warning: Invalid GATEWAY_TIMEOUT value '{_timeout_env}', using default 30 seconds", file=sys.stderr)
    DEFAULT_TIMEOUT = 30

class VirtualServerConfig:
    """Virtual server configuration with enabled flag support."""

    def __init__(self, name: str, enabled: bool, gateways: List[str], description: str = ""):
        self.name = name
        self.enabled = enabled
        self.gateways = gateways
        self.description = description or f"Tools from: {', '.join(gateways)}"

    @classmethod
    def from_yaml_entry(cls, name: str, config: Dict) -> Optional['VirtualServerConfig']:
        """Parse a YAML configuration entry into VirtualServerConfig."""
        if not isinstance(config, dict):
            return None

        enabled = config.get('enabled', True)
        gateways = config.get('gateways', [])
        description = config.get('description', f"Tools from: {', '.join(gateways)}")

        # Ensure gateways is a list
        if isinstance(gateways, str):
            gateways = [gateways]
        elif not isinstance(gateways, list):
            gateways = []

        return cls(name, enabled, gateways, description)

    @classmethod
    def from_legacy_line(cls, line: str) -> Optional['VirtualServerConfig']:
        """Parse a legacy virtual-servers.txt line into VirtualServerConfig."""
        line = line.strip()
        if not line or line.startswith('#'):
            return None

        parts = line.split('|')
        if len(parts) != 2:
            return None

        name = parts[0].strip()
        gateways = [g.strip() for g in parts[1].split(',')]

        # Legacy configurations are enabled by default
        enabled = True
        description = f"Tools from: {', '.join(gateways)}"

        return cls(name, enabled, gateways, description)

def get_jwt():
    """Generate JWT using the gateway.sh script."""
    result = subprocess.run(
        ["bash", "-c", f"cd {SCRIPT_DIR.parent} && source .env && source {SCRIPT_DIR}/lib/gateway.sh && get_jwt"],
        capture_output=True,
        text=True,
        cwd=SCRIPT_DIR.parent
    )
    if result.returncode != 0:
        print(f"Error generating JWT: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()

def get_existing_servers(jwt: str) -> Dict[str, Dict]:
    """Get existing virtual servers from the gateway."""
    import urllib.request

    try:
        req = urllib.request.Request(
            f"{GATEWAY_URL}/servers?limit=0&include_pagination=false",
            headers={"Authorization": f"Bearer {jwt}"}
        )
        with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as response:
            servers_data = json.loads(response.read().decode('utf-8'))
            servers = servers_data if isinstance(servers_data, list) else servers_data.get('servers', [])
            return {server.get('name', server.get('id', '')): server for server in servers}
    except Exception as e:
        print(f"Warning: Could not fetch existing servers: {e}", file=sys.stderr)
        return {}

def create_virtual_server(jwt: str, config: VirtualServerConfig) -> bool:
    """Create a virtual server via the gateway API."""
    import urllib.request

    # First, get all tools and filter by gateway
    tools_req = urllib.request.Request(
        f"{GATEWAY_URL}/tools?limit=0&include_pagination=false",
        headers={"Authorization": f"Bearer {jwt}"}
    )

    try:
        with urllib.request.urlopen(tools_req, timeout=DEFAULT_TIMEOUT) as response:
            tools_data = json.loads(response.read().decode('utf-8'))
            all_tools = tools_data if isinstance(tools_data, list) else tools_data.get('tools', [])
    except Exception as e:
        print(f"  ✗ {config.name} (error fetching tools: {e})")
        return False

    # Filter tools by gateway
    tool_ids = []
    for tool in all_tools:
        gateway_slug = (tool.get('gatewaySlug') or
                       tool.get('gateway_slug') or
                       tool.get('gateway', {}).get('slug') or
                       tool.get('gateway', {}).get('name', ''))
        if gateway_slug in config.gateways:
            tool_ids.append(tool.get('id'))

    if not tool_ids:
        print(f"  ⚠ {config.name} (no tools found for gateways: {', '.join(config.gateways)})")
        return False

    # Limit to 60 tools (IDE limit)
    tool_ids = tool_ids[:60]

    # Create virtual server with correct API format
    data = {
        "server": {
            "name": config.name,
            "description": config.description,
            "associated_tools": tool_ids,
            "enabled": config.enabled  # Add enabled flag to API call
        }
    }

    req = urllib.request.Request(
        f"{GATEWAY_URL}/servers",
        data=json.dumps(data).encode('utf-8'),
        headers={
            "Authorization": f"Bearer {jwt}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as response:
            result = json.loads(response.read().decode('utf-8'))
            server_id = result.get('id', 'unknown')
            status_icon = "✓" if config.enabled else "○"
            status_text = "enabled" if config.enabled else "disabled"
            print(f"  {status_icon} {config.name} ({status_text}, {len(tool_ids)} tools, id: {server_id})")
            return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        if "already exists" in error_body.lower() or "duplicate" in error_body.lower():
            status_icon = "✓" if config.enabled else "○"
            status_text = "enabled" if config.enabled else "disabled"
            print(f"  {status_icon} {config.name} (already exists, {status_text})")
            return True
        else:
            print(f"  ✗ {config.name} (error: {e.code})")
            if e.code == 400:
                print(f"      {error_body[:200]}")
            return False
    except urllib.error.URLError as ue:
        print(f"  ✗ {config.name} (network error: {ue.reason if hasattr(ue, 'reason') else str(ue)})")
        return False

def delete_virtual_server(jwt: str, server_name: str, server_id: str) -> bool:
    """Delete a virtual server via the gateway API."""
    import urllib.request

    req = urllib.request.Request(
        f"{GATEWAY_URL}/servers/{server_id}",
        headers={"Authorization": f"Bearer {jwt}"},
        method="DELETE"
    )

    try:
        with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as response:
            print(f"  ✗ {server_name} (deleted, was disabled)")
            return True
    except Exception as e:
        print(f"  ✗ {server_name} (failed to delete: {e})")
        return False

def load_configurations() -> List[VirtualServerConfig]:
    """Load virtual server configurations from YAML and legacy files."""
    configs = []

    # Load enhanced YAML configuration
    if VIRTUAL_SERVERS_FILE.exists():
        try:
            with open(VIRTUAL_SERVERS_FILE, 'r') as f:
                yaml_data = yaml.safe_load(f)
                virtual_servers = yaml_data.get('virtual_servers', {})

                for name, config in virtual_servers.items():
                    vs_config = VirtualServerConfig.from_yaml_entry(name, config)
                    if vs_config:
                        configs.append(vs_config)
        except Exception as e:
            print(f"Error loading enhanced YAML configuration: {e}", file=sys.stderr)
            print("Falling back to legacy configuration...", file=sys.stderr)

    # Load legacy configuration as fallback
    elif LEGACY_FILE.exists():
        print("Warning: Using legacy virtual-servers.txt format. Consider migrating to virtual-servers-enhanced.yml", file=sys.stderr)
        with open(LEGACY_FILE, 'r') as f:
            for line in f:
                config = VirtualServerConfig.from_legacy_line(line)
                if config:
                    configs.append(config)
    else:
        print(f"Error: Neither {VIRTUAL_SERVERS_FILE} nor {LEGACY_FILE} found", file=sys.stderr)
        sys.exit(1)

    return configs

def main():
    # Parse command line arguments
    force_refresh = "--force-refresh" in sys.argv
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("DRY RUN MODE: No actual changes will be made")
        print("=" * 60)

    configurations = load_configurations()

    if not configurations:
        print("No virtual server configurations found")
        return

    print(f"\nProcessing {len(configurations)} virtual server configurations...")
    print("=" * 60)

    # Generate JWT
    jwt = get_jwt()

    # Get existing servers
    existing_servers = get_existing_servers(jwt) if not dry_run else {}

    # Track statistics
    created = 0
    updated = 0
    disabled = 0
    deleted = 0
    failed = 0

    # Process each configuration
    for config in configurations:
        if not config.enabled:
            # Handle disabled servers
            if config.name in existing_servers and force_refresh:
                if not dry_run:
                    if delete_virtual_server(jwt, config.name, existing_servers[config.name].get('id', '')):
                        deleted += 1
                    else:
                        failed += 1
                else:
                    print(f"  ○ {config.name} (would be deleted - disabled)")
                    deleted += 1
            else:
                print(f"  ○ {config.name} (disabled - skipped)")
                disabled += 1
        else:
            # Handle enabled servers
            if not dry_run:
                if create_virtual_server(jwt, config):
                    if config.name in existing_servers:
                        updated += 1
                    else:
                        created += 1
                else:
                    failed += 1
            else:
                status_icon = "✓" if config.enabled else "○"
                print(f"  {status_icon} {config.name} (would be created/updated)")
                created += 1

    print("=" * 60)
    print(f"\nSummary:")
    print(f"  Created: {created}")
    print(f"  Updated: {updated}")
    print(f"  Disabled: {disabled}")
    if force_refresh:
        print(f"  Deleted: {deleted}")
    print(f"  Failed: {failed}")

    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
