# API Reference

## MCP Protocol

All servers in this monorepo implement the Model Context Protocol (MCP) specification.

### Common Endpoints

#### Initialize
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {}
}
```

#### List Tools
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

#### Call Tool
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "tool_name",
    "arguments": {}
  }
}
```

## Database Server API

### Tools

#### database_health
Check database service health and connection.

**Input Schema:**
```json
{}
```

**Response:**
```json
{
  "status": "connected",
  "database_url": "http://localhost:8000",
  "response": {}
}
```

#### list_databases
List all available databases.

**Input Schema:**
```json
{}
```

**Response:**
```json
{
  "databases": ["db1", "db2"],
  "count": 2
}
```

#### list_schemas
List all schemas in the database.

**Input Schema:**
```json
{}
```

**Response:**
```json
{
  "schemas": ["public", "private"],
  "count": 2
}
```

#### list_tables
List all tables in the database or specific schema.

**Input Schema:**
```json
{
  "schema_name": "public"
}
```

**Response:**
```json
{
  "tables": ["users", "posts"],
  "count": 2,
  "schema": "public"
}
```

#### execute_sql
Execute a SQL query (read-only).

**Input Schema:**
```json
{
  "sql": "SELECT * FROM users LIMIT 10",
  "parameters": {}
}
```

#### execute_write_sql
Execute a SQL write operation (INSERT, UPDATE, DELETE).

**Input Schema:**
```json
{
  "sql": "INSERT INTO users (name, email) VALUES ($1, $2)",
  "parameters": {
    "1": "John Doe",
    "2": "john@example.com"
  }
}
```

#### read_records
Read records from a table.

**Input Schema:**
```json
{
  "schema_name": "public",
  "table_name": "users",
  "limit": 100,
  "offset": 0,
  "order_by": "id DESC"
}
```

#### read_record
Read a specific record by ID.

**Input Schema:**
```json
{
  "schema_name": "public",
  "table_name": "users",
  "record_id": "123"
}
```

#### create_record
Create a new record in a table.

**Input Schema:**
```json
{
  "schema_name": "public",
  "table_name": "users",
  "data": {
    "name": "John Doe",
    "email": "john@example.com"
  }
}
```

#### update_record
Update an existing record.

**Input Schema:**
```json
{
  "schema_name": "public",
  "table_name": "users",
  "record_id": "123",
  "data": {
    "name": "Jane Doe"
  }
}
```

#### delete_record
Delete a record from a table.

**Input Schema:**
```json
{
  "schema_name": "public",
  "table_name": "users",
  "record_id": "123"
}
```

## Filesystem Server API

### Tools

#### list_files
List files in a directory with detailed information.

**Input Schema:**
```json
{
  "path": ".",
  "include_hidden": false
}
```

**Response:**
```json
{
  "path": ".",
  "files": [
    {
      "name": "example.txt",
      "path": "example.txt",
      "type": "file",
      "size": 1024,
      "modified": "2024-01-15T10:30:00Z",
      "permissions": "644"
    }
  ],
  "count": 1
}
```

#### read_file
Read contents of a text file safely.

**Input Schema:**
```json
{
  "path": "example.txt",
  "encoding": "utf-8",
  "max_size": 1048576
}
```

**Response:**
```json
{
  "path": "example.txt",
  "content": "File content here",
  "encoding": "utf-8",
  "size": 1024,
  "modified": "2024-01-15T10:30:00Z"
}
```

#### write_file
Write content to a file.

**Input Schema:**
```json
{
  "path": "new_file.txt",
  "content": "New content",
  "encoding": "utf-8"
}
```

#### create_directory
Create a directory.

**Input Schema:**
```json
{
  "path": "new_directory"
}
```

#### delete_file
Delete a file or directory.

**Input Schema:**
```json
{
  "path": "file_to_delete.txt"
}
```

#### get_file_info
Get detailed information about a file or directory.

**Input Schema:**
```json
{
  "path": "example.txt"
}
```

**Response:**
```json
{
  "path": "example.txt",
  "name": "example.txt",
  "type": "file",
  "size": 1024,
  "modified": "2024-01-15T10:30:00Z",
  "created": "2024-01-15T10:30:00Z",
  "permissions": "644",
  "owner": 1000,
  "group": 1000,
  "extension": ".txt",
  "mime_type": "text/plain"
}
```

#### search_files
Search for files matching a pattern.

**Input Schema:**
```json
{
  "pattern": "*.txt",
  "path": ".",
  "recursive": true
}
```

## Common Tools (All Servers)

### get_system_info
Get comprehensive system information.

**Input Schema:**
```json
{}
```

### echo
Echo back the provided message with metadata.

**Input Schema:**
```json
{
  "message": "Hello, World!"
}
```

### get_metrics
Get server performance metrics.

**Input Schema:**
```json
{}
```

### health_check
Perform a comprehensive health check.

**Input Schema:**
```json
{}
```

## Error Handling

All tools return consistent error responses:

```json
{
  "error": {
    "code": -32603,
    "message": "Internal error description"
  }
}
```

Common error codes:
- `-32000`: Rate limit exceeded
- `-32001`: Authentication failed
- `-32603`: Internal error
- `-32602`: Invalid parameters
