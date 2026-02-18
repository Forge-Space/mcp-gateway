#!/bin/bash

# Enhanced Virtual Server Registration Script
# Uses virtual-server-manager.py for conditional server creation
# Only creates servers that are enabled (skips disabled ones)

set -euo pipefail

# Source utility functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/logging.sh"

# Load configuration
CONFIG_DIR="${CONFIG_DIR:-$SCRIPT_DIR/../config}"
GATEWAY_URL="${GATEWAY_URL:-http://localhost:8000}"

# Get JWT token
if [[ -f "$SCRIPT_DIR/../.env" ]]; then
    source "$SCRIPT_DIR/../.env"
fi

if [[ -z "${GATEWAY_JWT:-}" ]]; then
    if command -v python3 &>/dev/null; then
        GATEWAY_JWT=$(python3 "$SCRIPT_DIR/../scripts/utils/create-jwt.py" 2>/dev/null)
        if [[ $? -ne 0 ]]; then
            log_error "Failed to generate JWT locally"
            exit 1
        fi
    else
        log_error "GATEWAY_JWT not set and python3 not available"
        exit 1
    fi
fi

log_info "Starting enhanced virtual server registration..."

# Use virtual server manager for conditional creation
python3 "$SCRIPT_DIR/virtual-server-manager.py" register-enhanced

log_info "Enhanced registration completed."
