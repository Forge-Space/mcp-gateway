#!/bin/bash
# scripts/validation/validate-patterns.sh
# UIForge Patterns Validation Script
set -euo pipefail

echo "🔍 Validating UIForge patterns compliance..."

FAILED=0

# 1. Validate ESLint configuration uses shared patterns
echo "📝 Checking ESLint configuration..."
if ! grep -q "require.*patterns/code-quality/eslint/base.config.js" .eslintrc.js; then
    echo "❌ ESLint configuration should extend shared patterns"
    FAILED=1
else
    echo "✅ ESLint configuration extends shared patterns"
fi

# 2. Validate Prettier configuration uses shared patterns
echo "🎨 Checking Prettier configuration..."
if ! grep -q "\$schema.*patterns/code-quality/prettier/base.config.json" .prettierrc.json; then
    echo "❌ Prettier configuration should reference shared patterns"
    FAILED=1
else
    echo "✅ Prettier configuration references shared patterns"
fi

# 3. Validate shared patterns exist
echo "📁 Checking shared patterns availability..."
PATTERNS_DIR="./patterns/code-quality"
if [ ! -f "$PATTERNS_DIR/eslint/base.config.js" ]; then
    echo "❌ ESLint base pattern missing: $PATTERNS_DIR/eslint/base.config.js"
    FAILED=1
else
    echo "✅ ESLint base pattern exists"
fi

if [ ! -f "$PATTERNS_DIR/prettier/base.config.json" ]; then
    echo "❌ Prettier base pattern missing: $PATTERNS_DIR/prettier/base.config.json"
    FAILED=1
else
    echo "✅ Prettier base pattern exists"
fi

# 4. Validate CI/CD uses shared workflows
echo "🔄 Checking CI/CD shared workflow usage..."
if grep -q "uses: ./.github/workflows/base-ci.yml" .github/workflows/ci.yml; then
    echo "✅ CI pipeline uses local base workflow"
elif grep -q "uses: ./.github/shared/workflows/base-ci.yml" .github/workflows/ci.yml; then
    echo "✅ CI pipeline uses shared workflow"
else
    echo "❌ CI pipeline should use a base workflow"
    FAILED=1
fi

# 5. Validate GitHub Actions versions
echo "⚙️  Checking GitHub Actions versions..."
REQUIRED_ACTIONS=("actions/checkout@v6" "actions/setup-node@v6" "actions/setup-python@v5")
for action in "${REQUIRED_ACTIONS[@]}"; do
    if grep -ql "$action" .github/workflows/ci.yml .github/shared/workflows/base-ci.yml 2>/dev/null; then
        echo "✅ Found required action: $action"
    else
        echo "⚠️  Missing recommended action: $action"
    fi
done

# 6. Validate Node.js version consistency
echo "📦 Checking Node.js version consistency..."
if grep -q '"node-version":' package.json; then
    NODE_VERSION=$(grep -o '"node-version": "[^"]*"' package.json | cut -d'"' -f4)
    if [ "$NODE_VERSION" = '"22"' ]; then
        echo "✅ Node.js version is v22 (consistent with standards)"
    else
        echo "⚠️  Node.js version is $NODE_VERSION (should be v22)"
    fi
else
    echo "ℹ️  Node.js version not specified in package.json (check .github/workflows)"
fi

# 7. Validate Python version consistency
echo "🐍 Checking Python version consistency..."
if [ -f "pyproject.toml" ]; then
    if grep -q 'python-version =' pyproject.toml; then
        PYTHON_VERSION=$(grep -o 'python-version = "[^"]*"' pyproject.toml | cut -d'"' -f4)
        if [ "$PYTHON_VERSION" = '"3.12"' ]; then
            echo "✅ Python version is 3.12 (consistent with standards)"
        else
            echo "⚠️  Python version is $PYTHON_VERSION (should be 3.12)"
        fi
    else
        echo "ℹ️  Python version not specified in pyproject.toml (check .github/workflows)"
    fi
else
    echo "ℹ️  No pyproject.toml found"
fi

# 8. Validate security scanning configuration
echo "🔒 Checking security scanning configuration..."
if [ -f ".github/workflows/snyk.yml" ]; then
    echo "✅ Snyk security scanning configured"
else
    echo "⚠️  Snyk security scanning not found"
fi

if grep -ql "github/codeql-action" .github/workflows/ci.yml .github/shared/workflows/base-ci.yml 2>/dev/null; then
    echo "✅ CodeQL security scanning configured"
else
    echo "⚠️  CodeQL security scanning not found"
fi

# 9. Validate coverage configuration
echo "📊 Checking coverage configuration..."
if grep -q "80" .github/shared/workflows/base-ci.yml 2>/dev/null || grep -q "80" .github/workflows/ci.yml 2>/dev/null; then
    echo "ℹ️  Coverage configuration found in CI workflows"
else
    echo "⚠️  Coverage threshold configuration not found"
fi

# 10. Validate branch protection
echo "🔐 Checking branch protection rules..."
if [ -f ".github/branch-protection.yml" ]; then
    echo "✅ Branch protection rules defined"
else
    echo "⚠️  Branch protection rules not found"
fi

# Summary
echo ""
if [ $FAILED -eq 0 ]; then
    echo "✅ All pattern validations passed!"
    echo "🎉 UIForge patterns integration is compliant"
else
    echo "❌ Some pattern validations failed."
    echo "🔧 Please address the issues above to ensure compliance."
    exit 1
fi
