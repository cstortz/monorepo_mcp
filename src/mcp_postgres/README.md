# PostgreSQL MCP Server

This module provides a Model Context Protocol (MCP) server specifically for PostgreSQL database operations with full integration to the advanced database_ws service.

## Features

- **PostgreSQL Database Operations**: Connect to and query PostgreSQL databases
- **Schema Management**: List databases, schemas, and tables
- **SQL Execution**: Execute read and write SQL queries with security validation
- **Advanced Prepared Statements**: Execute prepared SQL with caching and validation
- **CRUD Operations**: Full Create, Read, Update, Delete operations with pagination
- **SQL Security**: Comprehensive SQL injection protection and validation
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

#### Database Information
- `list_databases` - List all available PostgreSQL databases
- `list_schemas` - List all schemas in the PostgreSQL database
- `list_tables` - List all tables in the PostgreSQL database or specific schema
- `database_health` - Check PostgreSQL database service health and connection

#### Raw SQL Operations
- `execute_sql` - Execute a PostgreSQL SQL query (read-only) with security validation
- `execute_write_sql` - Execute a PostgreSQL SQL write operation with security validation

#### CRUD Operations
- `read_records` - Read records from a table with pagination and ordering
- `read_record` - Read a specific record by ID
- `create_record` - Create a new record in a table
- `update_record` - Update an existing record
- `delete_record` - Delete a record from a table
- `upsert_record` - Upsert a record (insert if not exists, update if exists)

#### Advanced Prepared Statements
- `execute_prepared_sql` - Execute a prepared SQL statement with advanced validation and caching
- `execute_prepared_select` - Execute a prepared SELECT statement with validation
- `execute_prepared_insert` - Execute a prepared INSERT statement with validation
- `execute_prepared_update` - Execute a prepared UPDATE statement with validation
- `execute_prepared_delete` - Execute a prepared DELETE statement with validation
- `validate_prepared_sql` - Validate a prepared SQL statement without executing it
- `get_prepared_statements` - Get information about cached prepared statements
- `clear_prepared_statements` - Clear all cached prepared statements
- `clear_specific_prepared_statement` - Clear a specific prepared statement by name

#### System Tools
- `get_system_info` - Get comprehensive system information
- `echo` - Echo back the provided message with metadata
- `list_files` - List files in a directory with detailed information
- `read_file` - Read contents of a text file safely
- `get_metrics` - Get server performance metrics
- `health_check` - Perform a comprehensive health check

## Configuration

The server connects to a PostgreSQL database service via the `DATABASE_WS_URL` environment variable (defaults to `http://localhost:8000`). This service should provide the following endpoints:

### Admin Endpoints
- `/admin/health` - Health check
- `/admin/databases` - List databases
- `/admin/schemas` - List schemas
- `/admin/tables` - List tables

### Raw SQL Endpoints
- `/raw/sql` - Execute read queries with security validation
- `/raw/sql/write` - Execute write queries with security validation

### CRUD Endpoints
- `/crud/{schema}/{table}` - CRUD operations for tables
- `/crud/{schema}/{table}/{id}` - CRUD operations for specific records

### Prepared Statement Endpoints
- `/crud/prepared/execute` - Execute prepared SQL with validation
- `/crud/prepared/select` - Execute prepared SELECT statements
- `/crud/prepared/insert` - Execute prepared INSERT statements
- `/crud/prepared/update` - Execute prepared UPDATE statements
- `/crud/prepared/delete` - Execute prepared DELETE statements
- `/crud/prepared/validate` - Validate prepared SQL without execution
- `/crud/prepared/statements` - Manage cached prepared statements

## Examples

### Basic SQL Execution
```json
{
  "tool": "execute_sql",
  "arguments": {
    "sql": "SELECT * FROM users WHERE age > $1",
    "parameters": {"1": 18}
  }
}
```

### Prepared Statement with Validation
```json
{
  "tool": "validate_prepared_sql",
  "arguments": {
    "sql": "SELECT * FROM users WHERE department = $1 AND active = $2",
    "parameters": {"1": "engineering", "2": true},
    "operation_type": "read"
  }
}
```

### CRUD Operations
```json
{
  "tool": "create_record",
  "arguments": {
    "schema_name": "public",
    "table_name": "users",
    "data": {
      "name": "John Doe",
      "email": "john@example.com",
      "age": 30
    }
  }
}
```

### Advanced Prepared Statement Execution
```json
{
  "tool": "execute_prepared_sql",
  "arguments": {
    "sql": "INSERT INTO users (name, email, department) VALUES ($1, $2, $3) RETURNING *",
    "parameters": {"1": "Jane Smith", "2": "jane@example.com", "3": "marketing"},
    "operation_type": "write"
  }
}
```

## Security Features

The MCP server integrates with the database_ws service to provide comprehensive security:

- **SQL Injection Protection**: All SQL queries are validated for injection attempts
- **Parameter Binding**: All queries use parameterized statements
- **Operation Type Validation**: Read/write operations are strictly validated
- **Prepared Statement Caching**: Frequently used queries are cached for performance
- **Input Sanitization**: All inputs are sanitized before processing

## Architecture

This module is designed to be part of a larger MCP ecosystem where you can have different database types:

- `mcp_postgres` - PostgreSQL database operations
- `mcp_mysql` - MySQL database operations (future)
- `mcp_mongodb` - MongoDB operations (future)
- etc.

Each module provides database-specific functionality while maintaining a consistent MCP interface.

## Integration with database_ws

This MCP server is fully integrated with the advanced database_ws service, which provides:

- **Connection Pooling**: Efficient database connection management
- **Prepared Statement Management**: Advanced caching and validation
- **Security Validation**: Comprehensive SQL injection protection
- **Performance Monitoring**: Built-in metrics and health checks
- **RESTful API**: Full REST API with OpenAPI documentation

The database_ws service handles all the complex database operations, while this MCP server provides a clean, standardized interface for MCP clients.
