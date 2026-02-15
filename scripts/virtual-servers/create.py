#!/usr/bin/env python3
"""
Create virtual servers from virtual-servers.txt using the gateway API.
Bypasses the tools sync requirement that causes 500 errors.
"""

import os
import sys
import json
import subprocess
from pathlib import Path

# Get script directory
SCRIPT_DIR = Path(__file__).parent.parent
REPO_ROOT = SCRIPT_DIR.parent
CONFIG_DIR = Path(os.environ.get("CONFIG_DIR", REPO_ROOT / "config"))
VIRTUAL_SERVERS_FILE = (
    CONFIG_DIR / "virtual-servers.txt"
    if (CONFIG_DIR / "virtual-servers.txt").exists()
    else REPO_ROOT / "config" / "virtual-servers.txt"
)
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


def get_jwt():
    """Generate JWT using the gateway.sh script."""
    result = subprocess.run(
        ["bash", "-c", f"cd {SCRIPT_DIR.parent} && source .env && source {SCRIPT_DIR}/lib/gateway.sh && get_jwt"],
        capture_output=True,
        text=True,
        cwd=SCRIPT_DIR.parent,
    )
    if result.returncode != 0:
        print(f"Error generating JWT: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def create_virtual_server(jwt, name, gateways):
    """Create a virtual server via the gateway API."""
    import urllib.request

    # First, get all tools and filter by gateway
    tools_req = urllib.request.Request(
        f"{GATEWAY_URL}/tools?limit=0&include_pagination=false", headers={"Authorization": f"Bearer {jwt}"}
    )

    try:
        with urllib.request.urlopen(tools_req, timeout=DEFAULT_TIMEOUT) as response:
            tools_data = json.loads(response.read().decode("utf-8"))
            all_tools = tools_data if isinstance(tools_data, list) else tools_data.get("tools", [])
    except Exception as e:
        print(f"  ✗ {name} (error fetching tools: {e})")
        return False

    # Filter tools by gateway
    tool_ids = []
    for tool in all_tools:
        gateway_slug = (
            tool.get("gatewaySlug")
            or tool.get("gateway_slug")
            or tool.get("gateway", {}).get("slug")
            or tool.get("gateway", {}).get("name", "")
        )
        if gateway_slug in gateways:
            tool_ids.append(tool.get("id"))

    if not tool_ids:
        print(f"  ⚠ {name} (no tools found for gateways: {', '.join(gateways)})")
        return False

    # Limit to 60 tools (IDE limit)
    tool_ids = tool_ids[:60]

    # Create virtual server with correct API format
    data = {"server": {"name": name, "description": f"Tools from: {', '.join(gateways)}", "associated_tools": tool_ids}}

    req = urllib.request.Request(
        f"{GATEWAY_URL}/servers",
        data=json.dumps(data).encode("utf-8"),
        headers={"Authorization": f"Bearer {jwt}", "Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as response:
            result = json.loads(response.read().decode("utf-8"))
            server_id = result.get("id", "unknown")
            print(f"  ✓ {name} (created, {len(tool_ids)} tools, id: {server_id})")
            return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        if "already exists" in error_body.lower() or "duplicate" in error_body.lower():
            print(f"  ✓ {name} (already exists)")
            return True
        else:
            print(f"  ✗ {name} (error: {e.code})")
            if e.code == 400:
                print(f"      {error_body[:200]}")
            return False
    except urllib.error.URLError as ue:
        print(f"  ✗ {name} (network error: {ue.reason if hasattr(ue, 'reason') else str(ue)})")
        return False


def main():
    if not VIRTUAL_SERVERS_FILE.exists():
        print(f"Error: {VIRTUAL_SERVERS_FILE} not found", file=sys.stderr)
        sys.exit(1)

    print("\nCreating virtual servers from virtual-servers.txt...")
    print("=" * 60)

    # Generate JWT
    jwt = get_jwt()

    # Read virtual servers
    created = 0
    failed = 0

    with open(VIRTUAL_SERVERS_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split("|")
            if len(parts) != 2:
                continue

            name = parts[0].strip()
            gateways = [g.strip() for g in parts[1].split(",")]

            if create_virtual_server(jwt, name, gateways):
                created += 1
            else:
                failed += 1

    print("=" * 60)
    print(f"\nSummary: {created} created/updated, {failed} failed")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
