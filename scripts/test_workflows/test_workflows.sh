#!/bin/bash
# Test Creation Workflows - Global Commands
# Quality Over Quantity: Every command creates real confidence

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root detection
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Help function
show_help() {
    cat << EOF
Test Creation Workflows - Global Commands

USAGE:
    test_workflows.sh <command> [options]

COMMANDS:
    quality-check          Run comprehensive test quality validation
    generate-report        Generate detailed quality report
    run-coverage          Execute test coverage analysis
    create-tests          Create high-quality tests for modules
    batch-create          Create tests for multiple modules
    validate-quality      Validate tests against quality standards

OPTIONS:
    --file <path>         Specify specific test file
    --module <path>       Specify module for test creation
    --type <type>         Test type: unit, integration, e2e
    --output <path>       Output file for reports
    --project-root <path> Project root directory
    --help               Show this help message

EXAMPLES:
    # Run quality check on entire project
    ./test_workflows.sh quality-check

    # Check specific test file
    ./test_workflows.sh quality-check --file tool_router/tests/test_scoring.py

    # Generate quality report
    ./test_workflows.sh generate-report --output quality_report.json

    # Run coverage analysis
    ./test_workflows.sh run-coverage

    # Create unit tests for a module
    ./test_workflows.sh create-tests --module tool_router/scoring/matcher.py --type unit

    # Create tests for multiple modules
    ./test_workflows.sh batch-create --module "**/scoring/*.py" --type unit

    # Validate test quality
    ./test_workflows.sh validate-quality --file tool_router/tests/test_scoring.py

QUALITY PRINCIPLES:
    • Quality Over Quantity - Every test provides real confidence
    • Business Logic First - Test what matters to users
    • Proper Isolation - Mock external dependencies appropriately
    • Error Coverage - Include failure scenarios and edge cases
    • Realistic Data - Use meaningful test scenarios

EOF
}

# Command: Quality Check
cmd_quality_check() {
    local file_path="${1:-}"
    local project_root="${2:-$PROJECT_ROOT}"
    
    log_info "Running test quality validation..."
    
    cd "$project_root"
    
    if [[ -n "$file_path" ]]; then
        log_info "Checking file: $file_path"
        python3 scripts/test_workflows/test_quality_validation.py check --file "$file_path"
    else
        log_info "Checking entire project..."
        python3 scripts/test_workflows/test_quality_validation.py check
    fi
    
    local exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        log_success "Quality check passed"
    else
        log_error "Quality check failed"
    fi
    
    return $exit_code
}

# Command: Generate Report
cmd_generate_report() {
    local output_path="${1:-}"
    local project_root="${2:-$PROJECT_ROOT}"
    local no_summary="${3:-false}"
    
    log_info "Generating test quality report..."
    
    cd "$project_root"
    
    local args=("report")
    if [[ -n "$output_path" ]]; then
        args+=("--output" "$output_path")
    fi
    if [[ "$no_summary" == "true" ]]; then
        args+=("--no-summary")
    fi
    
    python3 scripts/test_workflows/test_quality_validation.py "${args[@]}"
    
    local exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        log_success "Report generated successfully"
        if [[ -n "$output_path" ]]; then
            log_info "Report saved to: $output_path"
        fi
    else
        log_error "Report generation failed"
    fi
    
    return $exit_code
}

# Command: Run Coverage
cmd_run_coverage() {
    local project_root="${1:-$PROJECT_ROOT}"
    
    log_info "Running test coverage analysis..."
    
    cd "$project_root"
    
    # Check if pytest is available
    if ! command -v pytest &> /dev/null; then
        log_error "pytest not found. Please install it: pip install pytest pytest-cov"
        return 1
    fi
    
    # Run coverage analysis
    python3 scripts/test_workflows/test_quality_validation.py coverage
    
    local exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        log_success "Coverage analysis completed"
        
        # Display coverage summary if available
        if [[ -f "coverage.json" ]]; then
            log_info "Coverage report available in coverage.json and htmlcov/"
        fi
    else
        log_error "Coverage analysis failed"
    fi
    
    return $exit_code
}

# Command: Create Tests
cmd_create_tests() {
    local module_path="${1:-}"
    local test_type="${2:-unit}"
    local project_root="${3:-$PROJECT_ROOT}"
    
    if [[ -z "$module_path" ]]; then
        log_error "Module path is required for test creation"
        return 1
    fi
    
    log_info "Creating $test_type tests for module: $module_path"
    
    cd "$project_root"
    
    # Check if module exists
    if [[ ! -f "$module_path" ]]; then
        log_error "Module not found: $module_path"
        return 1
    fi
    
    python3 scripts/test_workflows/test_creation_workflows.py create "$module_path" --type "$test_type"
    
    local exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        log_success "Tests created successfully"
    else
        log_error "Test creation failed"
    fi
    
    return $exit_code
}

