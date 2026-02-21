#!/usr/bin/env bash
# Temporary script to remove all symlinks from scripts root

set -euo pipefail

# Get repository root and change to it
SCRIPT_DIR="$(dirname "$0")"
REPO_ROOT="$(cd "$SCRIPT_DIR" && git rev-parse --show-toplevel)"
if ! cd "$REPO_ROOT"; then
    echo "Error: Failed to change to repository root: $REPO_ROOT" >&2
    exit 1
fi

echo "Removing symlinks from scripts/ root..."

# List of symlinks to remove
SYMLINKS=(
    "scripts/register-gateways.sh"
    "scripts/list-prompts.sh"
    "scripts/cursor-mcp-wrapper.sh"
    "scripts/use-cursor-wrapper.sh"
    "scripts/refresh-cursor-jwt.sh"
    "scripts/verify-cursor-setup.sh"
    "scripts/list-servers.sh"
    "scripts/cleanup-duplicate-servers.sh"
    "scripts/create-virtual-servers.py"
    "scripts/create_jwt_token_standalone.py"
    "scripts/check-docker-updates.sh"
    "scripts/check-mcp-registry.py"
)

# Remove each symlink (only if it's actually a symlink)
for symlink in "${SYMLINKS[@]}"; do
    if [ -L "$symlink" ]; then
        rm -f "$symlink"
    elif [ -e "$symlink" ]; then
        echo "Skipping non-symlink: $symlink" >&2
    fi
done

echo "✓ All symlinks removed"
echo "Remaining in scripts/:"
ls -1 scripts/ | grep -v "^lib$" | grep -v "^gateway$" | grep -v "^cursor$" | grep -v "^virtual-servers$" | grep -v "^utils$" | grep -v "^README.md$" || echo "  (only subdirectories and README.md)"
