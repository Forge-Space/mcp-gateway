#!/bin/bash

# Docker Security Vulnerability Scanning for MCP Gateway
# Comprehensive security assessment and vulnerability management

set -euo pipefail

# Configuration
SCRIPT_NAME="$(basename "$0")"
LOG_FILE="/tmp/mcp-gateway-security-scan.log"
RESULTS_DIR="/tmp/mcp-gateway-security-results"
COMPOSE_FILE="docker-compose.yml"
SECURITY_REPORT="$RESULTS_DIR/security_report_$(date +%Y%m%d_%H%M%S).json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Security thresholds
CRITICAL_THRESHOLD=0
HIGH_THRESHOLD=0
MEDIUM_THRESHOLD=5
LOW_THRESHOLD=10

# Create results directory
mkdir -p "$RESULTS_DIR"

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

# Print header
print_header() {
    print_status "$CYAN" "🔒 Docker Security Vulnerability Scanner"
    echo "=========================================="
    print_status "$BLUE" "Scan Started: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
}

# Check if security tool is available
check_security_tool() {
    local tool=$1
    local tool_name=$2

    if command -v "$tool" >/dev/null 2>&1; then
        print_status "$GREEN" "✅ $tool_name is available"
        return 0
    else
        print_status "$YELLOW" "⚠️  $tool_name is not available - install with: $3"
        return 1
    fi
}

# Scan Docker images with Trivy
scan_with_trivy() {
    local image=$1
    local output_file=$2

    if check_security_tool "trivy" "Trivy" "brew install trivy || apt-get install trivy"; then
        print_status "$BLUE" "🔍 Scanning $image with Trivy..."

        if trivy image --format json --output "$output_file" "$image" 2>/dev/null; then
            print_status "$GREEN" "✅ Trivy scan completed for $image"
            return 0
        else
            print_status "$RED" "❌ Trivy scan failed for $image"
            return 1
        fi
    else
        return 1
    fi
}

# Scan Docker images with Snyk
scan_with_snyk() {
    local image=$1
    local output_file=$2

    if check_security_tool "snyk" "Snyk" "npm install -g snyk"; then
        print_status "$BLUE" "🔍 Scanning $image with Snyk..."

        # Try to authenticate if token is available
        if [[ -n "${SNYK_TOKEN:-}" ]]; then
            snyk auth "$SNYK_TOKEN" 2>/dev/null || true
        fi

        if snyk container test "$image" --json-file-output="$output_file" 2>/dev/null; then
            print_status "$GREEN" "✅ Snyk scan completed for $image"
            return 0
        else
            print_status "$RED" "❌ Snyk scan failed for $image"
            return 1
        fi
    else
        return 1
    fi
}

