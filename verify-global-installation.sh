#!/bin/bash

# Verify Global Claude Code Installation
# This script verifies that all global scripts are properly installed and working

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

echo -e "${BLUE}🔍 Verifying Global Claude Code Installation...${NC}"
echo ""

# Test if scripts are in PATH
test_script_in_path() {
    local script="$1"
    if command -v "$script" &> /dev/null; then
        print_success "✅ $script is in PATH"
        return 0
    else
        print_error "❌ $script is NOT in PATH"
        return 1
    fi
}

# Test script execution
test_script_execution() {
    local script="$1"
    local test_args="$2"

    if command -v "$script" &> /dev/null; then
        echo "Testing $script..."
        if [ -n "$test_args" ]; then
            "$script" "$test_args" > /dev/null 2>&1
        else
            "$script" --help > /dev/null 2>&1 || "$script" help > /dev/null 2>&1
        fi

        if [ $? -eq 0 ]; then
            print_success "✅ $script executes successfully"
            return 0
        else
            print_error "❌ $script failed to execute"
            return 1
        fi
    else
        print_error "❌ $script not found"
        return 1
    fi
}

print_status "1. Checking PATH availability..."

# Test core scripts
core_scripts=(
    "claude-code-manager"
    "claude-code-setup"
    "claude-code-verify"
    "claude-code-ui"
    "claude-code-monitor"
)

echo "Core Scripts:"
for script in "${core_scripts[@]}"; do
    test_script_in_path "$script"
done

print_status "2. Checking monitoring scripts..."

# Test monitoring scripts
monitoring_scripts=(
    "claude-code-performance"
    "claude-code-cost-tracker"
    "claude-code-health-check"
)

echo "Monitoring Scripts:"
for script in "${monitoring_scripts[@]}"; do
    test_script_in_path "$script"
done

print_status "3. Testing script execution..."

# Test a few key scripts
echo "Testing Core Scripts:"
test_script_execution "claude-code-manager" "help"
test_script_execution "claude-code-verify"

echo "Testing Monitoring Scripts:"
test_script_execution "claude-code-health-check"

print_status "4. Checking installation directories..."

# Check installation directories
if [ -d "$HOME/.local/bin" ]; then
    script_count=$(find "$HOME/.local/bin" -name "claude-code-*" -type f | wc -l)
    print_success "✅ Installation directory exists: $HOME/.local/bin"
    print_success "✅ Found $script_count Claude Code scripts"
else
    print_error "❌ Installation directory not found: $HOME/.local/bin"
fi

if [ -d "$HOME/.local/bin/claude-code-monitoring-scripts" ]; then
    python_script_count=$(find "$HOME/.local/bin/claude-code-monitoring-scripts" -name "*.py" -type f | wc -l)
    print_success "✅ Monitoring scripts directory exists"
    print_success "✅ Found $python_script_count Python monitoring scripts"
else
    print_error "❌ Monitoring scripts directory not found"
fi

print_status "5. Checking configuration files..."

# Check Claude Code configuration
if [ -d "$HOME/.claude" ]; then
    print_success "✅ Claude Code configuration directory exists"

    if [ -f "$HOME/.claude/CLAUDE.md" ]; then
        print_success "✅ Main configuration file exists"
    else
        print_warning "⚠️  Main configuration file not found"
    fi

    if [ -f "$HOME/.claude/mcp.json" ]; then
        print_success "✅ MCP configuration exists"
    else
        print_warning "⚠️  MCP configuration not found"
    fi
else
    print_warning "⚠️  Claude Code configuration directory not found"
fi

print_status "6. Checking desktop shortcuts..."

# Check desktop shortcuts on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    if [ -f "$HOME/Desktop/Claude Code Manager.command" ]; then
        print_success "✅ Desktop shortcut exists"
    else
        print_warning "⚠️  Desktop shortcut not found"
    fi
fi

print_status "7. Generating verification report..."

# Count total scripts
total_core=0
total_monitoring=0
total_scripts=0

for script in "${core_scripts[@]}"; do
    if command -v "$script" &> /dev/null; then
        ((total_core++))
    fi
done

for script in "${monitoring_scripts[@]}"; do
    if command -v "$script" &> /dev/null; then
        ((total_monitoring++))
    fi
done

total_scripts=$((total_core + total_monitoring))

echo ""
echo -e "${BLUE}📊 Verification Report:${NC}"
echo "=================================="
echo ""
echo -e "${GREEN}✅ Core Scripts Available: $total_core/${#core_scripts[@]}${NC}"
echo -e "${GREEN}✅ Monitoring Scripts Available: $total_monitoring/${#monitoring_scripts[@]}${NC}"
echo -e "${GREEN}✅ Total Scripts Available: $total_scripts${NC}"
echo ""

if [ $total_scripts -eq $((${#core_scripts[@]} + ${#monitoring_scripts[@]})) ]; then
    echo -e "${GREEN}🎉 All scripts are globally available!${NC}"
    echo ""
    echo -e "${BLUE}🚀 You can now use Claude Code enhanced features from anywhere:${NC}"
    echo ""
    echo -e "${GREEN}   claude-code-manager status${NC}"
    echo -e "${GREEN}   claude-code-manager ui${NC}"
    echo -e "${GREEN}   claude-code-manager monitor${NC}"
    echo -e "${GREEN}   claude-code-performance${NC}"
    echo -e "${GREEN}   claude-code-cost-tracker${NC}"
    echo -e "${GREEN}   claude-code-health-check${NC}"
    echo ""
    exit 0
else
    echo -e "${YELLOW}⚠️  Some scripts are not available. Check the errors above.${NC}"
    echo ""
    echo -e "${BLUE}🔧 Troubleshooting:${NC}"
    echo "1. Restart your terminal or run: source ~/.config/fish/config.fish"
    echo "2. Check installation: ls -la ~/.local/bin/claude-code-*"
    echo "3. Re-run installation: ./install-claude-code-global.sh"
    echo ""
    exit 1
fi
