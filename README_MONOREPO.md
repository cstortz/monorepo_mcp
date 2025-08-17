# MCP Monorepo

A true monorepo structure for MCP (Model Context Protocol) servers with shared core components and individual server instances.

## 🏗️ Architecture

This monorepo is organized into the following structure:

```
monorepo_mcp/
├── mcp_core/                 # Shared core components
│   ├── __init__.py
│   ├── config.py            # Server configuration
│   ├── logging.py           # Logging setup
│   ├── security.py          # Security management
│   ├── rate_limiter.py      # Rate limiting
│   ├── metrics.py           # Metrics collection
│   ├── session.py           # Client session management
│   └── server.py            # Base server implementation
├── mcp_database/            # Database MCP Server
│   ├── __init__.py
│   ├── tools.py             # Database tools
│   ├── server.py            # Database server implementation
│   └── __main__.py          # Entry point
├── mcp_filesystem/          # Filesystem MCP Server
│   ├── __init__.py
│   ├── tools.py             # Filesystem tools
│   ├── server.py            # Filesystem server implementation
│   └── __main__.py          # Entry point
├── config/                  # Configuration files
│   ├── database_server.yaml
│   └── filesystem_server.yaml
├── scripts/                 # Management scripts
│   ├── start_all_servers.sh
│   └── stop_all_servers.sh
├── start_database_server.py # Quick start script
├── start_filesystem_server.py # Quick start script
├── pyproject.toml           # Project configuration
└── requirements.txt         # Dependencies
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Required packages (install with `pip install -r requirements.txt`):
  - `psutil>=5.9.0`
  - `aiohttp>=3.8.0`
  - `PyYAML>=6.0`

### Starting Individual Servers

#### Database Server (Port 3003)
```bash
# Method 1: Direct script
python3 start_database_server.py

# Method 2: Module execution
python3 -m mcp_database

# Method 3: With custom config
python3 -m mcp_database --config config/database_server.yaml --port 3003
```

#### Filesystem Server (Port 3004)
```bash
# Method 1: Direct script
python3 start_filesystem_server.py

# Method 2: Module execution
python3 -m mcp_filesystem

# Method 3: With custom config
python3 -m mcp_filesystem --config config/filesystem_server.yaml --port 3004
```

### Starting All Servers

```bash
# Start all servers
./scripts/start_all_servers.sh

# Stop all servers
./scripts/stop_all_servers.sh
```

## 🔧 Configuration

### Environment Variables

- `MCP_AUTH_TOKEN`: Authentication token for server access

### Configuration Files

Each server can be configured using YAML files in the `config/` directory:

#### Database Server Configuration (`config/database_server.yaml`)
```yaml
server:
  host: "0.0.0.0"
  port: 3003
  
database:
  ws_url: "http://localhost:8000"
  
security:
  auth_enabled: true
  auth_token: "${MCP_AUTH_TOKEN}"
  
rate_limiting:
  requests_per_minute: 100
  
limits:
  max_connections: 50
```

#### Filesystem Server Configuration (`config/filesystem_server.yaml`)
```yaml
server:
  host: "0.0.0.0"
  port: 3004
  
filesystem:
  base_path: "/home/cstortz/repos"
  
security:
  auth_enabled: true
  auth_token: "${MCP_AUTH_TOKEN}"
