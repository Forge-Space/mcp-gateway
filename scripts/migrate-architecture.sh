#!/usr/bin/env bash
# Architecture Migration Script for MCP Gateway
# Migrates from flat structure to monorepo-style apps/ organization
# Safe, incremental, with rollback capability

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${PROJECT_ROOT}/.migration-backup-$(date +%Y%m%d-%H%M%S)"
DRY_RUN="${DRY_RUN:-false}"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# Backup current state
backup_project() {
    log_info "Creating backup at ${BACKUP_DIR}..."
    mkdir -p "${BACKUP_DIR}"

    # Backup critical directories
    [ -d "${PROJECT_ROOT}/tool_router" ] && cp -r "${PROJECT_ROOT}/tool_router" "${BACKUP_DIR}/" || log_warning "tool_router not found, skipping"
    [ -d "${PROJECT_ROOT}/web-admin" ] && cp -r "${PROJECT_ROOT}/web-admin" "${BACKUP_DIR}/" || log_warning "web-admin not found, skipping"
    [ -d "${PROJECT_ROOT}/src" ] && cp -r "${PROJECT_ROOT}/src" "${BACKUP_DIR}/" || log_warning "src not found, skipping"
    [ -d "${PROJECT_ROOT}/config" ] && cp -r "${PROJECT_ROOT}/config" "${BACKUP_DIR}/" || log_warning "config not found, skipping"
    [ -d "${PROJECT_ROOT}/scripts" ] && cp -r "${PROJECT_ROOT}/scripts" "${BACKUP_DIR}/" || log_warning "scripts not found, skipping"

    # Backup config files
    [ -f "${PROJECT_ROOT}/pyproject.toml" ] && cp "${PROJECT_ROOT}/pyproject.toml" "${BACKUP_DIR}/" || log_warning "pyproject.toml not found, skipping"
    [ -f "${PROJECT_ROOT}/docker-compose.yml" ] && cp "${PROJECT_ROOT}/docker-compose.yml" "${BACKUP_DIR}/" || log_warning "docker-compose.yml not found, skipping"
    cp "${PROJECT_ROOT}/Makefile" "${BACKUP_DIR}/" 2>/dev/null || true

    log_success "Backup created successfully"
}

# Phase 1: Create new directory structure
phase1_create_structure() {
    log_info "Phase 1: Creating new directory structure..."

    if [[ "${DRY_RUN}" == "true" ]]; then
        log_warning "DRY RUN: Would create directories:"
        echo "  - apps/tool-router/src/"
        echo "  - apps/tool-router/tests/"
        echo "  - apps/web-admin/src/"
        echo "  - apps/mcp-client/src/"
        echo "  - docker/"
        echo "  - config/development/"
        echo "  - config/production/"
        echo "  - config/test/"
        return 0
    fi

    cd "${PROJECT_ROOT}"

    # Create apps structure
    mkdir -p apps/tool-router/src
    mkdir -p apps/tool-router/tests/{unit,integration,e2e}
    mkdir -p apps/web-admin/src
    mkdir -p apps/mcp-client/src

    # Create docker directory
    mkdir -p docker

    # Create config environments
    mkdir -p config/{development,production,test,schemas}

    log_success "Phase 1 complete: Directory structure created"
}

# Phase 2: Move tool-router
phase2_move_tool_router() {
    log_info "Phase 2: Moving tool-router to apps/..."

    if [[ "${DRY_RUN}" == "true" ]]; then
        log_warning "DRY RUN: Would move tool_router/ to apps/tool-router/src/"
        return 0
    fi

    cd "${PROJECT_ROOT}"

    # Move tool_router source
    if [[ -d "tool_router" ]]; then
        log_info "Moving tool_router/ to apps/tool-router/src/tool_router/"
        cp -r tool_router apps/tool-router/src/

        # Move pyproject.toml and requirements.txt
        cp pyproject.toml apps/tool-router/
        cp requirements.txt apps/tool-router/

        log_success "tool-router moved successfully"
    else
        log_error "tool_router directory not found"
        return 1
    fi
}

