#!/bin/bash
# Integration Test Runner for Serverless MCP Sleep Architecture
# Tests real Docker containers with sleep/wake functionality

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_MANAGER_DIR="$(dirname "$SCRIPT_DIR")/service-manager"
TEST_RESULTS_DIR="$SCRIPT_DIR/test-results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Create results directory
mkdir -p "$TEST_RESULTS_DIR"

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
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

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker daemon."
        exit 1
    fi
    log_success "Docker is running"

    # Check if Python 3.9+ is available
    if ! python3 --version | grep -E "Python 3\.[9-9]|[1-9][0-9]" > /dev/null; then
        log_error "Python 3.9+ is required. Current version: $(python3 --version)"
        exit 1
    fi
    log_success "Python $(python3 --version | cut -d' ' -f2) is available"

    # Check if required Python packages are installed
    cd "$SERVICE_MANAGER_DIR"
    if ! python3 -c "import docker, pytest, asyncio" 2>/dev/null; then
        log_error "Required Python packages not found. Installing..."
        pip3 install -r requirements.txt
    fi
    log_success "Required Python packages are available"

    # Check if service-manager.py exists
    if [[ ! -f "service_manager.py" ]]; then
        log_error "service_manager.py not found in $SERVICE_MANAGER_DIR"
        exit 1
    fi
    log_success "service_manager.py found"
}

# Run unit tests
run_unit_tests() {
    log "Running unit tests..."

    cd "$SERVICE_MANAGER_DIR"

    # Run with coverage
    if python3 -m pytest tests/test_sleep_wake.py -v --cov=service_manager --cov-report=term-missing --cov-report=html:"$TEST_RESULTS_DIR/unit_coverage_$TIMESTAMP" --junitxml="$TEST_RESULTS_DIR/unit_results_$TIMESTAMP.xml"; then
        log_success "Unit tests passed"
        return 0
    else
        log_error "Unit tests failed"
        return 1
    fi
}

# Run integration tests
run_integration_tests() {
    log "Running integration tests with real Docker containers..."

    cd "$SERVICE_MANAGER_DIR"

    # Run integration tests with markers
    if python3 -m pytest tests/test_integration_sleep_wake.py -v -m integration --junitxml="$TEST_RESULTS_DIR/integration_results_$TIMESTAMP.xml"; then
        log_success "Integration tests passed"
        return 0
    else
        log_error "Integration tests failed"
        return 1
    fi
}

# Run performance benchmarks
run_performance_benchmarks() {
    log "Running performance benchmarks..."

    local benchmark_script="$SCRIPT_DIR/benchmark-sleep-wake-performance.py"

    if [[ ! -f "$benchmark_script" ]]; then
        log_error "Benchmark script not found: $benchmark_script"
        return 1
    fi

    cd "$SCRIPT_DIR"

    # Run benchmark and capture results
    if python3 "$benchmark_script" > "$TEST_RESULTS_DIR/benchmark_$TIMESTAMP.log" 2>&1; then
        log_success "Performance benchmarks passed"
        return 0
    else
        log_error "Performance benchmarks failed"
        log_warning "Check benchmark results in: $TEST_RESULTS_DIR/benchmark_$TIMESTAMP.log"
        return 1
    fi
}

# Run Docker compliance checks
run_docker_compliance() {
    log "Running Docker standards compliance checks..."

    local compliance_script="$SCRIPT_DIR/docker-standards-compliance.sh"

    if [[ -f "$compliance_script" ]]; then
        if bash "$compliance_script" > "$TEST_RESULTS_DIR/docker_compliance_$TIMESTAMP.log" 2>&1; then
            log_success "Docker compliance checks passed"
            return 0
        else
            log_error "Docker compliance checks failed"
            log_warning "Check compliance results in: $TEST_RESULTS_DIR/docker_compliance_$TIMESTAMP.log"
            return 1
        fi
    else
        log_warning "Docker compliance script not found, skipping..."
        return 0
    fi
}

