# Database MCP Server

A production-ready Model Context Protocol (MCP) server that provides database access through Claude Desktop. This enterprise-grade implementation includes authentication, SSL/TLS, monitoring, rate limiting, and comprehensive database operations through integration with the database_ws microservice.

## 🌟 Features

### 🔒 Security
- **Token-based authentication** with HMAC verification
- **IP allowlisting** and automatic blocking after failed attempts
- **Rate limiting** (configurable requests per minute)
- **SSL/TLS support** with modern cipher suites
- **Path traversal protection** for file operations
- **Security headers** via Nginx reverse proxy

### 📊 Monitoring & Observability
- **Structured JSON logging** with request tracing
- **Real-time metrics** (CPU, memory, connections, response times)
- **Health checks** with component status monitoring
- **Connection tracking** and session management
- **Prometheus integration** ready

### ⚡ Performance
- **Async/await** throughout for maximum concurrency
- **Connection pooling** with configurable limits
- **Request timeouts** and graceful degradation
- **Resource monitoring** and alerts

### 🛡️ Production Hardening
- **Non-root container** execution
- **Read-only filesystem** with tmpfs
- **Resource limits** (CPU/memory)
- **Graceful shutdown** handling
- **Automatic restart** policies

## 🛠️ Available Tools

### 🔧 System Tools
1. **`get_system_info`** - Comprehensive system metrics and server status
2. **`echo`** - Enhanced echo with client metadata and timestamps
3. **`list_files`** - Secure file browser with permissions and metadata
4. **`read_file`** - Safe file reading with size limits and path validation
5. **`get_metrics`** - Server performance dashboard and statistics
6. **`health_check`** - Component status monitoring and health assessment

### 🗄️ Database Tools
7. **`database_health`** - Check database service health and connection
8. **`list_databases`** - List all available databases
9. **`list_schemas`** - List all schemas in the database
10. **`list_tables`** - List all tables in the database or specific schema
11. **`execute_sql`** - Execute a SQL query (read-only)
12. **`execute_write_sql`** - Execute a SQL write operation (INSERT, UPDATE, DELETE)
13. **`read_records`** - Read records from a table with pagination
14. **`read_record`** - Read a specific record by ID
15. **`create_record`** - Create a new record in a table
16. **`update_record`** - Update an existing record
17. **`delete_record`** - Delete a record from a table

## 📋 Prerequisites

- **Python 3.8+**
- **psutil, aiohttp, PyYAML** packages (`pip install -r requirements.txt`)
- **database_ws microservice** running on localhost:8000
- **Docker** (optional, for containerized deployment)
- **OpenSSL** (for SSL certificates)
- **socat** or **netcat** (for Claude Desktop connection)

## ⚡ Quick Start

### 1. Generate Authentication Token
```bash
export MCP_AUTH_TOKEN=$(openssl rand -hex 32)
echo "MCP_AUTH_TOKEN=$MCP_AUTH_TOKEN" > .env
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Server
```bash
python3 production_mcp_server.py \
  --host 0.0.0.0 \
  --port 3003 \
  --auth-token $MCP_AUTH_TOKEN \
  --config config.yaml
```

### 4. Configure Claude Desktop
Add to your Claude Desktop configuration file:

**Location:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%/Claude/claude_desktop_config.json`

**Configuration:**
```json
{
  "mcpServers": {
    "database-mcp-server": {
      "command": "socat",
      "args": ["TCP:your-server-ip:3003", "STDIO"],
      "env": {
        "MCP_AUTH_TOKEN": "your-auth-token-here"
      }
    }
  }
}
```

## 🗄️ Database Configuration

The MCP server connects to the `database_ws` microservice to provide database access. Configure the database connection in `config.yaml`:

```yaml
database:
  ws_url: "http://localhost:8000"  # URL of the database_ws microservice
```

### Database Tools Usage Examples

#### Check Database Health
```bash
# Use the database_health tool to verify connection
```

#### List Database Structure
```bash
# List all databases
# List all schemas  
# List all tables in a schema
```

#### Execute SQL Queries
```bash
# Read-only queries
# Write operations (INSERT, UPDATE, DELETE)
```

#### CRUD Operations
```bash
# Create records
# Read records with pagination
# Update records
# Delete records
```

## 🐳 Docker Deployment

### Quick Docker Run
```bash
# Set environment
export MCP_AUTH_TOKEN=$(openssl rand -hex 32)

# Run container
docker build -f Dockerfile.production -t production-mcp-server .
docker run -d \
  --name mcp-server \
  -p 3001:3001 \
  -e MCP_AUTH_TOKEN=$MCP_AUTH_TOKEN \
  production-mcp-server
```