# Phase 3: Remove legacy files
phase3_remove_legacy() {
    log_info "Phase 3: Removing legacy duplicate files..."

    if [[ "${DRY_RUN}" == "true" ]]; then
        log_warning "DRY RUN: Would remove:"
        echo "  - apps/tool-router/src/tool_router/server.py (legacy)"
        echo "  - apps/tool-router/src/tool_router/gateway_client.py (legacy)"
        echo "  - apps/tool-router/src/tool_router/scoring.py (legacy)"
        echo "  - apps/tool-router/src/tool_router/args.py (legacy)"
        return 0
    fi

    cd "${PROJECT_ROOT}/apps/tool-router/src/tool_router"

    # Remove legacy files (superseded by modular versions)
    local legacy_files=(
        "server.py"
        "gateway_client.py"
        "scoring.py"
        "args.py"
    )

    for file in "${legacy_files[@]}"; do
        if [[ -f "${file}" ]]; then
            log_info "Removing legacy file: ${file}"
            rm "${file}"
        fi
    done

    log_success "Phase 3 complete: Legacy files removed"
}

# Phase 4: Consolidate tests
phase4_consolidate_tests() {
    log_info "Phase 4: Consolidating test files..."

    if [[ "${DRY_RUN}" == "true" ]]; then
        log_warning "DRY RUN: Would move test_*.py files to tests/unit/"
        return 0
    fi

    cd "${PROJECT_ROOT}/apps/tool-router/src/tool_router"

    # Move root-level test files to tests/unit/
    local test_files=(
        "test_args.py"
        "test_gateway_client.py"
        "test_scoring.py"
    )

    for test_file in "${test_files[@]}"; do
        if [[ -f "${test_file}" ]]; then
            log_info "Moving ${test_file} to tests/unit/"
            mv "${test_file}" "../../tests/unit/"
        fi
    done

    # Move existing tests/ directory content
    if [[ -d "tests" ]]; then
        log_info "Merging existing tests/ directory..."
        cp -r tests/* ../../tests/ 2>/dev/null || true
        rm -rf tests
    fi

    log_success "Phase 4 complete: Tests consolidated"
}

# Phase 5: Update import paths
phase5_update_imports() {
    log_info "Phase 5: Updating import paths..."

    if [[ "${DRY_RUN}" == "true" ]]; then
        log_warning "DRY RUN: Would update import statements in all Python files"
        return 0
    fi

    cd "${PROJECT_ROOT}/apps/tool-router"

    # Find all Python files and update imports
    find src/tool_router -name "*.py" -type f -exec sed -i.bak \
        -e 's/from tool_router\.server import/from tool_router.core.server import/g' \
        -e 's/from tool_router\.gateway_client import/from tool_router.gateway.client import/g' \
        -e 's/from tool_router\.scoring import/from tool_router.scoring.matcher import/g' \
        -e 's/from tool_router\.args import/from tool_router.args.builder import/g' \
        {} \;

    # Remove backup files
    find src/tool_router -name "*.py.bak" -delete

    log_success "Phase 5 complete: Import paths updated"
}

# Phase 6: Move web-admin
phase6_move_web_admin() {
    log_info "Phase 6: Moving web-admin to apps/..."

    if [[ "${DRY_RUN}" == "true" ]]; then
        log_warning "DRY RUN: Would move web-admin/ to apps/web-admin/"
        return 0
    fi

    cd "${PROJECT_ROOT}"

    if [[ -d "web-admin" ]]; then
        log_info "Moving web-admin/ to apps/web-admin/"

        # Move app directory to src
        mkdir -p apps/web-admin/src
        mv web-admin/app apps/web-admin/src/

        # Move other directories
        [[ -d "web-admin/components" ]] && mv web-admin/components apps/web-admin/src/
        [[ -d "web-admin/lib" ]] && mv web-admin/lib apps/web-admin/src/

        # Move config files
        mv web-admin/*.{json,ts,mjs,local} apps/web-admin/ 2>/dev/null || true

        log_success "web-admin moved successfully"
    fi
}

# Phase 7: Move mcp-client
phase7_move_mcp_client() {
    log_info "Phase 7: Moving mcp-client to apps/..."

    if [[ "${DRY_RUN}" == "true" ]]; then
        log_warning "DRY RUN: Would move src/index.ts to apps/mcp-client/src/"
        return 0
    fi

    cd "${PROJECT_ROOT}"

    if [[ -d "src" ]] && [[ -f "src/index.ts" ]]; then
        log_info "Moving src/ to apps/mcp-client/src/"
        mv src/* apps/mcp-client/src/

        # Copy relevant config files
        cp tsconfig.json apps/mcp-client/
        cp package.json apps/mcp-client/

        log_success "mcp-client moved successfully"
    fi
}

# Phase 8: Reorganize config
phase8_reorganize_config() {
    log_info "Phase 8: Reorganizing config files..."

    if [[ "${DRY_RUN}" == "true" ]]; then
        log_warning "DRY RUN: Would reorganize config/ by environment"
        return 0
    fi

    cd "${PROJECT_ROOT}/config"

    # Copy configs to development (default)
    cp features.yaml development/
    cp virtual-servers.json development/
    cp gateways.txt development/
    cp prompts.txt development/
    cp resources.txt development/

    # Copy to production (will be customized later)
    cp features.yaml production/
    cp virtual-servers.json production/

    # Copy to test (minimal config)
    cp features.yaml test/

    # Move schema
    mv virtual-servers.schema.json schemas/

    log_success "Phase 8 complete: Config reorganized"
}

# Phase 9: Move Docker files
phase9_move_docker() {
    log_info "Phase 9: Moving Docker files..."

    if [[ "${DRY_RUN}" == "true" ]]; then
        log_warning "DRY RUN: Would move Docker files to docker/"
        return 0
    fi

    cd "${PROJECT_ROOT}"

    # Move docker-compose files
    mv docker-compose.yml docker/

    # Move Dockerfiles to respective apps
    mv Dockerfile.tool-router apps/tool-router/Dockerfile
    [[ -f "Dockerfile.translate" ]] && mv Dockerfile.translate docker/
    [[ -f "Dockerfile.uiforge" ]] && mv Dockerfile.uiforge docker/

    log_success "Phase 9 complete: Docker files moved"
}

# Run tests
run_tests() {
    log_info "Running test suite..."

    cd "${PROJECT_ROOT}/apps/tool-router"

    if command -v python3.14 &> /dev/null; then
        python3.14 -m pytest tests/ -v --cov=src/tool_router --cov-report=term
    else
        log_warning "Python 3.14 not found, skipping tests"
    fi
}

# Rollback function
rollback() {
    log_error "Migration failed! Rolling back..."

    if [[ -d "${BACKUP_DIR}" ]]; then
        log_info "Restoring from backup: ${BACKUP_DIR}"

        # Restore directories
        [[ -d "${BACKUP_DIR}/tool_router" ]] && rm -rf "${PROJECT_ROOT}/tool_router" && cp -r "${BACKUP_DIR}/tool_router" "${PROJECT_ROOT}/"
        [[ -d "${BACKUP_DIR}/web-admin" ]] && rm -rf "${PROJECT_ROOT}/web-admin" && cp -r "${BACKUP_DIR}/web-admin" "${PROJECT_ROOT}/"
        [[ -d "${BACKUP_DIR}/src" ]] && rm -rf "${PROJECT_ROOT}/src" && cp -r "${BACKUP_DIR}/src" "${PROJECT_ROOT}/"

        # Restore config files
        [[ -f "${BACKUP_DIR}/pyproject.toml" ]] && cp "${BACKUP_DIR}/pyproject.toml" "${PROJECT_ROOT}/"
        [[ -f "${BACKUP_DIR}/docker-compose.yml" ]] && cp "${BACKUP_DIR}/docker-compose.yml" "${PROJECT_ROOT}/"

        log_success "Rollback complete"
    else
        log_error "Backup directory not found: ${BACKUP_DIR}"
    fi
}

# Main execution
main() {
    log_info "Starting MCP Gateway Architecture Migration"
    log_info "Project root: ${PROJECT_ROOT}"

    if [[ "${DRY_RUN}" == "true" ]]; then
        log_warning "DRY RUN MODE - No changes will be made"
    fi

    # Create backup
    backup_project

    # Execute phases
    trap rollback ERR

    phase1_create_structure
    phase2_move_tool_router
    phase3_remove_legacy
    phase4_consolidate_tests
    phase5_update_imports
    phase6_move_web_admin
    phase7_move_mcp_client
    phase8_reorganize_config
    phase9_move_docker

    # Run tests to verify
    if [[ "${DRY_RUN}" != "true" ]]; then
        run_tests
    fi

    log_success "Migration complete!"
    log_info "Backup saved at: ${BACKUP_DIR}"
    log_info "Next steps:"
    echo "  1. Review changes: git status"
    echo "  2. Run full test suite: make test-coverage"
    echo "  3. Update CI/CD workflows"
    echo "  4. Update documentation"
    echo "  5. Commit changes: git add . && git commit -m 'refactor: migrate to monorepo architecture'"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            echo "Usage: $0 [--dry-run] [--help]"
            echo ""
            echo "Options:"
            echo "  --dry-run    Show what would be done without making changes"
            echo "  --help       Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

main