```

## 🔌 Claude Desktop Configuration

### Database Server
```json
{
  "database-mcp-server": {
    "command": "socat",
    "args": ["TCP:dev01.int.stortz.tech:3003", "STDIO"],
    "env": {
      "MCP_AUTH_TOKEN": "6b649d2159b61bf69f0a05fd9fe03bd8ead6f8414271b69149bce3fcd1326aec"
    }
  }
}
```

### Filesystem Server
```json
{
  "filesystem-mcp-server": {
    "command": "socat",
    "args": ["TCP:dev01.int.stortz.tech:3004", "STDIO"],
    "env": {
      "MCP_AUTH_TOKEN": "6b649d2159b61bf69f0a05fd9fe03bd8ead6f8414271b69149bce3fcd1326aec"
    }
  }
}
```

## 🛠️ Development

### Adding a New Server

1. Create a new package in the monorepo:
   ```bash
   mkdir mcp_newserver
   touch mcp_newserver/__init__.py
   ```

2. Create the tools module (`mcp_newserver/tools.py`):
   ```python
   class NewServerTools:
       def __init__(self, config):
           self.config = config
       
       async def some_tool(self, **kwargs):
           # Tool implementation
           pass
   ```

3. Create the server implementation (`mcp_newserver/server.py`):
   ```python
   from mcp_core import BaseMCPServer
   from .tools import NewServerTools
   
   class NewServerMCPServer(BaseMCPServer):
       def __init__(self, config):
           super().__init__(config)
           self.tools_instance = NewServerTools(config)
           self.tools = self._initialize_tools()
       
       def _initialize_tools(self):
           return {
               "some_tool": {
                   "name": "some_tool",
                   "description": "Description of the tool",
                   "inputSchema": {
                       "type": "object",
                       "properties": {},
                       "required": []
                   }
               }
           }
   ```

4. Create the entry point (`mcp_newserver/__main__.py`):
   ```python
   import asyncio
   from mcp_core import ServerConfig, setup_logging
   from .server import NewServerMCPServer
   
   async def main():
       config = ServerConfig(port=3005)
       server = NewServerMCPServer(config)
       await server.start_server()
   
   if __name__ == "__main__":
       asyncio.run(main())
   ```

### Testing

```bash
# Test database server
python3 -m mcp_database --port 3003

# Test filesystem server
python3 -m mcp_filesystem --port 3004

# Test with custom configuration
python3 -m mcp_database --config config/database_server.yaml
```

## 📊 Monitoring

### Logs

- Database Server: `database_mcp_server.log`
- Filesystem Server: `filesystem_mcp_server.log`

### Metrics

Each server provides metrics through the `get_metrics` tool:
- Request counts
- Error rates
- Response times
- System resource usage

### Health Checks

Use the `health_check` tool to verify server status:
```bash
# Check database server health
curl -X POST http://localhost:3003/health

# Check filesystem server health
curl -X POST http://localhost:3004/health
```

## 🔒 Security

### Authentication

All servers support Bearer token authentication:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:3003/tools/list
```

### Rate Limiting

- Default: 100 requests per minute per IP
- Configurable per server

### IP Filtering

Configure allowed IP ranges in the configuration files:
```yaml
security:
  allowed_ips:
    - "192.168.1.0/24"
    - "10.0.0.0/8"
```

## 🚀 Deployment

### Production Deployment

1. Set environment variables:
   ```bash
   export MCP_AUTH_TOKEN="your-secure-token"
   ```

2. Start servers with proper configuration:
   ```bash
   python3 -m mcp_database --config config/database_server.yaml
   python3 -m mcp_filesystem --config config/filesystem_server.yaml
   ```

3. Use systemd services for automatic startup:
   ```bash
   sudo cp production-mcp-server.service /etc/systemd/system/
   sudo systemctl enable production-mcp-server
   sudo systemctl start production-mcp-server
   ```

### Docker Deployment

```dockerfile
FROM python:3.8-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

EXPOSE 3003 3004

CMD ["./scripts/start_all_servers.sh"]
```

## 📝 API Reference

### Common Tools (All Servers)

- `get_system_info`: Get system information
- `echo`: Echo back a message
- `get_metrics`: Get server metrics
- `health_check`: Perform health check

### Database Server Tools

- `database_health`: Check database connection
- `list_databases`: List available databases
- `list_schemas`: List database schemas
- `list_tables`: List tables in schema
- `execute_sql`: Execute read-only SQL
- `execute_write_sql`: Execute write SQL
- `read_records`: Read records from table
- `create_record`: Create new record
- `update_record`: Update existing record
- `delete_record`: Delete record

### Filesystem Server Tools

- `list_files`: List files in directory
- `read_file`: Read file contents
- `write_file`: Write content to file
- `create_directory`: Create directory
- `delete_file`: Delete file/directory
- `get_file_info`: Get file information
- `search_files`: Search for files

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.


