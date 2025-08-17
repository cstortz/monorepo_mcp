# MCP Server Bootstrap Prompt

You are tasked with creating a new Model Context Protocol (MCP) server from scratch. This server should be designed to run in a Docker container and integrate seamlessly with Claude Desktop.

## Requirements

Create a new MCP server with the following specifications:

**Server Name:** `mcp_[service_name]` (replace `[service_name]` with the actual service name)
**Port:** `300[X]` (assign the next available port)
**Purpose:** [Describe the specific purpose/functionality of this server]

## File Structure

Create the following directory structure:

```
monorepo_mcp/
├── src/
│   └── mcp_[service_name]/
│       ├── __init__.py
│       ├── __main__.py
│       ├── server.py
│       ├── tools.py
│       └── README.md
├── docker/
│   └── mcp_[service_name]/
│       ├── Dockerfile
│       ├── docker-compose.yml
│       ├── .dockerignore
│       └── .env.template
├── scripts/
│   ├── build-[service_name]-mcp.sh
│   ├── run-[service_name]-mcp.sh
│   └── deploy-[service_name]-mcp.sh
└── docker-compose.all.yml (update existing)
```

## Implementation Details

### 1. Core Server Files

**`src/mcp_[service_name]/__init__.py`:**
- Define the module with proper imports
- Export the main server class
- Include `__all__` list

**`src/mcp_[service_name]/__main__.py`:**
- Entry point for running the server as a module
- Include argument parsing for host, port, log level, and auth
- Support for `--no-auth` flag for development

**`src/mcp_[service_name]/server.py`:**
- Implement the main MCP server class `[ServiceName]MCPServer`
- Handle JSON-RPC protocol (version 2025-06-18)
- Implement proper request/response handling
- Include error handling for notifications (no response for `request_id: None`)
- Support authentication with configurable token
- Include proper logging

**`src/mcp_[service_name]/tools.py`:**
- Implement the tools class `[ServiceName]Tools`
- Define specific tools for the service functionality
- Include proper error handling and validation
- Support async operations where needed

### 2. Docker Configuration

**`docker/mcp_[service_name]/Dockerfile`:**
```dockerfile
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r mcpuser && useradd -r -g mcpuser mcpuser

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Switch to non-root user
USER mcpuser

# Expose port
EXPOSE 300[X]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import socket; socket.create_connection(('localhost', 300[X]), timeout=5)" || exit 1

# Run the server
CMD ["python", "-m", "mcp_[service_name]", "--host", "0.0.0.0", "--port", "300[X]", "--log-level", "INFO"]
```

**`docker/mcp_[service_name]/docker-compose.yml`:**
```yaml
version: '3.8'

services:
  [service-name]-mcp:
    build:
      context: ../..
      dockerfile: docker/mcp_[service_name]/Dockerfile
    container_name: [service-name]-mcp-server
    ports:
      - "300[X]:300[X]"
    environment:
      - MCP_AUTH_TOKEN=${MCP_AUTH_TOKEN:-}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - MCP_PORT=300[X]
    env_file:
      - .env
    volumes:
      - ../../src:/app/src:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import socket; socket.create_connection(('localhost', 300[X]), timeout=5)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
```

**`docker/mcp_[service_name]/.dockerignore`:**
```
.git
.gitignore
README.md
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
.env
.venv/
pip-log.txt
pip-delete-this-directory.txt
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.pytest_cache/
.mypy_cache/
.dmypy.json
dmypy.json
tests/
test_*
*_test.py
```

**`docker/mcp_[service_name]/.env.template`:**
```env
# MCP Server Configuration
MCP_AUTH_TOKEN=your_auth_token_here
LOG_LEVEL=INFO
MCP_PORT=300[X]

# Service-specific environment variables
# Add any additional environment variables needed for your service
```

### 3. Management Scripts

**`scripts/build-[service-name]-mcp.sh`:**
```bash
#!/bin/bash
set -e

echo "Building [Service Name] MCP Docker image..."

# Build the Docker image
docker build -f docker/mcp_[service_name]/Dockerfile -t [service-name]-mcp:latest .

echo "✅ [Service Name] MCP image built successfully!"
echo "Image: [service-name]-mcp:latest"
```

**`scripts/run-[service-name]-mcp.sh`:**
```bash
#!/bin/bash
set -e

echo "Starting [Service Name] MCP server..."

# Check if .env file exists
if [ ! -f "docker/mcp_[service_name]/.env" ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp docker/mcp_[service_name]/.env.template docker/mcp_[service_name]/.env
    echo "📝 Please edit docker/mcp_[service_name]/.env with your configuration"
fi

# Start the container
cd docker/mcp_[service_name]
docker-compose up -d

echo "✅ [Service Name] MCP server started!"
echo "🌐 Server running on port 300[X]"
echo "📊 Health check: http://localhost:300[X]/health"
echo "📝 Logs: docker-compose logs -f"
```

