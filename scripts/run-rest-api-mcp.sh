#!/bin/bash
set -e

echo "Starting REST API MCP server..."

# Check if .env file exists
if [ ! -f "docker/mcp_rest_api/.env" ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp docker/mcp_rest_api/env.template docker/mcp_rest_api/.env
    echo "📝 Please edit docker/mcp_rest_api/.env with your configuration"
fi

# Start the container
cd docker/mcp_rest_api
docker compose up -d

echo "✅ REST API MCP server started!"
echo "🌐 Server running on port 3004"
echo "📊 Health check: http://localhost:3004/health"
echo "📝 Logs: docker compose logs -f"
