#!/bin/bash

# Docker Performance Optimization Script for MCP Gateway
# Optimizes Docker daemon settings, cleans up resources, and improves performance

set -euo pipefail

# Configuration
SCRIPT_NAME="$(basename "$0")"
LOG_FILE="/tmp/mcp-gateway-optimize.log"
COMPOSE_FILE="docker-compose.yml"
BACKUP_DIR="/tmp/mcp-gateway-backup-$(date +%Y%m%d_%H%M%S)"

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

# Check if running as root (for system-level optimizations)
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_status "$YELLOW" "⚠️  Running as root - system optimizations will be applied"
        return 0
    else
        print_status "$BLUE" "ℹ️  Running as user - only user-level optimizations will be applied"
        return 1
    fi
}

# Check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_status "$RED" "ERROR: Docker is not running or accessible"
        exit 1
    fi
}

# Backup current configuration
backup_config() {
    print_status "$BLUE" "📦 Creating configuration backup..."
    mkdir -p "$BACKUP_DIR"

    # Backup docker-compose files
    if [[ -f "$COMPOSE_FILE" ]]; then
        cp "$COMPOSE_FILE" "$BACKUP_DIR/"
        print_status "$GREEN" "✅ Backed up $COMPOSE_FILE"
    fi

    # Backup Docker daemon config if exists
    if [[ -f /etc/docker/daemon.json ]] && check_root; then
        cp /etc/docker/daemon.json "$BACKUP_DIR/"
        print_status "$GREEN" "✅ Backed up Docker daemon configuration"
    fi

    log "Configuration backed up to $BACKUP_DIR"
}

# Clean up Docker resources
cleanup_docker_resources() {
    print_status "$BLUE" "🧹 Cleaning up Docker resources..."

    # Remove stopped containers
    local stopped_containers
    stopped_containers=$(docker ps -aq --filter "status=exited" 2>/dev/null || true)
    if [[ -n "$stopped_containers" ]]; then
        docker rm $stopped_containers
        print_status "$GREEN" "✅ Removed stopped containers"
    fi

    # Remove unused images
    local dangling_images
    dangling_images=$(docker images -f "dangling=true" -q 2>/dev/null || true)
    if [[ -n "$dangling_images" ]]; then
        docker rmi $dangling_images
        print_status "$GREEN" "✅ Removed dangling images"
    fi

    # Remove unused volumes (with confirmation)
    if [[ "${AUTO_CLEAN_VOLUMES:-false}" == "true" ]]; then
        local unused_volumes
        unused_volumes=$(docker volume ls -qf "dangling=true" 2>/dev/null || true)
        if [[ -n "$unused_volumes" ]]; then
            docker volume rm $unused_volumes
            print_status "$GREEN" "✅ Removed unused volumes"
        fi
    fi

    # Clean up build cache
    docker builder prune -f
    print_status "$GREEN" "✅ Cleaned build cache"

    # System prune
    if [[ "${SYSTEM_PRUNE:-false}" == "true" ]]; then
        docker system prune -f
        print_status "$GREEN" "✅ System prune completed"
    fi

    log "Docker cleanup completed"
}

# Optimize Docker daemon configuration
optimize_docker_daemon() {
    if ! check_root; then
        print_status "$YELLOW" "⚠️  Skipping Docker daemon optimization (requires root privileges)"
        return
    fi

    print_status "$BLUE" "⚙️  Optimizing Docker daemon configuration..."

    local daemon_config="/etc/docker/daemon.json"
    local temp_config="/tmp/daemon.json"

    # Create optimized daemon configuration
    cat > "$temp_config" << 'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "storage-opts": [
    "overlay2.override_kernel_check=true"
  ],
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 64000,
      "Soft": 64000
    }
  },
  "max-concurrent-downloads": 10,
  "max-concurrent-uploads": 5,
  "max-download-attempts": 5,
  "live-restore": true,
  "userland-proxy": false,
  "experimental": false,
  "metrics-addr": "127.0.0.1:9323",
  "exec-opts": ["native.cgroupdriver=systemd"],
  "bridge": "none",
  "ip-forward": true,
  "iptables": true
}
EOF

    # Backup existing config and apply new one
    if [[ -f "$daemon_config" ]]; then
        cp "$daemon_config" "${daemon_config}.backup.$(date +%Y%m%d_%H%M%S)"
    fi

    cp "$temp_config" "$daemon_config"
    print_status "$GREEN" "✅ Docker daemon configuration optimized"

    # Restart Docker daemon
    print_status "$YELLOW" "🔄 Restarting Docker daemon..."
    if systemctl restart docker 2>/dev/null; then
        print_status "$GREEN" "✅ Docker daemon restarted successfully"
    else
        print_status "$YELLOW" "⚠️  Could not restart Docker daemon (may require manual restart)"
    fi

    log "Docker daemon optimization completed"
}

