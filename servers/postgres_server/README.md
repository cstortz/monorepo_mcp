# PostgreSQL MCP Server

This is the PostgreSQL-specific MCP server that connects to an external database REST service.

## Architecture

The PostgreSQL MCP server follows a proper layered architecture:

```
MCP Server (Port 3001) → HTTP → Database Service (Port 8000) → PostgreSQL
```

### Components

1. **MCP Server**: Handles MCP protocol, authentication, rate limiting, tool definitions
2. **Database Service**: External REST service that handles database connections and queries
3. **PostgreSQL**: The actual database instance

## Configuration

The server is configured via `config.yaml`:

```yaml
server:
  host: "0.0.0.0"
  port: 3001

database_service:
  url: "http://dev01.int.stortz.tech:8000"
  timeout: 30
  retry_attempts: 3

security:
  auth_enabled: true
  auth_token: "${MCP_AUTH_TOKEN}"
  allowed_ips:
    - "127.0.0.1"
    - "::1"
```

### Environment Variables

- `MCP_AUTH_TOKEN`: Authentication token for the MCP server
- `MCP_DATABASE_SERVICE_URL`: Override database service URL
- `MCP_DATABASE_SERVICE_TIMEOUT`: Override timeout (seconds)
- `MCP_DATABASE_SERVICE_RETRY_ATTEMPTS`: Override retry attempts

## Available Tools

### Database Tools
- `database_health` - Check PostgreSQL service health
- `database_info` - Get detailed database information and configuration
- `test_connection` - Test database connection and connectivity
- `list_databases` - List all available databases
- `list_schemas` - List all schemas
- `list_tables` - List tables in a schema
- `execute_sql` - Execute read-only SQL queries
- `execute_write_sql` - Execute write SQL operations
- `read_records` - Read records from a table
- `read_record` - Read a specific record by ID
- `create_record` - Create a new record
- `update_record` - Update an existing record
- `delete_record` - Delete a record
- `upsert_record` - Upsert (Insert or Update) a record

### Admin Tools (Shared)
- `get_system_info` - Get system information
- `echo` - Echo input with metadata
- `get_metrics` - Get server metrics
- `health_check` - Check server health

### File Tools (Shared)
- `list_files` - List files in a directory
- `read_file` - Read file contents

## Starting the Server

```bash
# Activate virtual environment
source venv/bin/activate

# Start the server
python servers/postgres_server/start.py
```

## Testing

### Test Connection to External Service

```bash
python servers/postgres_server/test_external_connection.py
```

### Run Unit Tests

```bash
python -m pytest servers/postgres_server/tests/ -v
```

## Benefits of This Architecture

1. **Security**: Database credentials are isolated in the microservice
2. **Scalability**: Database service can be scaled independently
3. **Connection Management**: Connection pooling happens in the database service
4. **Language Flexibility**: Database service can be written in any language
5. **Deployment**: Each component can be deployed separately
6. **Testing**: Each layer can be tested independently

## Error Handling

The server includes robust error handling:

- **Connection Timeouts**: Configurable timeout with retry logic
- **Service Unavailable**: Proper handling of 503 errors
- **Database Errors**: Detailed error messages for database issues
- **Network Issues**: Graceful handling of connection failures

## Monitoring

The server provides comprehensive monitoring:

- Request metrics and performance tracking
- Connection status monitoring
- Error rate tracking
- System resource usage
