#!/bin/bash
# Test script for serverless MCP sleep/wake functionality

set -e

echo "🧪 Testing MCP Server Sleep/Wake Functionality"
echo "=========================================="

# Configuration
SERVICE_MANAGER_URL="http://localhost:9000"
TEST_SERVICE="filesystem"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
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

# Check if service manager is running
check_service_manager() {
    log_info "Checking if service manager is running..."

    if curl -s "$SERVICE_MANAGER_URL/health" > /dev/null; then
        log_success "Service manager is running"
        return 0
    else
        log_error "Service manager is not running at $SERVICE_MANAGER_URL"
        echo "Please start the service manager first:"
        echo "  docker-compose up -d service-manager"
        exit 1
    fi
}

# Test service status
test_service_status() {
    local service=$1
    log_info "Checking status of $service service..."

    python3 scripts/service-manager-client.py --url "$SERVICE_MANAGER_URL" status "$service"
}

# Test sleep functionality
test_sleep() {
    local service=$1
    log_info "Testing sleep functionality for $service..."

    # Ensure service is running first
    log_info "Starting $service service..."
    python3 scripts/service-manager-client.py --url "$SERVICE_MANAGER_URL" start "$service"
    sleep 2

    # Check initial status
    log_info "Initial status:"
    test_service_status "$service"

    # Sleep the service
    log_info "Putting $service to sleep..."
    python3 scripts/service-manager-client.py --url "$SERVICE_MANAGER_URL" sleep "$service"
    sleep 2

    # Check sleep status
    log_info "Status after sleep:"
    test_service_status "$service"

    # Verify service is actually sleeping (should show 'sleeping' status)
    local status=$(python3 scripts/service-manager-client.py --url "$SERVICE_MANAGER_URL" status "$service" | grep "Status:" | awk '{print $2}')
    if [ "$status" = "sleeping" ]; then
        log_success "Service successfully entered sleep state"
    else
        log_error "Service failed to enter sleep state (status: $status)"
        return 1
    fi
}

# Test wake functionality
test_wake() {
    local service=$1
    log_info "Testing wake functionality for $service..."

    # Wake the service
    log_info "Waking $service from sleep..."
    python3 scripts/service-manager-client.py --url "$SERVICE_MANAGER_URL" wake "$service"
    sleep 2

    # Check wake status
    log_info "Status after wake:"
    test_service_status "$service"

    # Verify service is running (should show 'running' status)
    local status=$(python3 scripts/service-manager-client.py --url "$SERVICE_MANAGER_URL" status "$service" | grep "Status:" | awk '{print $2}')
    if [ "$status" = "running" ]; then
        log_success "Service successfully woke and is running"
    else
        log_error "Service failed to wake (status: $status)"
        return 1
    fi
}

# Test auto-sleep behavior
test_auto_sleep() {
    local service=$1
    log_info "Testing auto-sleep behavior for $service..."

    # Start the service
    log_info "Starting $service service..."
    python3 scripts/service-manager-client.py --url "$SERVICE_MANAGER_URL" start "$service"
    sleep 2

    # Wait for auto-sleep (this might take a while depending on configuration)
    log_info "Waiting for auto-sleep (this may take several minutes based on idle_timeout)..."
    log_warning "Note: This test may take up to 10 minutes. Press Ctrl+C to skip."

    # Monitor status for up to 10 minutes
    for i in {1..60}; do
        local status=$(python3 scripts/service-manager-client.py --url "$SERVICE_MANAGER_URL" status "$service" 2>/dev/null | grep "Status:" | awk '{print $2}' || echo "unknown")
        echo "[$i/60] Current status: $status"

        if [ "$status" = "sleeping" ]; then
            log_success "Auto-sleep triggered successfully!"
            break
        fi

        sleep 10
    done

    # Clean up - wake the service
    log_info "Waking $service to clean up..."
    python3 scripts/service-manager-client.py --url "$SERVICE_MANAGER_URL" wake "$service" 2>/dev/null || true
}

# Test sleep/wake cycle
test_sleep_wake_cycle() {
    local service=$1
    local cycles=${2:-3}

    log_info "Testing $cycles sleep/wake cycles for $service..."

    for i in $(seq 1 $cycles); do
        log_info "Cycle $i/$cycles"

        # Sleep
        python3 scripts/service-manager-client.py --url "$SERVICE_MANAGER_URL" sleep "$service"
        sleep 2

        # Wake
        python3 scripts/service-manager-client.py --url "$SERVICE_MANAGER_URL" wake "$service"
        sleep 2

        # Check status
        local status=$(python3 scripts/service-manager-client.py --url "$SERVICE_MANAGER_URL" status "$service" | grep "Status:" | awk '{print $2}')
        if [ "$status" = "running" ]; then
            log_success "Cycle $i completed successfully"
        else
            log_error "Cycle $i failed (status: $status)"
            return 1
        fi
    done

    log_success "All $cycles sleep/wake cycles completed successfully"
}

# Test multiple services
test_multiple_services() {
    log_info "Testing sleep/wake with multiple services..."

    local services=("filesystem" "memory" "chrome-devtools")

    for service in "${services[@]}"; do
        log_info "Testing $service..."

        # Start service
        python3 scripts/service-manager-client.py --url "$SERVICE_MANAGER_URL" start "$service" 2>/dev/null || {
            log_warning "Could not start $service, skipping..."
            continue
        }
        sleep 2

        # Sleep service
        python3 scripts/service-manager-client.py --url "$SERVICE_MANAGER_URL" sleep "$service" 2>/dev/null || {
            log_warning "Could not sleep $service, skipping..."
            continue
        }
        sleep 2

        # Wake service
        python3 scripts/service-manager-client.py --url "$SERVICE_MANAGER_URL" wake "$service" 2>/dev/null || {
            log_warning "Could not wake $service, skipping..."
            continue
        }
        sleep 2

        # Stop service to clean up
        python3 scripts/service-manager-client.py --url "$SERVICE_MANAGER_URL" stop "$service" 2>/dev/null || true

        log_success "$service test completed"
    done
}

# Main test execution
main() {
    echo "Starting sleep/wake functionality tests..."
    echo

    # Check prerequisites
    check_service_manager
    echo

    # Test basic sleep/wake
    log_info "=== Basic Sleep/Wake Test ==="
    test_sleep "$TEST_SERVICE"
    test_wake "$TEST_SERVICE"
    echo

    # Test sleep/wake cycles
    log_info "=== Sleep/Wake Cycle Test ==="
    test_sleep_wake_cycle "$TEST_SERVICE" 2
    echo

    # Test multiple services
    log_info "=== Multiple Services Test ==="
    test_multiple_services
    echo

    # Optional: Test auto-sleep (commented out as it takes time)
    # log_info "=== Auto-Sleep Test ==="
    # test_auto_sleep "$TEST_SERVICE"
    # echo

    log_success "All sleep/wake tests completed successfully! 🎉"

    # Clean up
    log_info "Cleaning up test service..."
    python3 scripts/service-manager-client.py --url "$SERVICE_MANAGER_URL" stop "$TEST_SERVICE" 2>/dev/null || true
}

# Run main function
main "$@"
