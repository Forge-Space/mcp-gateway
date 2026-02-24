#!/usr/bin/env python3
"""Health check script for dribbble-mcp container."""

import subprocess
import sys
import urllib.error
import urllib.request


def main():
    """Check health via HTTP endpoint first, then process check."""
    # Try HTTP health check first (service-manager may provide this)
    try:
        response = urllib.request.urlopen("http://localhost:8035/health", timeout=5)
        if response.getcode() == 200:
            sys.exit(0)
    except Exception:
        pass

    # Fall back to process check
    try:
        result = subprocess.run(
            ["pgrep", "-f", "dribbble_mcp"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    main()
