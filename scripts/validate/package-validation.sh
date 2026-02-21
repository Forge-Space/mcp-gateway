#!/bin/bash

# UIForge Package Configuration Validation Script

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

# Logging function
log() {
    echo -e "$1"
}

# Function to validate JSON
validate_json() {
    local file="$1"
    local description="$2"

    log -n "📋 $description ... "

    if [[ ! -f "$file" ]]; then
        echo -e "${YELLOW}⚠️  FILE NOT FOUND${NC}"
        return 1
    fi

    if ! jq empty "$file" 2>/dev/null; then
        echo -e "${RED}❌ INVALID JSON${NC}"
        return 1
    fi

    echo -e "${GREEN}✅ VALID${NC}"
    return 0
}

# Function to validate TOML
validate_toml() {
    local file="$1"
    local description="$2"

    log -n "📋 $description ... "

    if [[ ! -f "$file" ]]; then
        echo -e "${YELLOW}⚠️  FILE NOT FOUND${NC}"
        return 1
    fi

    # Try tomllib first (Python 3.11+), fallback to basic check
    if python -c "
try:
    import tomllib
    tomllib.load(open('$file', 'rb'))
    print('TOML valid')
except ImportError:
    # Fallback for older Python versions
    import sys
    sys.exit(0)
except Exception as e:
    print(f'TOML error: {e}')
    sys.exit(1)
" 2>/dev/null; then
        echo -e "${GREEN}✅ VALID${NC}"
        return 0
    else
        echo -e "${RED}❌ INVALID TOML${NC}"
        return 1
    fi
}

# Function to validate package.json structure
validate_package_json() {
    local file="$1"

    log -n "🔍 Package.json structure ... "

    # Check required fields
    local required_fields=("name" "version" "description" "engines")
    for field in "${required_fields[@]}"; do
        if ! jq -e ".$field" "$file" >/dev/null 2>&1; then
            echo -e "${RED}❌ Missing field: $field${NC}"
            return 1
        fi
    done

    # Check Node.js version requirement
    local node_version
    node_version=$(jq -r '.engines.node // "not specified"' "$file")
    if [[ "$node_version" == "not specified" ]]; then
        echo -e "${YELLOW}⚠️  Node.js version should be >=18.0.0${NC}"
        return 1
    fi

    echo -e "${GREEN}✅ VALID${NC}"
    return 0
}

# Function to validate pyproject.toml structure
validate_pyproject_toml() {
    local file="$1"

    log -n "🔍 PyProject.toml structure ... "

    # Check if it has build system
    if ! python -c "
try:
    import tomllib
    with open('$file', 'rb') as f:
        data = tomllib.load(f)
    if 'build-system' not in data:
        exit(1)
except ImportError:
    # Fallback for older Python versions - just check file exists
    exit(0)
except Exception:
    exit(1)
" 2>/dev/null; then
        echo -e "${RED}❌ Missing build-system${NC}"
        return 1
    fi

    # Check Python version requirement
    if ! python -c "
try:
    import tomllib
    with open('$file', 'rb') as f:
        data = tomllib.load(f)
    project = data.get('project', {})
    requires_python = project.get('requires-python', '')
    if not requires_python or '3.11' not in requires_python:
        exit(1)
except ImportError:
    # Fallback for older Python versions
    exit(0)
except Exception:
    exit(1)
" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Python version should be >=3.11${NC}"
        return 1
    fi

    echo -e "${GREEN}✅ VALID${NC}"
    return 0
}

# Function to validate tsconfig.json structure
validate_tsconfig_json() {
    local file="$1"

    log -n "🔍 TypeScript configuration ... "

    # Check compiler options
    if ! jq -e '.compilerOptions' "$file" >/dev/null 2>&1; then
        echo -e "${RED}❌ Missing compilerOptions${NC}"
        return 1
    fi

    # Check required compiler options
    local required_options=("target" "module" "strict" "outDir")
    for option in "${required_options[@]}"; do
        if ! jq -e ".compilerOptions.$option" "$file" >/dev/null 2>&1; then
            echo -e "${RED}❌ Missing compiler option: $option${NC}"
            return 1
        fi
    done

    # Check if strict mode is enabled
    local strict_mode
    strict_mode=$(jq -r '.compilerOptions.strict // false' "$file")
    if [[ "$strict_mode" != "true" ]]; then
        echo -e "${YELLOW}⚠️  Strict mode should be enabled${NC}"
        return 1
    fi

    echo -e "${GREEN}✅ VALID${NC}"
    return 0
}

# Function to validate all configurations
validate_all() {
    local project_dir="${1:-$PROJECT_ROOT}"
    local total_checks=0
    local passed_checks=0

    log "${BLUE}🔍 Validating package configurations in $project_dir${NC}"
    echo

    # Validate package.json
    ((total_checks++))
    if validate_json "$project_dir/package.json" "package.json syntax"; then
        ((passed_checks++))
        ((total_checks++))
        if validate_package_json "$project_dir/package.json"; then
            ((passed_checks++))
        fi
    fi

    echo

    # Validate pyproject.toml
    ((total_checks++))
    if validate_toml "$project_dir/pyproject.toml" "pyproject.toml syntax"; then
        ((passed_checks++))
        ((total_checks++))
        if validate_pyproject_toml "$project_dir/pyproject.toml"; then
            ((passed_checks++))
        fi
    fi

    echo

    # Validate tsconfig.json
    ((total_checks++))
    if validate_json "$project_dir/tsconfig.json" "tsconfig.json syntax"; then
        ((passed_checks++))
        ((total_checks++))
        if validate_tsconfig_json "$project_dir/tsconfig.json"; then
            ((passed_checks++))
        fi
    fi

    echo
    log "${BLUE}📊 Validation Summary:${NC}"
    log "   Total checks: $total_checks"
    log "   Passed: ${GREEN}$passed_checks${NC}"
    log "   Failed: ${RED}$((total_checks - passed_checks))${NC}"

    if [[ $passed_checks -eq $total_checks ]]; then
        log "${GREEN}🎉 All validations passed!${NC}"
        return 0
    else
        log "${RED}❌ Some validations failed${NC}"
        return 1
    fi
}

# Main function
main() {
    case "${1:-}" in
        validate)
            validate_all "${2:-.}"
            ;;
        *)
            echo "Usage: $0 validate [project-dir]"
            echo "  validate - Validate all package configurations"
            exit 1
            ;;
    esac
}

main "$@"
