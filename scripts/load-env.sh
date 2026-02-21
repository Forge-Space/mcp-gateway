#!/bin/bash

# Environment Configuration Loader for UIForge Projects
# Loads environment files in the correct order: .env.shared → .env.{environment} → .env.local
# Usage: source scripts/load-env.sh [environment]

set -euo pipefail

# Default environment
ENVIRONMENT=${1:-development}

echo "🔧 Loading environment configuration for: ${ENVIRONMENT}"
echo "📋 Load order: .env.shared → .env.${ENVIRONMENT} → .env.local"

# Function to load environment file if it exists
load_env_file() {
    local env_file="$1"
    if [[ -f "$env_file" ]]; then
        echo "✅ Loading: $env_file"
        set -a
        source "$env_file"
        set +a
    else
        echo "⚠️  Skipping: $env_file (not found)"
    fi
}

# Load environment files in order
load_env_file ".env.shared"
load_env_file ".env.${ENVIRONMENT}"
load_env_file ".env.local"

echo "🎉 Environment configuration loaded successfully!"
echo ""
echo "📊 Environment variables loaded:"
echo "   - GATEWAY_HOST=${GATEWAY_HOST:-not set}"
echo "   - GATEWAY_PORT=${GATEWAY_PORT:-not set}"
echo "   - LOG_LEVEL=${LOG_LEVEL:-not set}"
echo "   - AUTH_REQUIRED=${AUTH_REQUIRED:-not set}"
echo "   - FORGE_SERVICE_MANAGER_PORT=${FORGE_SERVICE_MANAGER_PORT:-not set}"
echo "   - FORGE_UI_PORT=${FORGE_UI_PORT:-not set}"
echo ""
echo "💡 Tip: Use 'env | grep FORGE_' to see all FORGE_* variables"
