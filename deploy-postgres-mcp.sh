#!/bin/bash
set -euo pipefail

echo "🚀 Starting PostgreSQL MCP Server Deployment"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.template .env
    echo "⚠️  Please edit .env file with your configuration before running again"
    exit 1
fi

# Build the image
echo "📦 Building Docker image..."
docker build -t postgres-mcp:latest .

# Stop existing container if running
echo "🛑 Stopping existing container..."
docker compose down || true

# Start the container
echo "▶️  Starting PostgreSQL MCP Server..."
docker compose up -d

# Wait for container to be healthy
echo "⏳ Waiting for container to be healthy..."
timeout=60
counter=0
while [ $counter -lt $timeout ]; do
    if docker compose ps | grep -q "healthy"; then
        echo "✅ Container is healthy!"
        break
    fi
    sleep 2
    counter=$((counter + 2))
done

if [ $counter -eq $timeout ]; then
    echo "❌ Container failed to become healthy within $timeout seconds"
    echo "📝 Container logs:"
    docker compose logs
    exit 1
fi

echo "🎉 PostgreSQL MCP Server deployed successfully!"
echo "🔗 Server should be available at: http://localhost:3003"
echo ""
echo "📊 Container status:"
docker compose ps
