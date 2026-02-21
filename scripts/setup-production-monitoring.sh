#!/bin/bash

# Production Monitoring Setup Script
# Configures monitoring and alerting for production deployment

set -euo pipefail

# Configuration
SCRIPT_NAME="$(basename "$0")"
LOG_FILE="/tmp/mcp-gateway-monitoring-setup.log"
COMPOSE_FILE="docker-compose.production.yml"

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

# Setup Prometheus configuration
setup_prometheus() {
    print_status "$BLUE" "📊 Setting up Prometheus monitoring..."
    
    # Create Prometheus configuration directory
    mkdir -p config/prometheus
    
    # Create comprehensive Prometheus configuration
    cat > config/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'forge-mcp-gateway'
    environment: 'production'

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  # Gateway Service
  - job_name: 'forge-gateway'
    static_configs:
      - targets: ['gateway:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s
    scrape_timeout: 10s
    
  # Service Manager
  - job_name: 'forge-service-manager'
    static_configs:
      - targets: ['service-manager:9000']
    metrics_path: '/metrics'
    scrape_interval: 30s
    scrape_timeout: 10s
    
  # Tool Router
  - job_name: 'forge-tool-router'
    static_configs:
      - targets: ['tool-router:8080']
    metrics_path: '/metrics'
    scrape_interval: 30s
    scrape_timeout: 10s
    
  # PostgreSQL Database
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
    scrape_interval: 30s
    
  # Redis Cache
  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    scrape_interval: 30s
    
  # Node Exporter (System Metrics)
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 30s
    
  # Docker Container Metrics
  - job_name: 'docker'
    static_configs:
      - targets: ['docker-exporter:9323']
    scrape_interval: 30s
    
  # Ollama AI Service
  - job_name: 'ollama'
    static_configs:
      - targets: ['ollama:11434']
    metrics_path: '/metrics'
    scrape_interval: 30s

# Load rules once and periodically evaluate them
rule_files:
  - "forge_alert_rules.yml"
EOF

    # Create alert rules
    cat > config/prometheus/forge_alert_rules.yml << 'EOF'
groups:
  - name: forge_gateway_alerts
    rules:
      # Gateway High CPU Usage
      - alert: GatewayHighCPUUsage
        expr: rate(container_cpu_usage_seconds_total{name="forge-mcpgateway-prod"}[5m]) * 100 > 80
        for: 5m
        labels:
          severity: warning
          service: gateway
        annotations:
          summary: "Gateway CPU usage is above 80%"
          description: "Gateway CPU usage has been above 80% for more than 5 minutes."
      
      # Gateway High Memory Usage
      - alert: GatewayHighMemoryUsage
        expr: (container_memory_usage_bytes{name="forge-mcpgateway-prod"} / container_spec_memory_limit_bytes{name="forge-mcpgateway-prod"}) * 100 > 85
        for: 5m
        labels:
          severity: warning
          service: gateway
        annotations:
          summary: "Gateway memory usage is above 85%"
          description: "Gateway memory usage has been above 85% for more than 5 minutes."
      
      # Gateway Down
      - alert: GatewayDown
        expr: up{job="forge-gateway"} == 0
        for: 1m
        labels:
          severity: critical
          service: gateway
        annotations:
          summary: "Gateway service is down"
          description: "Gateway service has been down for more than 1 minute."
      
      # Service Manager High CPU Usage
      - alert: ServiceManagerHighCPUUsage
        expr: rate(container_cpu_usage_seconds_total{name="forge-service-manager-prod"}[5m]) * 100 > 70
        for: 5m
        labels:
          severity: warning
          service: service-manager
        annotations:
          summary: "Service Manager CPU usage is above 70%"
          description: "Service Manager CPU usage has been above 70% for more than 5 minutes."
      
      # Database Connection Issues
      - alert: DatabaseConnectionIssues
        expr: up{job="postgres"} == 0
        for: 2m
        labels:
          severity: critical
          service: database
        annotations:
          summary: "PostgreSQL database is down"
          description: "PostgreSQL database has been down for more than 2 minutes."
      
      # Redis Connection Issues
      - alert: RedisConnectionIssues
        expr: up{job="redis"} == 0
        for: 2m
        labels:
          severity: warning
          service: cache
        annotations:
          summary: "Redis cache is down"
          description: "Redis cache has been down for more than 2 minutes."
      
      # High Disk Usage
      - alert: HighDiskUsage
        expr: (node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes * 100 > 85
        for: 5m
        labels:
          severity: warning
          service: system
        annotations:
          summary: "Disk usage is above 85%"
          description: "Disk usage has been above 85% for more than 5 minutes."
      
      # Container Restart Rate
      - alert: HighContainerRestartRate
        expr: rate(container_start_time_seconds[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
          service: system
        annotations:
          summary: "High container restart rate"
          description: "Container restart rate is unusually high."
EOF

    print_status "$GREEN" "✅ Prometheus configuration created"
    log "Prometheus configuration setup completed"
}

# Setup Grafana configuration
setup_grafana() {
    print_status "$BLUE" "📈 Setting up Grafana dashboards..."
    
    # Create Grafana provisioning directories
    mkdir -p config/grafana/provisioning/{datasources,dashboards}
    
    # Create Grafana datasource configuration
    cat > config/grafana/provisioning/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
    jsonData:
      timeInterval: "15s"
      queryTimeout: "60s"
      httpMethod: "POST"
EOF

    # Create Grafana dashboard provisioning
    cat > config/grafana/provisioning/dashboards/dashboards.yml << 'EOF'
apiVersion: 1

providers:
  - name: 'forge-dashboards'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
EOF

    # Create main dashboard
    mkdir -p config/grafana/dashboards
    cat > config/grafana/dashboards/forge-overview.json << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "MCP Gateway Overview",
    "tags": ["forge", "mcp-gateway"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Gateway CPU Usage",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(container_cpu_usage_seconds_total{name=\"forge-mcpgateway-prod\"}[5m]) * 100",
            "legendFormat": "CPU %"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "thresholds": {
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 70},
                {"color": "red", "value": 85}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Gateway Memory Usage",
        "type": "stat",
        "targets": [
          {
            "expr": "(container_memory_usage_bytes{name=\"forge-mcpgateway-prod\"} / container_spec_memory_limit_bytes{name=\"forge-mcpgateway-prod\"}) * 100",
            "legendFormat": "Memory %"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "thresholds": {
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 75},
                {"color": "red", "value": 90}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "id": 3,
        "title": "Service Status",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=~\"forge-.*\"}",
            "legendFormat": "{{job}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "mappings": [
              {"options": {"0": {"text": "DOWN", "color": "red"}}, "type": "value"},
              {"options": {"1": {"text": "UP", "color": "green"}}, "type": "value"}
            ]
          }
        },
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8}
      }
    ],
    "time": {"from": "now-1h", "to": "now"},
    "refresh": "30s"
  }
}
EOF

    print_status "$GREEN" "✅ Grafana configuration created"
    log "Grafana configuration setup completed"
}

