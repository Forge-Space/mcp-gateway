#!/bin/bash

# Automated Incident Response System for MCP Gateway
# Provides automated response to common incidents and failures

set -euo pipefail

# Configuration
SCRIPT_NAME="$(basename "$0")"
LOG_FILE="/tmp/mcp-gateway-incident-response-$(date +%Y%m%d_%H%M%S).log"
COMPOSE_FILE="docker-compose.production.yml"
ENV_FILE=".env.production"

# Incident types
INCIDENT_SERVICE_DOWN="service_down"
INCIDENT_HIGH_CPU="high_cpu"
INCIDENT_HIGH_MEMORY="high_memory"
INCIDENT_HIGH_DISK="high_disk"
INCIDENT_NETWORK_ISSUE="network_issue"
INCIDENT_DATABASE_ISSUE="database_issue"

# Response actions
ACTION_RESTART="restart"
ACTION_SCALE_UP="scale_up"
ACTION_SCALE_DOWN="scale_down"
ACTION_LOGS="collect_logs"
ACTION_NOTIFY="notify"
ACTION_ESCALATE="escalate"

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

# Print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Check if service is healthy
is_service_healthy() {
    local service=$1
    local health_url=$2
    
    if curl -s --connect-timeout 5 --max-time 10 "$health_url" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Restart service
restart_service() {
    local service=$1
    local container_name="forge-${service}-prod"
    
    log "Attempting to restart service: $service"
    print_status "$YELLOW" "🔄 Restarting $service..."
    
    # Check if container exists
    if ! docker ps --format "{{.Names}}" | grep -q "^${container_name}$"; then
        log "Container $container_name not found, attempting to start service..."
        docker-compose -f "$COMPOSE_FILE" up -d "$service"
    else
        # Restart existing container
        docker-compose -f "$COMPOSE_FILE" restart "$service"
    fi
    
    # Wait for service to be healthy
    local max_wait=60
    local wait_time=0
    
    while [[ $wait_time -lt $max_wait ]]; do
        case $service in
            "gateway")
                if is_service_healthy "gateway" "http://localhost:8000/health"; then
                    print_status "$GREEN" "✅ $service is healthy after restart"
                    log "Service $service successfully restarted and is healthy"
                    return 0
                fi
                ;;
            "service-manager")
                if is_service_healthy "service-manager" "http://localhost:9000/health"; then
                    print_status "$GREEN" "✅ $service is healthy after restart"
                    log "Service $service successfully restarted and is healthy"
                    return 0
                fi
                ;;
        esac
        
        sleep 5
        wait_time=$((wait_time + 5))
    done
    
    print_status "$RED" "❌ $service failed to become healthy after restart"
    log "Service $service restart failed - manual intervention required"
    return 1
}

# Scale service
scale_service() {
    local service=$1
    local replicas=$2
    
    log "Scaling service $service to $replicas replicas"
    print_status "$YELLOW" "📊 Scaling $service to $replicas replicas..."
    
    docker-compose -f "$COMPOSE_FILE" up -d --scale "$service=$replicas"
    
    # Verify scaling
    local running_containers
    running_containers=$(docker-compose -f "$COMPOSE_FILE" ps -q "$service" | wc -l)
    
    if [[ $running_containers -eq $replicas ]]; then
        print_status "$GREEN" "✅ $service successfully scaled to $replicas replicas"
        log "Service $service successfully scaled to $replicas replicas"
    else
        print_status "$YELLOW" "⚠️  $service scaling may still be in progress (expected: $replicas, actual: $running_containers)"
        log "Service $service scaling in progress"
    fi
}