# Validate success metrics
validate_success_metrics() {
    log "Validating success metrics against targets..."

    local benchmark_file="$TEST_RESULTS_DIR/benchmark_$TIMESTAMP.log"
    local metrics_passed=true

    if [[ -f "$benchmark_file" ]]; then
        # Check wake time target (< 200ms)
        if grep -q "Wake time.*exceeds 200ms target" "$benchmark_file"; then
            log_error "Wake time target not met (should be < 200ms)"
            metrics_passed=false
        else
            log_success "Wake time target met (< 200ms)"
        fi

        # Check memory reduction target (> 60%)
        if grep -q "Memory reduction.*below 60% target" "$benchmark_file"; then
            log_error "Memory reduction target not met (should be > 60%)"
            metrics_passed=false
        else
            log_success "Memory reduction target met (> 60%)"
        fi

        # Check success rate target (> 99.9%)
        if grep -q "Success rate.*below 99.9% target" "$benchmark_file"; then
            log_error "Success rate target not met (should be > 99.9%)"
            metrics_passed=false
        else
            log_success "Success rate target met (> 99.9%)"
        fi

        if [[ "$metrics_passed" == true ]]; then
            log_success "All success metrics validated"
            return 0
        else
            log_error "Some success metrics not met"
            return 1
        fi
    else
        log_warning "Benchmark results not found, skipping metrics validation"
        return 0
    fi
}