# Setup Alertmanager
setup_alertmanager() {
    print_status "$BLUE" "🚨 Setting up Alertmanager..."
    
    # Create Alertmanager configuration
    mkdir -p config/alertmanager
    
    cat > config/alertmanager/alertmanager.yml << 'EOF'
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@your-domain.com'
  smtp_auth_username: 'alerts@your-domain.com'
  smtp_auth_password: 'your-email-password'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
    - match:
        severity: warning
      receiver: 'warning-alerts'

receivers:
  - name: 'web.hook'
    webhook_configs:
      - url: 'http://localhost:5001/'

  - name: 'critical-alerts'
    email_configs:
      - to: 'admin@your-domain.com'
        subject: '[CRITICAL] MCP Gateway Alert: {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          Labels: {{ range .Labels.SortedPairs }}{{ .Name }}={{ .Value }} {{ end }}
          {{ end }}

  - name: 'warning-alerts'
    email_configs:
      - to: 'ops@your-domain.com'
        subject: '[WARNING] MCP Gateway Alert: {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          Labels: {{ range .Labels.SortedPairs }}{{ .Name }}={{ .Value }} {{ end }}
          {{ end }}

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'cluster', 'service']
EOF

    print_status "$GREEN" "✅ Alertmanager configuration created"
    log "Alertmanager configuration setup completed"
}

# Setup log aggregation
setup_log_aggregation() {
    print_status "$BLUE" "📋 Setting up log aggregation..."
    
    # Create Loki configuration (optional)
    mkdir -p config/loki
    
    cat > config/loki/loki.yml << 'EOF'
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    address: 127.0.0.1
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
    final_sleep: 0s
    chunk_idle_period: 1h
    max_chunk_age: 1h
    chunk_target_size: 1048576
    chunk_retain_period: 30s

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/boltdb-shipper-active
    cache_location: /loki/boltdb-shipper-cache
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: false
  retention_period: 0s

compactor:
  shared_store: filesystem
  compaction_interval: 10m
  retention_enabled: true
  retain_delete_enabled: false
  max_compaction_retries: 3

analytics:
  reporting_enabled: false
EOF

    print_status "$GREEN" "✅ Log aggregation configuration created"
    log "Log aggregation setup completed"
}