# Collect diagnostic logs
collect_logs() {
    local service=$1
    local lines=${2:-100}
    local log_file="/tmp/${service}-incident-logs-$(date +%Y%m%d_%H%M%S).log"
    
    log "Collecting logs for service: $service"
    print_status "$BLUE" "📋 Collecting logs for $service..."
    
    # Get recent logs
    docker-compose -f "$COMPOSE_FILE" logs --tail="$lines" "$service" > "$log_file" 2>/dev/null || true
    
    # Get container logs if service is running
    local container_name="forge-${service}-prod"
    if docker ps --format "{{.Names}}" | grep -q "^${container_name}$"; then
        docker logs --tail="$lines" "$container_name" >> "$log_file" 2>/dev/null || true
    fi
    
    # Get system logs
    echo "=== System Information ===" >> "$log_file"
    echo "Timestamp: $(date)" >> "$log_file"
    echo "Docker Version: $(docker --version)" >> "$log_file"
    echo "Docker Compose Version: $(docker-compose --version)" >> "$log_FILE"
    echo "" >> "$log_file"
    
    echo "=== Container Status ===" >> "$log_file"
    docker-compose -f "$COMPOSE_FILE" ps "$service" >> "$log_file" 2>/dev/null || true
    echo "" >> "$log_file"
    
    echo "=== Resource Usage ===" >> "$log_file"
    if docker ps --format "{{.Names}}" | grep -q "^${container_name}$"; then
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" "$container_name" >> "$log_file" 2>/dev/null || true
    fi
    
    print_status "$GREEN" "✅ Logs collected: $log_file"
    log "Logs collected for $service: $log_file"
    
    echo "$log_file"
}

# Send notification (placeholder for actual notification system)
send_notification() {
    local severity=$1
    local service=$2
    local message=$3
    local action_taken=$4
    
    log "Sending notification: $severity - $service - $message - Action: $action_taken"
    print_status "$BLUE" "📢 Notification: $severity alert for $service"
    
    # In a real implementation, this would send to:
    # - Slack webhook
    # - Email
    # - PagerDuty
    # - Monitoring system
    
    echo "NOTIFICATION: [$severity] $service - $message - Action taken: $action_taken" | tee -a "$LOG_FILE"
}

# Escalate incident
escalate_incident() {
    local service=$1
    local issue=$2
    local severity=$3
    
    log "Escalating incident: $service - $issue - Severity: $severity"
    print_status "$RED" "🚨 Escalating incident for $service"
    
    # Collect logs before escalation
    local log_file
    log_file=$(collect_logs "$service" 200)
    
    # Create incident report
    local incident_file="/tmp/incident-${service}-$(date +%Y%m%d_%H%M%S).json"
    
    cat > "$incident_file" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "service": "$service",
  "issue": "$issue",
  "severity": "$severity",
  "logs_file": "$log_file",
  "system_info": {
    "hostname": "$(hostname)",
    "docker_version": "$(docker --version)",
    "compose_file": "$COMPOSE_FILE"
  },
  "actions_taken": [
    "Automated restart attempted",
    "Log collection completed",
    "Incident escalated"
  ],
  "status": "escalated"
}
EOF
    
    print_status "$RED" "📋 Incident escalated: $incident_file"
    send_notification "$severity" "$service" "$issue" "Incident escalated - manual intervention required"
    
    echo "$incident_file"
}

# Handle service down incident
handle_service_down() {
    local service=$1
    
    log "Handling service down incident: $service"
    print_status "$YELLOW" "🔧 Handling service down: $service"
    
    # Attempt restart
    if restart_service "$service"; then
        send_notification "INFO" "$service" "Service was down and successfully restarted" "Automated restart"
        return 0
    else
        # Collect logs and escalate
        local log_file
        log_file=$(collect_logs "$service" 200)
        escalate_incident "$service" "Service down and restart failed" "CRITICAL"
        return 1
    fi
}

# Handle high resource usage
handle_high_resources() {
    local service=$1
    local resource_type=$2
    local usage=$3
    
    log "Handling high $resource_type usage: $service (${usage}%)"
    print_status "$YELLOW" "📊 Handling high $resource_type usage: $service (${usage}%)"
    
    case $resource_type in
        "cpu")
            # Check if we can scale up (only for stateless services)
            if [[ "$service" == "gateway" ]] || [[ "$service" == "web-admin" ]]; then
                scale_service "$service" 2
                send_notification "INFO" "$service" "High CPU usage detected, scaled to 2 replicas" "Auto-scaling"
            else
                # For stateful services, just monitor and alert
                collect_logs "$service" 50
                send_notification "WARNING" "$service" "High CPU usage detected, manual review required" "Monitoring"
            fi
            ;;
        "memory")
            # Try restart first (might clear memory leaks)
            if restart_service "$service"; then
                send_notification "INFO" "$service" "High memory usage, service restarted" "Automated restart"
            else
                collect_logs "$service" 100
                escalate_incident "$service" "High memory usage and restart failed" "WARNING"
            fi
            ;;
        "disk")
            # Disk issues usually require manual intervention
            collect_logs "$service" 50
            escalate_incident "$service" "High disk usage detected" "CRITICAL"
            ;;
    esac
}