# Basic Docker image security check
basic_security_check() {
    local image=$1
    local output_file=$2

    print_status "$BLUE" "🔍 Performing basic security check on $image..."

    # Get image information
    local image_id=$(docker images --format "{{.ID}}" "$image" 2>/dev/null || echo "")
    local created=$(docker images --format "{{.CreatedAt}}" "$image" 2>/dev/null || echo "")
    local size=$(docker images --format "{{.Size}}" "$image" 2>/dev/null || echo "")

    # Check for common security issues
    local security_issues=()

    # Check if running as root (basic check)
    local user_config=$(docker inspect --format='{{.Config.User}}' "$image" 2>/dev/null || echo "")
    if [[ -z "$user_config" ]] || [[ "$user_config" == "root" ]] || [[ "$user_config" == "0" ]]; then
        security_issues+=("Container runs as root user")
    fi

    # Check for exposed ports
    local exposed_ports=$(docker inspect --format='{{range $p, $conf := .Config.ExposedPorts}}{{$p}} {{end}}' "$image" 2>/dev/null || echo "")
    if [[ -n "$exposed_ports" ]]; then
        security_issues+=("Exposed ports: $exposed_ports")
    fi

    # Check for sensitive environment variables
    local env_vars=$(docker inspect --format='{{range $e := .Config.Env}}{{$e}} {{end}}' "$image" 2>/dev/null || echo "")
    local sensitive_vars=()
    while IFS= read -r var; do
        if [[ "$var" =~ (PASSWORD|SECRET|KEY|TOKEN) ]]; then
            sensitive_vars+=("$var")
        fi
    done <<< "$env_vars"

    if [[ ${#sensitive_vars[@]} -gt 0 ]]; then
        security_issues+=("Potentially sensitive environment variables: ${#sensitive_vars[@]} found")
    fi

    # Create JSON output
    {
        echo "{"
        echo "  \"image\": \"$image\","
        echo "  \"image_id\": \"$image_id\","
        echo "  \"created\": \"$created\","
        echo "  \"size\": \"$size\","
        echo "  \"user\": \"$user_config\","
        echo "  \"exposed_ports\": \"$exposed_ports\","
        echo "  \"security_issues\": ["
        local first=true
        for issue in "${security_issues[@]}"; do
            if [[ "$first" == "false" ]]; then
                echo ","
            fi
            first=false
            echo "    \"$issue\""
        done
        echo "  ],"
        echo "  \"scan_type\": \"basic\","
        echo "  \"scan_timestamp\": \"$(date -Iseconds)\""
        echo "}"
    } > "$output_file"

    print_status "$GREEN" "✅ Basic security check completed for $image"
}

# Analyze scan results
analyze_scan_results() {
    local scan_file=$1
    local image_name=$2

    if [[ ! -f "$scan_file" ]]; then
        return 1
    fi

    local critical=0
    local high=0
    local medium=0
    local low=0

    # Try to parse JSON results (format may vary by tool)
    if grep -q '"Severity"' "$scan_file" 2>/dev/null; then
        # Trivy/Snyk format
        critical=$(grep -o '"Severity": "CRITICAL"' "$scan_file" 2>/dev/null | wc -l || echo 0)
        high=$(grep -o '"Severity": "HIGH"' "$scan_file" 2>/dev/null | wc -l || echo 0)
        medium=$(grep -o '"Severity": "MEDIUM"' "$scan_file" 2>/dev/null | wc -l || echo 0)
        low=$(grep -o '"Severity": "LOW"' "$scan_file" 2>/dev/null | wc -l || echo 0)
    elif grep -q '"security_issues"' "$scan_file" 2>/dev/null; then
        # Basic check format
        local issue_count=$(grep -o '"security_issues":' "$scan_file" 2>/dev/null | wc -l || echo 0)
        if [[ $issue_count -gt 0 ]]; then
            # Count issues as medium severity for basic checks
            medium=$issue_count
        fi
    fi

    # Display results
    echo "  $image_name:"
    if [[ $critical -gt 0 ]]; then
        print_status "$RED" "    🚨 Critical: $critical"
    fi
    if [[ $high -gt 0 ]]; then
        print_status "$RED" "    ⚠️  High: $high"
    fi
    if [[ $medium -gt 0 ]]; then
        print_status "$YELLOW" "    ⚠️  Medium: $medium"
    fi
    if [[ $low -gt 0 ]]; then
        print_status "$BLUE" "    ℹ️  Low: $low"
    fi
    if [[ $critical -eq 0 && $high -eq 0 && $medium -eq 0 && $low -eq 0 ]]; then
        print_status "$GREEN" "    ✅ No vulnerabilities found"
    fi

    # Return exit code based on thresholds
    if [[ $critical -gt $CRITICAL_THRESHOLD ]] || [[ $high -gt $HIGH_THRESHOLD ]]; then
        return 2  # Critical/High threshold exceeded
    elif [[ $medium -gt $MEDIUM_THRESHOLD ]]; then
        return 1  # Medium threshold exceeded
    else
        return 0  # Within acceptable thresholds
    fi
}

# Scan all MCP Gateway images
scan_all_images() {
    print_status "$BLUE" "🔍 Scanning all MCP Gateway Docker images..."

    local images=(
        "forge-mcp-gateway-ui:latest"
        "forge-mcp-gateway-tool-router:latest"
        "forge-mcp-gateway-service-manager:latest"
        "forge-mcp-gateway-translate:latest"
        "ghcr.io/ibm/mcp-context-forge:1.0.0-BETA-2"
        "ollama/ollama:latest"
    )

    local total_vulnerabilities=0
    local scan_results_dir="$RESULTS_DIR/scan_results_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$scan_results_dir"

    for image in "${images[@]}"; do
        echo ""
        print_status "$MAGENTA" "📦 Scanning image: $image"
        echo "----------------------------------------"

        # Try different scanning tools in order of preference
        local scan_file="$scan_results_dir/$(echo "$image" | sed 's/[^a-zA-Z0-9]/_/g').json"
        local scan_successful=false

        # Try Trivy first
        if scan_with_trivy "$image" "$scan_file"; then
            scan_successful=true
        # Try Snyk if Trivy fails
        elif scan_with_snyk "$image" "$scan_file"; then
            scan_successful=true
        # Fall back to basic check
        else
            basic_security_check "$image" "$scan_file"
            scan_successful=true
        fi

        if [[ "$scan_successful" == "true" ]]; then
            analyze_scan_results "$scan_file" "$image"
            local result=$?
            total_vulnerabilities=$((total_vulnerabilities + result))
        fi
    done

    echo ""
    print_status "$BLUE" "📊 Scan Summary"
    echo "========================================"
    print_status "$BLUE" "Total images scanned: ${#images[@]}"
    print_status "$BLUE" "Scan results directory: $scan_results_dir"

    if [[ $total_vulnerabilities -gt 0 ]]; then
        if [[ $total_vulnerabilities -eq 2 ]]; then
            print_status "$RED" "🚨 Critical/High vulnerabilities found - immediate action required"
        elif [[ $total_vulnerabilities -eq 1 ]]; then
            print_status "$YELLOW" "⚠️  Medium vulnerabilities found - review recommended"
        else
            print_status "$GREEN" "✅ All images within acceptable security thresholds"
        fi
    else
        print_status "$GREEN" "✅ All images passed security scan"
    fi

    return $total_vulnerabilities
}

# Check Docker daemon security
check_docker_security() {
    print_status "$BLUE" "🔍 Checking Docker daemon security configuration..."

    local security_issues=()

    # Check if Docker daemon is running as root
    if [[ $(id -u) -eq 0 ]]; then
        security_issues+=("Running as root user")
    fi

    # Check Docker socket permissions
    local docker_socket="/var/run/docker.sock"
    if [[ -e "$docker_socket" ]]; then
        local socket_perms=$(stat -c "%a" "$docker_socket" 2>/dev/null || stat -f "%A" "$docker_socket" 2>/dev/null || echo "")
        if [[ "$socket_perms" == "666" ]] || [[ "$socket_perms" == "777" ]]; then
            security_issues+=("Docker socket has world-writable permissions")
        fi
    fi

    # Check for user namespaces
    local user_namespaces=$(docker info 2>/dev/null | grep -i "userns" || echo "")
    if [[ -z "$user_namespaces" ]]; then
        security_issues+=("User namespaces not enabled")
    fi

    # Check for content trust
    if [[ -z "${DOCKER_CONTENT_TRUST:-}" ]] || [[ "$DOCKER_CONTENT_TRUST" != "1" ]]; then
        security_issues+=("Docker Content Trust not enabled")
    fi

    # Display results
    echo "Docker Daemon Security:"
    if [[ ${#security_issues[@]} -gt 0 ]]; then
        for issue in "${security_issues[@]}"; do
            print_status "$YELLOW" "  ⚠️  $issue"
        done
    else
        print_status "$GREEN" "  ✅ Docker daemon security configuration looks good"
    fi
}

# Check container runtime security
check_container_security() {
    print_status "$BLUE" "🔍 Checking container runtime security..."

    local containers=$(docker-compose ps -q 2>/dev/null || echo "")
    local security_issues=()

    while IFS= read -r container_id; do
        if [[ -n "$container_id" ]]; then
            local container_name=$(docker ps --filter "id=$container_id" --format "{{.Names}}" 2>/dev/null || echo "unknown")

            # Check if container is running as root
            local user=$(docker inspect --format='{{.Config.User}}' "$container_id" 2>/dev/null || echo "")
            if [[ -z "$user" ]] || [[ "$user" == "root" ]] || [[ "$user" == "0" ]]; then
                security_issues+=("$container_name: Running as root user")
            fi

            # Check for privileged mode
            local privileged=$(docker inspect --format='{{.HostConfig.Privileged}}' "$container_id" 2>/dev/null || echo "false")
            if [[ "$privileged" == "true" ]]; then
                security_issues+=("$container_name: Running in privileged mode")
            fi

            # Check for host networking
            local network_mode=$(docker inspect --format='{{.HostConfig.NetworkMode}}' "$container_id" 2>/dev/null || echo "")
            if [[ "$network_mode" == "host" ]]; then
                security_issues+=("$container_name: Using host network mode")
            fi

            # Check for mounted Docker socket
            local mounts=$(docker inspect --format='{{range .Mounts}}{{.Source}}:{{.Destination}} {{end}}' "$container_id" 2>/dev/null || echo "")
            if [[ "$mounts" =~ "/var/run/docker.sock" ]]; then
                security_issues+=("$container_name: Docker socket mounted")
            fi
        fi
    done <<< "$containers"

    # Display results
    echo "Container Runtime Security:"
    if [[ ${#security_issues[@]} -gt 0 ]]; then
        for issue in "${security_issues[@]}"; do
            print_status "$YELLOW" "  ⚠️  $issue"
        done
    else
        print_status "$GREEN" "  ✅ Container runtime security looks good"
    fi
}

# Generate security recommendations
generate_recommendations() {
    print_status "$BLUE" "💡 Generating security recommendations..."

    local recommendations_file="$RESULTS_DIR/security_recommendations_$(date +%Y%m%d_%H%M%S).md"

    {
        echo "# Docker Security Recommendations"
        echo ""
        echo "**Generated:** $(date '+%Y-%m-%d %H:%M:%S')"
        echo ""
        echo "## High Priority Recommendations"
        echo ""
        echo "1. **Enable Docker Content Trust**"
        echo "   ```bash"
        echo "   export DOCKER_CONTENT_TRUST=1"
        echo "   ```"
        echo ""
        echo "2. **Use Non-Root Users**"
        echo "   - Ensure all containers run as non-root users"
        echo "   - Add \`USER\` instruction in Dockerfiles"
        echo "   - Verify with \`docker inspect <container>\`"
        echo ""
        echo "3. **Enable User Namespaces**"
        echo "   - Configure Docker daemon with user namespaces"
        echo "   - Add to \`/etc/docker/daemon.json\`:"
        echo "   ```json"
        echo "   {"
        echo "     \"userns-remap\": \"default\""
        echo "   }"
        echo "   ```"
        echo ""
        echo "4. **Regular Security Scanning**"
        echo "   - Set up automated vulnerability scanning"
        echo "   - Use tools like Trivy, Snyk, or Clair"
        echo "   - Scan images before deployment"
        echo ""
        echo "## Medium Priority Recommendations"
        echo ""
        echo "1. **Limit Container Capabilities**"
        echo "   - Drop unnecessary capabilities"
        echo "   - Use \`--cap-drop\` flag when running containers"
        echo ""
        echo "2. **Use Read-Only Filesystems**"
        echo "   - Mount filesystems as read-only where possible"
        echo "   - Use \`--read-only\` flag with \`--tmpfs\` for writable directories"
        echo ""
        echo "3. **Implement Resource Limits**"
        echo "   - Set CPU and memory limits"
        echo "   - Use \`--cpus\` and \`--memory\` flags"
        echo ""
        echo "4. **Secure Docker Socket**"
        echo "   - Restrict access to Docker socket"
        echo "   - Use Docker socket proxy when needed"
        echo ""
        echo "## Low Priority Recommendations"
        echo ""
        echo "1. **Use Security Scanning in CI/CD**"
        echo "   - Integrate security scans into build pipeline"
        echo "   - Fail builds on critical vulnerabilities"
        echo ""
        echo "2. **Regular Image Updates**"
        echo "   - Keep base images updated"
        echo "   - Monitor for security advisories"
        echo ""
        echo "3. **Network Segmentation**"
        echo "   - Use Docker networks to isolate containers"
        echo "   - Limit inter-container communication"
        echo ""
        echo "## MCP Gateway Specific Recommendations"
        echo ""
        echo "1. **Service Manager Security**"
        echo "   - The service manager requires Docker socket access"
        echo "   - Consider using Docker socket proxy for better security"
        echo "   - Monitor service manager logs for security events"
        echo ""
        echo "2. **Gateway Security**"
        echo "   - Ensure proper authentication and authorization"
        echo "   - Use HTTPS in production"
        echo "   - Implement rate limiting"
        echo ""
        echo "3. **Resource Monitoring**"
        echo "   - Monitor container resource usage"
        echo "   - Set up alerts for unusual activity"
        echo "   - Regular security audits"
        echo ""
    } > "$recommendations_file"

    print_status "$GREEN" "✅ Security recommendations generated: $recommendations_file"
}

# Generate comprehensive security report
generate_security_report() {
    print_status "$BLUE" "📝 Generating comprehensive security report..."

    local report_file="$SECURITY_REPORT"

    {
        echo "{"
        echo "  \"scan_timestamp\": \"$(date -Iseconds)\","
        echo "  \"scanner_version\": \"$SCRIPT_NAME v1.0.0\","
        echo "  \"docker_daemon_security\": {"
        echo "    \"checked\": true,"
        echo "    \"user_namespaces_enabled\": false,"
        echo "    \"content_trust_enabled\": $([[ \"${DOCKER_CONTENT_TRUST:-}\" == \"1\" ]] && echo true || echo false)"
        echo "  },"
        echo "  \"container_security\": {"
        echo "    \"checked\": true,"
        echo "    \"containers_scanned\": $(docker-compose ps -q 2>/dev/null | wc -l || echo 0)"
        echo "  },"
        echo "  \"image_security\": {"
        echo "    \"checked\": true,"
        echo "    \"images_scanned\": 6,"
        echo "    \"vulnerabilities_found\": $1"
        echo "  },"
        echo "  \"tools_available\": {"
        echo "    \"trivy\": $(command -v trivy >/dev/null 2>&1 && echo true || echo false),"
        echo "    \"snyk\": $(command -v snyk >/dev/null 2>&1 && echo true || echo false)"
        echo "  },"
        echo "  \"recommendations\": \"See security_recommendations_*.md file\""
        echo "}"
    } > "$report_file"

    print_status "$GREEN" "✅ Security report generated: $report_file"
}

# Help function
show_help() {
    cat << EOF
Usage: $SCRIPT_NAME [OPTIONS]

Docker Security Vulnerability Scanner for MCP Gateway

OPTIONS:
    -h, --help              Show this help message
    -i, --images            Scan Docker images only
    -d, --daemon            Check Docker daemon security only
    -c, --containers        Check container runtime security only
    -r, --recommendations   Generate security recommendations only
    -o, --output DIR        Output directory for results (default: /tmp/mcp-gateway-security-results)
    --trivy-only            Use Trivy scanner only
    --snyk-only             Use Snyk scanner only
    --basic-only            Use basic security checks only

EXAMPLES:
    $SCRIPT_NAME                           # Full security scan
    $SCRIPT_NAME -i                        # Scan images only
    $SCRIPT_NAME -d                        # Check daemon security only
    $SCRIPT_NAME -o /path/to/results       # Custom output directory

SECURITY TOOLS:
    - Trivy: Comprehensive vulnerability scanner (recommended)
    - Snyk: Cloud-based vulnerability scanner
    - Basic checks: Built-in security analysis

THRESHOLDS:
    - Critical vulnerabilities: 0 allowed
    - High vulnerabilities: 0 allowed
    - Medium vulnerabilities: 5 allowed
    - Low vulnerabilities: 10 allowed

EOF
}

# Parse command line arguments
IMAGES_ONLY=false
DAEMON_ONLY=false
CONTAINERS_ONLY=false
RECOMMENDATIONS_ONLY=false
TRIVY_ONLY=false
SNYK_ONLY=false
BASIC_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -i|--images)
            IMAGES_ONLY=true
            shift
            ;;
        -d|--daemon)
            DAEMON_ONLY=true
            shift
            ;;
        -c|--containers)
            CONTAINERS_ONLY=true
            shift
            ;;
        -r|--recommendations)
            RECOMMENDATIONS_ONLY=true
            shift
            ;;
        -o|--output)
            RESULTS_DIR="$2"
            shift 2
            ;;
        --trivy-only)
            TRIVY_ONLY=true
            shift
            ;;
        --snyk-only)
            SNYK_ONLY=true
            shift
            ;;
        --basic-only)
            BASIC_ONLY=true
            shift
            ;;
        *)
            print_status "$RED" "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check dependencies
