# Docker Deployment for MCP Monorepo

This document describes how to deploy the MCP servers using Docker containers. Each server can be run individually or all together.

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
        ┌─────────────────────────────────────────────┐
        │  Individual Docker Containers              │
        │  ┌─────────────┐ ┌─────────────┐           │
        │  │ postgres-mcp│ │filesystem-  │           │
        │  │ Port: 3003  │ │mcp          │           │
        │  │             │ │Port: 3005   │           │
        │  └─────────────┘ └─────────────┘           │
        └─────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  database_ws    │
                    │  REST API       │
                    │  (External)     │
                    └─────────────────┘
```

## 📁 Available Servers

### 1. PostgreSQL MCP Server (`mcp_postgres`)
- **Port**: 3003
- **Purpose**: PostgreSQL database operations
- **Tools**: Database queries, schema management, CRUD operations
- **Dependencies**: External database REST API

### 2. Filesystem MCP Server (`mcp_filesystem`)
- **Port**: 3005
- **Purpose**: File system operations
- **Tools**: File listing, reading, writing, navigation
- **Dependencies**: None (local filesystem access)

## 🚀 Quick Start

### Option 1: Run All Servers Together
```bash
# Build and run all servers
./scripts/run-all-servers.sh

# Stop all servers
./scripts/stop-all-servers.sh
```

### Option 2: Run Individual Servers
```bash
# PostgreSQL MCP Server
./scripts/run-postgres-mcp.sh

# Filesystem MCP Server
./scripts/run-filesystem-mcp.sh
```

### Option 3: Manual Docker Commands
```bash
# Build all images
./scripts/build-all-servers.sh

# Run all servers
docker compose -f docker-compose.all.yml up -d

# Run individual server
cd docker/mcp_postgres && docker compose up -d
cd docker/mcp_filesystem && docker compose up -d
```

## ⚙️ Configuration

### Environment Variables
Create a `.env` file in the root directory:
```bash
# Authentication (optional)
MCP_AUTH_TOKEN=your-auth-token-here

# Database service URL (for postgres server)
DATABASE_WS_URL=http://dev01.int.stortz.tech:8000

# Logging level
LOG_LEVEL=INFO
```

### Port Configuration
Each server runs on a different port:
- **PostgreSQL MCP**: 3003
- **Filesystem MCP**: 3005

## 🔧 Management Commands

### Start Services
```bash
# All servers
./scripts/run-all-servers.sh

# Individual servers
./scripts/run-postgres-mcp.sh
./scripts/run-filesystem-mcp.sh
```

### Stop Services
```bash
# All servers
./scripts/stop-all-servers.sh

# Individual servers
cd docker/mcp_postgres && docker compose down
cd docker/mcp_filesystem && docker compose down
```

### View Logs
```bash
# All servers
docker compose -f docker-compose.all.yml logs -f

# Individual servers
cd docker/mcp_postgres && docker compose logs -f
cd docker/mcp_filesystem && docker compose logs -f
```

### Check Status
```bash
# All servers
docker compose -f docker-compose.all.yml ps

# Individual servers
cd docker/mcp_postgres && docker compose ps
cd docker/mcp_filesystem && docker compose ps
```

## 🧪 Testing

### Health Checks
Each container includes health checks:
```bash
# Check health status
docker compose -f docker-compose.all.yml ps

# Manual health check
docker exec postgres-mcp-server python -c "import asyncio; from src.mcp_postgres.__main__ import main; asyncio.run(main())"
```

### Connection Tests
```bash
# Test PostgreSQL MCP
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0.0"}}}' | nc localhost 3003

# Test Filesystem MCP
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0.0"}}}' | nc localhost 3005
```

## 🔍 Troubleshooting

### Container Issues
```bash
# Check logs
docker compose -f docker-compose.all.yml logs [service-name]

# Check resource usage
docker stats

# Restart specific service
docker compose -f docker-compose.all.yml restart [service-name]
```

### Build Issues
```bash
# Clean build
docker system prune -f
./scripts/build-all-servers.sh

# Build specific service
docker build -t postgres-mcp:latest -f docker/mcp_postgres/Dockerfile .
```

### Network Issues
```bash
# Check network connectivity
docker network ls
docker network inspect mcp-monorepo_mcp-network

# Restart network
docker compose -f docker-compose.all.yml down
docker compose -f docker-compose.all.yml up -d
```

## 📊 Monitoring

### Resource Monitoring
```bash
# Container stats
docker stats

# Resource usage by service
docker compose -f docker-compose.all.yml top
```

### Health Monitoring
```bash
# Health status
docker compose -f docker-compose.all.yml ps

# Health check logs
docker inspect postgres-mcp-server | grep -A 5 "Health"
```

## 🔐 Security

### Non-root Users
All containers run as non-root user `mcpuser` for security.

### Network Isolation
Containers run in isolated Docker networks.

### Environment Variables
Sensitive configuration is passed via environment variables.

### Volume Mounts
Filesystem server has read-only access to `/tmp` for safety.

## 📝 Claude Desktop Configuration

For each server, you'll need a separate connection in Claude Desktop:

### PostgreSQL MCP
```json
{
  "mcpServers": {
    "postgres-mcp-server": {
      "command": "socat",
      "args": ["-", "TCP:localhost:3003"],
      "env": {}
    }
  }
}
```

### Filesystem MCP
```json
{
  "mcpServers": {
    "filesystem-mcp-server": {
      "command": "socat",
      "args": ["-", "TCP:localhost:3005"],
      "env": {}
    }
  }
}
```
