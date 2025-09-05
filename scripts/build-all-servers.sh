#!/bin/bash

# Build All MCP Servers Script

set -e

echo "🐳 Building All MCP Server Docker Images"
echo "========================================"

# Build PostgreSQL MCP Server
echo "📦 Building PostgreSQL MCP Server..."
docker build -t postgres-mcp:latest -f docker/mcp_postgres/Dockerfile .

# Build Filesystem MCP Server
echo "📦 Building Filesystem MCP Server..."
docker build -t filesystem-mcp:latest -f docker/mcp_filesystem/Dockerfile .

# Build REST API MCP Server
echo "📦 Building REST API MCP Server..."
docker build -t rest-api-mcp:latest -f docker/mcp_rest_api/Dockerfile .

echo "✅ All Docker images built successfully!"
echo ""
echo "🚀 To run all servers:"
echo "   docker compose -f docker-compose.all.yml up -d"
echo ""
echo "🔧 To run individual servers:"
echo "   cd docker/mcp_postgres && docker compose up -d"
echo "   cd docker/mcp_filesystem && docker compose up -d"
echo "   cd docker/mcp_rest_api && docker compose up -d"