# Handle database issues
handle_database_issues() {
    local issue=$1
    
    log "Handling database issue: $issue"
    print_status "$YELLOW" "🗄️  Handling database issue: $issue"
    
    case $issue in
        "connection_failed")
            # Try to restart database
            if restart_service "postgres"; then
                send_notification "INFO" "postgres" "Database connection failed, service restarted" "Automated restart"
            else
                escalate_incident "postgres" "Database connection failed and restart failed" "CRITICAL"
            fi
            ;;
        "high_load")
            # Monitor and collect logs
            collect_logs "postgres" 100
            send_notification "WARNING" "postgres" "Database high load detected" "Monitoring"
            ;;
        "disk_space")
            escalate_incident "postgres" "Database disk space critical" "CRITICAL"
            ;;
    esac
}

# Analyze and respond to incident
analyze_incident() {
    local service=$1
    local incident_type=$2
    local details=$3
    
    log "Analyzing incident: $service - $incident_type - $details"
    
    case $incident_type in
        "$INCIDENT_SERVICE_DOWN")
            handle_service_down "$service"
            ;;
        "$INCIDENT_HIGH_CPU")
            handle_high_resources "$service" "cpu" "$details"
            ;;
        "$INCIDENT_HIGH_MEMORY")
            handle_high_resources "$service" "memory" "$details"
            ;;
        "$INCIDENT_HIGH_DISK")
            handle_high_resources "$service" "disk" "$details"
            ;;
        "$INCIDENT_DATABASE_ISSUE")
            handle_database_issues "$details"
            ;;
        *)
            log "Unknown incident type: $incident_type"
            collect_logs "$service" 100
            escalate_incident "$service" "Unknown incident type: $incident_type" "WARNING"
            ;;
    esac
}

# Monitor and auto-respond
auto_monitor() {
    local interval=${1:-60}
    
    log "Starting automated incident response with ${interval}s interval..."
    
    while true; do
        log "Running incident response check..."
        
        # Check service health
        local services=("gateway" "service-manager" "postgres" "redis" "web-admin")
        
        for service in "${services[@]}"; do
            local container_name="forge-${service}-prod"
            
            # Check if container is running
            if ! docker ps --format "{{.Names}}" | grep -q "^${container_name}$"; then
                analyze_incident "$service" "$INCIDENT_SERVICE_DOWN" "Container not running"
                continue
            fi
            
            # Check resource usage
            local stats
            stats=$(docker stats --no-stream --format "{{.CPUPerc}}\t{{.MemPerc}}" "$container_name" 2>/dev/null || echo "")
            
            if [[ -n "$stats" ]]; then
                local cpu_percent=$(echo "$stats" | cut -f1 | sed 's/%//')
                local mem_percent=$(echo "$stats" | cut -f2 | sed 's/%//')
                
                # Check CPU usage
                if (( $(echo "$cpu_percent > 90" | bc -l 2>/dev/null || echo "0") )); then
                    analyze_incident "$service" "$INCIDENT_HIGH_CPU" "$cpu_percent"
                fi
                
                # Check memory usage
                if (( $(echo "$mem_percent > 90" | bc -l 2>/dev/null || echo "0") )); then
                    analyze_incident "$service" "$INCIDENT_HIGH_MEMORY" "$mem_percent"
                fi
            fi
            
            # Check service-specific health
            case $service in
                "gateway")
                    if ! is_service_healthy "gateway" "http://localhost:8000/health"; then
                        analyze_incident "$service" "$INCIDENT_SERVICE_DOWN" "Health check failed"
                    fi
                    ;;
                "service-manager")
                    if ! is_service_healthy "service-manager" "http://localhost:9000/health"; then
                        analyze_incident "$service" "$INCIDENT_SERVICE_DOWN" "Health check failed"
                    fi
                    ;;
            esac
        done
        
        # Check system resources
        local disk_usage
        disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//' 2>/dev/null || echo "0")
        
        if (( disk_usage > 90 )); then
            analyze_incident "system" "$INCIDENT_HIGH_DISK" "$disk_usage"
        fi
        
        log "Incident response check completed. Next cycle in ${interval}s..."
        sleep "$interval"
    done
}

