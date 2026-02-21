#!/bin/bash

# Production Readiness Validation Script
# Validates all prerequisites for production deployment of scalable architecture
# Usage: ./scripts/validate-production-readiness.sh

set -euo pipefail

echo "🚀 MCP Gateway Production Readiness Validation"
echo "=============================================="
echo "Validating production deployment prerequisites for scalable architecture"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Function to check if environment variable is set and not default
check_env_var() {
    local var="$1"
    local value="${!var:-}"
    [[ -n "$value" && "$value" != "REPLACE_"* && "$value" != "REPLACE_ME" ]]
}

echo -e "${BLUE}🔧 Checking Environment Configuration${NC}"
echo "--------------------------------------"

validate ".env.shared exists" "check_file '.env.shared'"
validate ".env.development exists" "check_file '.env.development'"
validate ".env.production exists" "check_file '.env.production'"
validate ".env.example exists" "check_file '.env.example'"

echo ""
echo -e "${BLUE}🔑 Checking Security Configuration${NC}"
echo "-------------------------------------"

# Load environment files to check variables
if [[ -f ".env.shared" ]]; then
    set -a
    source .env.shared
    set +a
    
    validate "JWT_SECRET_KEY is configured" "check_env_var 'JWT_SECRET_KEY'"
    validate "AUTH_ENCRYPTION_SECRET is configured" "check_env_var 'AUTH_ENCRYPTION_SECRET'"
    validate "PLATFORM_ADMIN_EMAIL is configured" "check_env_var 'PLATFORM_ADMIN_EMAIL'"
    validate "GATEWAY_HOST is configured" "check_env_var 'GATEWAY_HOST'"
    validate "GATEWAY_PORT is configured" "check_env_var 'GATEWAY_PORT'"
else
    echo -e "${YELLOW}⚠️  Cannot validate variables: .env.shared not found${NC}"
fi

echo ""
echo -e "${BLUE}📁 Checking Configuration Files${NC}"
echo "--------------------------------"

validate "services.yml exists" "check_file 'config/services.yml'"
validate "scaling-policies.yml exists" "check_file 'config/scaling-policies.yml'"
validate "sleep_settings.yml exists" "check_file 'config/sleep_settings.yml'"
validate "resource-limits.yml exists" "check_file 'config/resource-limits.yml'"
validate "monitoring.yml exists" "check_file 'config/monitoring.yml'"
validate "monitoring-dashboard.yml exists" "check_file 'config/monitoring-dashboard.yml'"
validate "docker-standards-checklist.yml exists" "check_file 'config/docker-standards-checklist.yml'"
validate "gateways.txt exists" "check_file 'config/gateways.txt'"

echo ""
echo -e "${BLUE}🐳 Checking Docker Configuration${NC}"
echo "------------------------------------"

validate "docker-compose.yml exists" "check_file 'docker-compose.yml'"
validate "docker-compose.scalable.yml exists" "check_file 'docker-compose.scalable.yml'"
validate "Dockerfile.tool-router exists" "check_file 'Dockerfile.tool-router'"
validate "Dockerfile.translate exists" "check_file 'Dockerfile.translate'"
validate "start.sh exists and is executable" "[[ -x 'start.sh' ]]"

echo ""
echo -e "${BLUE}📋 Checking Required Directories${NC}"
echo "--------------------------------"

validate "data directory exists" "[[ -d 'data' ]]"
validate "logs directory exists" "[[ -d 'logs' ]]"
validate "test-results directory exists" "[[ -d 'test-results' ]]"
validate "config directory exists" "[[ -d 'config' ]]"

echo ""
echo -e "${BLUE}🔍 Checking Service Dependencies${NC}"
echo "-------------------------------------"

validate "Service manager configuration exists" "check_file 'service-manager/service_manager.py'"
validate "Tool router configuration exists" "check_file 'tool_router/args.py'"
validate "Gateway registration script exists" "check_file 'scripts/gateway/register.sh'"

echo ""
echo -e "${BLUE}📝 Checking Documentation${NC}"
echo "-----------------------------"

validate "PROJECT_CONTEXT.md exists" "check_file 'PROJECT_CONTEXT.md'"
validate "README.md exists" "check_file 'README.md'"
validate "CHANGELOG.md exists" "check_file 'CHANGELOG.md'"
validate "SCALABLE_ARCHITECTURE_GUIDE.md exists" "check_file 'docs/SCALABLE_ARCHITECTURE_GUIDE.md'"

echo ""
echo -e "${BLUE}🧪 Checking Testing Infrastructure${NC}"
echo "---------------------------------------"

validate "Test suite exists" "check_file 'tests/test_scalable_architecture.py'"
validate "Service manager tests exist" "check_file 'service-manager/tests/test_service_manager.py'"
validate "pytest configuration exists" "check_file 'pyproject.toml'"

echo ""
echo -e "${BLUE}🔧 Checking Build Tools${NC}"
echo "-------------------------"

validate "Makefile exists" "check_file 'Makefile'"
validate "package.json exists" "check_file 'package.json'"
validate "requirements.txt exists" "check_file 'requirements.txt'"

echo ""
echo -e "${BLUE}📊 Validation Summary${NC}"
echo "===================="
echo "Total checks: $TOTAL_CHECKS"
echo -e "Passed: ${GREEN}$PASSED_CHECKS${NC}"
echo -e "Failed: ${RED}$FAILED_CHECKS${NC}"

if [[ $FAILED_CHECKS -eq 0 ]]; then
    echo ""
    echo -e "${GREEN}🎉 All production readiness validations passed!${NC}"
    echo "✅ System is ready for production deployment"
    echo ""
    echo "🚀 Next steps:"
    echo "   1. Generate secrets: make generate-secrets"
    echo "   2. Update .env.shared with generated secrets"
    echo "   3. Start services: make start"
    echo "   4. Register gateways: make register"
    echo "   5. Run health checks: make test"
    echo ""
    echo "📋 Production deployment is ready!"
    exit 0
else
    echo ""
    echo -e "${RED}❌ Some validations failed. Please review the issues above.${NC}"
    echo ""
    echo "💡 To fix production readiness issues:"
    echo "   1. Ensure all environment files exist and are configured"
    echo "   2. Generate secrets with: make generate-secrets"
    echo "   3. Verify all configuration files are present"
    echo "   4. Check directory permissions and structure"
    echo "   5. Run validation again after fixing issues"
    echo ""
    exit 1
fi