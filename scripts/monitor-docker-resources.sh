#!/bin/bash

# Docker Resource Monitoring Script for MCP Gateway
# Monitors CPU, memory, and resource usage for all MCP Gateway services

set -euo pipefail

# Configuration
SCRIPT_NAME="$(basename "$0")"
LOG_FILE="/tmp/mcp-gateway-monitor.log"
ALERT_THRESHOLD_CPU=80
ALERT_THRESHOLD_MEMORY=80
ALERT_THRESHOLD_DISK=85
CHECK_INTERVAL=30
COMPOSE_FILE="docker-compose.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_status "$RED" "ERROR: Docker is not running or accessible"
        exit 1
    fi
}

# Get container resource usage
get_container_stats() {
    local container_name=$1
    local stats
    stats=$(docker stats --no-stream --format "table {{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}" "$container_name" 2>/dev/null || echo "")

    if [[ -z "$stats" ]]; then
        echo "N/A\tN/A\tN/A\tN/A\tN/A"
        return
    fi

    # Skip header line and get actual stats
    echo "$stats" | tail -n 1
}

# Parse memory usage
parse_memory_usage() {
    local mem_usage=$1
    local mem_value mem_unit

    if [[ "$mem_usage" == "N/A" ]]; then
        echo "0"
        return
    fi

    # Extract value and unit (e.g., "256MiB" -> "256" "MiB")
    mem_value=$(echo "$mem_usage" | sed 's/\([0-9.]*\).*/\1/')
    mem_unit=$(echo "$mem_usage" | sed 's/[0-9.]*\([A-Za-z]*\).*/\1/')

    # Convert to MB
    case "$mem_unit" in
        "MiB"|"Mi") echo "$mem_value" ;;
        "GiB"|"Gi") echo "$(echo "$mem_value * 1024" | bc -l)" ;;
        "KiB"|"Ki") echo "$(echo "$mem_value / 1024" | bc -l)" ;;
        "B") echo "$(echo "$mem_value / 1024 / 1024" | bc -l)" ;;
        *) echo "0" ;;
    esac
}

# Parse CPU percentage
parse_cpu_usage() {
    local cpu_perc=$1

    if [[ "$cpu_perc" == "N/A" ]]; then
        echo "0"
        return
    fi

    # Remove % sign and convert to number
    echo "$cpu_perc" | sed 's/%//'
}

# Check alert thresholds
check_alerts() {
    local container_name=$1
    local cpu_perc=$2
    local mem_perc=$3

    local cpu_num mem_num
    cpu_num=$(parse_cpu_usage "$cpu_perc")
    mem_num=$(parse_cpu_usage "$mem_perc")

    # Check CPU threshold
    if (( $(echo "$cpu_num > $ALERT_THRESHOLD_CPU" | bc -l) )); then
        print_status "$RED" "🚨 ALERT: High CPU usage for $container_name: $cpu_perc%"
        log "ALERT: High CPU usage for $container_name: $cpu_perc%"
    fi

    # Check memory threshold
    if (( $(echo "$mem_num > $ALERT_THRESHOLD_MEMORY" | bc -l) )); then
        print_status "$RED" "🚨 ALERT: High memory usage for $container_name: $mem_perc%"
        log "ALERT: High memory usage for $container_name: $mem_perc%"
    fi
}

# Get disk usage
get_disk_usage() {
    local disk_usage
    disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    echo "$disk_usage"
}

