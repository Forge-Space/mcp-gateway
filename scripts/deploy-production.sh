#!/bin/bash

# Production Deployment Script for MCP Gateway
# Deploys the complete MCP Gateway system to production

set -euo pipefail

# Configuration
SCRIPT_NAME="$(basename "$0")"
LOG_FILE="/tmp/mcp-gateway-deploy-$(date +%Y%m%d_%H%M%S).log"
BACKUP_DIR="/tmp/mcp-gateway-backup-$(date +%Y%m%d_%H%M%S)"
COMPOSE_FILE="docker-compose.production.yml"
ENV_FILE=".env.production"

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

# Check prerequisites
check_prerequisites() {
    print_status "$BLUE" "🔍 Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker >/dev/null 2>&1; then
        print_status "$RED" "❌ Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose >/dev/null 2>&1; then
        print_status "$RED" "❌ Docker Compose is not installed"
        exit 1
    fi
    
    # Check if production files exist
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        print_status "$RED" "❌ Production compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    if [[ ! -f "$ENV_FILE" ]]; then
        print_status "$RED" "❌ Production environment file not found: $ENV_FILE"
        print_status "$YELLOW" "💡 Copy .env.production.example to $ENV_FILE and configure it"
        exit 1
    fi
    
    # Check Docker is running
    if ! docker info >/dev/null 2>&1; then
        print_status "$RED" "❌ Docker is not running"
        exit 1
    fi
    
    print_status "$GREEN" "✅ Prerequisites check passed"
    log "Prerequisites check completed"
}

# Backup current deployment
backup_current_deployment() {
    print_status "$BLUE" "📦 Backing up current deployment..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup docker-compose files
    if [[ -f "$COMPOSE_FILE" ]]; then
        cp "$COMPOSE_FILE" "$BACKUP_DIR/"
    fi
    
    if [[ -f "$ENV_FILE" ]]; then
        cp "$ENV_FILE" "$BACKUP_DIR/"
    fi
    
    # Backup current running containers info
    if docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" > "$BACKUP_DIR/running_containers.txt" 2>/dev/null; then
        print_status "$GREEN" "✅ Backed up running containers info"
    fi
    
    # Backup volumes if they exist
    if docker volume ls --format "{{.Name}}" | grep -q "forge"; then
        docker volume ls --format "{{.Name}}" | grep forge > "$BACKUP_DIR/volumes.txt"
        print_status "$GREEN" "✅ Backed up volumes list"
    fi
    
    print_status "$GREEN" "✅ Backup completed: $BACKUP_DIR"
    log "Backup completed: $BACKUP_DIR"
}

# Validate configuration
validate_configuration() {
    print_status "$BLUE" "🔍 Validating production configuration..."
    
    # Validate docker-compose file
    if docker-compose -f "$COMPOSE_FILE" config >/dev/null 2>&1; then
        print_status "$GREEN" "✅ Docker Compose configuration is valid"
    else
        print_status "$RED" "❌ Docker Compose configuration has errors"
        docker-compose -f "$COMPOSE_FILE" config
        exit 1
    fi
    
    # Check required environment variables
    local required_vars=(
        "JWT_SECRET"
        "POSTGRES_PASSWORD"
        "REDIS_PASSWORD"
        "GRAFANA_PASSWORD"
    )
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$ENV_FILE" || grep -q "^${var}=your-" "$ENV_FILE"; then
            print_status "$RED" "❌ Required environment variable $var is not configured"
            print_status "$YELLOW" "💡 Please set $var in $ENV_FILE"
            exit 1
        fi
    done
    
    print_status "$GREEN" "✅ Configuration validation passed"
    log "Configuration validation completed"
}