# Show help
show_help() {
    cat << EOF
Usage: $SCRIPT_NAME [OPTIONS]

Automated Incident Response System for MCP Gateway

OPTIONS:
    -a, --analyze SERVICE TYPE DETAILS    Analyze and respond to specific incident
    -r, --restart SERVICE                 Restart a service
    -s, --scale SERVICE REPLICAS          Scale a service
    -l, --logs SERVICE [LINES]            Collect logs for service
    -m, --monitor [SECONDS]               Auto-monitor and respond (default: 60)
    -n, --notify SEVERITY SERVICE MESSAGE  Send notification
    -e, --escalate SERVICE ISSUE SEVERITY Escalate incident
    -f, --file FILE                       Docker compose file
    -h, --help                            Show this help message

INCIDENT TYPES:
    service_down       - Service is not running or not responding
    high_cpu          - High CPU usage (>90%)
    high_memory       - High memory usage (>90%)
    high_disk         - High disk usage (>90%)
    network_issue     - Network connectivity problems
    database_issue    - Database-specific issues

EXAMPLES:
    $SCRIPT_NAME -a gateway service_down "Container not running"
    $SCRIPT_NAME -r gateway
    $SCRIPT_NAME -s gateway 2
    $SCRIPT_NAME -l gateway 200
    $SCRIPT_NAME -m 30
    $SCRIPT_NAME -e postgres connection_failed CRITICAL

EOF
}

# Parse command line arguments
RUN_ANALYZE=false
RUN_RESTART=false
RUN_SCALE=false
RUN_LOGS=false
RUN_MONITOR=false
RUN_NOTIFY=false
RUN_ESCALATE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -a|--analyze)
            RUN_ANALYZE=true
            SERVICE="$2"
            INCIDENT_TYPE="$3"
            DETAILS="$4"
            shift 4
            ;;
        -r|--restart)
            RUN_RESTART=true
            SERVICE="$2"
            shift 2
            ;;
        -s|--scale)
            RUN_SCALE=true
            SERVICE="$2"
            REPLICAS="$3"
            shift 3
            ;;
        -l|--logs)
            RUN_LOGS=true
            SERVICE="$2"
            LINES="${3:-100}"
            shift 3
            ;;
        -m|--monitor)
            RUN_MONITOR=true
            INTERVAL="${2:-60}"
            shift 2
            ;;
        -n|--notify)
            RUN_NOTIFY=true
            SEVERITY="$2"
            SERVICE="$3"
            MESSAGE="$4"
            shift 4
            ;;
        -e|--escalate)
            RUN_ESCALATE=true
            SERVICE="$2"
            ISSUE="$3"
            SEVERITY="$4"
            shift 4
            ;;
        -f|--file)
            COMPOSE_FILE="$2"
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
    echo "🚨 MCP Gateway Automated Incident Response"
    echo "=========================================="
    
    log "Starting incident response system"
    
    if [[ "$RUN_ANALYZE" == "true" ]]; then
        analyze_incident "$SERVICE" "$INCIDENT_TYPE" "$DETAILS"
    elif [[ "$RUN_RESTART" == "true" ]]; then
        restart_service "$SERVICE"
    elif [[ "$RUN_SCALE" == "true" ]]; then
        scale_service "$SERVICE" "$REPLICAS"
    elif [[ "$RUN_LOGS" == "true" ]]; then
        collect_logs "$SERVICE" "$LINES"
    elif [[ "$RUN_NOTIFY" == "true" ]]; then
        send_notification "$SEVERITY" "$SERVICE" "$MESSAGE" "Manual notification"
    elif [[ "$RUN_ESCALATE" == "true" ]]; then
        escalate_incident "$SERVICE" "$ISSUE" "$SEVERITY"
    elif [[ "$RUN_MONITOR" == "true" ]]; then
        auto_monitor "$INTERVAL"
    else
        echo "No action specified. Use -h for help."
        exit 1
    fi
}

# Trap to handle interruption
trap 'log "Incident response interrupted"; exit 0' INT TERM

# Run main function
main "$@"