**`scripts/deploy-[service-name]-mcp.sh`:**
```bash
#!/bin/bash
set -e

echo "Deploying [Service Name] MCP server..."

# Build and deploy
./scripts/build-[service-name]-mcp.sh
./scripts/run-[service-name]-mcp.sh

# Wait for health check
echo "⏳ Waiting for server to be healthy..."
for i in {1..30}; do
    if curl -f http://localhost:300[X]/health >/dev/null 2>&1; then
        echo "✅ Server is healthy!"
        break
    fi
    echo "⏳ Waiting... ($i/30)"
    sleep 2
done

echo "🎉 [Service Name] MCP server deployed successfully!"
```

### 4. Update Master Docker Compose

Update `docker-compose.all.yml` to include the new service:

```yaml
# Add this service to the existing docker-compose.all.yml
[service-name]-mcp:
  build:
    context: .
    dockerfile: docker/mcp_[service_name]/Dockerfile
  container_name: [service-name]-mcp-server
  ports:
    - "300[X]:300[X]"
  environment:
    - MCP_AUTH_TOKEN=${MCP_AUTH_TOKEN:-}
    - LOG_LEVEL=${LOG_LEVEL:-INFO}
    - MCP_PORT=300[X]
  env_file:
    - docker/mcp_[service_name]/.env
  volumes:
    - ./src:/app/src:ro
  restart: unless-stopped
  healthcheck:
    test: ["CMD", "python", "-c", "import socket; socket.create_connection(('localhost', 300[X]), timeout=5)"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 5s
  deploy:
    resources:
      limits:
        memory: 512M
        cpus: '0.5'
      reservations:
        memory: 256M
        cpus: '0.25'
```

### 5. Update Management Scripts

Update the following scripts to include the new service:

**`scripts/build-all-servers.sh`:**
```bash
# Add this line to the existing script
./scripts/build-[service-name]-mcp.sh
```

**`scripts/run-all-servers.sh`:**
```bash
# Add this line to the existing script
./scripts/run-[service-name]-mcp.sh
```

**`scripts/stop-all-servers.sh`:**
```bash
# Add this line to the existing script
docker stop [service-name]-mcp-server || true
```

### 6. Update Documentation

**`src/mcp_[service_name]/README.md`:**
```markdown
# [Service Name] MCP Server

## Description
[Describe what this MCP server does and what tools it provides]

## Tools
- `[tool_name]`: [Description of the tool and its parameters]

## Configuration
- `MCP_AUTH_TOKEN`: Authentication token for the server
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `MCP_PORT`: Port number for the server

## Usage

### Local Development
```bash
# Activate virtual environment
source venv/bin/activate

# Run server
python -m mcp_[service_name] --host 0.0.0.0 --port 300[X] --log-level INFO --no-auth
```

### Docker
```bash
# Build and run
./scripts/build-[service-name]-mcp.sh
./scripts/run-[service-name]-mcp.sh

# Or deploy all servers
./scripts/run-all-servers.sh
```

## Claude Desktop Configuration
Add this to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "[service-name]-mcp": {
      "command": "socat",
      "args": ["-", "TCP:localhost:300[X]"],
      "env": {}
    }
  }
}
```

## Architecture
[Describe the architecture and how it integrates with other services]
```

### 7. Requirements

Create or update `requirements.txt` to include necessary dependencies:

```txt
# Add any specific dependencies needed for your service
aiohttp>=3.8.0
pydantic>=2.0.0
# Add other dependencies as needed
```

## Implementation Checklist

- [ ] Create all directory structures
- [ ] Implement core server files (`__init__.py`, `__main__.py`, `server.py`, `tools.py`)
- [ ] Create Docker configuration files
- [ ] Create management scripts
- [ ] Update master docker-compose file
- [ ] Update existing management scripts
- [ ] Create comprehensive README
- [ ] Test server startup and basic functionality
- [ ] Test Docker build and run
- [ ] Verify Claude Desktop integration
- [ ] Update documentation

## Testing

After implementation, test the following:

1. **Local Development:**
   ```bash
   python -m mcp_[service_name] --host 0.0.0.0 --port 300[X] --log-level INFO --no-auth
   ```

2. **Docker Build:**
   ```bash
   ./scripts/build-[service-name]-mcp.sh
   ```

3. **Docker Run:**
   ```bash
   ./scripts/run-[service-name]-mcp.sh
   ```

4. **Health Check:**
   ```bash
   curl http://localhost:300[X]/health
   ```

5. **Claude Desktop Integration:**
   - Add the server configuration to Claude Desktop
   - Test tool execution
   - Verify proper JSON-RPC communication

## Notes

- Ensure all JSON-RPC responses follow the protocol specification
- Handle notifications properly (no response for `request_id: None`)
- Include proper error handling and logging
- Follow security best practices (non-root user in Docker, environment variables)
- Make scripts executable: `chmod +x scripts/*.sh`
- Test thoroughly before committing

This prompt provides a complete template for bootstrapping any new MCP server with Docker support and proper integration with the existing monorepo structure.
