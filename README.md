# Monorepo MCP Server

A monorepo structure for Model Context Protocol (MCP) servers that allows multiple servers to exist in the codebase but be started individually. This enterprise-grade implementation includes authentication, SSL/TLS, monitoring, rate limiting, and comprehensive tools.

## 🌟 Features

### 🏗️ Monorepo Architecture
- **Multiple server support** - Each server can be started independently
- **Shared core components** - Common utilities, tools, and configurations
- **Individual configurations** - Each server has its own config and startup script
- **Modular design** - Easy to add new servers or modify existing ones
- **External database services** - Proper separation of concerns with REST-based database access

### 🔒 Security
- **Token-based authentication** with HMAC verification
- **IP allowlisting** and automatic blocking after failed attempts
- **Rate limiting** (configurable requests per minute)
- **SSL/TLS support** with modern cipher suites
- **Path traversal protection** for file operations
- **Database credential isolation** in external services

### 📊 Monitoring & Observability
- **Structured JSON logging** with request tracing
- **Real-time metrics** (CPU, memory, connections, response times)
- **Health checks** with component status monitoring
- **Connection tracking** and session management
- **Database service monitoring** with retry logic and timeout handling

### ⚡ Performance
- **Async/await** throughout for maximum concurrency
- **Connection pooling** with configurable limits
- **Request timeouts** and graceful degradation
- **Resource monitoring** and alerts
- **External service integration** with proper error handling and retries

## 🏗️ Project Structure

```
monorepo_mcp/
├── core/                    # Shared core components
│   ├── __init__.py
│   ├── base_server.py      # Base MCP server class
│   ├── tools/              # Shared tools
│   │   ├── __init__.py
│   │   ├── admin_tools.py  # Admin tools (system info, metrics, etc.)
│   │   ├── file_tools.py   # File operations
│   │   └── database_tools.py # Database operations
│   ├── security.py         # Security utilities
│   ├── metrics.py          # Metrics collection
│   └── config.py           # Configuration management
├── servers/                 # Individual server implementations
│   ├── postgres_server/    # PostgreSQL MCP server
│   │   ├── __init__.py
│   │   ├── server.py       # Main server implementation
│   │   ├── config.yaml     # Server-specific config
│   │   ├── start.py        # Startup script
│   │   └── tests/          # Server-specific tests
│   ├── mysql_server/       # MySQL MCP server
│   │   ├── __init__.py
│   │   ├── server.py
│   │   ├── config.yaml
│   │   ├── start.py
│   │   └── tests/
│   └── redis_server/       # Redis MCP server
│       ├── __init__.py
│       ├── server.py
│       ├── config.yaml
│       ├── start.py
│       └── tests/
├── shared/                  # Shared resources
│   ├── templates/          # Configuration templates
│   ├── scripts/            # Utility scripts
│   └── docs/               # Documentation
├── tests/                   # Global tests
│   ├── test_core.py
│   ├── test_security.py
│   └── test_integration.py
├── requirements.txt         # Global dependencies
├── setup.py                # Package setup
└── README.md               # This file
```

## 🛠️ Available Tools

### 🔧 Admin Tools (Available in all servers)
1. **`get_system_info`** - Comprehensive system metrics and server status
2. **`echo`** - Enhanced echo with client metadata and timestamps
3. **`list_files`** - Secure file browser with permissions and metadata
4. **`read_file`** - Safe file reading with size limits and path validation
5. **`get_metrics`** - Server performance dashboard and statistics
6. **`health_check`** - Component status monitoring and health assessment

### 🗄️ Database Tools (PostgreSQL/MySQL servers)
7. **`database_health`** - Check database service health and connection
8. **`database_info`** - Get detailed database information and configuration
9. **`test_connection`** - Test database connection and connectivity
10. **`list_databases`** - List all available databases
11. **`list_schemas`** - List all schemas in the database
12. **`list_tables`** - List all tables in the database or specific schema
13. **`execute_sql`** - Execute a SQL query (read-only)
14. **`execute_write_sql`** - Execute a SQL write operation (INSERT, UPDATE, DELETE)
15. **`read_records`** - Read records from a table with pagination
16. **`read_record`** - Read a specific record by ID
17. **`create_record`** - Create a new record in a table
18. **`update_record`** - Update an existing record
19. **`delete_record`** - Delete a record from a table
20. **`upsert_record`** - Upsert (Insert or Update) a record

