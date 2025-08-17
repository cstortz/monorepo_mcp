#!/bin/bash

# Run PostgreSQL MCP Server

set -e

echo "🚀 Starting PostgreSQL MCP Server"
echo "================================"

cd docker/mcp_postgres

# Build if image doesn't exist
if ! docker image inspect postgres-mcp:latest >/dev/null 2>&1; then
    echo "📦 Building PostgreSQL MCP Server image..."
    docker build -t postgres-mcp:latest -f Dockerfile ../..
fi

# Run the container
echo "▶️  Starting PostgreSQL MCP Server..."
docker compose up -d

echo "✅ PostgreSQL MCP Server started!"
echo "🔗 Server available at: http://localhost:3003"
echo ""
echo "📊 Container status:"
docker compose ps
