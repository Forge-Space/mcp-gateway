#!/bin/bash

# Validate cleanup operations and ensure nothing is broken
set -euo pipefail

PROJECT_NAME=${1:-"forge-mcp-gateway"}
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
VALIDATION_LOG="validation-${PROJECT_NAME}-${TIMESTAMP}.log"

echo "🧪 Validating cleanup for ${PROJECT_NAME}..."
echo "📝 Log file: ${VALIDATION_LOG}"

# Start validation log
{
    echo "Cleanup Validation Log: ${PROJECT_NAME}"
    echo "=================================="
    echo "Started: $(date)"
    echo "Timestamp: ${TIMESTAMP}"
    echo ""
} > "${VALIDATION_LOG}"

# Function to log validation results
log_validation() {
    local test_name="$1"
    local result="$2"
    local details="$3"

    echo "[$result] $test_name" >> "${VALIDATION_LOG}"
    if [ -n "$details" ]; then
        echo "   $details" >> "${VALIDATION_LOG}"
    fi
    echo "" >> "${VALIDATION_LOG}"

    if [ "$result" = "PASS" ]; then
        echo "✅ $test_name"
    else
        echo "❌ $test_name"
        echo "   $details"
    fi
}

# Validate ESLint configurations
echo "🔍 Validating ESLint configurations..."
if command -v npx >/dev/null 2>&1 && [ -f "package.json" ]; then
    if npx eslint --print-config . >/dev/null 2>&1; then
        log_validation "ESLint Configuration" "PASS" "ESLint config is valid"
    else
        log_validation "ESLint Configuration" "FAIL" "ESLint config is invalid"
    fi
else
    log_validation "ESLint Configuration" "SKIP" "ESLint not available"
fi

# Validate Prettier configurations
echo "🎨 Validating Prettier configurations..."
if command -v npx >/dev/null 2>&1 && [ -f "package.json" ]; then
    if npx prettier --check . >/dev/null 2>&1; then
        log_validation "Prettier Configuration" "PASS" "Prettier config is valid"
    else
        log_validation "Prettier Configuration" "FAIL" "Prettier config is invalid"
    fi
else
    log_validation "Prettier Configuration" "SKIP" "Prettier not available"
fi

# Validate YAML configurations
echo "📄 Validating YAML configurations..."
if command -v yamllint >/dev/null 2>&1; then
    yaml_files=$(find . -name "*.yml" -o -name "*.yaml" 2>/dev/null || true)
    if [ -n "$yaml_files" ]; then
        if yamllint $yaml_files >/dev/null 2>&1; then
            log_validation "YAML Configuration" "PASS" "All YAML files are valid"
        else
            log_validation "YAML Configuration" "FAIL" "Some YAML files are invalid"
        fi
    else
        log_validation "YAML Configuration" "SKIP" "No YAML files found"
    fi
else
    log_validation "YAML Configuration" "SKIP" "yamllint not available"
fi

# Validate JSON configurations
echo "📋 Validating JSON configurations..."
json_files=$(find . -name "*.json" -not -path "*/node_modules/*" 2>/dev/null || true)
if [ -n "$json_files" ]; then
    invalid_json=0
    for file in $json_files; do
        if ! python -m json.tool "$file" >/dev/null 2>&1; then
            echo "Invalid JSON: $file" >> "${VALIDATION_LOG}"
            invalid_json=$((invalid_json + 1))
        fi
    done

    if [ $invalid_json -eq 0 ]; then
        log_validation "JSON Configuration" "PASS" "All JSON files are valid"
    else
        log_validation "JSON Configuration" "FAIL" "$invalid_json JSON files are invalid"
    fi
else
    log_validation "JSON Configuration" "SKIP" "No JSON files found"
fi

# Validate package.json scripts
echo "📦 Validating package.json scripts..."
if [ -f "package.json" ]; then
    if python -m json.tool package.json >/dev/null 2>&1; then
        # Check if required scripts exist
        scripts=$(cat package.json 2>/dev/null | python -c "import sys, json; data=json.load(sys.stdin); print(' '.join(data.get('scripts', {}).keys()))" 2>/dev/null || echo "")

        missing_scripts=""
        for script in lint build test; do
            if ! echo "$scripts" | grep -q "$script"; then
                missing_scripts="$missing_scripts $script"
            fi
        done

        if [ -z "$missing_scripts" ]; then
            log_validation "Package Scripts" "PASS" "All required scripts present"
        else
            log_validation "Package Scripts" "WARN" "Missing scripts:$missing_scripts"
        fi
    else
        log_validation "Package Scripts" "FAIL" "package.json is invalid"
    fi
else
    log_validation "Package Scripts" "SKIP" "package.json not found"
fi

