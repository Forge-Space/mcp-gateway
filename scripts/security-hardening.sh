#!/bin/bash

# Security Hardening Validation Script for MCP Gateway
# Validates and implements security hardening measures

set -euo pipefail

# Configuration
SCRIPT_NAME="$(basename "$0")"
LOG_FILE="/tmp/mcp-gateway-security-hardening-$(date +%Y%m%d_%H%M%S).log"
REPORT_FILE="/tmp/mcp-gateway-security-report-$(date +%Y%m%d_%H%M%S).json"
COMPOSE_FILE="docker-compose.production.yml"

# Security thresholds
MIN_PASSWORD_LENGTH=32
MAX_LOGIN_ATTEMPTS=5
SESSION_TIMEOUT=3600
SSL_MIN_VERSION="TLSv1.2"

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

# Security check functions
check_password_security() {
    local service=$1
    local password_var=$2

    log "Checking password security for $service"

    if [[ -f "$ENV_FILE" ]]; then
        local password
        password=$(grep "^${password_var}=" "$ENV_FILE" | cut -d'=' -f2- 2>/dev/null || echo "")

        if [[ -z "$password" ]]; then
            print_status "$RED" "❌ Password not configured for $service"
            return 1
        fi

        if [[ ${#password} -lt $MIN_PASSWORD_LENGTH ]]; then
            print_status "$RED" "❌ Password too short for $service (${#password} < $MIN_PASSWORD_LENGTH)"
            return 1
        fi

        if [[ "$password" == *"your-"* ]] || [[ "$password" == *"example"* ]] || [[ "$password" == *"test"* ]]; then
            print_status "$RED" "❌ Default/weak password detected for $service"
            return 1
        fi

        print_status "$GREEN" "✅ Password security validated for $service"
        return 0
    else
        print_status "$YELLOW" "⚠️  Environment file not found: $ENV_FILE"
        return 1
    fi
}

check_container_security() {
    local container_name=$1
    local service_name=$2

    log "Checking container security for $service_name"

    if ! docker ps --format "{{.Names}}" | grep -q "^${container_name}$"; then
        print_status "$YELLOW" "⚠️  Container $container_name not running"
        return 1
    fi

    # Check if running as root
    local user_id
    user_id=$(docker inspect "$container_name" --format='{{.Config.User}}' 2>/dev/null || echo "")

    if [[ -z "$user_id" ]] || [[ "$user_id" == "0" ]] || [[ "$user_id" == "root" ]]; then
        print_status "$RED" "❌ Container $service_name running as root user"
        return 1
    fi

    print_status "$GREEN" "✅ Container security validated for $service_name"
    return 0
}

check_network_security() {
    log "Checking network security"

    # Check exposed ports
    local exposed_ports
    exposed_ports=$(docker-compose -f "$COMPOSE_FILE" ps --format "{{.Ports}}" 2>/dev/null | grep -v "0.0.0.0" | wc -l || echo "0")

    if [[ $exposed_ports -gt 0 ]]; then
        print_status "$YELLOW" "⚠️  $exposed_ports ports exposed to host"
    else
        print_status "$GREEN" "✅ No ports exposed to host"
    fi

    # Check for unnecessary services
    local running_services
    running_services=$(docker-compose -f "$COMPOSE_FILE" ps --services | wc -l || echo "0")

    if [[ $running_services -gt 10 ]]; then
        print_status "$YELLOW" "⚠️  High number of running services: $running_services"
    else
        print_status "$GREEN" "✅ Reasonable number of running services: $running_services"
    fi
}

check_volume_security() {
    log "Checking volume security"

    # Check for sensitive mounts
    local sensitive_volumes=0
    local volumes
    volumes=$(docker-compose -f "$COMPOSE_FILE" config --volumes 2>/dev/null || echo "")

    if echo "$volumes" | grep -q "/etc"; then
        print_status "$RED" "❌ System configuration files mounted"
        sensitive_volumes=$((sensitive_volumes + 1))
    fi

    if echo "$volumes" | grep -q "/root"; then
        print_status "$RED" "❌ Root directory mounted"
        sensitive_volumes=$((sensitive_volumes + 1))
    fi

    if [[ $sensitive_volumes -eq 0 ]]; then
        print_status "$GREEN" "✅ Volume security validated"
    else
        print_status "$RED" "❌ $sensitive_volumes sensitive volume mounts detected"
    fi
}

check_environment_security() {
    log "Checking environment variable security"

    if [[ -f "$ENV_FILE" ]]; then
        local secrets_found=0
        local weak_secrets=0

        # Check for secrets in environment file
        while IFS= read -r line; do
            if [[ "$line" =~ ^(JWT_SECRET|POSTGRES_PASSWORD|REDIS_PASSWORD|GRAFANA_PASSWORD)= ]]; then
                secrets_found=$((secrets_found + 1))
                local value=$(echo "$line" | cut -d'=' -f2-)

                if [[ ${#value} -lt $MIN_PASSWORD_LENGTH ]]; then
                    weak_secrets=$((weak_secrets + 1))
                fi
            fi
        done < "$ENV_FILE"

        if [[ $secrets_found -eq 0 ]]; then
            print_status "$RED" "❌ No security secrets found in environment file"
        else
            print_status "$GREEN" "✅ $secrets_found security secrets found"

            if [[ $weak_secrets -gt 0 ]]; then
                print_status "$RED" "❌ $weak_secrets weak secrets detected"
            else
                print_status "$GREEN" "✅ All secrets meet minimum length requirements"
            fi
        fi

        # Check file permissions
        local file_perms
        file_perms=$(stat -c "%a" "$ENV_FILE" 2>/dev/null || echo "644")

        if [[ "$file_perms" == "600" ]] || [[ "$file_perms" == "640" ]]; then
            print_status "$GREEN" "✅ Environment file permissions are secure ($file_perms)"
        else
            print_status "$YELLOW" "⚠️  Environment file permissions may be too permissive ($file_perms)"
        fi
    else
        print_status "$RED" "❌ Environment file not found"
    fi
}

check_ssl_configuration() {
    log "Checking SSL/TLS configuration"

    # Check if SSL is configured
    if [[ -f "$ENV_FILE" ]]; then
        local ssl_cert
        local ssl_key
        ssl_cert=$(grep "^SSL_CERT_PATH=" "$ENV_FILE" | cut -d'=' -f2- 2>/dev/null || echo "")
        ssl_key=$(grep "^SSL_KEY_PATH=" "$ENV_FILE" | cut -d'=' -f2- 2>/dev/null || echo "")

        if [[ -n "$ssl_cert" ]] && [[ -n "$ssl_key" ]]; then
            print_status "$GREEN" "✅ SSL configuration found"

            # Check certificate existence
            if [[ -f "$ssl_cert" ]]; then
                print_status "$GREEN" "✅ SSL certificate file exists"

                # Check certificate expiration
                if command -v openssl >/dev/null 2>&1; then
                    local cert_expiry
                    cert_expiry=$(openssl x509 -in "$ssl_cert" -noout -enddate 2>/dev/null | cut -d'=' -f2 || echo "")

                    if [[ -n "$cert_expiry" ]]; then
                        local expiry_timestamp
                        expiry_timestamp=$(date -d "$cert_expiry" +%s 2>/dev/null || echo "0")
                        local current_timestamp
                        current_timestamp=$(date +%s)
                        local days_until_expiry
                        days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))

                        if [[ $days_until_expiry -lt 30 ]]; then
                            print_status "$RED" "❌ SSL certificate expires in $days_until_expiry days"
                        else
                            print_status "$GREEN" "✅ SSL certificate valid for $days_until_expiry days"
                        fi
                    fi
                fi
            else
                print_status "$RED" "❌ SSL certificate file not found: $ssl_cert"
            fi

            if [[ -f "$ssl_key" ]]; then
                print_status "$GREEN" "✅ SSL key file exists"

                # Check key permissions
                local key_perms
                key_perms=$(stat -c "%a" "$ssl_key" 2>/dev/null || echo "644")

                if [[ "$key_perms" == "600" ]]; then
                    print_status "$GREEN" "✅ SSL key permissions are secure ($key_perms)"
                else
                    print_status "$RED" "❌ SSL key permissions are too permissive ($key_perms)"
                fi
            else
                print_status "$RED" "❌ SSL key file not found: $ssl_key"
            fi
        else
            print_status "$YELLOW" "⚠️  SSL configuration not found"
        fi
    fi
}

check_logging_security() {
    log "Checking logging security"

    # Check if logging is configured
    local log_config=0

    if docker-compose -f "$COMPOSE_FILE" config 2>/dev/null | grep -q "logging"; then
        log_config=$((log_config + 1))
        print_status "$GREEN" "✅ Docker logging configured"
    fi

    # Check log rotation
    if docker-compose -f "$COMPOSE_FILE" config 2>/dev/null | grep -q "max-size"; then
        log_config=$((log_config + 1))
        print_status "$GREEN" "✅ Log rotation configured"
    fi

    # Check for audit logging
    if [[ -f "$ENV_FILE" ]]; then
        if grep -q "AUDIT_LOGGING=true" "$ENV_FILE"; then
            log_config=$((log_config + 1))
            print_status "$GREEN" "✅ Audit logging enabled"
        else
            print_status "$YELLOW" "⚠️  Audit logging not enabled"
        fi
    fi

    if [[ $log_config -ge 2 ]]; then
        print_status "$GREEN" "✅ Logging security validated"
    else
        print_status "$YELLOW" "⚠️  Logging security needs improvement"
    fi
}

check_access_control() {
    log "Checking access control"

    # Check for authentication
    local auth_config=0

    if [[ -f "$ENV_FILE" ]]; then
        if grep -q "JWT_SECRET" "$ENV_FILE"; then
            auth_config=$((auth_config + 1))
            print_status "$GREEN" "✅ JWT authentication configured"
        fi

        if grep -q "SESSION_TIMEOUT" "$ENV_FILE"; then
            auth_config=$((auth_config + 1))
            local session_timeout
            session_timeout=$(grep "^SESSION_TIMEOUT=" "$ENV_FILE" | cut -d'=' -f2- 2>/dev/null || echo "0")

            if [[ $session_timeout -le $SESSION_TIMEOUT ]]; then
                print_status "$GREEN" "✅ Session timeout configured ($session_timeout seconds)"
            else
                print_status "$YELLOW" "⚠️  Session timeout too long ($session_timeout seconds)"
            fi
        fi

        if grep -q "CORS_ORIGIN" "$ENV_FILE"; then
            auth_config=$((auth_config + 1))
            print_status "$GREEN" "✅ CORS configuration found"
        fi
    fi

    if [[ $auth_config -ge 2 ]]; then
        print_status "$GREEN" "✅ Access control validated"
    else
        print_status "$YELLOW" "⚠️  Access control needs improvement"
    fi
}

check_docker_security() {
    log "Checking Docker daemon security"

    # Check Docker daemon configuration
    local docker_config="/etc/docker/daemon.json"
    local security_score=0

    if [[ -f "$docker_config" ]]; then
        # Check for security settings
        if grep -q '"live-restore": true' "$docker_config"; then
            security_score=$((security_score + 1))
            print_status "$GREEN" "✅ Live restore enabled"
        fi

        if grep -q '"userland-proxy": false' "$docker_config"; then
            security_score=$((security_score + 1))
            print_status "$GREEN" "✅ Userland proxy disabled"
        fi

        if grep -q '"no-new-privileges": true' "$docker_config"; then
            security_score=$((security_score + 1))
            print_status "$GREEN" "✅ No new privileges enabled"
        fi
    else
        print_status "$YELLOW" "⚠️  Docker daemon configuration not found"
    fi

    # Check Docker version
    local docker_version
    docker_version=$(docker --version | grep -oE '[0-9]+\.[0-9]+' | head -1)

    if [[ -n "$docker_version" ]]; then
        local major_version
        major_version=$(echo "$docker_version" | cut -d'.' -f1)

        if [[ $major_version -ge 20 ]]; then
            security_score=$((security_score + 1))
            print_status "$GREEN" "✅ Docker version is recent ($docker_version)"
        else
            print_status "$YELLOW" "⚠️  Docker version may be outdated ($docker_version)"
        fi
    fi

    if [[ $security_score -ge 2 ]]; then
        print_status "$GREEN" "✅ Docker security validated"
    else
        print_status "$YELLOW" "⚠️  Docker security needs improvement"
    fi
}

generate_security_report() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    echo "{"
    echo "  \"timestamp\": \"$timestamp\","
    echo "  \"checks\": {"

    # Run all checks and collect results
    local checks=(
        "password_security"
        "container_security"
        "network_security"
        "volume_security"
        "environment_security"
        "ssl_configuration"
        "logging_security"
        "access_control"
        "docker_security"
    )

    local first=true
    for check in "${checks[@]}"; do
        if [[ "$first" == "true" ]]; then
            first=false
        else
            echo ","
        fi

        echo -n "    \"$check\": \"$(eval "$check" >/dev/null 2>&1 && echo "PASS" || echo "FAIL")\""
    done

    echo ""
    echo "  },"

    # Calculate overall score
    local total_checks=${#checks[@]}
    local passed_checks=0

    for check in "${checks[@]}"; do
        if eval "$check" >/dev/null 2>&1; then
            passed_checks=$((passed_checks + 1))
        fi
    done

    local security_score=$((passed_checks * 100 / total_checks))

    echo "  \"summary\": {"
    echo "    \"total_checks\": $total_checks,"
    echo "    \"passed_checks\": $passed_checks,"
    echo "    \"failed_checks\": $((total_checks - passed_checks)),"
    echo "    \"security_score\": $security_score"
    echo "  },"

    echo "  \"recommendations\": ["

    if [[ $security_score -lt 80 ]]; then
        echo "    \"Security hardening required - score below 80%\","
    fi

    if [[ $passed_checks -lt $total_checks ]]; then
        echo "    \"Address failed security checks\","
    fi

    echo "    \"Regular security audits recommended\","
    echo "    \"Keep Docker and dependencies updated\","
    echo "    \"Monitor for security vulnerabilities\""
    echo "  ]"
    echo "}"
}

apply_security_hardening() {
    log "Applying security hardening measures"

    # Set secure file permissions
    if [[ -f "$ENV_FILE" ]]; then
        chmod 600 "$ENV_FILE"
        print_status "$GREEN" "✅ Set secure permissions on environment file"
    fi

    # Create security directories
    local dirs=("config/ssl" "logs/security" "backups/security")

    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            chmod 700 "$dir"
            print_status "$GREEN" "✅ Created secure directory: $dir"
        fi
    done

    # Generate secure passwords if needed
    if [[ -f "$ENV_FILE" ]]; then
        local passwords_updated=false

        while IFS= read -r line; do
            if [[ "$line" =~ ^(JWT_SECRET|POSTGRES_PASSWORD|REDIS_PASSWORD|GRAFANA_PASSWORD)=your- ]]; then
                local var_name=$(echo "$line" | cut -d'=' -f1)
                local new_password=$(openssl rand -base64 32)

                # Update the environment file
                sed -i "s/^${var_name}=your-.*/${var_name}=${new_password}/" "$ENV_FILE"
                passwords_updated=true

                print_status "$GREEN" "✅ Updated secure password for $var_name"
            fi
        done < "$ENV_FILE"

        if [[ "$passwords_updated" == "true" ]]; then
            print_status "$YELLOW" "⚠️  Passwords updated - services may need restart"
        fi
    fi

    print_status "$GREEN" "✅ Security hardening applied"
}

# Show help
show_help() {
    cat << EOF
Usage: $SCRIPT_NAME [OPTIONS]

Security Hardening Validation Script for MCP Gateway

OPTIONS:
    -c, --check          Run all security checks
    -r, --report         Generate security report only
    -a, --apply          Apply security hardening measures
    -p, --passwords      Check password security only
    -C, --containers     Check container security only
    -n, --network        Check network security only
    -e, --environment    Check environment security only
    -s, --ssl           Check SSL configuration only
    -l, --logging       Check logging security only
    -f, --file FILE      Docker compose file (default: docker-compose.production.yml)
    -h, --help          Show this help message

SECURITY CHECKS:
    password_security    - Validates password strength and configuration
    container_security   - Checks container user permissions and security
    network_security     - Validates network configuration and exposure
    volume_security      - Checks volume mounts and permissions
    environment_security - Validates environment variable security
    ssl_configuration    - Validates SSL/TLS configuration
    logging_security     - Validates logging and audit configuration
    access_control       - Validates authentication and authorization
    docker_security      - Validates Docker daemon security

EXAMPLES:
    $SCRIPT_NAME                          # Run all security checks
    $SCRIPT_NAME -r                      # Generate security report only
    $SCRIPT_NAME -a                      # Apply security hardening
    $SCRIPT_NAME -p -e -s                # Check passwords, environment, and SSL

SECURITY THRESHOLDS:
    Minimum password length: $MIN_PASSWORD_LENGTH characters
    Maximum login attempts: $MAX_LOGIN_ATTEMPTS
    Session timeout: $SESSION_TIMEOUT seconds
    Minimum SSL version: $SSL_MIN_VERSION

EOF
}

# Parse command line arguments
RUN_CHECK=false
RUN_REPORT=false
RUN_APPLY=false
RUN_PASSWORDS=false
RUN_CONTAINERS=false
RUN_NETWORK=false
RUN_ENVIRONMENT=false
RUN_SSL=false
RUN_LOGGING=false

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
        -a|--apply)
            RUN_APPLY=true
            shift
            ;;
        -p|--passwords)
            RUN_PASSWORDS=true
            shift
            ;;
        -C|--containers)
            RUN_CONTAINERS=true
            shift
            ;;
        -n|--network)
            RUN_NETWORK=true
            shift
            ;;
        -e|--environment)
            RUN_ENVIRONMENT=true
            shift
            ;;
        -s|--ssl)
            RUN_SSL=true
            shift
            ;;
        -l|--logging)
            RUN_LOGGING=true
            shift
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
    echo "🔒 MCP Gateway Security Hardening"
    echo "=================================="

    log "Starting security hardening validation"

    if [[ "$RUN_APPLY" == "true" ]]; then
        apply_security_hardening
    elif [[ "$RUN_REPORT" == "true" ]]; then
        generate_security_report > "$REPORT_FILE"
        print_status "$GREEN" "✅ Security report generated: $REPORT_FILE"
        cat "$REPORT_FILE"
    elif [[ "$RUN_PASSWORDS" == "true" ]]; then
        check_password_security "gateway" "JWT_SECRET"
        check_password_security "postgres" "POSTGRES_PASSWORD"
        check_password_security "redis" "REDIS_PASSWORD"
        check_password_security "grafana" "GRAFANA_PASSWORD"
    elif [[ "$RUN_CONTAINERS" == "true" ]]; then
        check_container_security "forge-gateway-prod" "gateway"
        check_container_security "forge-service-manager-prod" "service-manager"
        check_container_security "forge-postgres-prod" "postgres"
        check_container_security "forge-redis-prod" "redis"
        check_container_security "forge-web-admin-prod" "web-admin"
    elif [[ "$RUN_NETWORK" == "true" ]]; then
        check_network_security
    elif [[ "$RUN_ENVIRONMENT" == "true" ]]; then
        check_environment_security
    elif [[ "$RUN_SSL" == "true" ]]; then
        check_ssl_configuration
    elif [[ "$RUN_LOGGING" == "true" ]]; then
        check_logging_security
        check_access_control
    else
        # Default: run all checks
        check_password_security "gateway" "JWT_SECRET"
        check_password_security "postgres" "POSTGRES_PASSWORD"
        check_password_security "redis" "REDIS_PASSWORD"
        check_password_security "grafana" "GRAFANA_PASSWORD"

        check_container_security "forge-gateway-prod" "gateway"
        check_container_security "forge-service-manager-prod" "service-manager"
        check_container_security "forge-postgres-prod" "postgres"
        check_container_security "forge-redis-prod" "redis"
        check_container_security "forge-web-admin-prod" "web-admin"

        check_network_security
        check_volume_security
        check_environment_security
        check_ssl_configuration
        check_logging_security
        check_access_control
        check_docker_security

        # Generate summary report
        generate_security_report > "$REPORT_FILE"

        log "Security hardening validation completed"
        print_status "$GREEN" "✅ Security report generated: $REPORT_FILE"
        echo "Log file: $LOG_FILE"
    fi
}

# Trap to handle interruption
trap 'log "Security hardening interrupted"; exit 0' INT TERM

# Run main function
main "$@"
