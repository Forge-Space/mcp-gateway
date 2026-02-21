#!/bin/bash
# Monitoring Dashboard for Scalable MCP Gateway
# Real-time monitoring and visualization of the scalable architecture

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
GATEWAY_URL="http://localhost:4444"
SERVICE_MANAGER_URL="http://localhost:9000"
TOOL_ROUTER_URL="http://localhost:8030"
REFRESH_INTERVAL=5

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# Clear screen and show header
show_header() {
    clear
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║              Scalable MCP Gateway Monitoring Dashboard         ║${NC}"
    echo -e "${CYAN}║                     Real-time Status                        ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Show service status
show_service_status() {
    echo -e "${MAGENTA}📊 Service Status${NC}"
    echo "┌─────────────────────────────────────────────────────────────────┐"
    echo "│ Service           │ Status    │ CPU    │ Memory   │ Uptime        │"
    echo "├─────────────────────────────────────────────────────────────────┤"

    # Get container stats
    local containers=$(docker-compose -f docker-compose.scalable.yml ps -q 2>/dev/null || echo "")

    for container_id in $containers; do
        if [[ -n "$container_id" ]]; then
            local container_info=$(docker inspect "$container_id" 2>/dev/null || echo "{}")
            local container_name=$(echo "$container_info" | jq -r '.[0].Name' 2>/dev/null | sed 's/^.\///' || echo "unknown")
            local container_status=$(echo "$container_info" | jq -r '.[0].State.Status' 2>/dev/null || echo "unknown")

            # Get resource usage
            local stats=$(docker stats --no-stream --format "table {{.CPUPerc}}\t{{.MemUsage}}" "$container_id" 2>/dev/null | tail -1 || echo "0%\t0B")
            local cpu_usage=$(echo "$stats" | cut -f1)
            local memory_usage=$(echo "$stats" | cut -f2)

            # Calculate uptime
            local started_at=$(echo "$container_info" | jq -r '.[0].State.StartedAt' 2>/dev/null || echo "")
            local uptime="N/A"

            if [[ -n "$started_at" && "$started_at" != "null" ]]; then
                local start_timestamp=$(date -d "$started_at" +%s 2>/dev/null || echo "0")
                local current_timestamp=$(date +%s)
                local uptime_seconds=$((current_timestamp - start_timestamp))

                if [[ $uptime_seconds -gt 86400 ]]; then
                    uptime="$((uptime_seconds / 86400))d $(((uptime_seconds % 86400) / 3600))h"
                elif [[ $uptime_seconds -gt 3600 ]]; then
                    uptime="$((uptime_seconds / 3600))h $(((uptime_seconds % 3600) / 60))m"
                else
                    uptime="$((uptime_seconds / 60))m $((uptime_seconds % 60))s"
                fi
            fi

            # Color code status
            local status_color="$GREEN"
            if [[ "$container_status" == "running" ]]; then
                status_color="$GREEN"
            elif [[ "$container_status" == "paused" ]]; then
                status_color="$YELLOW"
            else
                status_color="$RED"
            fi

            printf "│ %-16s │ ${status_color}%-9s${NC} │ %-6s │ %-8s │ %-12s │\n" \
                "$container_name" "$container_status" "$cpu_usage" "$memory_usage" "$uptime"
        fi
    done

    echo "└─────────────────────────────────────────────────────────────────┘"
    echo ""
}

# Show API status
show_api_status() {
    echo -e "${MAGENTA}🔌 API Status${NC}"
    echo "┌─────────────────────────────────────────────────────────────────┐"
    echo "│ API Endpoint       │ Status    │ Response Time │ Last Check     │"
    echo "├─────────────────────────────────────────────────────────────────┤"

    local apis=(
        "Gateway:$GATEWAY_URL/health"
        "Service Manager:$SERVICE_MANAGER_URL/health"
        "Tool Router:$TOOL_ROUTER_URL/health"
    )

    for api_info in "${apis[@]}"; do
        local api_name=$(echo "$api_info" | cut -d':' -f1)
        local api_url=$(echo "$api_info" | cut -d':' -f2-)

        local start_time=$(date +%s%N)
        local status="DOWN"
        local response_time="N/A"

        if curl -f -s "$api_url" > /dev/null 2>&1; then
            local end_time=$(date +%s%N)
            response_time=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds
            status="UP"
        fi

        # Color code status
        local status_color="$GREEN"
        if [[ "$status" == "UP" ]]; then
            status_color="$GREEN"
        else
            status_color="$RED"
        fi

        printf "│ %-16s │ ${status_color}%-9s${NC} │ %-11s │ %-13s │\n" \
            "$api_name" "$status" "${response_time}ms" "$(date '+%H:%M:%S')"
    done

    echo "└─────────────────────────────────────────────────────────────────┘"
    echo ""
}

# Show dynamic services
show_dynamic_services() {
    echo -e "${MAGENTA}🔄 Dynamic Services${NC}"
    echo "┌─────────────────────────────────────────────────────────────────┐"
    echo "│ Service           │ State     │ Sleep Policy │ Last Activity  │"
    echo "├─────────────────────────────────────────────────────────────────┤"

    # Get services from service manager
    local services_response=$(curl -s "$SERVICE_MANAGER_URL/services/status" 2>/dev/null || echo "{}")

    if [[ "$services_response" != "{}" ]]; then
        # Parse services (simplified parsing)
        echo "$services_response" | jq -r '. as $data | keys[] as $key | "\($key)\t\($data[$key].state // "unknown")\t\($data[$key].sleep_policy.enabled // false)\t\($data[$key].last_activity // "never")"' 2>/dev/null | while IFS=$'\t' read -r service state policy activity; do
            if [[ -n "$service" ]]; then
                # Color code state
                local state_color="$GREEN"
                if [[ "$state" == "running" ]]; then
                    state_color="$GREEN"
                elif [[ "$state" == "sleeping" ]]; then
                    state_color="$YELLOW"
                elif [[ "$state" == "stopped" ]]; then
                    state_color="$RED"
                else
                    state_color="$NC"
                fi

                # Format activity
                local activity_formatted="$activity"
                if [[ "$activity" == "never" ]]; then
                    activity_formatted="Never"
                else
                    activity_formatted=$(date -d "$activity" '+%H:%M:%S' 2>/dev/null || echo "$activity")
                fi

                printf "│ %-16s │ ${state_color}%-9s${NC} │ %-11s │ %-13s │\n" \
                    "$service" "$state" "$policy" "$activity_formatted"
            fi
        done
    else
        printf "│ %-63s │\n" "No dynamic services data available"
    fi

    echo "└─────────────────────────────────────────────────────────────────┘"
    echo ""
}

# Show resource optimization
show_resource_optimization() {
    echo -e "${MAGENTA}⚡ Resource Optimization${NC}"
    echo "┌─────────────────────────────────────────────────────────────────┐"
    echo "│ Metric                │ Current   │ Target   │ Savings        │"
    echo "├─────────────────────────────────────────────────────────────────┤"

    # Get cost metrics
    local cost_response=$(curl -s "$SERVICE_MANAGER_URL/metrics/cost" 2>/dev/null || echo "{}")

    if [[ "$cost_response" != "{}" ]]; then
        local current_cost=$(echo "$cost_response" | jq -r '.current_cost // "N/A"' 2>/dev/null)
        local baseline_cost=$(echo "$cost_response" | jq -r '.baseline_cost // "N/A"' 2>/dev/null)
        local savings=$(echo "$cost_response" | jq -r '.savings // "N/A"' 2>/dev/null)
        local savings_percentage=$(echo "$cost_response" | jq -r '.savings_percentage // "N/A"' 2>/dev/null)

        printf "│ %-20s │ %-9s │ %-8s │ %-13s │\n" \
            "Infrastructure Cost" "$current_cost" "$baseline_cost" "$savings"
        printf "│ %-20s │ %-9s │ %-8s │ %-13s │\n" \
            "Cost Savings" "${savings_percentage}%" "40-60%" "$(echo "$savings_percentage" | sed 's/%//')% of target"
    else
        printf "│ %-63s │\n" "Cost metrics not available"
    fi

    # Calculate memory efficiency
    local total_memory=0
    local used_memory=0

    local containers=$(docker-compose -f docker-compose.scalable.yml ps -q 2>/dev/null || echo "")
    for container_id in $containers; do
        if [[ -n "$container_id" ]]; then
            local container_info=$(docker inspect "$container_id" 2>/dev/null || echo "{}")
            local memory_limit=$(echo "$container_info" | jq -r '.[0].HostConfig.Memory // 0' 2>/dev/null || echo "0")
            local memory_usage=$(docker stats --no-stream --format "{{.MemUsage}}" "$container_id" 2>/dev/null | sed 's/[^0-9.]//g' || echo "0")

            total_memory=$((total_memory + memory_limit))
            used_memory=$((used_memory + $(echo "$memory_usage * 1024 * 1024" | bc 2>/dev/null || echo "0")))
        fi
    done

    if [[ $total_memory -gt 0 ]]; then
        local memory_efficiency=$(( (total_memory - used_memory) * 100 / total_memory ))
        printf "│ %-20s │ %-9s │ %-8s │ %-13s │\n" \
            "Memory Efficiency" "${memory_efficiency}%" "80-90%" "$(echo "$memory_efficiency" | sed 's/%//')% of target"
    fi

    echo "└─────────────────────────────────────────────────────────────────┘"
    echo ""
}

# Show performance metrics
show_performance_metrics() {
    echo -e "${MAGENTA}🚀 Performance Metrics${NC}"
    echo "┌─────────────────────────────────────────────────────────────────┐"
    echo "│ Metric                │ Value     │ Target   │ Status         │"
    echo "├─────────────────────────────────────────────────────────────────┤"

    # Test wake time
    local start_time=$(date +%s%N)
    if curl -X POST "$SERVICE_MANAGER_URL/services/filesystem/wake" \
           -s > /dev/null 2>&1; then
        local end_time=$(date +%s%N)
        local wake_time=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds

        local wake_status="GOOD"
        local wake_color="$GREEN"
        if [[ $wake_time -gt 200 ]]; then
            wake_status="SLOW"
            wake_color="$YELLOW"
        fi

        printf "│ %-20s │ ${wake_color}%-9s${NC} │ %-8s │ %-13s │\n" \
            "Wake Time" "${wake_time}ms" "<200ms" "$wake_status"
    else
        printf "│ %-20s │ %-9s │ %-8s │ %-13s │\n" \
            "Wake Time" "N/A" "<200ms" "UNKNOWN"
    fi

    # Test response time
    start_time=$(date +%s%N)
    if curl -f -s "$GATEWAY_URL/health" > /dev/null 2>&1; then
        end_time=$(date +%s%N)
        local response_time=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds

        local response_status="GOOD"
        local response_color="$GREEN"
        if [[ $response_time -gt 100 ]]; then
            response_status="SLOW"
            response_color="$YELLOW"
        fi

        printf "│ %-20s │ ${response_color}%-9s${NC} │ %-8s │ %-13s │\n" \
            "Response Time" "${response_time}ms" "<100ms" "$response_status"
    else
        printf "│ %-20s │ %-9s │ %-8s │ %-13s │\n" \
            "Response Time" "N/A" "<100ms" "DOWN"
    fi

    echo "└─────────────────────────────────────────────────────────────────┘"
    echo ""
}

# Show alerts
show_alerts() {
    echo -e "${MAGENTA}🚨 Active Alerts${NC}"
    echo "┌─────────────────────────────────────────────────────────────────┐"
    echo "│ Alert                 │ Severity  │ Message                        │"
    echo "├─────────────────────────────────────────────────────────────────┤"

    local alerts_found=false

    # Check for unhealthy services
    local containers=$(docker-compose -f docker-compose.scalable.yml ps -q 2>/dev/null || echo "")
    for container_id in $containers; do
        if [[ -n "$container_id" ]]; then
            local container_info=$(docker inspect "$container_id" 2>/dev/null || echo "{}")
            local container_name=$(echo "$container_info" | jq -r '.[0].Name' 2>/dev/null | sed 's/^.\///' || echo "unknown")
            local container_status=$(echo "$container_info" | jq -r '.[0].State.Status' 2>/dev/null || echo "unknown")

            if [[ "$container_status" != "running" && "$container_status" != "paused" ]]; then
                printf "│ %-21s │ %-9s │ %-30s │\n" \
                    "$container_name" "ERROR" "Service is not running"
                alerts_found=true
            fi
        fi
    done

    # Check API connectivity
    local apis=(
        "Gateway:$GATEWAY_URL/health"
        "Service Manager:$SERVICE_MANAGER_URL/health"
        "Tool Router:$TOOL_ROUTER_URL/health"
    )

    for api_info in "${apis[@]}"; do
        local api_name=$(echo "$api_info" | cut -d':' -f1)
        local api_url=$(echo "$api_info" | cut -d':' -f2-)

        if ! curl -f -s "$api_url" > /dev/null 2>&1; then
            printf "│ %-21s │ %-9s │ %-30s │\n" \
                "$api_name API" "ERROR" "API endpoint is not responding"
            alerts_found=true
        fi
    done

    # Check resource usage
    local containers=$(docker-compose -f docker-compose.scalable.yml ps -q 2>/dev/null || echo "")
    for container_id in $containers; do
        if [[ -n "$container_id" ]]; then
            local stats=$(docker stats --no-stream --format "{{.CPUPerc}}\t{{.MemPerc}}" "$container_id" 2>/dev/null | tail -1 || echo "0%\t0%")
            local cpu_usage=$(echo "$stats" | cut -f1 | sed 's/%//')
            local memory_usage=$(echo "$stats" | cut -f2 | sed 's/%//')

            local container_info=$(docker inspect "$container_id" 2>/dev/null || echo "{}")
            local container_name=$(echo "$container_info" | jq -r '.[0].Name' 2>/dev/null | sed 's/^.\///' || echo "unknown")

            # Convert to float for comparison
            local cpu_float=$(echo "$cpu_usage" | bc -l 2>/dev/null || echo "0")
            local memory_float=$(echo "$memory_usage" | bc -l 2>/dev/null || echo "0")

            if (( $(echo "$cpu_float > 80" | bc -l) )); then
                printf "│ %-21s │ %-9s │ %-30s │\n" \
                    "$container_name" "WARNING" "High CPU usage: ${cpu_usage}%"
                alerts_found=true
            fi

            if (( $(echo "$memory_float > 80" | bc -l) )); then
                printf "│ %-21s │ %-9s │ %-30s │\n" \
                    "$container_name" "WARNING" "High memory usage: ${memory_usage}%"
                alerts_found=true
            fi
        fi
    done

    if [[ "$alerts_found" == "false" ]]; then
        printf "│ %-63s │\n" "No active alerts - System is healthy"
    fi

    echo "└─────────────────────────────────────────────────────────────────┘"
    echo ""
}

# Show quick actions
show_quick_actions() {
    echo -e "${MAGENTA}⚡ Quick Actions${NC}"
    echo "┌─────────────────────────────────────────────────────────────────┐"
    echo "│ [1] Wake All Services    │ [2] Sleep All Services   │ [3] Restart Core │"
    echo "│ [4] View Logs           │ [5] Generate Report     │ [0] Exit         │"
    echo "└─────────────────────────────────────────────────────────────────┘"
    echo ""
}

# Handle user input
handle_input() {
    read -n 1 -s input
    echo ""

    case $input in
        1)
            log "Waking all services..."
            curl -X POST "$SERVICE_MANAGER_URL/services/wake-all" -s > /dev/null || log_warning "Failed to wake all services"
            ;;
        2)
            log "Sleeping all services..."
            curl -X POST "$SERVICE_MANAGER_URL/services/sleep-all" -s > /dev/null || log_warning "Failed to sleep all services"
            ;;
        3)
            log "Restarting core services..."
            docker-compose -f docker-compose.scalable.yml restart gateway service-manager tool-router
            ;;
        4)
            log "Opening logs..."
            docker-compose -f docker-compose.scalable.yml logs -f --tail=50
            ;;
        5)
            log "Generating report..."
            ./scripts/test-scalable.sh report
            ;;
        0)
            log "Exiting monitoring dashboard..."
            exit 0
            ;;
        *)
            log "Invalid option. Press 0-5 for actions."
            ;;
    esac
}

# Main monitoring loop
main() {
    log "Starting monitoring dashboard..."

    # Check if services are running
    if ! curl -f -s "$GATEWAY_URL/health" > /dev/null 2>&1; then
        log_error "Gateway is not running. Please start the services first."
        echo "Run: ./scripts/deploy-scalable.sh deploy"
        exit 1
    fi

    log "Monitoring dashboard started. Press 0 to exit."

    while true; do
        show_header
        show_service_status
        show_api_status
        show_dynamic_services
        show_resource_optimization
        show_performance_metrics
        show_alerts
        show_quick_actions

        echo -e "${CYAN}Press any key for actions, or wait $REFRESH_INTERVAL seconds to refresh...${NC}"

        # Wait for input or timeout
        if read -t $REFRESH_INTERVAL -n 1 input 2>/dev/null; then
            handle_input
        fi
    done
}

# Run main function
main "$@"
