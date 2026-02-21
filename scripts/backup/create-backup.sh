#!/bin/bash

# Create comprehensive backup of project before cleanup
set -euo pipefail

PROJECT_NAME=${1:-"forge-mcp-gateway"}
BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/${PROJECT_NAME}-${TIMESTAMP}.tar.gz"

echo "🔄 Creating backup for ${PROJECT_NAME}..."

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Create backup with all important files
echo "📦 Packing project files..."
tar -czf "${BACKUP_FILE}" \
    --exclude=node_modules \
    --exclude=.git \
    --exclude=dist \
    --exclude=build \
    --exclude=coverage \
    --exclude=.pytest_cache \
    --exclude=.ruff_cache \
    --exclude=.venv \
    --exclude="*.log" \
    --exclude="backups" \
    .

# Create backup manifest
echo "📋 Creating backup manifest..."
cat > "${BACKUP_DIR}/${PROJECT_NAME}-${TIMESTAMP}-manifest.txt" << EOF
Backup Manifest for ${PROJECT_NAME}
=====================================
Created: $(date)
Timestamp: ${TIMESTAMP}
Backup File: ${BACKUP_FILE}

Files Included:
- All source code
- Configuration files
- Documentation
- Scripts
- Docker files
- Environment templates

Files Excluded:
- node_modules/
- .git/
- dist/
- build/
- coverage/
- .pytest_cache/
- .ruff_cache/
- .venv/
- *.log
- backups/

Git Status:
$(git status --porcelain 2>/dev/null || echo "Not a git repository")

Git Branch:
$(git branch --show-current 2>/dev/null || echo "Not a git repository")

Git Last Commit:
$(git log -1 --oneline 2>/dev/null || echo "Not a git repository")
EOF

echo "✅ Backup created successfully!"
echo "📍 Location: ${BACKUP_FILE}"
echo "📋 Manifest: ${BACKUP_DIR}/${PROJECT_NAME}-${TIMESTAMP}-manifest.txt"
echo ""
echo "🔄 To restore:"
echo "tar -xzf ${BACKUP_FILE}"
