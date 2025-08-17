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
- **CRITICAL:** Use correct import paths for mcp_core:
  ```python
  from ..mcp_core import ServerConfig, setup_logging
  ```

**`src/mcp_[service_name]/server.py`:**
- Implement the main MCP server class `[ServiceName]MCPServer`
- Handle JSON-RPC protocol (version 2025-06-18)
- Implement proper request/response handling
- Include error handling for notifications (no response for `request_id: None`)
- Support authentication with configurable token
- Include proper logging
- **CRITICAL:** Use correct import paths for mcp_core:
  ```python
  from ..mcp_core import BaseMCPServer, ServerConfig, ClientSession
  ```

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
docker compose up -d

echo "✅ [Service Name] MCP server started!"
echo "🌐 Server running on port 300[X]"
echo "📊 Health check: http://localhost:300[X]/health"
echo "📝 Logs: docker compose logs -f"
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

### 8. Environment Variables and Container Networking

**CRITICAL:** When creating MCP servers that connect to external services, always use environment variables instead of hardcoded URLs.

#### **Environment Variable Configuration:**

**`src/mcp_[service_name]/tools.py`:**
```python
import os

class [ServiceName]Tools:
    def __init__(self, service_url: str = None):
        if service_url is None:
            service_url = os.getenv('[SERVICE]_URL', 'http://localhost:8000')
        self.service_url = service_url
```

**`src/mcp_[service_name]/__main__.py`:**
```python
# Command line argument (no default)
parser.add_argument('--service-url', help='Service URL (defaults to [SERVICE]_URL env var)')

# Configuration priority: CLI arg → Environment var → Config file → Default
service_url = args.service_url or os.getenv('[SERVICE]_URL') or config_data.get('service', {}).get('url', 'http://localhost:8000')
```

**`src/mcp_core/config.py`:**
```python
@dataclass
class ServerConfig:
    # ... other fields ...
    service_url: str = None  # Allow None for environment variable fallback
```

#### **Docker Environment Variables:**

**`docker/mcp_[service_name]/docker-compose.yml`:**
```yaml
services:
  [service-name]-mcp:
    environment:
      - [SERVICE]_URL=${[SERVICE]_URL:-http://localhost:8000}
      - MCP_AUTH_TOKEN=${MCP_AUTH_TOKEN:-}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
```

**`docker/mcp_[service_name]/.env.template`:**
```env
# Service-specific environment variables
[SERVICE]_URL=http://your-service-host:port
MCP_AUTH_TOKEN=your_auth_token_here
LOG_LEVEL=INFO
```

#### **Common Service URL Patterns:**
- **Database Service:** `DATABASE_WS_URL=http://database-service:8000`
- **API Service:** `API_URL=http://api-service:8080`
- **File Service:** `FILE_SERVICE_URL=http://file-service:9000`
- **Cache Service:** `CACHE_URL=http://cache-service:6379`

#### **Container Networking Considerations:**
- **Service Discovery:** Use service names instead of localhost in container networks
- **Port Mapping:** Ensure external services are accessible from containers
- **Health Checks:** Verify service connectivity before starting MCP server
- **Fallback URLs:** Always provide sensible defaults for local development

## Implementation Checklist

- [ ] Create all directory structures
- [ ] Implement core server files (`__init__.py`, `__main__.py`, `server.py`, `tools.py`)
  - [ ] **CRITICAL:** Use correct import paths (`from ..mcp_core import`)
  - [ ] **CRITICAL:** Test imports work before Docker build
- [ ] Create Docker configuration files
  - [ ] **CRITICAL:** Set correct build context (`context: ../..`)
  - [ ] **CRITICAL:** Remove obsolete `version` field
  - [ ] **CRITICAL:** Configure environment variables for external services
  - [ ] **CRITICAL:** Use service names instead of localhost in container networks
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

6. **Environment Variable Testing:**
   ```bash
   # Test environment variable usage
   docker exec [service-name]-mcp-server env | grep [SERVICE]_URL
   
   # Test service connectivity
   docker exec [service-name]-mcp-server curl -f [SERVICE_URL]/health
   
   # Verify no localhost connections in logs
   docker logs [service-name]-mcp-server | grep -i localhost
   ```

## Notes

- Ensure all JSON-RPC responses follow the protocol specification
- Handle notifications properly (no response for `request_id: None`)
- Include proper error handling and logging
- Follow security best practices (non-root user in Docker, environment variables)
- Make scripts executable: `chmod +x scripts/*.sh`
- Test thoroughly before committing

## 🚨 Common Pitfalls to Avoid

### Import Path Issues
- **❌ WRONG:** `from mcp_core import BaseMCPServer`
- **✅ CORRECT:** `from ..mcp_core import BaseMCPServer`
- **Why:** The mcp_core module is in the same src directory, so use relative imports

### Docker Build Context Issues
- **❌ WRONG:** `build: .` (in individual docker-compose.yml files)
- **✅ CORRECT:** 
  ```yaml
  build:
    context: ../..
    dockerfile: docker/mcp_[service_name]/Dockerfile
  ```
- **Why:** requirements.txt is in the root directory, not in the docker subdirectory

### Docker Compose Version Warnings
- **❌ WRONG:** Include `version: '3.8'` in docker-compose.yml
- **✅ CORRECT:** Remove version field entirely
- **Why:** The version field is obsolete in modern Docker Compose

### Module Import Errors
If you see `ModuleNotFoundError: No module named 'mcp_core'`:
1. Check that import uses relative path: `from ..mcp_core import`
2. Verify mcp_core module exists in `src/mcp_core/`
3. Ensure Docker build context is set correctly
4. Rebuild Docker image after import fixes

### Container Networking Issues
If you see connection errors to `localhost` in containerized environments:
1. **❌ WRONG:** Hardcoded `localhost:8000` in tools or config
2. **✅ CORRECT:** Use environment variables with proper fallbacks
3. **Check:** Environment variable is set in docker-compose.yml
4. **Verify:** Container can reach external services (not localhost)
5. **Test:** Rebuild image after environment variable fixes
6. **Debug:** Add logging to see what URL is being used

### Environment Variable Priority
Always follow this priority order for configuration:
1. **Command Line Arguments** (highest priority)
2. **Environment Variables** (container-friendly)
3. **Configuration Files** (fallback)
4. **Default Values** (development only)

This prompt provides a complete template for bootstrapping any new MCP server with Docker support and proper integration with the existing monorepo structure.
