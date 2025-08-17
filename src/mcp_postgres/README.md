# PostgreSQL MCP Server

This module provides a Model Context Protocol (MCP) server specifically for PostgreSQL database operations.

## Features

- **PostgreSQL Database Operations**: Connect to and query PostgreSQL databases
- **Schema Management**: List databases, schemas, and tables
- **SQL Execution**: Execute read and write SQL queries
- **Health Monitoring**: Check database connection health
- **MCP Protocol Support**: Full MCP protocol implementation

## Usage

### Starting the Server

```bash
# Basic usage
python -m mcp_postgres --host 0.0.0.0 --port 3003 --no-auth

# With authentication
python -m mcp_postgres --host 0.0.0.0 --port 3003 --auth-token YOUR_TOKEN

# With configuration file
python -m mcp_postgres --config config.yaml
```

### Available Tools

- `list_databases` - List all available PostgreSQL databases
- `list_schemas` - List all schemas in the PostgreSQL database
- `list_tables` - List all tables in the PostgreSQL database or specific schema
- `execute_sql` - Execute a PostgreSQL SQL query (read-only)
- `execute_write_sql` - Execute a PostgreSQL SQL write operation
- `database_health` - Check PostgreSQL database service health and connection

## Configuration

The server connects to a PostgreSQL database service via the `DATABASE_WS_URL` environment variable (defaults to `http://localhost:8000`). This service should provide the following endpoints:

- `/admin/health` - Health check
- `/admin/databases` - List databases
- `/admin/schemas` - List schemas
- `/admin/tables` - List tables
- `/crud/raw-sql` - Execute read queries
- `/crud/raw-sql/write` - Execute write queries

## Architecture

This module is designed to be part of a larger MCP ecosystem where you can have different database types:

- `mcp_postgres` - PostgreSQL database operations
- `mcp_mysql` - MySQL database operations (future)
- `mcp_mongodb` - MongoDB operations (future)
- etc.

Each module provides database-specific functionality while maintaining a consistent MCP interface.
