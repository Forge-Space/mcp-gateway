#!/usr/bin/env bash
# List enabled virtual servers from virtual-servers.txt
# Usage: ./list-enabled.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_DIR="${CONFIG_DIR:-$REPO_ROOT/config}"
VIRTUAL_SERVERS_FILE="$CONFIG_DIR/virtual-servers.txt"

# Check if file exists
if [[ ! -f "$VIRTUAL_SERVERS_FILE" ]]; then
    echo "Error: $VIRTUAL_SERVERS_FILE not found" >&2
    exit 1
fi

echo "Enabled Virtual Servers:"
echo "======================="
echo ""

enabled_count=0
disabled_count=0
total_count=0

while IFS= read -r line || [[ -n "$line" ]]; do
    # Skip empty lines and comments
    if [[ -z "$line" ]] || [[ "$line" =~ ^[[:space:]]*# ]]; then
        continue
    fi

    # Parse the line
    IFS='|' read -r name _ enabled_flag <<< "$line"

    # Count total servers
    total_count=$((total_count + 1))

    # Normalize enabled_flag: trim whitespace and convert to lowercase using parameter expansion
    enabled_flag="${enabled_flag//[[:space:]]/}"        # Convert to lowercase for comparison (portable way)
    enabled_flag=$(echo "$enabled_flag" | tr '[:upper:]' '[:lower:]')

    # Check enabled status (default is enabled if no flag, anything other than "false" is enabled)
    if [ -z "$enabled_flag" ] || [ "$enabled_flag" != "false" ]; then
        echo "✓ $name"
        enabled_count=$((enabled_count + 1))
    else
        disabled_count=$((disabled_count + 1))
    fi
done < "$VIRTUAL_SERVERS_FILE"

echo ""
echo "Summary:"
echo "  Enabled:  $enabled_count"
echo "  Disabled: $disabled_count"
echo "  Total:    $total_count"