# Optimize Docker Compose configuration
optimize_compose_config() {
    print_status "$BLUE" "📝 Optimizing Docker Compose configuration..."

    if [[ ! -f "$COMPOSE_FILE" ]]; then
        print_status "$YELLOW" "⚠️  Docker Compose file not found: $COMPOSE_FILE"
        return
    fi

    # Check if resource limits are already configured
    local has_resource_limits
    has_resource_limits=$(grep -c "resources:" "$COMPOSE_FILE" 2>/dev/null || echo "0")

    if (( has_resource_limits > 0 )); then
        print_status "$GREEN" "✅ Resource limits already configured in $COMPOSE_FILE"
    else
        print_status "$YELLOW" "⚠️  No resource limits found in $COMPOSE_FILE"
        print_status "$BLUE" "💡 Consider adding resource limits to improve performance"
    fi

    # Check health checks
    local has_health_checks
    has_health_checks=$(grep -c "healthcheck:" "$COMPOSE_FILE" 2>/dev/null || echo "0")

    if (( has_health_checks > 0 )); then
        print_status "$GREEN" "✅ Health checks configured in $COMPOSE_FILE"
    else
        print_status "$YELLOW" "⚠️  No health checks found in $COMPOSE_FILE"
    fi

    log "Docker Compose configuration analysis completed"
}

# Optimize system settings
optimize_system_settings() {
    if ! check_root; then
        print_status "$YELLOW" "⚠️  Skipping system optimization (requires root privileges)"
        return
    fi

    print_status "$BLUE" "🖥️  Optimizing system settings..."

    # Optimize sysctl settings for Docker
    local sysctl_conf="/etc/sysctl.d/99-docker-optimization.conf"

    cat > "$sysctl_conf" << 'EOF'
# Docker Performance Optimizations
# Increase network buffer sizes
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216

# Increase file descriptor limits
fs.file-max = 2097152

# Optimize for container workloads
vm.max_map_count = 262144
vm.swappiness = 10

# Network optimization
net.ipv4.tcp_congestion_control = bbr
EOF

    # Apply sysctl settings
    if sysctl -p "$sysctl_conf" 2>/dev/null; then
        print_status "$GREEN" "✅ System settings optimized"
    else
        print_status "$YELLOW" "⚠️  Could not apply all system settings"
    fi

    log "System optimization completed"
}

# Check Docker performance metrics
check_performance_metrics() {
    print_status "$BLUE" "📊 Checking Docker performance metrics..."

    # Get Docker system info
    local docker_version
    docker_version=$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo "Unknown")
    print_status "$GREEN" "🐳 Docker version: $docker_version"

    # Check system resources
    local total_memory
    total_memory=$(free -h | awk 'NR==2{print $2}')
    print_status "$GREEN" "💾 Total memory: $total_memory"

    local cpu_cores
    cpu_cores=$(nproc 2>/dev/null || echo "Unknown")
    print_status "$GREEN" "🔄 CPU cores: $cpu_cores"

    # Check Docker disk usage
    local docker_disk_usage
    docker_disk_usage=$(docker system df --format "{{.Type}}: {{.Size}}" 2>/dev/null || echo "Unknown")
    print_status "$GREEN" "💿 Docker disk usage:"
    echo "$docker_disk_usage" | while IFS= read -r line; do
        echo "  $line"
    done

    # Check active containers
    local active_containers
    active_containers=$(docker ps -q | wc -l 2>/dev/null || echo "0")
    print_status "$GREEN" "📦 Active containers: $active_containers"

    log "Performance metrics collected"
}

# Validate Docker Compose configuration
validate_compose_config() {
    print_status "$BLUE" "🔍 Validating Docker Compose configuration..."

    if [[ ! -f "$COMPOSE_FILE" ]]; then
        print_status "$RED" "❌ Docker Compose file not found: $COMPOSE_FILE"
        return 1
    fi

    # Validate syntax
    if docker-compose -f "$COMPOSE_FILE" config >/dev/null 2>&1; then
        print_status "$GREEN" "✅ Docker Compose configuration is valid"
    else
        print_status "$RED" "❌ Docker Compose configuration has errors"
        docker-compose -f "$COMPOSE_FILE" config
        return 1
    fi

    log "Docker Compose validation completed"
}

