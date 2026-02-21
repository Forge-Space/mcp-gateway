#!/bin/bash

# Advanced Monitoring and Alerting Script for MCP Gateway
# Implements comprehensive monitoring with automated alerting and incident response

set -euo pipefail

# Configuration
SCRIPT_NAME="$(basename "$0")"
LOG_FILE="/tmp/mcp-gateway-monitoring-$(date +%Y%m%d_%H%M%S).log"
ALERT_LOG="/tmp/mcp-gateway-alerts-$(date +%Y%m%d_%H%M%S).log"
METRICS_FILE="/tmp/mcp-gateway-metrics-$(date +%Y%m%d_%H%M%S).json"
COMPOSE_FILE="docker-compose.production.yml"

# Alert thresholds
CPU_THRESHOLD=80
MEMORY_THRESHOLD=85
DISK_THRESHOLD=90
ERROR_RATE_THRESHOLD=5
RESPONSE_TIME_THRESHOLD=2000

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Alert function
alert() {
    local severity=$1
    local message=$2
    local service=$3

    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local alert_entry="{\"timestamp\":\"$timestamp\",\"severity\":\"$severity\",\"service\":\"$service\",\"message\":\"$message\"}"

    echo "$alert_entry" | tee -a "$ALERT_LOG"

    case $severity in
        "CRITICAL")
            echo -e "${RED}🚨 CRITICAL ALERT${NC}: $message (Service: $service)"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️  WARNING${NC}: $message (Service: $service)"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️  INFO${NC}: $message (Service: $service)"
            ;;
    esac
}

# Check service health
check_service_health() {
    local service=$1
    local health_url=$2

    if ! curl -s --connect-timeout 5 --max-time 10 "$health_url" >/dev/null 2>&1; then
        alert "CRITICAL" "Service is not responding" "$service"
        return 1
    fi

    # Check response time
    local response_time
    response_time=$(curl -o /dev/null -s -w '%{time_total}' --connect-timeout 5 --max-time 10 "$health_url" 2>/dev/null || echo "999")

    # Convert to milliseconds
    local response_time_ms=$(echo "$response_time * 1000" | bc 2>/dev/null || echo "999999")

    if (( $(echo "$response_time_ms > $RESPONSE_TIME_THRESHOLD" | bc -l 2>/dev/null || echo "0") )); then
        alert "WARNING" "High response time: ${response_time_ms}ms" "$service"
    fi

    echo "$response_time_ms"
}

# Check Docker container metrics
check_container_metrics() {
    local container_name=$1
    local service_name=$2

    if ! docker ps --format "{{.Names}}" | grep -q "^${container_name}$"; then
        alert "CRITICAL" "Container is not running" "$service_name"
        return 1
    fi

    # Get container stats
    local stats
    stats=$(docker stats --no-stream --format "{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" "$container_name" 2>/dev/null || echo "")

    if [[ -z "$stats" ]]; then
        alert "WARNING" "Could not retrieve container stats" "$service_name"
        return 1
    fi

    # Parse stats
    local cpu_percent=$(echo "$stats" | cut -f1 | sed 's/%//')
    local mem_usage=$(echo "$stats" | cut -f2)
    local mem_percent=$(echo "$stats" | cut -f3 | sed 's/%//')

    # Check CPU usage
    if (( $(echo "$cpu_percent > $CPU_THRESHOLD" | bc -l 2>/dev/null || echo "0") )); then
        alert "WARNING" "High CPU usage: ${cpu_percent}%" "$service_name"
    fi

    # Check memory usage
    if (( $(echo "$mem_percent > $MEMORY_THRESHOLD" | bc -l 2>/dev/null || echo "0") )); then
        alert "WARNING" "High memory usage: ${mem_percent} (${mem_usage})" "$service_name"
    fi

    echo "{\"cpu_percent\":$cpu_percent,\"memory_percent\":$mem_percent,\"memory_usage\":\"$mem_usage\"}"
}

# Check system resources
check_system_resources() {
    # CPU usage
    local cpu_usage
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//' 2>/dev/null || echo "0")

    if (( $(echo "$cpu_usage > $CPU_THRESHOLD" | bc -l 2>/dev/null || echo "0") )); then
        alert "WARNING" "High system CPU usage: ${cpu_usage}%" "System"
    fi

    # Memory usage
    local mem_usage
    mem_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}' 2>/dev/null || echo "0")

    if (( $(echo "$mem_usage > $MEMORY_THRESHOLD" | bc -l 2>/dev/null || echo "0") )); then
        alert "WARNING" "High system memory usage: ${mem_usage}%" "System"
    fi

    # Disk usage
    local disk_usage
    disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//' 2>/dev/null || echo "0")

    if (( disk_usage > DISK_THRESHOLD )); then
        alert "CRITICAL" "High disk usage: ${disk_usage}%" "System"
    fi

    echo "{\"cpu_percent\":$cpu_usage,\"memory_percent\":$mem_usage,\"disk_percent\":$disk_usage}"
}

