#!/bin/bash
# Docker Build Optimization Script for MCP Gateway
# Implements advanced BuildKit features and caching strategies

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGISTRY="${REGISTRY:-ghcr.io/ibm}"
PROJECT_NAME="mcp-gateway"
BUILDKIT_CONFIG="./docker/buildkitd.toml"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if BuildKit is available
check_buildkit() {
    print_status "Checking BuildKit availability..."

    if ! docker buildx version >/dev/null 2>&1; then
        print_error "BuildKit is not available. Please install docker-buildx-plugin."
        exit 1
    fi

    # Check if buildx builder is running
    if ! docker buildx inspect default >/dev/null 2>&1; then
        print_status "Creating BuildKit builder..."
        docker buildx create --name default --driver docker-container --config "${BUILDKIT_CONFIG}" --bootstrap
    else
        print_status "BuildKit builder already exists"
    fi

    print_success "BuildKit is ready"
}

# Function to optimize Docker build with advanced caching
build_optimized() {
    local service="${1:-tool-router}"
    local dockerfile="${2:-Dockerfile.tool-router.optimized}"
    local target="${3:-runtime}"

    print_status "Building optimized ${service} image..."

    # Build arguments for optimization
    local build_args=(
        "--build-arg" "BUILDKIT_INLINE_CACHE=1"
        "--build-arg" "PYTHONOPTIMIZE=2"
        "--build-arg" "PYTHONDONTWRITEBYTECODE=1"
    )

    # Cache configuration
    local cache_args=(
        "--cache-from" "type=registry,ref=${REGISTRY}/${PROJECT_NAME}-${service}:cache"
        "--cache-to" "type=registry,ref=${REGISTRY}/${PROJECT_NAME}-${service}:cache,mode=max"
        "--cache-from" "type=local,src=/tmp/.buildx-cache-${service}"
        "--cache-to" "type=local,dest=/tmp/.buildx-cache-${service}"
    )

    # Build command
    local build_cmd=(
        "buildx" "build"
        "--builder" "default"
        "--target" "${target}"
        "--platform" "linux/amd64,linux/arm64"
        "--tag" "${REGISTRY}/${PROJECT_NAME}-${service}:latest"
        "--tag" "${REGISTRY}/${PROJECT_NAME}-${service}:$(date +%Y%m%d-%H%M%S)"
        "${build_args[@]}"
        "${cache_args[@]}"
        "--file" "${dockerfile}"
        "."
    )

    print_status "Executing: docker ${build_cmd[*]}"

    if docker "${build_cmd[@]}" --push; then
        print_success "Successfully built and pushed ${service} image"
    else
        print_error "Failed to build ${service} image"
        return 1
    fi
}

# Function to analyze image size and layers
analyze_image() {
    local image="${1:-${REGISTRY}/${PROJECT_NAME}-tool-router:latest}"

    print_status "Analyzing image: ${image}"

    # Pull image if not present
    if ! docker image inspect "${image}" >/dev/null 2>&1; then
        print_status "Pulling image for analysis..."
        docker pull "${image}"
    fi

    # Show image size
    local size=$(docker image inspect "${image}" --format='{{.Size}}' | numfmt --to=iec)
    print_status "Image size: ${size}"

    # Show layer information if dive is available
    if command -v dive >/dev/null 2>&1; then
        print_status "Running dive analysis..."
        dive "${image}" --ci --lowestEfficiency 0.9 --highestWastedBytes 10000000
    else
        print_warning "dive not installed. Install with: brew install dive"
    fi

    # Show history
    print_status "Image layers:"
    docker history "${image}" --human --no-trunc
}

# Function to clean up build cache
cleanup_cache() {
    print_status "Cleaning up BuildKit cache..."

    # Remove old local cache
    docker buildx prune --filter type=local --force --all

    # Remove unused build cache
    docker buildx prune --force --all

    # Remove dangling images
    docker image prune --force

    print_success "Cache cleanup completed"
}

