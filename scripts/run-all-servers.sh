#!/bin/bash

# Run All MCP Servers

set -e

echo "🚀 Starting All MCP Servers"
echo "==========================="

# Build all images first
echo "📦 Building all server images..."
./scripts/build-all-servers.sh

# Run all servers using docker compose
echo "▶️  Starting all servers..."
docker compose -f docker-compose.all.yml up -d

echo "✅ All MCP Servers started!"
echo ""
echo "🔗 Servers available at:"
echo "   PostgreSQL MCP: http://localhost:3003"
echo "   REST API MCP: http://localhost:3004"
echo "   Filesystem MCP: http://localhost:3005"
echo ""
echo "📊 Container status:"
docker compose -f docker-compose.all.yml ps