# Monitor containers
monitor_containers() {
    local containers
    containers=$(docker-compose -f "$COMPOSE_FILE" ps --services 2>/dev/null || echo "")

    if [[ -z "$containers" ]]; then
        print_status "$YELLOW" "No containers found in $COMPOSE_FILE"
        return
    fi

    print_status "$BLUE" "📊 MCP Gateway Resource Monitor"
    echo "=========================================="
    printf "%-25s %-10s %-15s %-10s %-15s %-15s\n" "CONTAINER" "CPU %" "MEMORY USAGE" "MEM %" "NET I/O" "BLOCK I/O"
    echo "------------------------------------------"

    local total_cpu=0
    local total_memory_mb=0
    local container_count=0

    while IFS= read -r container; do
        if [[ -n "$container" ]]; then
            local container_id
            container_id=$(docker-compose -f "$COMPOSE_FILE" ps -q "$container" 2>/dev/null | head -n1 || echo "")

            if [[ -n "$container_id" ]]; then
                local container_name
                container_name=$(docker ps --filter "id=$container_id" --format "{{.Names}}" 2>/dev/null || echo "$container")

                local stats
                stats=$(get_container_stats "$container_name")

                local cpu_perc mem_usage mem_perc net_io block_io
                IFS=$'\t' read -r cpu_perc mem_usage mem_perc net_io block_io <<< "$stats"

                # Calculate totals
                local cpu_num mem_mb
                cpu_num=$(parse_cpu_usage "$cpu_perc")
                mem_mb=$(parse_memory_usage "$mem_usage")

                total_cpu=$(echo "$total_cpu + $cpu_num" | bc -l)
                total_memory_mb=$(echo "$total_memory_mb + $mem_mb" | bc -l)
                container_count=$((container_count + 1))

                # Print container stats
                printf "%-25s %-10s %-15s %-10s %-15s %-15s\n" \
                    "${container_name:0:24}" \
                    "$cpu_perc" \
                    "$mem_usage" \
                    "$mem_perc" \
                    "$net_io" \
                    "$block_io"

                # Check alerts
                check_alerts "$container_name" "$cpu_perc" "$mem_perc"
            fi
        fi
    done <<< "$containers"

    echo "------------------------------------------"

    # Summary
    local avg_cpu avg_memory_mb
    if (( container_count > 0 )); then
        avg_cpu=$(echo "scale=2; $total_cpu / $container_count" | bc -l)
        avg_memory_mb=$(echo "scale=2; $total_memory_mb / $container_count" | bc -l)

        print_status "$GREEN" "📈 Summary: $container_count containers | Avg CPU: ${avg_cpu}% | Avg Memory: ${avg_memory_mb}MB"
    fi

    # Check disk usage
    local disk_usage
    disk_usage=$(get_disk_usage)
    if (( disk_usage > ALERT_THRESHOLD_DISK )); then
        print_status "$RED" "🚨 ALERT: High disk usage: ${disk_usage}%"
        log "ALERT: High disk usage: ${disk_usage}%"
    else
        print_status "$GREEN" "💾 Disk usage: ${disk_usage}%"
    fi
}

# Continuous monitoring mode
continuous_monitor() {
    print_status "$BLUE" "🔄 Starting continuous monitoring (interval: ${CHECK_INTERVAL}s)"
    print_status "$YELLOW" "Press Ctrl+C to stop monitoring"

    while true; do
        clear
        monitor_containers
        echo
        print_status "$BLUE" "Next check in ${CHECK_INTERVAL}s... ($(date '+%H:%M:%S'))"
        sleep "$CHECK_INTERVAL"
    done
}

# Help function
show_help() {
    cat << EOF
Usage: $SCRIPT_NAME [OPTIONS]

Docker Resource Monitoring Script for MCP Gateway

OPTIONS:
    -c, --continuous    Run in continuous monitoring mode
    -i, --interval N    Set check interval in seconds (default: 30)
    -t, --threshold N   Set alert threshold percentage (default: 80)
    -f, --file FILE     Docker compose file (default: docker-compose.yml)
    -l, --log FILE      Log file path (default: /tmp/mcp-gateway-monitor.log)
    -h, --help          Show this help message

EXAMPLES:
    $SCRIPT_NAME                          # Single check
    $SCRIPT_NAME -c                       # Continuous monitoring
    $SCRIPT_NAME -c -i 60                 # Continuous with 60s interval
    $SCRIPT_NAME -t 90                    # Set alert threshold to 90%

EOF
}

# Parse command line arguments
CONTINUOUS_MODE=false
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--continuous)
            CONTINUOUS_MODE=true
            shift
            ;;
        -i|--interval)
            CHECK_INTERVAL="$2"
            shift 2
            ;;
        -t|--threshold)
            ALERT_THRESHOLD_CPU="$2"
            ALERT_THRESHOLD_MEMORY="$2"
            shift 2
            ;;
        -f|--file)
            COMPOSE_FILE="$2"
            shift 2
            ;;
        -l|--log)
            LOG_FILE="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            print_status "$RED" "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Main execution
main() {
    log "Starting MCP Gateway resource monitoring"

    # Check prerequisites
    check_docker

    # Check if bc is available for calculations
    if ! command -v bc >/dev/null 2>&1; then
        print_status "$YELLOW" "Warning: 'bc' not found, some calculations may not work"
    fi

    if [[ "$CONTINUOUS_MODE" == "true" ]]; then
        continuous_monitor
    else
        monitor_containers
    fi

    log "Monitoring session completed"
}

# Trap to handle interruption
trap 'log "Monitoring interrupted"; exit 0' INT TERM

# Run main function
main "$@"
