#!/usr/bin/env bash
set -euo pipefail

# Test script for Virtual Server Lifecycle Management
# This script tests the enable/disable functionality

echo "🧪 Testing Virtual Server Lifecycle Management"
echo "============================================"

# Check if gateway is running
if ! docker compose ps gateway | grep -q "Up"; then
    echo "❌ Gateway is not running. Start it with: make start"
    exit 1
fi

echo "✅ Gateway is running"

# Test 1: List services
echo ""
echo "📋 Test 1: List services"
if make list-services; then
    echo "✅ list-services command works"
else
    echo "❌ list-services command failed"
    exit 1
fi

# Test 2: Try to disable a service
echo ""
echo "🔧 Test 2: Disable sequential-thinking service"
if make disable-server SERVICE=sequential-thinking; then
    echo "✅ disable-server command works"
else
    echo "❌ disable-server command failed"
    exit 1
fi

# Test 3: Verify service is disabled
echo ""
echo "🔍 Test 3: Verify service is disabled"
if make list-services | grep -q "sequential-thinking.*✗ No"; then
    echo "✅ Service shows as disabled"
else
    echo "❌ Service does not show as disabled"
    exit 1
fi

# Test 4: Try to enable the service
echo ""
echo "🔧 Test 4: Enable sequential-thinking service"
if make enable-server SERVICE=sequential-thinking; then
    echo "✅ enable-server command works"
else
    echo "❌ enable-server command failed"
    exit 1
fi

# Test 5: Verify service is enabled
echo ""
echo "🔍 Test 5: Verify service is enabled"
if make list-services | grep -q "sequential-thinking.*✓ Yes"; then
    echo "✅ Service shows as enabled"
else
    echo "❌ Service does not show as enabled"
    exit 1
fi

echo ""
echo "🎉 All tests passed! Virtual Server Lifecycle Management is working correctly."
echo ""
echo "📖 Usage examples:"
echo "  make list-services                    # List all services with status"
echo "  make disable-server SERVICE=name      # Disable a service"
echo "  make enable-server SERVICE=name       # Enable a service"
