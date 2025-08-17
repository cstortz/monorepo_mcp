#!/bin/bash

# Test script for Database MCP Server
# This script tests the basic functionality of the database MCP server

set -e

echo "🧪 Testing Database MCP Server..."

# Check if database_ws is running
echo "📡 Checking database_ws microservice..."
if curl -s http://localhost:8000/admin/health > /dev/null; then
    echo "✅ database_ws is running"
else
    echo "❌ database_ws is not running on localhost:8000"
    echo "Please start the database_ws microservice first"
    exit 1
fi

# Check if MCP server is running
echo "🔍 Checking MCP server..."
if curl -s http://localhost:3003 > /dev/null 2>&1; then
    echo "✅ MCP server is running on port 3003"
else
    echo "⚠️  MCP server not detected on port 3003"
    echo "You may need to start it manually:"
    echo "python3 production_mcp_server.py --config config.yaml"
fi

echo ""
echo "🎯 Database MCP Server Setup Complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Configure Claude Desktop to connect to the MCP server"
echo "2. Use database tools like:"
echo "   - database_health"
echo "   - list_databases"
echo "   - list_schemas"
echo "   - execute_sql"
echo "   - read_records"
echo ""
echo "🔧 Configuration file: config.yaml"
echo "🌐 Server port: 3003"
echo "🗄️ Database service: localhost:8000"