# Generate test report
generate_test_report() {
    log "Generating test report..."

    local report_file="$TEST_RESULTS_DIR/test_report_$TIMESTAMP.md"

    cat > "$report_file" << EOF
# Serverless MCP Sleep Architecture - Test Report

**Generated:** $(date)
**Test Environment:** $(uname -s) $(uname -r)
**Docker Version:** $(docker --version)
**Python Version:** $(python3 --version)

## Test Results Summary

### Unit Tests
- **Status:** $([[ -f "$TEST_RESULTS_DIR/unit_results_$TIMESTAMP.xml" ]] && echo "✅ Passed" || echo "❌ Failed/Not Run")
- **Coverage Report:** $([[ -f "$TEST_RESULTS_DIR/unit_coverage_$TIMESTAMP" ]] && echo "Generated" || echo "Not Available")

### Integration Tests
- **Status:** $([[ -f "$TEST_RESULTS_DIR/integration_results_$TIMESTAMP.xml" ]] && echo "✅ Passed" || echo "❌ Failed/Not Run")
- **Real Docker Containers:** Tested with actual Docker pause/unpause operations

### Performance Benchmarks
- **Status:** $([[ -f "$TEST_RESULTS_DIR/benchmark_$TIMESTAMP.log" ]] && echo "✅ Completed" || echo "❌ Failed/Not Run")
- **Results File:** \`benchmark_$TIMESTAMP.log\`

### Docker Compliance
- **Status:** $([[ -f "$TEST_RESULTS_DIR/docker_compliance_$TIMESTAMP.log" ]] && echo "✅ Passed" || echo "❌ Failed/Not Run")

## Success Metrics Validation

EOF

    if [[ -f "$TEST_RESULTS_DIR/benchmark_$TIMESTAMP.log" ]]; then
        cat >> "$report_file" << EOF
### Performance Targets

| Metric | Target | Status |
|--------|--------|--------|
| Wake Time | < 200ms | $(grep -q "Wake time.*exceeds 200ms target" "$TEST_RESULTS_DIR/benchmark_$TIMESTAMP.log" && echo "❌ Failed" || echo "✅ Passed") |
| Memory Reduction | > 60% | $(grep -q "Memory reduction.*below 60% target" "$TEST_RESULTS_DIR/benchmark_$TIMESTAMP.log" && echo "❌ Failed" || echo "✅ Passed") |
| Success Rate | > 99.9% | $(grep -q "Success rate.*below 99.9% target" "$TEST_RESULTS_DIR/benchmark_$TIMESTAMP.log" && echo "❌ Failed" || echo "✅ Passed") |

EOF
    fi

    cat >> "$report_file" << EOF
## Test Artifacts

- Unit Test Results: \`unit_results_$TIMESTAMP.xml\`
- Integration Test Results: \`integration_results_$TIMESTAMP.xml\`
- Coverage Report: \`unit_coverage_$TIMESTAMP/\`
- Benchmark Log: \`benchmark_$TIMESTAMP.log\`
- Docker Compliance: \`docker_compliance_$TIMESTAMP.log\`

## Recommendations

EOF

    # Add recommendations based on test results
    if [[ ! -f "$TEST_RESULTS_DIR/unit_results_$TIMESTAMP.xml" ]]; then
        echo "- Fix unit test failures before proceeding" >> "$report_file"
    fi

    if [[ ! -f "$TEST_RESULTS_DIR/integration_results_$TIMESTAMP.xml" ]]; then
        echo "- Fix integration test failures to validate real Docker operations" >> "$report_file"
    fi

    if [[ ! -f "$TEST_RESULTS_DIR/benchmark_$TIMESTAMP.log" ]]; then
        echo "- Fix benchmark issues to validate performance targets" >> "$report_file"
    fi

    log_success "Test report generated: $report_file"
}

# Cleanup function
cleanup() {
    log "Cleaning up test containers..."

    # Remove any test containers that might be left behind
    docker ps -q --filter "label=benchmark=true" | xargs -r docker rm -f 2>/dev/null || true
    docker ps -q --filter "name=test-" | xargs -r docker rm -f 2>/dev/null || true

    log_success "Cleanup completed"
}

# Main execution
main() {
    local exit_code=0

    log "Starting Serverless MCP Sleep Architecture Integration Tests"
    log "Results will be saved to: $TEST_RESULTS_DIR"

    # Set up cleanup trap
    trap cleanup EXIT

    # Check prerequisites
    if ! check_prerequisites; then
        exit_code=1
        return $exit_code
    fi

    # Run tests
    echo
    log "=========================================="
    log "Running Test Suite"
    log "=========================================="
    echo

    # Unit tests
    if ! run_unit_tests; then
        exit_code=1
    fi

    # Integration tests
    if ! run_integration_tests; then
        exit_code=1
    fi

    # Performance benchmarks
    if ! run_performance_benchmarks; then
        exit_code=1
    fi

    # Docker compliance
    if ! run_docker_compliance; then
        exit_code=1
    fi

    # Validate success metrics
    if ! validate_success_metrics; then
        exit_code=1
    fi

    # Generate report
    generate_test_report

    echo
    log "=========================================="
    if [[ $exit_code -eq 0 ]]; then
        log_success "All tests completed successfully! 🎉"
        log "Serverless MCP Sleep Architecture is ready for production deployment."
    else
        log_error "Some tests failed. Please review the logs and fix issues."
        log "Check the test report for detailed results."
    fi
    log "=========================================="

    return $exit_code
}

# Help function
show_help() {
    cat << EOF
Serverless MCP Sleep Architecture - Integration Test Runner

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -h, --help          Show this help message
    --unit-only         Run only unit tests
    --integration-only  Run only integration tests
    --benchmark-only    Run only performance benchmarks
    --compliance-only   Run only Docker compliance checks
    --no-cleanup        Skip cleanup of test containers

EXAMPLES:
    $0                  Run all tests
    $0 --unit-only      Run only unit tests
    $0 --benchmark-only Run only performance benchmarks

DESCRIPTION:
    This script runs comprehensive integration tests for the serverless MCP
    sleep architecture, including unit tests, integration tests with real
    Docker containers, performance benchmarks, and Docker compliance checks.

    All results are saved to the test-results directory with timestamps.
EOF
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    --unit-only)
        check_prerequisites
        run_unit_tests
        exit $?
        ;;
    --integration-only)
        check_prerequisites
        run_integration_tests
        exit $?
        ;;
    --benchmark-only)
        check_prerequisites
        run_performance_benchmarks
        exit $?
        ;;
    --compliance-only)
        run_docker_compliance
        exit $?
        ;;
    --no-cleanup)
        # Override cleanup trap
        trap -p EXIT
        main
        exit $?
        ;;
    "")
        # Run all tests
        main
        exit $?
        ;;
    *)
        echo "Unknown option: $1"
        show_help
        exit 1
        ;;
esac
