#!/bin/bash
set -e

echo "Deploying REST API MCP server..."

# Build and deploy
./scripts/build-rest-api-mcp.sh
./scripts/run-rest-api-mcp.sh

# Wait for health check
echo "⏳ Waiting for server to be healthy..."
for i in {1..30}; do
    if curl -f http://localhost:3004/health >/dev/null 2>&1; then
        echo "✅ Server is healthy!"
        break
    fi
    echo "⏳ Waiting... ($i/30)"
    sleep 2
done

echo "🎉 REST API MCP server deployed successfully!"
