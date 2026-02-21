#!/bin/bash
# scripts/setup-labels.sh
# Create comprehensive labels for Forge Space MCP Gateway
set -euo pipefail

echo "🏷️  Creating labels for Forge Space MCP Gateway..."

# Phase Labels
echo "📋 Creating Phase labels..."
gh label create phase-3 --color "FBCA04" --description "Phase 3 Tool Router AI" || echo "Label phase-3 already exists"
gh label create phase-5 --color "0075CA" --description "Phase 5 Next.js Admin UI" || echo "Label phase-5 already exists"
gh label create phase-6 --color "2ECC71" --description "Phase 6 Production Optimization" || echo "Label phase-6 already exists"
gh label create phase-7 --color "E67E22" --description "Phase 7 Advanced Features" || echo "Label phase-7 already exists"
gh label create phase-8 --color "9B59B6" --description "Phase 8 Ecosystem Integration" || echo "Label phase-8 already exists"

# MCP Component Labels
echo "🔧 Creating MCP Component labels..."
gh label create mcp-server --color "0075CA" --description "MCP server implementations" || echo "Label mcp-server already exists"
gh label create mcp-tools --color "2ECC71" --description "MCP tool implementations" || echo "Label mcp-tools already exists"
gh label create mcp-gateway --color "FBCA04" --description "Gateway-specific features" || echo "Label mcp-gateway already exists"
gh label create virtual-servers --color "E67E22" --description "Virtual server management" || echo "Label virtual-servers already exists"
gh label create tool-router --color "9B59B6" --description "Tool routing functionality" || echo "Label tool-router already exists"

# Infrastructure Labels
echo "🏗️  Creating Infrastructure labels..."
gh label create docker --color "0075CA" --description "Docker and containerization" || echo "Label docker already exists"
gh label create self-hosted --color "2ECC71" --description "Self-hosted solutions" || echo "Label self-hosted already exists"
gh label create microservices --color "FBCA04" --description "Microservice architecture" || echo "Label microservices already exists"
gh label create performance --color "E67E22" --description "Performance optimizations" || echo "Label performance already exists"
gh label create monitoring --color "9B59B6" --description "Monitoring and observability" || echo "Label monitoring already exists"

# Feature Labels
echo "✨ Creating Feature labels..."
gh label create ai-enhancement --color "FF69B4" --description "AI-powered features" || echo "Label ai-enhancement already exists"
gh label create security --color "DC143C" --description "Security improvements" || echo "Label security already exists"
gh label create documentation --color "8B4513" --description "Documentation updates" || echo "Label documentation already exists"
gh label create bug-fix --color "F1C40F" --description "Bug fixes and patches" || echo "Label bug-fix already exists"
gh label create enhancement --color "3498DB" --description "Feature enhancements" || echo "Label enhancement already exists"

echo "✅ Label creation complete!"
echo ""
echo "📊 Labels created:"
echo "  Phase Labels: phase-3, phase-5, phase-6, phase-7, phase-8"
echo "  MCP Labels: mcp-server, mcp-tools, mcp-gateway, virtual-servers, tool-router"
echo "  Infrastructure: docker, self-hosted, microservices, performance, monitoring"
echo "  Feature Labels: ai-enhancement, security, documentation, bug-fix, enhancement"
echo ""
echo "📖 See .github/LABEL_TEMPLATES.md for usage guidelines"
