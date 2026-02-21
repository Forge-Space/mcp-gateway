#!/bin/bash
# Validate patterns implementation
# Usage: ./scripts/validate-patterns.sh

set -euo pipefail

echo "🔍 Validating Hybrid Shared Repository Strategy Implementation"
echo "============================================================"

# Function to check if file exists
check_file() {
    local file_path="$1"
    local description="$2"

    if [[ -f "$file_path" ]]; then
        echo "✅ $description: $file_path"
        return 0
    else
        echo "❌ $description: $file_path (MISSING)"
        return 1
    fi
}

# Function to check if directory exists
check_dir() {
    local dir_path="$1"
    local description="$2"

    if [[ -d "$dir_path" ]]; then
        echo "✅ $description: $dir_path"
        return 0
    else
        echo "❌ $description: $dir_path (MISSING)"
        return 1
    fi
}

# Function to validate YAML syntax
validate_yaml() {
    local file_path="$1"
    local description="$2"

    if command -v yq >/dev/null 2>&1; then
        if yq eval '.' "$file_path" >/dev/null 2>&1; then
            echo "✅ $description: Valid YAML"
            return 0
        else
            echo "❌ $description: Invalid YAML syntax"
            return 1
        fi
    else
        echo "⚠️  $description: yq not available, skipping YAML validation"
        return 0
    fi
}

# Check core scripts
echo ""
echo "📜 Checking Core Scripts..."
check_file "scripts/bootstrap-project.sh" "Bootstrap script"
check_file "scripts/sync-patterns.sh" "Sync patterns script"

# Check GitHub workflow structure
echo ""
echo "🔧 Checking GitHub Workflow Structure..."
check_dir ".github/workflows" "Workflows directory"
check_dir ".github/workflows/base" "Base workflows directory"
check_dir ".github/workflows/reusable" "Reusable workflows directory"
check_dir ".github/configs" "Configurations directory"
check_dir ".github/templates" "Templates directory"
check_dir ".github/templates/project-setup" "Project setup templates"

# Check specific workflow files
echo ""
echo "📋 Checking Workflow Files..."
check_file ".github/workflows/ci-shared.yml" "Shared CI workflow"
check_file ".github/workflows/base/ci.yml" "Base CI workflow"
check_file ".github/workflows/reusable/setup-node.yml" "Node.js setup workflow"
check_file ".github/workflows/reusable/setup-python.yml" "Python setup workflow"
check_file ".github/workflows/reusable/upload-coverage.yml" "Coverage upload workflow"

# Check configuration files
echo ""
echo "⚙️  Checking Configuration Files..."
check_file ".github/configs/codecov.yml" "Codecov configuration"
check_file ".github/configs/codeql-config.yml" "CodeQL configuration"
check_file ".github/configs/branch-protection.yml" "Branch protection configuration"

# Check template files
echo ""
echo "📄 Checking Template Files..."
check_file ".github/templates/project-setup/gateway.md" "Gateway project template"

# Validate YAML files
echo ""
echo "🔍 Validating YAML Syntax..."
validate_yaml ".github/workflows/ci-shared.yml" "Shared CI workflow"
validate_yaml ".github/workflows/base/ci.yml" "Base CI workflow"
validate_yaml ".github/workflows/reusable/setup-node.yml" "Node.js setup workflow"
validate_yaml ".github/workflows/reusable/setup-python.yml" "Python setup workflow"
validate_yaml ".github/workflows/reusable/upload-coverage.yml" "Coverage upload workflow"
validate_yaml ".github/configs/codecov.yml" "Codecov configuration"
validate_yaml ".github/configs/codeql-config.yml" "CodeQL configuration"
validate_yaml ".github/configs/branch-protection.yml" "Branch protection configuration"

# Check documentation
echo ""
echo "📚 Checking Documentation..."
check_file "docs/hybrid-shared-repository-strategy.md" "Strategy documentation"

# Summary
echo ""
echo "============================================================"
echo "📊 Validation Summary"
echo "============================================================"

# Count total checks
total_checks=0
passed_checks=0

# Simple validation count (approximate)
files_to_check=(
    "scripts/bootstrap-project.sh"
    "scripts/sync-patterns.sh"
    ".github/workflows/ci-shared.yml"
    ".github/workflows/base/ci.yml"
    ".github/workflows/reusable/setup-node.yml"
    ".github/workflows/reusable/setup-python.yml"
    ".github/workflows/reusable/upload-coverage.yml"
    ".github/configs/codecov.yml"
    ".github/configs/codeql-config.yml"
    ".github/configs/branch-protection.yml"
    ".github/templates/project-setup/gateway.md"
    "docs/hybrid-shared-repository-strategy.md"
)

dirs_to_check=(
    ".github/workflows"
    ".github/workflows/base"
    ".github/workflows/reusable"
    ".github/configs"
    ".github/templates"
    ".github/templates/project-setup"
)

for file in "${files_to_check[@]}"; do
    ((total_checks++))
    if [[ -f "$file" ]]; then
        ((passed_checks++))
    fi
done

for dir in "${dirs_to_check[@]}"; do
    ((total_checks++))
    if [[ -d "$dir" ]]; then
        ((passed_checks++))
    fi
done

success_rate=$((passed_checks * 100 / total_checks))

echo "Total Checks: $total_checks"
echo "Passed: $passed_checks"
echo "Success Rate: $success_rate%"

if [[ $success_rate -ge 90 ]]; then
    echo "🎉 Implementation is EXCELLENT!"
elif [[ $success_rate -ge 80 ]]; then
    echo "✅ Implementation is GOOD!"
elif [[ $success_rate -ge 70 ]]; then
    echo "⚠️  Implementation needs some attention"
else
    echo "❌ Implementation needs significant work"
fi

echo ""
echo "🚀 Next Steps:"
echo "1. Test the bootstrap script: bash scripts/bootstrap-project.sh gateway test-project"
echo "2. Test the sync script: bash scripts/sync-patterns.sh v1.0 gateway"
echo "3. Validate workflows in GitHub Actions"
echo "4. Roll out to other UIForge projects"

echo ""
echo "📖 For detailed usage instructions, see: docs/hybrid-shared-repository-strategy.md"
