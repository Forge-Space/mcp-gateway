#!/usr/bin/env bash
# Standardized error handling for MCP Gateway scripts

set -euo pipefail

# Standard exit codes (exported for use in sourcing scripts)
export E_SUCCESS=0
export E_MISSING_DEPENDENCY=1
export E_GATEWAY_UNREACHABLE=2
export E_CONFIG_INVALID=3
export E_AUTH_FAILED=4
export E_DOCKER_ERROR=5

# Global error handler
handle_error() {
    local exit_code=$?
    local line_no=$1
    log_err "Error on line $line_no (exit code: $exit_code)"
    exit "$exit_code"
}

trap 'handle_error ${LINENO}' ERR

# Dependency checker
require_command() {
    local cmd="$1"
    local install_hint="${2:-}"
    if ! command -v "$cmd" &>/dev/null; then
        log_err "Required command not found: $cmd"
        [[ -n "$install_hint" ]] && log_info "Install with: $install_hint"
        exit "$E_MISSING_DEPENDENCY"
    fi
}

# Check gateway reachability
check_gateway() {
    local url="${1:-http://localhost:4444}"
    local timeout="${2:-5}"
    if ! curl -sf --max-time "$timeout" "$url/health" &>/dev/null; then
        log_err "Gateway unreachable at $url"
        log_info "Ensure gateway is running: make start"
        exit "$E_GATEWAY_UNREACHABLE"
    fi
}

# Check Docker is running
check_docker() {
    if ! docker info &>/dev/null; then
        log_err "Docker is not running or not accessible"
        log_info "Start Docker Desktop or ensure Docker daemon is running"
        exit "$E_DOCKER_ERROR"
    fi
}

# Validate environment variable is set
require_env() {
    local var_name="$1"
    local hint="${2:-}"
    if [[ -z "${!var_name:-}" ]]; then
        log_err "Required environment variable not set: $var_name"
        [[ -n "$hint" ]] && log_info "$hint"
        exit "$E_CONFIG_INVALID"
    fi
}

# Validate file exists
require_file() {
    local file_path="$1"
    local hint="${2:-}"
    if [[ ! -f "$file_path" ]]; then
        log_err "Required file not found: $file_path"
        [[ -n "$hint" ]] && log_info "$hint"
        exit "$E_CONFIG_INVALID"
    fi
}

# Validate directory exists
require_directory() {
    local dir_path="$1"
    local hint="${2:-}"
    if [[ ! -d "$dir_path" ]]; then
        log_err "Required directory not found: $dir_path"
        [[ -n "$hint" ]] && log_info "$hint"
        exit "$E_CONFIG_INVALID"
    fi
}
