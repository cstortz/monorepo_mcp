# Docker Deployment for PostgreSQL MCP Server

This document describes how to deploy the PostgreSQL MCP Server using Docker containers.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│  Claude Desktop                                    │
│  (MCP Client)                                      │
└─────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  socat          │
                    │  (TCP Proxy)    │
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  postgres-mcp   │
                    │  (Docker)       │
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  database_ws    │
                    │  REST API       │
                    │  (External)     │
                    └─────────────────┘
```

## 📁 Docker Files

### `Dockerfile`
- **Base Image**: `python:3.11-slim`
- **Security**: Non-root user (`mcpuser`)
- **Dependencies**: System packages (gcc, g++, curl)
- **Entry Point**: `src.mcp_postgres.__main__`
- **Health Check**: Tests MCP server startup

### `docker-compose.yml`
- **Service**: `postgres-mcp`
- **Environment**: Configurable via environment variables
- **Networks**: Isolated network for MCP services
- **Health Check**: Monitors container health

### `.dockerignore`
- **Excludes**: Development files, documentation, tests
- **Includes**: Core application files
- **Optimization**: Reduces build context size

## 🚀 Quick Start

### 1. Build the Image
```bash
# Using the build script
./build-postgres-mcp.sh

# Or manually
docker build -t postgres-mcp:latest .
```

### 2. Run the Container
```bash
# Using docker compose (recommended)
docker compose up -d

# Or run directly
docker run --rm -it postgres-mcp:latest
```

### 3. Test the Container
```bash
# Test basic functionality
docker run --rm -it postgres-mcp:latest python -c "import asyncio; from src.mcp_postgres.__main__ import main; asyncio.run(main())"

# Check container health
docker compose ps
```

## ⚙️ Configuration

### Environment Variables
```bash
# Copy template and edit
cp .env.template .env

# Edit .env with your settings:
MCP_AUTH_TOKEN=your-auth-token-here
DATABASE_WS_URL=http://dev01.int.stortz.tech:8000
LOG_LEVEL=INFO
```

### Docker Compose Configuration
```yaml
services:
  postgres-mcp:
    build: .
    environment:
      - MCP_AUTH_TOKEN=${MCP_AUTH_TOKEN}
      - DATABASE_WS_URL=${DATABASE_WS_URL}
      - LOG_LEVEL=${LOG_LEVEL}
    ports:
      - "3003:3003"
```

## 🚀 Production Deployment

### Using the deployment script
```bash
# First time setup
cp .env.template .env
# Edit .env with your production settings

# Deploy
./deploy-postgres-mcp.sh
```

### Manual production deployment
```bash
# Build production image
docker build -t postgres-mcp:latest .

# Run with production compose
docker compose -f docker-compose.production.yml up -d
```

## �� Management Commands

### Start the service
```bash
docker compose up -d
```

### Stop the service
```bash
docker compose down
```

### View logs
```bash
docker compose logs -f postgres-mcp
```

### Restart the service
```bash
docker compose restart postgres-mcp
```

### Update the service
```bash
docker compose down
docker build -t postgres-mcp:latest .
docker compose up -d
```

## 🧪 Testing

### Health Check
```bash
# Check if container is healthy
docker compose ps

# Manual health check
docker exec postgres-mcp-server python -c "import asyncio; from src.mcp_postgres.__main__ import main; asyncio.run(main())"
```

### Connection Test
```bash
# Test MCP server connection
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0.0"}}}' | nc localhost 3003
```

## 🔍 Troubleshooting

### Container won't start
```bash
# Check logs
docker compose logs postgres-mcp

# Check environment variables
docker compose config
```

### Health check failing
```bash
# Check if dependencies are available
docker exec postgres-mcp-server python -c "import src.mcp_postgres"

# Check if database service is reachable
docker exec postgres-mcp-server curl -f http://dev01.int.stortz.tech:8000/admin/health
```

### Performance issues
```bash
# Check resource usage
docker stats postgres-mcp-server

# Check container limits
docker inspect postgres-mcp-server | grep -A 10 "HostConfig"
```

## 📊 Monitoring

### Resource Monitoring
```bash
# CPU and memory usage
docker stats postgres-mcp-server

# Container logs
docker compose logs -f postgres-mcp
```

### Health Monitoring
```bash
# Health status
docker compose ps

# Health check logs
docker inspect postgres-mcp-server | grep -A 5 "Health"
```

## 🔐 Security

### Non-root user
The container runs as non-root user `mcpuser` for security.

### Read-only filesystem (Production)
Production deployment uses read-only filesystem with tmpfs for temporary files.

### Network isolation
Container runs in isolated Docker network.

### Environment variables
Sensitive configuration is passed via environment variables, not baked into the image.
