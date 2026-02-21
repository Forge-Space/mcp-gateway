#!/bin/bash

# Environment Configuration Validation Script
# Validates the consolidated environment configuration system
# Usage: ./scripts/validate/env-validation.sh

set -euo pipefail

echo "🔍 Environment Configuration Validation"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Validation counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Function to run validation check
validate() {
    local description="$1"
    local command="$2"

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -n "📋 $description ... "

    if eval "$command" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

# Function to check if file exists and is readable
check_file() {
    local file="$1"
    [[ -f "$file" && -r "$file" ]]
}

# Function to check if environment variable is set
check_env_var() {
    local var="$1"
    [[ -n "${!var:-}" ]]
}

# Function to validate environment file syntax
validate_env_syntax() {
    local file="$1"

    # Check for common syntax issues
    if grep -q "^[^#].*[^=]$" "$file" 2>/dev/null; then
        return 1  # Lines without = that aren't comments
    fi

    if grep -q "^[^#].*=$" "$file" 2>/dev/null; then
        return 1  # Lines ending with = (empty values)
    fi

    return 0
}

echo ""
echo "🔧 Checking Environment Files"
echo "----------------------------"

validate "Shared environment file exists" "check_file '.env.shared'"
validate "Development environment file exists" "check_file '.env.development'"
validate "Production environment file exists" "check_file '.env.production'"
validate "Example environment file exists" "check_file '.env.example'"
validate "Environment loader script exists" "check_file 'scripts/load-env.sh'"

echo ""
echo "📝 Validating Environment File Syntax"
echo "------------------------------------"

validate "Shared environment file syntax" "validate_env_syntax '.env.shared'"
validate "Development environment file syntax" "validate_env_syntax '.env.development'"
validate "Production environment file syntax" "validate_env_syntax '.env.production'"
validate "Example environment file syntax" "validate_env_syntax '.env.example'"

echo ""
echo "🔍 Checking Required Environment Variables"
echo "-----------------------------------------"

# Load shared environment to check variables
if [[ -f ".env.shared" ]]; then
    set -a
    source .env.shared
    set +a

    validate "GATEWAY_HOST is set" "check_env_var 'GATEWAY_HOST'"
    validate "GATEWAY_PORT is set" "check_env_var 'GATEWAY_PORT'"
    validate "DATABASE_URL is set" "check_env_var 'DATABASE_URL'"
    validate "JWT_SECRET_KEY is set" "check_env_var 'JWT_SECRET_KEY'"
    validate "AUTH_ENCRYPTION_SECRET is set" "check_env_var 'AUTH_ENCRYPTION_SECRET'"
    validate "PLATFORM_ADMIN_EMAIL is set" "check_env_var 'PLATFORM_ADMIN_EMAIL'"
    validate "FORGE_SERVICE_MANAGER_PORT is set" "check_env_var 'FORGE_SERVICE_MANAGER_PORT'"
    validate "FORGE_UI_PORT is set" "check_env_var 'FORGE_UI_PORT'"
    validate "FORGE_TOOL_ROUTER_PORT is set" "check_env_var 'FORGE_TOOL_ROUTER_PORT'"
else
    echo -e "${YELLOW}⚠️  Cannot validate variables: .env.shared not found${NC}"
fi

echo ""
echo "🐳 Validating Docker Compose Configuration"
echo "--------------------------------------------"

validate "Docker Compose file exists" "check_file 'docker-compose.yml'"
validate "Docker Compose file references shared env" "grep -q '.env.shared' docker-compose.yml"
validate "Docker Compose file references dev env" "grep -q '.env.development' docker-compose.yml"
validate "Docker Compose uses GATEWAY_PORT variable" "grep -q 'GATEWAY_PORT' docker-compose.yml"
validate "Docker Compose uses FORGE_UI_PORT variable" "grep -q 'FORGE_UI_PORT' docker-compose.yml"

echo ""
echo "🔄 Checking Environment Loading Script"
echo "-------------------------------------"

validate "Environment loader is executable" "[[ -x 'scripts/load-env.sh' ]]"
validate "Environment loader has proper shebang" "head -1 scripts/load-env.sh | grep -q '#!/bin/bash'"

echo ""
echo "📋 Checking Backup Files"
echo "------------------------"

validate "Original .env backed up" "check_file 'backups/.env.backup'"
validate "Original .env.development backed up" "check_file 'backups/.env.development.backup'"
validate "Original .env.production backed up" "check_file 'backups/.env.production.backup'"
validate "Original .env.example backed up" "check_file 'backups/.env.example.backup'"

echo ""
echo "🔍 Testing Environment Loading"
echo "-----------------------------"

if [[ -f "scripts/load-env.sh" ]]; then
    # Test environment loading in subshell
    if (
        cd "$(mktemp -d)" 2>/dev/null || cd /tmp
        cp /Users/lucassantana/Desenvolvimento/forge-mcp-gateway/.env.shared . 2>/dev/null || true
        cp /Users/lucassantana/Desenvolvimento/forge-mcp-gateway/.env.development . 2>/dev/null || true
        cp /Users/lucassantana/Desenvolvimento/forge-mcp-gateway/scripts/load-env.sh . 2>/dev/null || true
        chmod +x load-env.sh 2>/dev/null || true

        # Test loading (suppress output)
        source load-env.sh development >/dev/null 2>&1

        # Check if variables were loaded
        [[ -n "${GATEWAY_HOST:-}" && -n "${GATEWAY_PORT:-}" ]]
    ); then
        echo -e "📋 Environment loading test ... ${GREEN}✅ PASS${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        echo -e "📋 Environment loading test ... ${RED}❌ FAIL${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
else
    echo -e "${YELLOW}⚠️  Cannot test environment loading: script not found${NC}"
fi

echo ""
echo "📊 Validation Summary"
echo "===================="
echo "Total checks: $TOTAL_CHECKS"
echo -e "Passed: ${GREEN}$PASSED_CHECKS${NC}"
echo -e "Failed: ${RED}$FAILED_CHECKS${NC}"

if [[ $FAILED_CHECKS -eq 0 ]]; then
    echo ""
    echo -e "${GREEN}🎉 All environment configuration validations passed!${NC}"
    echo "✅ Environment consolidation is complete and working correctly."
    exit 0
else
    echo ""
    echo -e "${RED}❌ Some validations failed. Please review the issues above.${NC}"
    echo "💡 Run the validation again after fixing the issues."
    exit 1
fi
