#!/usr/bin/env python3
"""
Check MCP Registry for new or updated servers.

Compares current gateways.txt and docker-compose.yml with the MCP Registry
to identify new servers or version updates.
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


def load_current_servers() -> Dict[str, Set[str]]:
    """Load currently configured servers from gateways.txt and docker-compose.yml."""
    servers = {
        "active_local": set(),
        "active_remote": set(),
        "commented": set(),
    }

    script_dir = Path(__file__).parent
    gateways_file = script_dir / "gateways.txt"

    if gateways_file.exists():
        with open(gateways_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("# Removed") or line.startswith("# -"):
                    continue

                if line.startswith("#"):
                    # Commented server
                    match = re.match(r"#\s*([^|]+)\|", line)
                    if match:
                        servers["commented"].add(match.group(1).strip())
                elif "|" in line and not line.startswith("#"):
                    # Active server
                    parts = line.split("|")
                    name = parts[0].strip()
                    url = parts[1].strip()

                    if url.startswith("http://") and not url.startswith("http://localhost"):
                        servers["active_local"].add(name)
                    else:
                        servers["active_remote"].add(name)

    return servers


def fetch_registry_servers() -> List[Dict]:
    """Fetch server list from MCP Registry API."""
    registry_url = "https://registry.modelcontextprotocol.io/api/servers"

    try:
        req = Request(registry_url)
        req.add_header("User-Agent", "mcp-gateway-checker/1.0")

        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data.get("servers", [])
    except (URLError, HTTPError) as e:
        print(f"Error fetching registry: {e}", file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing registry response: {e}", file=sys.stderr)
        return []


def generate_report(current: Dict[str, Set[str]], registry: List[Dict]) -> str:
    """Generate markdown report of new and updated servers."""
    report_lines = ["# MCP Server Update Report", ""]

    # Extract current server names (all categories combined)
    current_all = (
        current["active_local"] | current["active_remote"] | current["commented"]
    )
    current_all_lower = {name.lower() for name in current_all}

    # Find new servers
    new_servers = []
    for server in registry:
        name = server.get("name", "")
        if name and name.lower() not in current_all_lower:
            new_servers.append(server)

    if new_servers:
        report_lines.extend(["## New Servers Available", ""])
        for server in new_servers[:10]:  # Limit to top 10
            name = server.get("name", "Unknown")
            desc = server.get("description", "No description")
            url = server.get("url", "")
            report_lines.append(f"- **{name}**: {desc}")
            if url:
                report_lines.append(f"  - URL: `{url}`")
        report_lines.append("")
    else:
        report_lines.extend(["## New Servers Available", "", "No new servers found.", ""])

    # Check commented servers status
    if current["commented"]:
        report_lines.extend(["## Commented Servers Status", ""])
        for name in sorted(current["commented"]):
            if name.lower() in ["sqlite", "github"]:
                report_lines.append(
                    f"- **{name}**: Local server, requires environment variables"
                )
            elif name.lower() in ["cloudflare-observability", "cloudflare-bindings"]:
                report_lines.append(
                    f"- **{name}**: Requires Cloudflare authentication in Admin UI"
                )
            elif name.lower() == "v0":
                report_lines.append(
                    f"- **{name}**: Requires Vercel authentication in Admin UI"
                )
            else:
                report_lines.append(f"- **{name}**: Commented, check documentation")
        report_lines.append("")

    # Summary
    report_lines.extend([
        "## Summary",
        "",
        f"- **Active Local Servers**: {len(current['active_local'])}",
        f"- **Active Remote Servers**: {len(current['active_remote'])}",
        f"- **Commented Servers**: {len(current['commented'])}",
        f"- **New Servers Available**: {len(new_servers)}",
        "",
        "---",
        "",
        "To add a new server:",
        "1. Add to `config/gateways.txt` with format: `Name|URL|Transport`",
        "2. Run `make register` to register the gateway",
        "3. For remote servers requiring auth, configure in Admin UI",
    ])

    return "\n".join(report_lines)


def main():
    """Main execution."""
    print("Checking MCP Registry for updates...")

    current_servers = load_current_servers()
    registry_servers = fetch_registry_servers()

    if not registry_servers:
        print("Warning: Could not fetch registry data", file=sys.stderr)
        sys.exit(1)

    report = generate_report(current_servers, registry_servers)

    # Write report to file
    script_dir = Path(__file__).parent
    report_file = script_dir.parent / "mcp-registry-report.md"

    with open(report_file, "w") as f:
        f.write(report)

    print(f"Report generated: {report_file}")
    print("\n" + report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