# Prepare production environment
prepare_environment() {
    print_status "$BLUE" "🔧 Preparing production environment..."
    
    # Create necessary directories
    local dirs=("data" "logs" "config/prometheus" "config/grafana/provisioning" "config/grafana/dashboards")
    
    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            print_status "$GREEN" "✅ Created directory: $dir"
        fi
    done
    
    # Set proper permissions
    chmod 755 data logs config
    
    # Create Prometheus configuration if not exists
    if [[ ! -f "config/prometheus/prometheus.yml" ]]; then
        cat > config/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'forge-gateway'
    static_configs:
      - targets: ['gateway:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'forge-service-manager'
    static_configs:
      - targets: ['service-manager:9000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 30s
EOF
        print_status "$GREEN" "✅ Created Prometheus configuration"
    fi
    
    print_status "$GREEN" "✅ Environment preparation completed"
    log "Environment preparation completed"
}

# Deploy services
deploy_services() {
    print_status "$BLUE" "🚀 Deploying MCP Gateway services..."
    
    # Pull latest images
    print_status "$BLUE" "📥 Pulling latest images..."
    docker-compose -f "$COMPOSE_FILE" pull
    
    # Stop existing services if running
    if docker-compose -f "$COMPOSE_FILE" ps -q | grep -q .; then
        print_status "$YELLOW" "🛑 Stopping existing services..."
        docker-compose -f "$COMPOSE_FILE" down
    fi
    
    # Start services
    print_status "$BLUE" "🔄 Starting services..."
    docker-compose -f "$COMPOSE_FILE" up -d
    
    # Wait for services to be healthy
    print_status "$BLUE" "⏳ Waiting for services to be healthy..."
    sleep 30
    
    # Check service health
    local unhealthy_services=0
    local services=("gateway" "service-manager" "postgres" "redis")
    
    for service in "${services[@]}"; do
        local health_status
        health_status=$(docker-compose -f "$COMPOSE_FILE" ps -q "$service" | xargs docker inspect --format='{{.State.Health.Status}}' 2>/dev/null || echo "unknown")
        
        if [[ "$health_status" == "healthy" ]]; then
            print_status "$GREEN" "✅ $service is healthy"
        else
            print_status "$YELLOW" "⚠️  $service status: $health_status"
            ((unhealthy_services++))
        fi
    done
    
    if (( unhealthy_services > 0 )); then
        print_status "$YELLOW" "⚠️  $unhealthy_services services may need more time to start"
    else
        print_status "$GREEN" "✅ All core services are healthy"
    fi
    
    log "Services deployment completed"
}

# Verify deployment
verify_deployment() {
    print_status "$BLUE" "🔍 Verifying deployment..."
    
    # Check if all services are running
    local running_services
    running_services=$(docker-compose -f "$COMPOSE_FILE" ps --services --filter "status=running" | wc -l)
    
    print_status "$GREEN" "📊 Running services: $running_services"
    
    # Check accessible endpoints
    local endpoints=(
        "Gateway:http://localhost:8000/health"
        "Service Manager:http://localhost:9000/health"
        "Grafana:http://localhost:3001"
        "Prometheus:http://localhost:9090"
    )
    
    for endpoint in "${endpoints[@]}"; do
        local service_name=$(echo "$endpoint" | cut -d':' -f1)
        local url=$(echo "$endpoint" | cut -d':' -f2-)
        
        print_status "$BLUE" "🔗 Checking $service_name: $url"
        
        # Simple connectivity check
        if curl -s --connect-timeout 5 "$url" >/dev/null 2>&1; then
            print_status "$GREEN" "✅ $service_name is accessible"
        else
            print_status "$YELLOW" "⚠️  $service_name may not be ready yet"
        fi
    done
    
    # Show resource usage
    print_status "$BLUE" "📊 Resource usage:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" || true
    
    print_status "$GREEN" "✅ Deployment verification completed"
    log "Deployment verification completed"
}

# Show deployment summary
show_deployment_summary() {
    print_status "$GREEN" "🎉 MCP Gateway Production Deployment Summary"
    echo "=================================================="
    print_status "$BLUE" "📋 Deployment Information:"
    echo "  • Compose File: $COMPOSE_FILE"
    echo "  • Environment: $ENV_FILE"
    echo "  • Log File: $LOG_FILE"
    echo "  • Backup: $BACKUP_DIR"
    echo ""
    print_status "$BLUE" "🌐 Access URLs:"
    echo "  • Gateway API: http://localhost:8000"
    echo "  • Admin UI: http://localhost:3000"
    echo "  • Grafana Dashboard: http://localhost:3001"
    echo "  • Prometheus: http://localhost:9090"
    echo ""
    print_status "$BLUE" "🔧 Management Commands:"
    echo "  • View logs: docker-compose -f $COMPOSE_FILE logs -f [service]"
    echo "  • Stop services: docker-compose -f $COMPOSE_FILE down"
    echo "  • Restart services: docker-compose -f $COMPOSE_FILE restart"
    echo "  • Monitor resources: ./scripts/monitor-docker-resources.sh"
    echo ""
    print_status "$BLUE" "📊 Monitoring:"
    echo "  • Resource monitoring: ./scripts/monitor-docker-resources.sh -c"
    echo "  • Performance optimization: ./scripts/optimize-docker-performance.sh -a"
    echo ""
    print_status "$GREEN" "✅ Deployment completed successfully!"
}

# Help function
show_help() {
    cat << EOF
Usage: $SCRIPT_NAME [OPTIONS]

Production Deployment Script for MCP Gateway

OPTIONS:
    -c, --check          Check prerequisites only
    -b, --backup         Backup current deployment only
    -v, --validate       Validate configuration only
    -p, --prepare        Prepare environment only
    -d, --deploy         Deploy services only
    -f, --file FILE      Docker compose file (default: docker-compose.production.yml)
    -e, --env FILE       Environment file (default: .env.production)
    -l, --log FILE       Log file path (auto-generated if not specified)
    -h, --help          Show this help message

EXAMPLES:
    $SCRIPT_NAME                          # Full deployment
    $SCRIPT_NAME -c                       # Check prerequisites only
    $SCRIPT_NAME -b -v                    # Backup and validate only
    $SCRIPT_NAME -d                       # Deploy services only

REQUIREMENTS:
    - Docker and Docker Compose installed
    - Production environment file configured
    - Sufficient system resources for all services

EOF
}

# Parse command line arguments
RUN_ALL=true
RUN_CHECK=false
RUN_BACKUP=false
RUN_VALIDATE=false
RUN_PREPARE=false
RUN_DEPLOY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--check)
            RUN_ALL=false
            RUN_CHECK=true
            shift
            ;;
        -b|--backup)
            RUN_ALL=false
            RUN_BACKUP=true
            shift
            ;;
        -v|--validate)
            RUN_ALL=false
            RUN_VALIDATE=true
            shift
            ;;
        -p|--prepare)
            RUN_ALL=false
            RUN_PREPARE=true
            shift
            ;;
        -d|--deploy)
            RUN_ALL=false
            RUN_DEPLOY=true
            shift
            ;;
        -f|--file)
            COMPOSE_FILE="$2"
            shift 2
            ;;
        -e|--env)
            ENV_FILE="$2"
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
    print_status "$BLUE" "🚀 MCP Gateway Production Deployment"
    echo "=================================================="
    
    log "Starting production deployment"
    
    # Run deployment steps based on flags
    if [[ "$RUN_ALL" == "true" ]]; then
        check_prerequisites
        backup_current_deployment
        validate_configuration
        prepare_environment
        deploy_services
        verify_deployment
    else
        if [[ "$RUN_CHECK" == "true" ]]; then
            check_prerequisites
        fi
        
        if [[ "$RUN_BACKUP" == "true" ]]; then
            backup_current_deployment
        fi
        
        if [[ "$RUN_VALIDATE" == "true" ]]; then
            validate_configuration
        fi
        
        if [[ "$RUN_PREPARE" == "true" ]]; then
            prepare_environment
        fi
        
        if [[ "$RUN_DEPLOY" == "true" ]]; then
            deploy_services
            verify_deployment
        fi
    fi
    
    # Show summary
    show_deployment_summary
    
    log "Production deployment completed successfully"
}

# Trap to handle interruption
trap 'log "Deployment interrupted"; exit 0' INT TERM

# Run main function
main "$@"