### Docker Compose (Recommended)
```bash
# Copy environment template
cp .env.template .env
# Edit .env with your values

# Deploy with SSL and Nginx
docker-compose -f docker-compose.production.yml up -d
```

## 🔧 Configuration

### Command Line Options
```bash
python3 production_mcp_server.py --help

Options:
  --host HOST              Host to bind to (default: 0.0.0.0)
  --port PORT              Port to bind to (default: 3001)
  --ssl-cert PATH          SSL certificate file
  --ssl-key PATH           SSL private key file
  --auth-token TOKEN       Authentication token
  --no-auth                Disable authentication
  --max-connections N      Maximum connections (default: 50)
  --rate-limit N           Rate limit requests/minute (default: 100)
  --log-level LEVEL        Log level (DEBUG/INFO/WARNING/ERROR)
```

### Environment Variables
```bash
MCP_AUTH_TOKEN=your-secure-token
MCP_HOST=0.0.0.0
MCP_PORT=3001
MCP_LOG_LEVEL=INFO
MCP_SSL_CERT=/path/to/cert.pem
MCP_SSL_KEY=/path/to/key.pem
MCP_RATE_LIMIT=100
MCP_MAX_CONNECTIONS=50
```

## 🔐 SSL/TLS Setup

### Generate Self-Signed Certificate (Development)
```bash
# Create SSL directory
mkdir -p ssl

# Generate private key
openssl genrsa -out ssl/server.key 2048

# Generate certificate
openssl req -new -x509 -key ssl/server.key -out ssl/server.crt -days 365 \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=your-domain.com"
```

### Production Certificate (Let's Encrypt)
```bash
# Install certbot
sudo apt-get install certbot

# Get certificate
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/server.crt
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/server.key
```

### Claude Desktop SSL Configuration
```json
{
  "mcpServers": {
    "production-mcp-server": {
      "command": "socat",
      "args": [
        "OPENSSL:your-domain.com:3001,verify=1,cafile=/path/to/ca.crt",
        "STDIO"
      ],
      "env": {
        "MCP_AUTH_TOKEN": "your-secure-token"
      }
    }
  }
}
```

## 🚀 Production Deployment

### Systemd Service
```bash
# Copy service file
sudo cp production-mcp-server.service /etc/systemd/system/

# Create user
sudo useradd -r -s /bin/false mcpuser

# Create directories
sudo mkdir -p /opt/mcp-server/logs
sudo chown mcpuser:mcpuser /opt/mcp-server/logs

# Update service file with your paths and token
sudo nano /etc/systemd/system/production-mcp-server.service

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable production-mcp-server
sudo systemctl start production-mcp-server

# Check status
sudo systemctl status production-mcp-server
```

### Automated Deployment
```bash
chmod +x deployment.sh
./deployment.sh
```

## 📊 Monitoring

### Health Check
```bash
# Manual health check
curl -X POST http://localhost:3001 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"health_check","arguments":{}}}'

# Container health check
docker exec mcp-server python health_check.py
```

### Metrics Dashboard
Access server metrics through the `get_metrics` tool or check logs:
```bash
# View logs
tail -f /var/log/mcp-server/server.log

# Docker logs
docker logs -f mcp-server

# Systemd logs
sudo journalctl -u production-mcp-server -f
```

## 🧪 Testing

### Basic Connectivity Test
```bash
chmod +x test_production.sh
./test_production.sh your-server-ip 3001 your-auth-token
```

### Manual Testing
```bash
# Test connection
nc -z your-server-ip 3001

# Test authentication
echo '{"jsonrpc":"2.0","method":"auth","params":{"token":"your-token"}}' | nc your-server-ip 3001

# Test tool call
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_system_info","arguments":{}}}' | nc your-server-ip 3001
```

## 🔧 Customization

### Adding New Tools
1. Add tool definition to `self.tools` in `ProductionMCPServer.__init__()`
2. Implement handler method `async def _tool_your_tool_name()`
3. Add case in `handle_call_tool()` method

Example:
```python
# In __init__
"my_custom_tool": {
    "name": "my_custom_tool",
    "description": "Does something custom",
    "inputSchema": {
        "type": "object",
        "properties": {
            "param": {"type": "string", "description": "Parameter"}
        },
        "required": ["param"]
    }
}

# Handler method
async def _tool_my_custom_tool(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
    param = args.get("param", "")
    # Your logic here
    return {"content": [{"type": "text", "text": f"Result: {param}"}]}

# In handle_call_tool
elif tool_name == "my_custom_tool":
    result = await self._tool_my_custom_tool(arguments, client_session)
```

