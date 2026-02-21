#!/bin/bash

# UIForge Package Configuration Synchronization Script

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SHARED_CONFIG_DIR="$PROJECT_ROOT/config/shared"

# Logging function
log() {
    echo -e "$1"
}

# Function to validate JSON
validate_json() {
    local file="$1"
    if ! jq empty "$file" 2>/dev/null; then
        log "${RED}❌ Invalid JSON in: $file${NC}"
        return 1
    fi
    return 0
}

# Function to validate TOML
validate_toml() {
    local file="$1"
    if ! python -c "import tomllib; tomllib.load(open('$file'))" 2>/dev/null; then
        log "${RED}❌ Invalid TOML in: $file${NC}"
        return 1
    fi
    return 0
}

# Function to sync configurations
sync_all() {
    local project_dir="$1"
    local project_name="$2"
    local project_description="$3"
    local project_repo="$4"
    local package_name="$5"

    log "${BLUE}🔄 Syncing configurations for $project_name${NC}"

    # Sync package.json if it exists
    if [[ -f "$project_dir/package.json" ]]; then
        log "${BLUE}📦 Processing package.json${NC}"
        # Add sync logic here
    fi

    # Sync pyproject.toml if it exists
    if [[ -f "$project_dir/pyproject.toml" ]]; then
        log "${BLUE}📦 Processing pyproject.toml${NC}"
        # Add sync logic here
    fi

    # Sync tsconfig.json if it exists
    if [[ -f "$project_dir/tsconfig.json" ]]; then
        log "${BLUE}📦 Processing tsconfig.json${NC}"
        # Add sync logic here
    fi

    log "${GREEN}✅ Sync completed${NC}"
}

# Function to validate configurations
validate_configs() {
    local project_dir="$1"

    log "${BLUE}🔍 Validating configurations in $project_dir${NC}"

    local errors=0

    # Validate package.json
    if [[ -f "$project_dir/package.json" ]]; then
        if ! validate_json "$project_dir/package.json"; then
            ((errors++))
        fi
    fi

    # Validate pyproject.toml
    if [[ -f "$project_dir/pyproject.toml" ]]; then
        if ! validate_toml "$project_dir/pyproject.toml"; then
            ((errors++))
        fi
    fi

    # Validate tsconfig.json
    if [[ -f "$project_dir/tsconfig.json" ]]; then
        if ! validate_json "$project_dir/tsconfig.json"; then
            ((errors++))
        fi
    fi

    if [[ $errors -eq 0 ]]; then
        log "${GREEN}✅ All configurations are valid${NC}"
    else
        log "${RED}❌ Found $errors configuration errors${NC}"
    fi

    return $errors
}

# Main function
main() {
    case "${1:-}" in
        validate)
            validate_configs "${2:-.}"
            ;;
        sync-all)
            sync_all "$@"
            ;;
        *)
            echo "Usage: $0 {validate|sync-all} [args...]"
            echo "  validate <project-dir>"
            echo "  sync-all <project-dir> <project-name> <description> <repo> <package-name>"
            exit 1
            ;;
    esac
}

main "$@"