# Restart services with optimization
restart_services() {
    print_status "$BLUE" "🔄 Restarting services with optimizations..."

    if [[ ! -f "$COMPOSE_FILE" ]]; then
        print_status "$YELLOW" "⚠️  No Docker Compose file found, skipping service restart"
        return
    fi

    # Stop services
    if docker-compose -f "$COMPOSE_FILE" down 2>/dev/null; then
        print_status "$GREEN" "✅ Services stopped"
    else
        print_status "$YELLOW" "⚠️  Some services may not have been running"
    fi

    # Start services
    if docker-compose -f "$COMPOSE_FILE" up -d 2>/dev/null; then
        print_status "$GREEN" "✅ Services started with optimizations"

        # Wait a moment and check status
        sleep 5
        if docker-compose -f "$COMPOSE_FILE" ps 2>/dev/null; then
            print_status "$GREEN" "✅ Services are running"
        fi
    else
        print_status "$RED" "❌ Failed to start services"
        return 1
    fi

    log "Services restarted with optimizations"
}

# Help function
show_help() {
    cat << EOF
Usage: $SCRIPT_NAME [OPTIONS]

Docker Performance Optimization Script for MCP Gateway

OPTIONS:
    -a, --all           Run all optimizations (cleanup, daemon, system, services)
    -c, --cleanup       Clean up Docker resources only
    -d, --daemon        Optimize Docker daemon configuration (requires root)
    -s, --system        Optimize system settings (requires root)
    -r, --restart       Restart services with optimizations
    -f, --file FILE     Docker compose file (default: docker-compose.yml)
    -l, --log FILE      Log file path (default: /tmp/mcp-gateway-optimize.log)
    --auto-clean-volumes  Automatically clean unused volumes
    --system-prune      Run full system prune
    -h, --help          Show this help message

EXAMPLES:
    $SCRIPT_NAME -a                    # Run all optimizations
    $SCRIPT_NAME -c                    # Clean up resources only
    $SCRIPT_NAME -d -s                 # Optimize daemon and system (requires root)
    $SCRIPT_NAME -r                    # Restart services only

REQUIREMENTS:
    - Docker and Docker Compose installed
    - Root privileges for system-level optimizations
    - bc command for calculations

EOF
}

# Parse command line arguments
RUN_ALL=false
RUN_CLEANUP=false
RUN_DAEMON=false
RUN_SYSTEM=false
RUN_RESTART=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -a|--all)
            RUN_ALL=true
            shift
            ;;
        -c|--cleanup)
            RUN_CLEANUP=true
            shift
            ;;
        -d|--daemon)
            RUN_DAEMON=true
            shift
            ;;
        -s|--system)
            RUN_SYSTEM=true
            shift
            ;;
        -r|--restart)
            RUN_RESTART=true
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
        --auto-clean-volumes)
            AUTO_CLEAN_VOLUMES=true
            shift
            ;;
        --system-prune)
            SYSTEM_PRUNE=true
            shift
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
    print_status "$BLUE" "🚀 MCP Gateway Docker Performance Optimization"
    echo "=================================================="

    log "Starting Docker performance optimization"

    # Check prerequisites
    check_docker

    # Create backup
    backup_config

    # Run optimizations based on flags
    if [[ "$RUN_ALL" == "true" ]]; then
        cleanup_docker_resources
        optimize_docker_daemon
        optimize_system_settings
        optimize_compose_config
        validate_compose_config
        restart_services
    else
        if [[ "$RUN_CLEANUP" == "true" ]]; then
            cleanup_docker_resources
        fi

        if [[ "$RUN_DAEMON" == "true" ]]; then
            optimize_docker_daemon
        fi

        if [[ "$RUN_SYSTEM" == "true" ]]; then
            optimize_system_settings
        fi

        if [[ "$RUN_RESTART" == "true" ]]; then
            restart_services
        fi

        # Always run these checks
        optimize_compose_config
        validate_compose_config
    fi

    # Show performance metrics
    check_performance_metrics

    print_status "$GREEN" "✅ Docker performance optimization completed!"
    print_status "$BLUE" "📝 Log file: $LOG_FILE"
    print_status "$BLUE" "📦 Backup directory: $BACKUP_DIR"

    log "Optimization completed successfully"
}

# Trap to handle interruption
trap 'log "Optimization interrupted"; exit 0' INT TERM

# Run main function
main "$@"
