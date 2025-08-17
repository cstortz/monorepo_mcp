#!/bin/bash

HOST=${1:-localhost}
PORT=${2:-3001}
TOKEN=${3:-your-auth-token}

echo "🧪 Testing Production MCP Server at $HOST:$PORT"

# Test 1: Basic connection
echo "1️⃣  Testing connection..."
if nc -z $HOST $PORT; then
    echo "✅ Port is open"
else
    echo "❌ Cannot connect to $HOST:$PORT"
    exit 1
fi

# Test 2: Authentication (if using plain TCP)
echo "2️⃣  Testing authentication..."
echo "{\"jsonrpc\":\"2.0\",\"method\":\"auth\",\"params\":{\"token\":\"$TOKEN\"}}" | nc $HOST $PORT

echo ""

# Test 3: Initialize
echo "3️⃣  Testing initialize..."
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}' | nc $HOST $PORT

echo ""

# Test 4: List tools
echo "4️⃣  Testing list tools..."
echo '{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}' | nc $HOST $PORT

echo ""

# Test 5: Health check
echo "5️⃣  Testing health check..."
echo '{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "health_check", "arguments": {}}}' | nc $HOST $PORT

echo ""

# Test 6: Get metrics
echo "6️⃣  Testing metrics..."
echo '{"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "get_metrics", "arguments": {}}}' | nc $HOST $PORT

echo ""

# Test 7: SSL connection (if available)
if command -v openssl &> /dev/null; then
    echo "7️⃣  Testing SSL connection..."
    echo '{"jsonrpc": "2.0", "id": 5, "method": "tools/list", "params": {}}' | openssl s_client -connect $HOST:$PORT -quiet 2>/dev/null || echo "⚠️  SSL not available or not configured"
fi

echo ""
echo "🎉 Production testing complete!"