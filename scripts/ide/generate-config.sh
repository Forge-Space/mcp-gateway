#!/usr/bin/env bash
# Generate IDE configuration for MCP Gateway
# Usage: ./generate-config.sh --ide=windsurf --server=cursor-router [--token=JWT]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Default values
IDE=""
SERVER_NAME=""
GATEWAY_URL="${GATEWAY_URL:-http://localhost:4444}"
JWT_TOKEN="${JWT_TOKEN:-}"

# Parse arguments
for arg in "$@"; do
    case $arg in
        --ide=*)
            IDE="${arg#*=}"
            shift
            ;;
        --server=*)
            SERVER_NAME="${arg#*=}"
            shift
            ;;
        --url=*)
            GATEWAY_URL="${arg#*=}"
            shift
            ;;
        --token=*)
            JWT_TOKEN="${arg#*=}"
            shift
            ;;
        --help)
            echo "Usage: $0 --ide=<windsurf|cursor> --server=<server-name> [--url=<gateway-url>] [--token=<jwt>]"
            echo ""
            echo "Options:"
            echo "  --ide        Target IDE (windsurf or cursor)"
            echo "  --server     Virtual server name"
            echo "  --url        Gateway URL (default: http://localhost:4444)"
            echo "  --token      JWT token for authenticated access (optional)"
            echo ""
            echo "Environment Variables:"
            echo "  GATEWAY_URL  Gateway base URL"
            echo "  JWT_TOKEN    JWT authentication token"
            exit 0
            ;;
        *)
            echo "Unknown option: $arg"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Validate required arguments
if [[ -z "$IDE" ]]; then
    echo "Error: --ide is required"
    echo "Use --help for usage information"
    exit 1
fi

if [[ -z "$SERVER_NAME" ]]; then
    echo "Error: --server is required"
    echo "Use --help for usage information"
    exit 1
fi

# Validate IDE
if [[ "$IDE" != "windsurf" && "$IDE" != "cursor" ]]; then
    echo "Error: --ide must be 'windsurf' or 'cursor'"
    exit 1
fi

# Fetch server UUID from gateway API
echo "Fetching server UUID for '$SERVER_NAME'..." >&2

# Try to get server info from gateway
SERVER_UUID=""
if command -v curl &> /dev/null; then
    # Use curl to fetch server list
    RESPONSE=$(curl -s "${GATEWAY_URL}/api/virtual-servers" 2>/dev/null || echo "")

    if [[ -n "$RESPONSE" ]]; then
        # Try to extract UUID using basic text processing
        # This is a simplified version - in production, use jq or python
        SERVER_UUID=$(echo "$RESPONSE" | grep -o "\"name\":\"${SERVER_NAME}\"" -A 10 | grep -o "\"uuid\":\"[^\"]*\"" | head -1 | cut -d'"' -f4 || echo "")
    fi
fi

# If we couldn't fetch UUID, use server name as fallback
if [[ -z "$SERVER_UUID" ]]; then
    echo "Warning: Could not fetch server UUID from gateway. Using server name as UUID." >&2
    SERVER_UUID="$SERVER_NAME"
fi

echo "Generating $IDE configuration for server: $SERVER_NAME (UUID: $SERVER_UUID)" >&2

# Generate configuration using Python
python3 -c "
import json
import sys
sys.path.insert(0, '${PROJECT_ROOT}')

from tool_router.api.ide_config import generate_ide_config

config = generate_ide_config(
    ide='${IDE}',
    server_name='${SERVER_NAME}',
    server_uuid='${SERVER_UUID}',
    gateway_url='${GATEWAY_URL}',
    jwt_token='${JWT_TOKEN}' if '${JWT_TOKEN}' else None,
)

print(json.dumps(config, indent=2))
"

echo "" >&2
echo "Configuration generated successfully!" >&2
echo "Copy the JSON above to your IDE's mcp.json file." >&2
