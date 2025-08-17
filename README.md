# MCP Monorepo

A production-ready monorepo for MCP (Model Context Protocol) servers with shared core components and specialized server instances.

## 🏗️ Architecture

This monorepo follows industry-standard practices with a clean separation of concerns:

```
mcp-monorepo/
├── src/                     # Source code
│   ├── mcp_core/           # Shared core components
│   ├── mcp_database/       # Database MCP Server
│   └── mcp_filesystem/     # Filesystem MCP Server
├── tests/                  # Test suite
├── docs/                   # Documentation
├── scripts/                # Management scripts
├── config/                 # Configuration files
├── examples/               # Example usage
├── venv/                   # Virtual environment
├── pyproject.toml          # Project configuration
└── requirements.txt        # Dependencies
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd mcp-monorepo

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .
```

### Running Servers

#### Individual Servers
```bash
# Database Server (Port 3003)
python -m mcp_database

# Filesystem Server (Port 3004)
python -m mcp_filesystem
```

#### All Servers
```bash
# Start all servers
./scripts/start_all_servers.sh

# Stop all servers
./scripts/stop_all_servers.sh
```

## 📦 Packages

### mcp_core
Shared components used by all MCP servers:
- Configuration management
- Structured logging
- Security and authentication
- Rate limiting
- Metrics collection
- Client session management
- Base server implementation

### mcp_database
Database MCP Server providing:
- Database health checks
- Schema discovery
- SQL query execution
- CRUD operations
- Record management

### mcp_filesystem
Filesystem MCP Server providing:
- File listing and navigation
- File reading and writing
- Directory operations
- File search capabilities
- File metadata access

## 🔧 Configuration

Each server can be configured using YAML files in the `config/` directory:

```yaml
# config/database_server.yaml
server:
  host: "0.0.0.0"
  port: 3003
  
database:
  ws_url: "http://localhost:8000"
  
security:
  auth_enabled: true
  auth_token: "${MCP_AUTH_TOKEN}"
```

## 🔌 Claude Desktop Integration

### Database Server
```json
{
  "database-mcp-server": {
    "command": "socat",
    "args": ["TCP:dev01.int.stortz.tech:3003", "STDIO"],
    "env": {
      "MCP_AUTH_TOKEN": "your-auth-token"
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
      "MCP_AUTH_TOKEN": "your-auth-token"
    }
  }
}
```

## 🧪 Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black src/
flake8 src/
mypy src/
```

### Adding a New Server

1. Create a new package in `src/mcp_newserver/`
2. Extend `BaseMCPServer` from `mcp_core`
3. Implement your tools
4. Add configuration in `config/`
5. Update documentation

## 📚 Documentation

- [API Reference](docs/api.md)
- [Configuration Guide](docs/configuration.md)
- [Development Guide](docs/development.md)
- [Deployment Guide](docs/deployment.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.