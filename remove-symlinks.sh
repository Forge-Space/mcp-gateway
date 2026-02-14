#!/usr/bin/env bash
# Temporary script to remove all symlinks from scripts root

set -e
cd "$(dirname "$0")"

echo "Removing symlinks from scripts/ root..."

rm -f scripts/register-gateways.sh
rm -f scripts/list-prompts.sh
rm -f scripts/cursor-mcp-wrapper.sh
rm -f scripts/use-cursor-wrapper.sh
rm -f scripts/refresh-cursor-jwt.sh
rm -f scripts/verify-cursor-setup.sh
rm -f scripts/list-servers.sh
rm -f scripts/cleanup-duplicate-servers.sh
rm -f scripts/create-virtual-servers.py
rm -f scripts/create_jwt_token_standalone.py
rm -f scripts/check-docker-updates.sh
rm -f scripts/check-mcp-registry.py

echo "✓ All symlinks removed"
echo "Remaining in scripts/:"
ls -1 scripts/ | grep -v "^lib$" | grep -v "^gateway$" | grep -v "^cursor$" | grep -v "^virtual-servers$" | grep -v "^utils$" | grep -v "^README.md$" || echo "  (only subdirectories and README.md)"
