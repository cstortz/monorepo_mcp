#!/bin/bash

# Run Filesystem MCP Server

set -e

echo "🚀 Starting Filesystem MCP Server"
echo "================================"

cd docker/mcp_filesystem

# Build if image doesn't exist
if ! docker image inspect filesystem-mcp:latest >/dev/null 2>&1; then
    echo "📦 Building Filesystem MCP Server image..."
    docker build -t filesystem-mcp:latest -f Dockerfile ../..
fi

# Run the container
echo "▶️  Starting Filesystem MCP Server..."
docker compose up -d

echo "✅ Filesystem MCP Server started!"
echo "🔗 Server available at: http://localhost:3005"
echo ""
echo "📊 Container status:"
docker compose ps