# Check error rates from logs
check_error_rates() {
    local service=$1
    local log_pattern=$2
    local time_window=5  # minutes

    # Count errors in recent logs
    local error_count
    error_count=$(docker-compose -f "$COMPOSE_FILE" logs --since="${time_window}m" "$service" 2>/dev/null | grep -i -c "error\|exception\|failed" || echo "0")

    # Count total log entries
    local total_count
    total_count=$(docker-compose -f "$COMPOSE_FILE" logs --since="${time_window}m" "$service" 2>/dev/null | wc -l || echo "1")

    # Calculate error rate
    local error_rate
    error_rate=$(echo "scale=2; $error_count * 100 / $total_count" | bc 2>/dev/null || echo "0")

    if (( $(echo "$error_rate > $ERROR_RATE_THRESHOLD" | bc -l 2>/dev/null || echo "0") )); then
        alert "WARNING" "High error rate: ${error_rate}% (${error_count}/${total_count} entries)" "$service"
    fi

    echo "{\"error_count\":$error_count,\"total_count\":$total_count,\"error_rate\":$error_rate}"
}

# Automated incident response
incident_response() {
    local severity=$1
    local service=$2
    local issue=$3

    case $severity in
        "CRITICAL")
            # Restart service if critical
            if [[ "$issue" == *"not running"* ]] || [[ "$issue" == *"not responding"* ]]; then
                log "Attempting automatic restart of $service..."
                docker-compose -f "$COMPOSE_FILE" restart "$service" 2>/dev/null || true
                alert "INFO" "Automatic restart initiated for $service" "IncidentResponse"
            fi

            # Scale up if resource constraints
            if [[ "$issue" == *"High CPU"* ]] || [[ "$issue" == *"High memory"* ]]; then
                log "Resource constraint detected, checking scaling options..."
                # Could implement auto-scaling here
                alert "INFO" "Resource constraint detected for $service - manual intervention may be required" "IncidentResponse"
            fi
            ;;
        "WARNING")
            # Log warning for later analysis
            log "Warning condition detected for $service: $issue"
            ;;
    esac
}

# Generate metrics report
generate_metrics_report() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    echo "{"
    echo "  \"timestamp\": \"$timestamp\","
    echo "  \"services\": {"

    local services=("gateway" "service-manager" "postgres" "redis" "web-admin")
    local first=true

    for service in "${services[@]}"; do
        if [[ "$first" == "true" ]]; then
            first=false
        else
            echo ","
        fi

        echo "    \"$service\": {"

        # Get container metrics
        local container_name="forge-${service}-prod"
        if docker ps --format "{{.Names}}" | grep -q "$container_name"; then
            local metrics=$(check_container_metrics "$container_name" "$service")
            echo "      \"container_metrics\": $metrics,"
        else
            echo "      \"container_metrics\": null,"
        fi

        # Get health metrics if applicable
        case $service in
            "gateway")
                local health_time=$(check_service_health "gateway" "http://localhost:8000/health")
                echo "      \"response_time_ms\": $health_time,"
                ;;
            "service-manager")
                local health_time=$(check_service_health "service-manager" "http://localhost:9000/health")
                echo "      \"response_time_ms\": $health_time,"
                ;;
        esac

        # Get error rates
        local error_metrics=$(check_error_rates "$service" ".*")
        echo "      \"error_metrics\": $error_metrics"

        echo -n "    }"
    done

    echo ""
    echo "  },"

    # System metrics
    local system_metrics=$(check_system_resources)
    echo "  \"system_metrics\": $system_metrics,"

    # Alert summary
    local critical_count
    local warning_count
    critical_count=$(grep -c '"severity":"CRITICAL"' "$ALERT_LOG" 2>/dev/null || echo "0")
    warning_count=$(grep -c '"severity":"WARNING"' "$ALERT_LOG" 2>/dev/null || echo "0")

    echo "  \"alert_summary\": {"
    echo "    \"critical_alerts\": $critical_count,"
    echo "    \"warning_alerts\": $warning_count"
    echo "  }"
    echo "}"
}