## 🛡️ Security Considerations

### Authentication
- **Always use strong tokens**: Generate with `openssl rand -hex 32`
- **Rotate tokens regularly**: Update both server and client configurations
- **Use environment variables**: Never hardcode tokens in files

### Network Security
- **Use SSL/TLS in production**: Encrypt all communications
- **Restrict IP access**: Configure `allowed_ips` for known clients
- **Use firewall rules**: Block unnecessary ports
- **Monitor failed attempts**: Check logs for suspicious activity

### File System Security
- **Path validation**: Server restricts access to working directory
- **File size limits**: Configurable maximum file sizes
- **Read-only deployment**: Use read-only containers when possible

## 🐛 Troubleshooting

### Common Issues

#### Server Won't Start
```bash
# Check port availability
sudo netstat -tlnp | grep 3001

# Check permissions
ls -la production_mcp_server.py

# Check logs
sudo journalctl -u production-mcp-server -n 50
```

#### Authentication Failures
```bash
# Verify token
echo $MCP_AUTH_TOKEN

# Check server logs
grep "Authentication failed" /var/log/mcp-server/server.log

# Test token manually
echo '{"jsonrpc":"2.0","method":"auth","params":{"token":"your-token"}}' | nc localhost 3001
```

#### Claude Desktop Connection Issues
```bash
# Test socat connectivity
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | socat - TCP:your-server:3001

# Check Claude Desktop logs (macOS)
tail -f ~/Library/Logs/Claude/claude_desktop.log

# Verify configuration syntax
python -m json.tool claude_desktop_config.json
```

#### SSL Certificate Problems
```bash
# Test SSL connection
openssl s_client -connect your-domain.com:3001

# Verify certificate
openssl x509 -in ssl/server.crt -text -noout

# Check certificate expiration
openssl x509 -in ssl/server.crt -enddate -noout
```

### Performance Issues
```bash
# Monitor resource usage
docker stats mcp-server

# Check system metrics
python3 -c "
import psutil
print(f'CPU: {psutil.cpu_percent()}%')
print(f'Memory: {psutil.virtual_memory().percent}%')
print(f'Disk: {psutil.disk_usage(\"/\").percent}%')
"

# Analyze connection patterns
grep "Client connected" /var/log/mcp-server/server.log | tail -20
```

## 📝 Configuration Updates Required

Before running in production, update these files with your specific values:

### 🔧 Required Updates

1. **`.env` file** - Copy from `.env.template` and set:
   - `MCP_AUTH_TOKEN` - Generate with `openssl rand -hex 32`
   - `MCP_HOST` - Your server IP/domain
   - SSL certificate paths (if using SSL)

2. **`nginx.conf`** - Update:
   - `server_name your-domain.com` → your actual domain
   - SSL certificate paths
   - Upstream server address if not using Docker

3. **`production-mcp-server.service`** - Update:
   - `User=mcpuser` → your service user
   - `WorkingDirectory=/opt/mcp-server` → your installation path
   - `Environment=MCP_AUTH_TOKEN=your-secure-token-here` → your token
   - SSL certificate paths

4. **`docker-compose.production.yml`** - Update:
   - Volume mounts for your data/logs/SSL directories
   - Environment variables
   - Port mappings if needed

5. **Claude Desktop config** - Update:
   - `your-server-ip` → your actual server IP/domain
   - `your-auth-token` → your actual auth token
   - SSL settings if using HTTPS

6. **`deployment.sh`** - Update:
   - `DEPLOY_DIR="/opt/mcp-server"` → your deployment path
   - User/group names
   - Service name if changed

### 🌐 Network Configuration

7. **Firewall rules**:
   ```bash
   sudo ufw allow 3001/tcp comment "MCP Server"
   sudo ufw allow 443/tcp comment "HTTPS"
   ```

8. **DNS/Domain setup** (if using SSL):
   - Point your domain to server IP
   - Configure SSL certificates
   - Update security groups/firewall rules

## 📞 Support

For issues or questions:

1. **Check logs**: `/var/log/mcp-server/server.log`
2. **Run health check**: `python health_check.py`
3. **Test connectivity**: `./test_production.sh`
4. **Verify configuration**: Check all updated files above

## 📄 License

This project is provided as-is for educational and production use. Modify according to your security and compliance requirements.