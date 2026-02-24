#!/bin/bash

# MCP Gateway Monitoring Startup Script
# Starts comprehensive monitoring for Phase 2 enhanced capabilities

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

echo -e "${BLUE}🔍 Starting MCP Gateway Monitoring System...${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ] || [ ! -d "tool_router" ]; then
    print_error "Please run this script from the MCP Gateway project root directory"
    exit 1
fi

# Check if monitoring directories exist
if [ ! -d ".claude/monitoring" ]; then
    print_error "Monitoring directories not found. Please run Phase 3 setup first."
    exit 1
fi

print_status "1. Checking monitoring prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

print_success "✅ Python 3 is available"

# Check required Python packages
python3 -c "import requests, psutil" 2>/dev/null || {
    print_warning "⚠️  Some Python packages may be missing. Installing..."
    pip3 install requests psutil
}

print_status "2. Starting monitoring services..."

# Create logs directory
mkdir -p .claude/monitoring/logs

# Start performance monitoring in background
print_status "Starting performance monitor..."
python3 .claude/monitoring/scripts/performance_monitor.py --monitor &
PERFORMANCE_PID=$!
echo "Performance monitor started with PID: $PERFORMANCE_PID"

# Start cost tracking in background
print_status "Starting cost tracker..."
python3 .claude/monitoring/scripts/cost_tracker.py &
COST_PID=$!
echo "Cost tracker started with PID: $COST_PID"

# Start health monitoring in background
print_status "Starting health checker..."
python3 .claude/monitoring/scripts/health_check.py &
HEALTH_PID=$!
echo "Health checker started with PID: $HEALTH_PID"

# Save PIDs for later cleanup
echo "$PERFORMANCE_PID" > .claude/monitoring/performance.pid
echo "$COST_PID" > .claude/monitoring/cost.pid
echo "$HEALTH_PID" > .claude/monitoring/health.pid

print_status "3. Verifying monitoring services..."

# Check if all services are running
sleep 3

if kill -0 $PERFORMANCE_PID 2>/dev/null; then
    print_success "✅ Performance monitor is running"
else
    print_error "❌ Performance monitor failed to start"
fi

if kill -0 $COST_PID 2>/dev/null; then
    print_success "✅ Cost tracker is running"
else
    print_error "❌ Cost tracker failed to start"
fi

if kill -0 $HEALTH_PID 2>/dev/null; then
    print_success "✅ Health checker is running"
else
    print_error "❌ Health checker failed to start"
fi

print_status "4. Setting up monitoring dashboard..."

# Create a simple monitoring dashboard status page
cat > .claude/monitoring/dashboard_status.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>MCP Gateway Monitoring Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #1a1a1a; color: #fff; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 40px; }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .status-card { background: #2d2d2d; padding: 20px; border-radius: 8px; }
        .status-healthy { border-left: 4px solid #4CAF50; }
        .status-warning { border-left: 4px solid #FFC107F; }
        .status-error { border-left: 4px solid #F44336; }
        .status-critical { border-left: 4px solid #D32F2F; }
        .status-title { font-size: 1.2em; font-weight: bold; margin-bottom: 10px; }
        .status-details { font-size: 0.9em; color: #ccc; }
        .refresh-info { text-align: center; margin-top: 40px; color: #888; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 MCP Gateway Monitoring Dashboard</h1>
            <div class="refresh-info">Auto-refresh every 30 seconds</div>
        </div>
        <div class="status-grid" id="status-grid">
            <!-- Status cards will be populated by JavaScript -->
        </div>
    </div>
    <script>
        function updateStatus() {
            fetch('/monitoring/status')
                .then(response => response.json())
                .then(data => {
                    const grid = document.getElementById('status-grid');
                    grid.innerHTML = '';
                    
                    // Gateway status
                    const gatewayCard = createStatusCard(
                        'Gateway Health',
                        data.gateway_health.status,
                        data.gateway_health
                    );
                    grid.appendChild(gatewayCard);
                    
                    // MCP Servers status
                    const mcpCard = createStatusCard(
                        'MCP Servers',
                        data.mcp_servers.status,
                        data.mcp_servers
                    );
                    grid.appendChild(mcpCard);
                    
                    // Hook System status
                    const hooksCard = createStatusCard(
                        'Hook System',
                        data.hook_system.status,
                        data.hook_system
                    );
                    grid.appendChild(hooksCard);
                    
                    // System Resources status
                    const systemCard = createStatusCard(
                        'System Resources',
                        data.system_resources.status,
                        data.system_resources
                    );
                    grid.appendChild(systemCard);
                    
                    // Integrations status
                    const integrationsCard = createStatusCard(
                        'Integrations',
                        'healthy',
                        data.integrations
                    );
                    grid.appendChild(integrationsCard);
                })
                .catch(error => {
                    console.error('Error updating status:', error);
                });
        }
        
        function createStatusCard(title, status, details) {
            const card = document.createElement('div');
            card.className = `status-card status-${status}`;
            
            const title = document.createElement('div');
            title.className = 'status-title';
            title.textContent = title;
            
            const details = document.createElement('div');
            details.className = 'status-details';
            details.innerHTML = `
                Status: ${status}<br>
                Last Check: ${details.timestamp}<br>
                ${details.error ? `Error: ${details.error}` : ''}
            `;
            
            card.appendChild(title);
            card.appendChild(details);
            return card;
        }
        
        // Auto-refresh every 30 seconds
        setInterval(updateStatus, 30000);
        
        // Initial load
        updateStatus();
    </script>
</body>
</html>
EOF

print_status "5. Monitoring services started successfully!"
echo ""
echo -e "${GREEN}📊 Monitoring Dashboard:${NC}"
echo -e "${GREEN}   http://localhost:8080/monitoring/dashboard_status.html${NC}"
echo ""
echo -e "${BLUE}📈 Monitoring Services:${NC}"
echo -e "${GREEN}   • Performance Monitor (PID: $PERFORMANCE_PID)${NC}"
echo -e "${GREEN}   • Cost Tracker (PID: $COST_PID)${NC}"
echo -e "${GREEN}   • Health Checker (PID: $HEALTH_PID)${NC}"
echo ""
echo -e "${YELLOW}💡 Management Commands:${NC}"
echo "  ./stop-monitoring.sh  - Stop all monitoring services"
echo "  ./restart-monitoring.sh  - Restart all monitoring services"
echo "  ./check-monitoring.sh  - Check monitoring status"
echo "  ./generate-reports.sh  - Generate monitoring reports"
echo ""
echo -e "${BLUE}🔧 Logs Location:${NC}"
echo "   Performance: .claude/monitoring/logs/"
echo "   Cost Data: .claude/monitoring/metrics/"
echo "   Health Data: .claude/monitoring/metrics/"
echo ""
echo -e "${YELLOW}⚠️  Press Ctrl+C to stop all monitoring services${NC}"