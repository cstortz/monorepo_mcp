#!/bin/bash
set -e

echo "Building REST API MCP Docker image..."

# Build the Docker image
docker build -f docker/mcp_rest_api/Dockerfile -t rest-api-mcp:latest .

echo "✅ REST API MCP image built successfully!"
echo "Image: rest-api-mcp:latest"