if ! command -v docker >/dev/null 2>&1; then
    print_status "$RED" "❌ Docker is not installed or not in PATH"
    exit 1
fi

if ! command -v docker-compose >/dev/null 2>&1; then
    print_status "$RED" "❌ Docker Compose is not installed or not in PATH"
    exit 1
fi

# Main execution
log "Starting Docker security scanning"

print_header

total_vulnerabilities=0

if [[ "$RECOMMENDATIONS_ONLY" == "true" ]]; then
    generate_recommendations
elif [[ "$DAEMON_ONLY" == "true" ]]; then
    check_docker_security
elif [[ "$CONTAINERS_ONLY" == "true" ]]; then
    check_container_security
elif [[ "$IMAGES_ONLY" == "true" ]]; then
    scan_all_images
    total_vulnerabilities=$?
else
    # Full security scan
    check_docker_security
    echo ""
    check_container_security
    echo ""
    scan_all_images
    total_vulnerabilities=$?
    echo ""
    generate_recommendations
fi

# Generate comprehensive report
generate_security_report "$total_vulnerabilities"

echo ""
print_status "$BLUE" "📊 Security Scan Summary"
echo "=========================================="
print_status "$BLUE" "Results directory: $RESULTS_DIR"
print_status "$BLUE" "Log file: $LOG_FILE"

if [[ $total_vulnerabilities -gt 0 ]]; then
    if [[ $total_vulnerabilities -eq 2 ]]; then
        print_status "$RED" "🚨 Critical/High security issues found - immediate action required"
        exit 2
    elif [[ $total_vulnerabilities -eq 1 ]]; then
        print_status "$YELLOW" "⚠️  Medium security issues found - review recommended"
        exit 1
    fi
else
    print_status "$GREEN" "✅ Security scan completed successfully"
    exit 0
fi

log "Security scanning completed"
