# MCP Monorepo

A production-ready monorepo for MCP (Model Context Protocol) servers with shared core components and specialized server instances.

## 🏗️ Architecture

This monorepo follows industry-standard practices with a clean separation of concerns:

```
mcp-monorepo/
├── src/                     # Source code
│   ├── mcp_core/           # Shared core components
│   ├── mcp_postgres/       # PostgreSQL MCP Server
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
# PostgreSQL Server (Port 3003)
python -m mcp_postgres

# Filesystem Server (Port 3005)
python -m mcp_filesystem
```

#### All Servers
```bash
# Start all servers
./scripts/run-all-servers.sh

# Stop all servers
./scripts/stop-all-servers.sh
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

### mcp_postgres
PostgreSQL MCP Server providing:
- PostgreSQL database operations
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
# config/postgres_server.yaml
server:
  host: 0.0.0.0
  port: 3003

security:
  auth_enabled: true
  auth_token: your-token-here

database:
  ws_url: http://dev01.int.stortz.tech:8000
```

## 🐳 Docker Deployment

For Docker deployment instructions, see [DOCKER-README.md](DOCKER-README.md).

### Quick Docker Commands
```bash
# Run all servers in Docker
./scripts/run-all-servers.sh

# Run individual servers
./scripts/run-postgres-mcp.sh
./scripts/run-filesystem-mcp.sh
```

## 🛡️ Security Features

### Authentication
- Token-based authentication
- IP allowlisting/blocklisting
- Failed attempt tracking
- Session management

### Rate Limiting
- Sliding window rate limiting
- Configurable limits per client
- Automatic cleanup of old records

### Access Control
- File system access restrictions
- Working directory confinement
- Maximum file size limits
- Safe tool execution

## 📊 Monitoring and Metrics

### Built-in Metrics
- Request counts and error rates
- Response time statistics
- Connection tracking
- System resource usage
- Tool usage statistics

### Health Checks
- CPU, memory, and disk monitoring
- Connection limit checking
- Error rate monitoring
- Overall system health status

### Logging
- Structured JSON logging
- Request tracing
- Error tracking
- Performance monitoring

## 🚀 Production Deployment

### Docker Deployment

```bash
# Build and run all servers
./scripts/run-all-servers.sh

# Or run individually
./scripts/run-postgres-mcp.sh
./scripts/run-filesystem-mcp.sh
```

### Systemd Service

```ini
[Unit]
Description=MCP Server
After=network.target

[Service]
Type=simple
User=mcp
WorkingDirectory=/opt/mcp
Environment=PATH=/opt/mcp/.venv/bin
ExecStart=/opt/mcp/.venv/bin/python -m mcp_postgres
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Environment Configuration

```bash
# Production environment variables
export MCP_AUTH_TOKEN="your-production-token"
export DATABASE_WS_URL="http://your-database-api:8000"
export LOG_LEVEL="INFO"
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
make test

# Run specific test files
pytest tests/test_postgres_server.py -v
pytest tests/test_filesystem_server.py -v
```

### Test Coverage
```bash
# Generate coverage report
pytest --cov=src tests/
```

## 📝 Development

### Code Quality
```bash
# Run linting
make lint

# Format code
make format

# Clean up
make clean
```

### Adding New Servers
1. Create a new directory in `src/` (e.g., `src/mcp_newserver/`)
2. Implement the server following the pattern in existing servers
3. Add Docker configuration in `docker/mcp_newserver/`
4. Update scripts and documentation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
