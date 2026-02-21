#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/logging.sh"

GATEWAY_URL="${GATEWAY_URL:-http://localhost:8000}"

if [[ -f "$SCRIPT_DIR/../.env" ]]; then
    source "$SCRIPT_DIR/../.env"
fi

if [[ -z "${GATEWAY_JWT:-}" ]]; then
    if command -v python3 &>/dev/null; then
        GATEWAY_JWT=$(python3 "$SCRIPT_DIR/../scripts/utils/create-jwt.py" 2>/dev/null) || {
            log_error "Failed to generate JWT locally"
            exit 1
        }
    else
        log_error "GATEWAY_JWT not set and python3 not available"
        exit 1
    fi
fi

log_info "Starting enhanced virtual server registration..."
python3 "$SCRIPT_DIR/virtual-server-manager.py" register-enhanced
log_info "Enhanced registration completed."