### 🔴 Redis Tools (Redis server)
18. **`redis_health`** - Check Redis service health and connection
19. **`redis_keys`** - List keys in Redis with pattern matching
20. **`redis_get`** - Get value for a key
21. **`redis_set`** - Set value for a key
22. **`redis_delete`** - Delete a key
23. **`redis_scan`** - Scan keys with pattern matching

## 🏗️ Database Service Architecture

The monorepo follows a proper layered architecture for database access:

```
MCP Server (Port 3001) → HTTP → Database Service (Port 8000) → Database
```

### Why This Architecture?

1. **Security**: Database credentials are isolated in the microservice
2. **Scalability**: Database service can be scaled independently
3. **Connection Management**: Connection pooling happens in the database service
4. **Language Flexibility**: Database service can be written in any language
5. **Deployment**: Each component can be deployed separately
6. **Testing**: Each layer can be tested independently

### Current Database Service

The PostgreSQL server is configured to use an external database service at:
- **URL**: `http://dev01.int.stortz.tech:8000`
- **Endpoints**: `/admin/health`, `/admin/databases`, `/query`, etc.
- **Configuration**: Set in `servers/postgres_server/config.yaml`

### Benefits

- **Proper Separation of Concerns**: MCP protocol handling vs database operations
- **Enhanced Security**: No database credentials in MCP server
- **Better Error Handling**: Dedicated error handling for database operations
- **Monitoring**: Separate monitoring for database service performance
- **Flexibility**: Easy to switch database services or add new ones

## 📋 Prerequisites

- **Python 3.8+**
- **psutil, aiohttp, PyYAML** packages (`pip install -r requirements.txt`)
- **Database services** (PostgreSQL, MySQL, Redis) as needed
- **Docker** (optional, for containerized deployment)
- **OpenSSL** (for SSL certificates)

## ⚡ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start a Specific Server

#### PostgreSQL Server
```bash
cd servers/postgres_server
python start.py
```

#### MySQL Server
```bash
cd servers/mysql_server
python start.py
```

#### Redis Server
```bash
cd servers/redis_server
python start.py
```

### 3. Configure Claude Desktop
Add to your Claude Desktop configuration file:

**Location:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%/Claude/claude_desktop_config.json`

**Configuration:**
```json
{
  "mcpServers": {
    "postgres-mcp-server": {
      "command": "python",
      "args": ["/path/to/monorepo_mcp/servers/postgres_server/start.py"],
      "env": {
        "MCP_AUTH_TOKEN": "your-auth-token-here"
      }
    },
    "mysql-mcp-server": {
      "command": "python",
      "args": ["/path/to/monorepo_mcp/servers/mysql_server/start.py"],
      "env": {
        "MCP_AUTH_TOKEN": "your-auth-token-here"
      }
    },
    "redis-mcp-server": {
      "command": "python",
      "args": ["/path/to/monorepo_mcp/servers/redis_server/start.py"],
      "env": {
        "MCP_AUTH_TOKEN": "your-auth-token-here"
      }
    }
  }
}
```

## 🧪 Testing

### Run All Tests
```bash
python -m pytest tests/
```

### Run Specific Server Tests
```bash
# PostgreSQL server tests
python -m pytest servers/postgres_server/tests/

# MySQL server tests
python -m pytest servers/mysql_server/tests/

# Redis server tests
python -m pytest servers/redis_server/tests/
```

### Run Integration Tests
```bash
python -m pytest tests/test_integration.py
```

## 🚀 Adding a New Server

1. **Create server directory** in `servers/`
2. **Copy template** from `shared/templates/server_template/`
3. **Implement server-specific logic** in `server.py`
4. **Configure** in `config.yaml`
5. **Add tests** in `tests/`
6. **Update documentation**

## 📝 Development

### Code Style
- Follow PEP 8
- Use type hints
- Add docstrings
- Write tests for new features

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
