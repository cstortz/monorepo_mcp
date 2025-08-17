#!/bin/bash

# Stop All MCP Servers

set -e

echo "🛑 Stopping All MCP Servers"
echo "==========================="

# Stop all servers using docker compose
echo "🛑 Stopping all servers..."
docker compose -f docker-compose.all.yml down

# Also stop individual server containers if running
echo "🛑 Stopping individual server containers..."
cd docker/mcp_postgres && docker compose down 2>/dev/null || true
cd ../mcp_filesystem && docker compose down 2>/dev/null || true
cd ../..

echo "✅ All MCP Servers stopped!"
