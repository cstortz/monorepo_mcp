#!/bin/bash

# PostgreSQL MCP Server Docker Build Script

set -e

echo "🐳 Building PostgreSQL MCP Server Docker Image"
echo "=============================================="

# Build the Docker image
echo "�� Building Docker image..."
docker build -t postgres-mcp:latest .

echo "✅ Docker image built successfully!"
echo ""
echo "🚀 To run the container:"
echo "   docker run --rm -it postgres-mcp:latest"
echo ""
echo "🔧 To run with docker-compose:"
echo "   docker-compose up"
echo ""
echo "🧪 To test the container:"
echo "   docker run --rm -it postgres-mcp:latest python -c 'import asyncio; from src.mcp_postgres.__main__ import main; asyncio.run(main())'"