# Continuous monitoring mode
continuous_monitoring() {
    local interval=${1:-60}  # seconds

    log "Starting continuous monitoring with ${interval}s interval..."

    while true; do
        log "Running monitoring cycle..."

        # Clear current alert log for this cycle
        > "$ALERT_LOG"

        # Check all services
        local services=("gateway" "service-manager" "postgres" "redis" "web-admin")

        for service in "${services[@]}"; do
            log "Checking $service..."

            # Container metrics
            local container_name="forge-${service}-prod"
            check_container_metrics "$container_name" "$service"

            # Health checks for applicable services
            case $service in
                "gateway")
                    check_service_health "gateway" "http://localhost:8000/health"
                    ;;
                "service-manager")
                    check_service_health "service-manager" "http://localhost:9000/health"
                    ;;
            esac

            # Error rate monitoring
            check_error_rates "$service" ".*"
        done

        # System resources
        check_system_resources

        # Generate metrics report
        generate_metrics_report > "$METRICS_FILE"

        # Check for critical alerts and trigger incident response
        if grep -q '"severity":"CRITICAL"' "$ALERT_LOG" 2>/dev/null; then
            log "Critical alerts detected, triggering incident response..."

            while IFS= read -r line; do
                local severity=$(echo "$line" | jq -r '.severity' 2>/dev/null || echo "UNKNOWN")
                local service=$(echo "$line" | jq -r '.service' 2>/dev/null || echo "UNKNOWN")
                local message=$(echo "$line" | jq -r '.message' 2>/dev/null || echo "UNKNOWN")

                if [[ "$severity" == "CRITICAL" ]]; then
                    incident_response "$severity" "$service" "$message"
                fi
            done < "$ALERT_LOG"
        fi

        log "Monitoring cycle completed. Next cycle in ${interval}s..."
        sleep "$interval"
    done
}

# Show help
show_help() {
    cat << EOF
Usage: $SCRIPT_NAME [OPTIONS]

Advanced Monitoring and Alerting Script for MCP Gateway

OPTIONS:
    -c, --check          Run single monitoring check
    -r, --report         Generate metrics report only
    -m, --monitor SECS   Continuous monitoring (default: 60 seconds)
    -a, --alerts         Show recent alerts
    -f, --file FILE      Docker compose file (default: docker-compose.production.yml)
    -l, --log FILE       Log file path (auto-generated if not specified)
    -h, --help          Show this help message

EXAMPLES:
    $SCRIPT_NAME                          # Single monitoring check
    $SCRIPT_NAME -m 30                    # Continuous monitoring every 30 seconds
    $SCRIPT_NAME -r                       # Generate metrics report only
    $SCRIPT_NAME -a                       # Show recent alerts

ALERT THRESHOLDS:
    CPU: ${CPU_THRESHOLD}%
    Memory: ${MEMORY_THRESHOLD}%
    Disk: ${DISK_THRESHOLD}%
    Error Rate: ${ERROR_RATE_THRESHOLD}%
    Response Time: ${RESPONSE_TIME_THRESHOLD}ms

EOF
}

# Parse command line arguments
RUN_CHECK=false
RUN_REPORT=false
RUN_MONITOR=false
RUN_ALERTS=false
MONITOR_INTERVAL=60

while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--check)
            RUN_CHECK=true
            shift
            ;;
        -r|--report)
            RUN_REPORT=true
            shift
            ;;
        -m|--monitor)
            RUN_MONITOR=true
            MONITOR_INTERVAL="${2:-60}"
            shift 2
            ;;
        -a|--alerts)
            RUN_ALERTS=true
            shift
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
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Main execution
main() {
    echo "🔍 MCP Gateway Advanced Monitoring"
    echo "=================================="

    log "Starting advanced monitoring"

    if [[ "$RUN_MONITOR" == "true" ]]; then
        continuous_monitoring "$MONITOR_INTERVAL"
    elif [[ "$RUN_REPORT" == "true" ]]; then
        generate_metrics_report
    elif [[ "$RUN_ALERTS" == "true" ]]; then
        if [[ -f "$ALERT_LOG" ]]; then
            echo "Recent alerts:"
            cat "$ALERT_LOG"
        else
            echo "No alert log found"
        fi
    else
        # Default: single check
        > "$ALERT_LOG"

        local services=("gateway" "service-manager" "postgres" "redis" "web-admin")

        for service in "${services[@]}"; do
            log "Checking $service..."

            local container_name="forge-${service}-prod"
            check_container_metrics "$container_name" "$service"

            case $service in
                "gateway")
                    check_service_health "gateway" "http://localhost:8000/health"
                    ;;
                "service-manager")
                    check_service_health "service-manager" "http://localhost:9000/health"
                    ;;
            esac

            check_error_rates "$service" ".*"
        done

        check_system_resources
        generate_metrics_report

        log "Monitoring check completed"
        echo "Log file: $LOG_FILE"
        echo "Alerts: $ALERT_LOG"
        echo "Metrics: $METRICS_FILE"
    fi
}

# Trap to handle interruption
trap 'log "Monitoring interrupted"; exit 0' INT TERM

# Run main function
main "$@"