# Validate Docker configuration
echo "🐳 Validating Docker configuration..."
if [ -f "docker-compose.yml" ]; then
    if command -v docker-compose >/dev/null 2>&1; then
        if docker-compose config >/dev/null 2>&1; then
            log_validation "Docker Compose" "PASS" "docker-compose.yml is valid"
        else
            log_validation "Docker Compose" "FAIL" "docker-compose.yml is invalid"
        fi
    else
        log_validation "Docker Compose" "SKIP" "docker-compose not available"
    fi

    # Validate Dockerfiles
    dockerfiles=$(find . -name "Dockerfile*" 2>/dev/null || true)
    if [ -n "$dockerfiles" ]; then
        invalid_dockerfiles=0
        for dockerfile in $dockerfiles; do
            if ! grep -q "^FROM" "$dockerfile"; then
                echo "Invalid Dockerfile (no FROM): $dockerfile" >> "${VALIDATION_LOG}"
                invalid_dockerfiles=$((invalid_dockerfiles + 1))
            fi
        done

        if [ $invalid_dockerfiles -eq 0 ]; then
            log_validation "Dockerfiles" "PASS" "All Dockerfiles are valid"
        else
            log_validation "Dockerfiles" "FAIL" "$invalid_dockerfiles Dockerfiles are invalid"
        fi
    else
        log_validation "Dockerfiles" "SKIP" "No Dockerfiles found"
    fi
else
    log_validation "Docker Configuration" "SKIP" "docker-compose.yml not found"
fi

# Validate documentation
echo "📝 Validating documentation..."
if [ -f "README.md" ]; then
    if grep -q "^# " README.md; then
        log_validation "README" "PASS" "README.md has proper structure"
    else
        log_validation "README" "FAIL" "README.md lacks proper structure"
    fi
else
    log_validation "README" "SKIP" "README.md not found"
fi

# Validate CI/CD workflows
echo "🔄 Validating CI/CD workflows..."
if [ -d ".github/workflows" ]; then
    workflow_files=$(find .github/workflows -name "*.yml" -o -name "*.yaml" 2>/dev/null || true)
    if [ -n "$workflow_files" ]; then
        if command -v yamllint >/dev/null 2>&1; then
            if yamllint $workflow_files >/dev/null 2>&1; then
                log_validation "CI/CD Workflows" "PASS" "All workflows are valid"
            else
                log_validation "CI/CD Workflows" "FAIL" "Some workflows are invalid"
            fi
        else
            log_validation "CI/CD Workflows" "SKIP" "yamllint not available"
        fi
    else
        log_validation "CI/CD Workflows" "SKIP" "No workflow files found"
    fi
else
    log_validation "CI/CD Workflows" "SKIP" ".github/workflows not found"
fi

# Validate environment files
echo "🔧 Validating environment files..."
env_files=$(find . -name ".env*" -type f 2>/dev/null || true)
if [ -n "$env_files" ]; then
    log_validation "Environment Files" "INFO" "Found $(echo $env_files | wc -w) environment files"

    # Check for example files
    if [ -f ".env.example" ]; then
        log_validation "Environment Example" "PASS" ".env.example exists"
    else
        log_validation "Environment Example" "WARN" ".env.example missing"
    fi
else
    log_validation "Environment Files" "SKIP" "No environment files found"
fi

# Final summary
{
    echo "Validation Summary"
    echo "=================="
    echo "Completed: $(date)"
    echo ""

    # Count results
    pass_count=$(grep -c "\[PASS\]" "${VALIDATION_LOG}" || echo "0")
    fail_count=$(grep -c "\[FAIL\]" "${VALIDATION_LOG}" || echo "0")
    warn_count=$(grep -c "\[WARN\]" "${VALIDATION_LOG}" || echo "0")
    skip_count=$(grep -c "\[SKIP\]" "${VALIDATION_LOG}" || echo "0")
    info_count=$(grep -c "\[INFO\]" "${VALIDATION_LOG}" || echo "0")

    echo "Results:"
    echo "- Pass: $pass_count"
    echo "- Fail: $fail_count"
    echo "- Warn: $warn_count"
    echo "- Skip: $skip_count"
    echo "- Info: $info_count"
    echo ""
    echo "Total: $((pass_count + fail_count + warn_count + skip_count + info_count))"

    if [ $fail_count -eq 0 ]; then
        echo "Status: SUCCESS"
    else
        echo "Status: FAILED"
    fi
} >> "${VALIDATION_LOG}"

# Display summary
echo ""
echo "📊 Validation Summary:"
grep -E "\[(PASS|FAIL|WARN|SKIP|INFO)\]" "${VALIDATION_LOG}" | while read line; do
    case "$line" in
        *"[PASS]"*) echo "✅ $line" ;;
        *"[FAIL]"*) echo "❌ $line" ;;
        *"[WARN]"*) echo "⚠️ $line" ;;
        *"[SKIP]"*) echo "⏭️ $line" ;;
        *"[INFO]"*) echo "ℹ️ $line" ;;
    esac
done | sed 's/\[.*\] //'

echo ""
echo "📝 Full log: ${VALIDATION_LOG}"

# Exit with appropriate code
fail_count=$(grep -c "\[FAIL\]" "${VALIDATION_LOG}" || echo "0")
if [ $fail_count -eq 0 ]; then
    echo "🎉 All validations passed!"
    exit 0
else
    echo "🚨 $fail_count validation(s) failed!"
    exit 1
fi