# Create monitoring startup script
create_monitoring_script() {
    print_status "$BLUE" "🔧 Creating monitoring management script..."
    
    cat > scripts/manage-monitoring.sh << 'EOF'
#!/bin/bash

# Monitoring Management Script for MCP Gateway

set -euo pipefail

SCRIPT_NAME="$(basename "$0")"
COMPOSE_FILE="docker-compose.production.yml"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Start monitoring services
start_monitoring() {
    print_status "$BLUE" "🚀 Starting monitoring services..."
    docker-compose -f "$COMPOSE_FILE" up -d prometheus grafana
    print_status "$GREEN" "✅ Monitoring services started"
}

# Stop monitoring services
stop_monitoring() {
    print_status "$BLUE" "🛑 Stopping monitoring services..."
    docker-compose -f "$COMPOSE_FILE" stop prometheus grafana
    print_status "$GREEN" "✅ Monitoring services stopped"
}

# Check monitoring status
check_monitoring() {
    print_status "$BLUE" "🔍 Checking monitoring status..."
    
    services=("prometheus" "grafana")
    
    for service in "${services[@]}"; do
        local status
        status=$(docker-compose -f "$COMPOSE_FILE" ps -q "$service" | xargs docker inspect --format='{{.State.Status}}' 2>/dev/null || echo "not_found")
        
        if [[ "$status" == "running" ]]; then
            print_status "$GREEN" "✅ $service is running"
        else
            print_status "$RED" "❌ $service is not running (status: $status)"
        fi
    done
}

# Show monitoring URLs
show_urls() {
    print_status "$BLUE" "🌐 Monitoring URLs:"
    echo "  • Prometheus: http://localhost:9090"
    echo "  • Grafana: http://localhost:3001"
    echo "  • Alertmanager: http://localhost:9093"
}

# Help function
show_help() {
    cat << EOF
Usage: $SCRIPT_NAME [COMMAND]

Monitoring Management Script for MCP Gateway

COMMANDS:
    start       Start monitoring services
    stop        Stop monitoring services
    status      Check monitoring status
    urls        Show monitoring URLs
    help        Show this help message

EXAMPLES:
    $SCRIPT_NAME start
    $SCRIPT_NAME status
    $SCRIPT_NAME stop

EOF
}

# Main execution
case "${1:-help}" in
    start)
        start_monitoring
        ;;
    stop)
        stop_monitoring
        ;;
    status)
        check_monitoring
        ;;
    urls)
        show_urls
        ;;
    help|*)
        show_help
        ;;
esac
EOF

    chmod +x scripts/manage-monitoring.sh
    print_status "$GREEN" "✅ Monitoring management script created"
    log "Monitoring management script created"
}

# Main execution
main() {
    print_status "$BLUE" "🔧 MCP Gateway Production Monitoring Setup"
    echo "=================================================="
    
    log "Starting monitoring setup"
    
    setup_prometheus
    setup_grafana
    setup_alertmanager
    setup_log_aggregation
    create_monitoring_script
    
    print_status "$GREEN" "🎉 Production monitoring setup completed!"
    echo ""
    print_status "$BLUE" "📋 Next Steps:"
    echo "  1. Review and update alert configurations in config/alertmanager/alertmanager.yml"
    echo "  2. Update email settings in Alertmanager configuration"
    echo "  3. Start monitoring: ./scripts/manage-monitoring.sh start"
    echo "  4. Access dashboards:"
    echo "     • Prometheus: http://localhost:9090"
    echo "     • Grafana: http://localhost:3001"
    echo "     • Alertmanager: http://localhost:9093"
    echo ""
    print_status "$BLUE" "🔧 Management Commands:"
    echo "  • Start monitoring: ./scripts/manage-monitoring.sh start"
    echo "  • Stop monitoring: ./scripts/manage-monitoring.sh stop"
    echo "  • Check status: ./scripts/manage-monitoring.sh status"
    echo "  • Show URLs: ./scripts/manage-monitoring.sh urls"
    
    log "Production monitoring setup completed successfully"
}

# Trap to handle interruption
trap 'log "Monitoring setup interrupted"; exit 0' INT TERM

# Run main function
main "$@"