# Command: Batch Create Tests
cmd_batch_create() {
    local module_pattern="${1:-}"
    local test_type="${2:-unit}"
    local project_root="${3:-$PROJECT_ROOT}"
    
    if [[ -z "$module_pattern" ]]; then
        log_error "Module pattern is required for batch test creation"
        return 1
    fi
    
    log_info "Creating $test_type tests for modules matching: $module_pattern"
    
    cd "$project_root"
    
    python3 scripts/test_workflows/test_creation_workflows.py batch "$module_pattern" --type "$test_type"
    
    local exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        log_success "Batch test creation completed"
    else
        log_error "Batch test creation failed"
    fi
    
    return $exit_code
}

# Command: Validate Quality
cmd_validate_quality() {
    local file_path="${1:-}"
    local project_root="${2:-$PROJECT_ROOT}"
    
    log_info "Validating test quality against standards..."
    
    cd "$project_root"
    
    if [[ -n "$file_path" ]]; then
        log_info "Validating file: $file_path"
        python3 scripts/test_workflows/test_quality_validation.py check --file "$file_path"
    else
        log_info "Validating entire project..."
        python3 scripts/test_workflows/test_quality_validation.py check
    fi
    
    local exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        log_success "Quality validation passed"
    else
        log_error "Quality validation failed"
    fi
    
    return $exit_code
}

# Command: Quick Analysis (combines multiple checks)
cmd_quick_analysis() {
    local project_root="${1:-$PROJECT_ROOT}"
    
    log_info "Running quick test quality analysis..."
    
    # 1. Run quality check
    log_info "1/3: Running quality validation..."
    if ! cmd_quality_check "" "$project_root"; then
        log_warning "Quality check found issues"
    fi
    
    echo
    
    # 2. Run coverage analysis
    log_info "2/3: Running coverage analysis..."
    if ! cmd_run_coverage "$project_root"; then
        log_warning "Coverage analysis failed"
    fi
    
    echo
    
    # 3. Generate summary report
    log_info "3/3: Generating summary report..."
    local report_file="test_quality_summary_$(date +%Y%m%d_%H%M%S).json"
    if cmd_generate_report "$report_file" "$project_root" "true"; then
        log_success "Quick analysis completed"
        log_info "Summary report: $report_file"
    else
        log_error "Report generation failed"
        return 1
    fi
    
    return 0
}

# Setup function - ensure dependencies are available
setup_environment() {
    local project_root="${1:-$PROJECT_ROOT}"
    
    log_info "Setting up test creation environment..."
    
    cd "$project_root"
    
    # Check Python dependencies
    local required_packages=("pytest" "pytest-cov" "pytest-asyncio")
    local missing_packages=()
    
    for package in "${required_packages[@]}"; do
        if ! python3 -c "import $package" 2>/dev/null; then
            missing_packages+=("$package")
        fi
    done
    
    if [[ ${#missing_packages[@]} -gt 0 ]]; then
        log_warning "Missing required packages: ${missing_packages[*]}"
        log_info "Installing missing packages..."
        pip install "${missing_packages[@]}"
    fi
    
    # Ensure test directories exist
    local test_dirs=("tool_router/tests/unit" "tool_router/tests/integration" "tool_router/tests/e2e")
    
    for dir in "${test_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            log_info "Creating test directory: $dir"
            mkdir -p "$dir"
            # Create __init__.py files
            touch "$dir/__init__.py"
        fi
    done
    
    log_success "Environment setup completed"
}

# Main execution logic
main() {
    local command=""
    local file_path=""
    local module_path=""
    local module_pattern=""
    local test_type="unit"
    local output_path=""
    local project_root="$PROJECT_ROOT"
    local no_summary="false"
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help)
                show_help
                exit 0
                ;;
            --file)
                file_path="$2"
                shift 2
                ;;
            --module)
                module_path="$2"
                shift 2
                ;;
            --module-pattern)
                module_pattern="$2"
                shift 2
                ;;
            --type)
                test_type="$2"
                shift 2
                ;;
            --output)
                output_path="$2"
                shift 2
                ;;
            --project-root)
                project_root="$2"
                shift 2
                ;;
            --no-summary)
                no_summary="true"
                shift
                ;;
            quality-check|generate-report|run-coverage|create-tests|batch-create|validate-quality|quick-analysis|setup)
                command="$1"
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Validate project root
    if [[ ! -d "$project_root" ]]; then
        log_error "Project root not found: $project_root"
        exit 1
    fi
    
    # Ensure we're in a Python project with tool_router
    if [[ ! -d "$project_root/tool_router" ]]; then
        log_error "tool_router directory not found in project root"
        exit 1
    fi
    
    # Execute command
    case $command in
        quality-check)
            cmd_quality_check "$file_path" "$project_root"
            ;;
        generate-report)
            cmd_generate_report "$output_path" "$project_root" "$no_summary"
            ;;
        run-coverage)
            cmd_run_coverage "$project_root"
            ;;
        create-tests)
            cmd_create_tests "$module_path" "$test_type" "$project_root"
            ;;
        batch-create)
            cmd_batch_create "$module_pattern" "$test_type" "$project_root"
            ;;
        validate-quality)
            cmd_validate_quality "$file_path" "$project_root"
            ;;
        quick-analysis)
            cmd_quick_analysis "$project_root"
            ;;
        setup)
            setup_environment "$project_root"
            ;;
        "")
            log_error "No command specified"
            show_help
            exit 1
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Execute main function with all arguments
main "$@"