# Function to benchmark build performance
benchmark_build() {
    local service="${1:-tool-router}"
    local dockerfile="${2:-Dockerfile.tool-router}"

    print_status "Benchmarking build performance for ${service}..."

    # Build without cache first
    print_status "Cold build (no cache)..."
    local start_time=$(date +%s)

    if docker buildx build \
        --builder default \
        --no-cache \
        --file "${dockerfile}" \
        --tag "benchmark-${service}:cold" \
        "." >/dev/null 2>&1; then
        local cold_time=$(($(date +%s) - start_time))
        print_success "Cold build completed in ${cold_time}s"
    else
        print_error "Cold build failed"
        return 1
    fi

    # Build with cache
    print_status "Warm build (with cache)..."
    start_time=$(date +%s)

    if docker buildx build \
        --builder default \
        --file "${dockerfile}" \
        --tag "benchmark-${service}:warm" \
        "." >/dev/null 2>&1; then
        local warm_time=$(($(date +%s) - start_time))
        print_success "Warm build completed in ${warm_time}s"

        # Calculate improvement
        if [ "${cold_time}" -gt 0 ]; then
            local improvement=$(( (cold_time - warm_time) * 100 / cold_time ))
            print_status "Cache improvement: ${improvement}% faster"
        fi
    else
        print_error "Warm build failed"
        return 1
    fi

    # Cleanup benchmark images
    docker rmi "benchmark-${service}:cold" "benchmark-${service}:warm" >/dev/null 2>&1 || true
}

# Function to generate build report
generate_report() {
    local report_file="docker-build-report-$(date +%Y%m%d-%H%M%S).md"

    print_status "Generating build report: ${report_file}"

    cat > "${report_file}" << EOF
# Docker Build Optimization Report
Generated: $(date)

## Build Environment
- Docker Version: $(docker --version)
- BuildKit Version: $(docker buildx version)
- Registry: ${REGISTRY}

## Image Analysis
EOF

    # Analyze main images
    for service in tool-router gateway service-manager; do
        local image="${REGISTRY}/${PROJECT_NAME}-${service}:latest"
        if docker image inspect "${image}" >/dev/null 2>&1; then
            local size=$(docker image inspect "${image}" --format='{{.Size}}' | numfmt --to=iec)
            local layers=$(docker image inspect "${image}" --format='{{len .RootFS.Layers}}')

            cat >> "${report_file}" << EOF
### ${service}
- Size: ${size}
- Layers: ${layers}
EOF
        fi
    done

    cat >> "${report_file}" << EOF

## Optimization Recommendations
1. Use multi-stage builds to reduce image size
2. Implement proper layer caching
3. Use distroless or minimal base images
4. Optimize .dockerignore to reduce build context
5. Implement BuildKit cache mounts

## Performance Metrics
- Build context size: $(du -sh . | cut -f1)
- Cache hit rate: Check individual build logs
- Layer efficiency: Use dive tool for detailed analysis
EOF

    print_success "Report generated: ${report_file}"
}

# Main function
main() {
    local command="${1:-help}"

    case "${command}" in
        "build")
            check_buildkit
            build_optimized "${2:-tool-router}" "${3:-Dockerfile.tool-router.optimized}" "${4:-runtime}"
            ;;
        "analyze")
            analyze_image "${2:-${REGISTRY}/${PROJECT_NAME}-tool-router:latest}"
            ;;
        "cleanup")
            cleanup_cache
            ;;
        "benchmark")
            check_buildkit
            benchmark_build "${2:-tool-router}" "${3:-Dockerfile.tool-router}"
            ;;
        "report")
            generate_report
            ;;
        "all")
            check_buildkit
            build_optimized "tool-router" "Dockerfile.tool-router.optimized" "runtime"
            build_optimized "gateway" "Dockerfile.gateway" "production"
            analyze_image "${REGISTRY}/${PROJECT_NAME}-tool-router:latest"
            generate_report
            ;;
        "help"|*)
            cat << EOF
Docker Build Optimization Script for MCP Gateway

Usage: $0 <command> [options]

Commands:
  build [service] [dockerfile] [target]  Build optimized image with advanced caching
  analyze [image]                   Analyze image size and layers
  cleanup                           Clean up build cache
  benchmark [service] [dockerfile]  Benchmark build performance
  report                           Generate build optimization report
  all                              Run complete optimization pipeline
  help                             Show this help message

Examples:
  $0 build tool-router Dockerfile.tool-router.optimized runtime
  $0 analyze ghcr.io/ibm/mcp-gateway-tool-router:latest
  $0 benchmark tool-router Dockerfile.tool-router
  $0 cleanup
  $0 report
  $0 all

Environment Variables:
  REGISTRY    Container registry (default: ghcr.io/ibm)
EOF
            ;;
    esac
}

# Run main function with all arguments
main "$@"
