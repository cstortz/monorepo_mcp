"""
PostgreSQL MCP Server Implementation

This module provides a PostgreSQL-specific MCP server with database tools.
"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional
import sys
import os

# Add the core module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.base_server import BaseMCPServer
from core.security import ClientSession


class PostgreSQLTools:
    """PostgreSQL-specific tools"""
    
    def __init__(self, config):
        self.config = config
        self.database_url = config.database_service_url
        self.timeout = config.database_service_timeout
        self.retry_attempts = config.database_service_retry_attempts
    
    def get_tools(self) -> Dict[str, Any]:
        """Get PostgreSQL tools definitions"""
        return {
            "database_health": {
                "name": "database_health",
                "description": "Check PostgreSQL service health and connection",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "database_info": {
                "name": "database_info",
                "description": "Get detailed database information and configuration",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "test_connection": {
                "name": "test_connection",
                "description": "Test database connection and connectivity",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "list_databases": {
                "name": "list_databases",
                "description": "List all available PostgreSQL databases",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "list_schemas": {
                "name": "list_schemas",
                "description": "List all schemas in the PostgreSQL database",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "list_tables": {
                "name": "list_tables",
                "description": "List all tables in the PostgreSQL database or specific schema",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "schema_name": {
                            "type": "string",
                            "description": "Schema name to list tables for (optional)"
                        }
                    },
                    "required": []
                }
            },
            "execute_sql": {
                "name": "execute_sql",
                "description": "Execute a PostgreSQL SQL query (read-only)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": "SQL query to execute"
                        },
                        "parameters": {
                            "type": "object",
                            "description": "Query parameters (optional)"
                        }
                    },
                    "required": ["sql"]
                }
            },
            "execute_write_sql": {
                "name": "execute_write_sql",
                "description": "Execute a PostgreSQL SQL write operation (INSERT, UPDATE, DELETE)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": "SQL write query to execute"
                        },
                        "parameters": {
                            "type": "object",
                            "description": "Query parameters (optional)"
                        }
                    },
                    "required": ["sql"]
                }
            },
            "read_records": {
                "name": "read_records",
                "description": "Read records from a PostgreSQL table",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "schema_name": {
                            "type": "string",
                            "description": "Schema name"
                        },
                        "table_name": {
                            "type": "string",
                            "description": "Table name"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of records to return",
                            "default": 100
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Number of records to skip",
                            "default": 0
                        },
                        "order_by": {
                            "type": "string",
                            "description": "Order by clause (optional)"
                        }
                    },
                    "required": ["schema_name", "table_name"]
                }
            },
            "read_record": {
                "name": "read_record",
                "description": "Read a specific record by ID from a PostgreSQL table",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "schema_name": {
                            "type": "string",
                            "description": "Schema name"
                        },
                        "table_name": {
                            "type": "string",
                            "description": "Table name"
                        },
                        "record_id": {
                            "type": "string",
                            "description": "Record ID"
                        }
                    },
                    "required": ["schema_name", "table_name", "record_id"]
                }
            },
            "create_record": {
                "name": "create_record",
                "description": "Create a new record in a PostgreSQL table",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "schema_name": {
                            "type": "string",
                            "description": "Schema name"
                        },
                        "table_name": {
                            "type": "string",
                            "description": "Table name"
                        },
                        "data": {
                            "type": "object",
                            "description": "Record data"
                        }
                    },
                    "required": ["schema_name", "table_name", "data"]
                }
            },
            "update_record": {
                "name": "update_record",
                "description": "Update an existing record in a PostgreSQL table",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "schema_name": {
                            "type": "string",
                            "description": "Schema name"
                        },
                        "table_name": {
                            "type": "string",
                            "description": "Table name"
                        },
                        "record_id": {
                            "type": "string",
                            "description": "Record ID"
                        },
                        "data": {
                            "type": "object",
                            "description": "Updated record data"
                        }
                    },
                    "required": ["schema_name", "table_name", "record_id", "data"]
                }
            },
            "delete_record": {
                "name": "delete_record",
                "description": "Delete a record from a PostgreSQL table",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "schema_name": {
                            "type": "string",
                            "description": "Schema name"
                        },
                        "table_name": {
                            "type": "string",
                            "description": "Table name"
                        },
                        "record_id": {
                            "type": "string",
                            "description": "Record ID"
                        }
                    },
                    "required": ["schema_name", "table_name", "record_id"]
                }
            },
            "upsert_record": {
                "name": "upsert_record",
                "description": "Upsert (Insert or Update) a record in a PostgreSQL table",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "schema_name": {
                            "type": "string",
                            "description": "Schema name"
                        },
                        "table_name": {
                            "type": "string",
                            "description": "Table name"
                        },
                        "record_id": {
                            "type": "string",
                            "description": "Record ID for upsert condition"
                        },
                        "data": {
                            "type": "object",
                            "description": "Record data to upsert"
                        }
                    },
                    "required": ["schema_name", "table_name", "record_id", "data"]
                }
            }
        }
    
    async def _make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to the database service with retry logic and timeout"""
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        for attempt in range(self.retry_attempts):
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    url = f"{self.database_url}{endpoint}"
                    
                    if method == "GET":
                        async with session.get(url) as response:
                            if response.status == 200:
                                return await response.json()
                            elif response.status == 503:
                                return {"error": "Database service unavailable"}
                            elif response.status == 500:
                                return {"error": f"Database service error: {await response.text()}"}
                            else:
                                return {"error": f"HTTP {response.status}: {await response.text()}"}
                    elif method == "POST":
                        async with session.post(url, json=data) as response:
                            if response.status == 200:
                                return await response.json()
                            elif response.status == 503:
                                return {"error": "Database service unavailable"}
                            elif response.status == 500:
                                return {"error": f"Database service error: {await response.text()}"}
                            else:
                                return {"error": f"HTTP {response.status}: {await response.text()}"}
                    elif method == "PATCH":
                        async with session.patch(url, json=data) as response:
                            if response.status == 200:
                                return await response.json()
                            elif response.status == 503:
                                return {"error": "Database service unavailable"}
                            elif response.status == 500:
                                return {"error": f"Database service error: {await response.text()}"}
                            else:
                                return {"error": f"HTTP {response.status}: {await response.text()}"}
                    else:
                        return {"error": f"Unsupported method: {method}"}
                        
            except asyncio.TimeoutError:
                if attempt == self.retry_attempts - 1:
                    return {"error": f"Request timeout after {self.timeout}s"}
                continue
            except aiohttp.ClientError as e:
                if attempt == self.retry_attempts - 1:
                    return {"error": f"Cannot connect to database service: {str(e)}"}
                continue
            except Exception as e:
                return {"error": f"Request failed: {str(e)}"}
        
        return {"error": f"Request failed after {self.retry_attempts} attempts"}
    
    async def database_health(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """Check PostgreSQL service health"""
        result = await self._make_request("/admin/health")
        
        if "error" in result:
            content = f"❌ PostgreSQL Health Check Failed:\n{result['error']}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
        
        content = f"""✅ PostgreSQL Health Check:

Status: {result.get('status', 'Unknown')}
Version: {result.get('version', 'Unknown')}
Uptime: {result.get('uptime', 'Unknown')}
Active Connections: {result.get('active_connections', 'Unknown')}
Max Connections: {result.get('max_connections', 'Unknown')}"""
        
        return {"content": [{"type": "text", "text": content}]}
    
    async def database_info(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """Get detailed database information"""
        result = await self._make_request("/admin/db-info")
        
        if "error" in result:
            content = f"❌ Failed to get database info:\n{result['error']}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
        
        content = f"""📊 PostgreSQL Database Information:

Database Name: {result.get('database_name', 'Unknown')}
Database Version: {result.get('version', 'Unknown')}
Server Version: {result.get('server_version', 'Unknown')}
Encoding: {result.get('encoding', 'Unknown')}
Collation: {result.get('collation', 'Unknown')}
Timezone: {result.get('timezone', 'Unknown')}
Max Connections: {result.get('max_connections', 'Unknown')}
Current Connections: {result.get('current_connections', 'Unknown')}
Active Connections: {result.get('active_connections', 'Unknown')}
Idle Connections: {result.get('idle_connections', 'Unknown')}"""
        
        return {"content": [{"type": "text", "text": content}]}
    
    async def test_connection(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """Test database connection and connectivity"""
        result = await self._make_request("/admin/test-connection")
        
        if "error" in result:
            content = f"❌ Database Connection Test Failed:\n{result['error']}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
        
        content = f"""🔗 Database Connection Test:

Status: {result.get('status', 'Unknown')}
Connection Time: {result.get('connection_time', 'Unknown')}
Database: {result.get('database', 'Unknown')}
Host: {result.get('host', 'Unknown')}
Port: {result.get('port', 'Unknown')}
User: {result.get('user', 'Unknown')}
SSL Mode: {result.get('ssl_mode', 'Unknown')}"""
        
        return {"content": [{"type": "text", "text": content}]}
    
    async def list_databases(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """List all PostgreSQL databases"""
        result = await self._make_request("/admin/databases")
        
        if "error" in result:
            content = f"❌ Failed to list databases:\n{result['error']}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
        
        databases = result.get('databases', [])
        content = f"🗄️ PostgreSQL Databases ({len(databases)}):\n\n"
        
        for db in databases:
            content += f"📁 {db.get('name', 'Unknown')}\n"
            content += f"   Size: {db.get('size', 'Unknown')}\n"
            content += f"   Tables: {db.get('tables', 'Unknown')}\n\n"
        
        return {"content": [{"type": "text", "text": content}]}
    
    async def list_schemas(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """List all schemas in PostgreSQL"""
        result = await self._make_request("/admin/schemas")
        
        if "error" in result:
            content = f"❌ Failed to list schemas:\n{result['error']}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
        
        schemas = result.get('schemas', [])
        content = f"📋 PostgreSQL Schemas ({len(schemas)}):\n\n"
        
        for schema in schemas:
            content += f"📁 {schema.get('name', 'Unknown')}\n"
            content += f"   Tables: {schema.get('tables', 'Unknown')}\n"
            content += f"   Owner: {schema.get('owner', 'Unknown')}\n\n"
        
        return {"content": [{"type": "text", "text": content}]}
    
    async def list_tables(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """List tables in PostgreSQL"""
        schema_name = args.get("schema_name")
        
        if schema_name:
            # Use the specific schema endpoint
            endpoint = f"/admin/tables/{schema_name}"
        else:
            # Use the general tables endpoint
            endpoint = "/admin/tables"
        
        result = await self._make_request(endpoint)
        
        if "error" in result:
            content = f"❌ Failed to list tables:\n{result['error']}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
        
        tables = result.get('tables', [])
        schema_text = f" in schema '{schema_name}'" if schema_name else ""
        content = f"📊 PostgreSQL Tables{schema_text} ({len(tables)}):\n\n"
        
        for table in tables:
            content += f"📋 {table.get('table_name', table.get('name', 'Unknown'))}\n"
            content += f"   Schema: {table.get('schema', 'Unknown')}\n"
            content += f"   Type: {table.get('table_type', 'Unknown')}\n"
            content += f"   Owner: {table.get('owner', 'Unknown')}\n"
            if 'rows' in table:
                content += f"   Rows: {table.get('rows', 'Unknown')}\n"
            if 'size' in table:
                content += f"   Size: {table.get('size', 'Unknown')}\n"
            content += "\n"
        
        return {"content": [{"type": "text", "text": content}]}
    
    async def execute_sql(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """Execute a read-only SQL query"""
        sql = args.get("sql")
        parameters = args.get("parameters", {})
        
        data = {
            "sql": sql,
            "parameters": parameters,
            "readonly": True
        }
        
        result = await self._make_request("/query", method="POST", data=data)
        
        if "error" in result:
            content = f"❌ SQL execution failed:\n{result['error']}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
        
        rows = result.get('rows', [])
        columns = result.get('columns', [])
        row_count = result.get('row_count', 0)
        
        content = f"✅ SQL Query Results:\n\n"
        content += f"Query: {sql}\n"
        content += f"Rows returned: {row_count}\n\n"
        
        if columns and rows:
            # Add column headers
            content += " | ".join(columns) + "\n"
            content += "-" * (len(" | ".join(columns))) + "\n"
            
            # Add data rows
            for row in rows[:10]:  # Limit to first 10 rows
                content += " | ".join(str(cell) for cell in row) + "\n"
            
            if len(rows) > 10:
                content += f"\n... and {len(rows) - 10} more rows"
        
        return {"content": [{"type": "text", "text": content}]}
    
    async def execute_write_sql(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """Execute a write SQL operation"""
        sql = args.get("sql")
        parameters = args.get("parameters", {})
        
        data = {
            "sql": sql,
            "parameters": parameters,
            "readonly": False
        }
        
        result = await self._make_request("/query", method="POST", data=data)
        
        if "error" in result:
            content = f"❌ SQL write operation failed:\n{result['error']}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
        
        affected_rows = result.get('affected_rows', 0)
        
        content = f"✅ SQL Write Operation Completed:\n\n"
        content += f"Query: {sql}\n"
        content += f"Rows affected: {affected_rows}\n"
        
        return {"content": [{"type": "text", "text": content}]}
    
    async def read_records(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """Read records from a table"""
        schema_name = args.get("schema_name")
        table_name = args.get("table_name")
        limit = args.get("limit", 100)
        offset = args.get("offset", 0)
        order_by = args.get("order_by")
        
        sql = f"SELECT * FROM {schema_name}.{table_name}"
        if order_by:
            sql += f" ORDER BY {order_by}"
        sql += f" LIMIT {limit} OFFSET {offset}"
        
        data = {
            "sql": sql,
            "parameters": {},
            "readonly": True
        }
        
        result = await self._make_request("/query", method="POST", data=data)
        
        if "error" in result:
            content = f"❌ Failed to read records:\n{result['error']}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
        
        rows = result.get('rows', [])
        columns = result.get('columns', [])
        
        content = f"📖 Records from {schema_name}.{table_name}:\n\n"
        content += f"Showing {len(rows)} records (limit: {limit}, offset: {offset})\n\n"
        
        if columns and rows:
            # Add column headers
            content += " | ".join(columns) + "\n"
            content += "-" * (len(" | ".join(columns))) + "\n"
            
            # Add data rows
            for row in rows:
                content += " | ".join(str(cell) for cell in row) + "\n"
        
        return {"content": [{"type": "text", "text": content}]}
    
    async def read_record(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """Read a specific record by ID"""
        schema_name = args.get("schema_name")
        table_name = args.get("table_name")
        record_id = args.get("record_id")
        
        sql = f"SELECT * FROM {schema_name}.{table_name} WHERE id = %s"
        
        data = {
            "sql": sql,
            "parameters": [record_id],
            "readonly": True
        }
        
        result = await self._make_request("/query", method="POST", data=data)
        
        if "error" in result:
            content = f"❌ Failed to read record:\n{result['error']}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
        
        rows = result.get('rows', [])
        columns = result.get('columns', [])
        
        if not rows:
            content = f"❌ Record not found: ID {record_id} in {schema_name}.{table_name}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
        
        content = f"📖 Record {record_id} from {schema_name}.{table_name}:\n\n"
        
        if columns and rows:
            row = rows[0]
            for i, column in enumerate(columns):
                content += f"{column}: {row[i]}\n"
        
        return {"content": [{"type": "text", "text": content}]}
    
    async def create_record(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """Create a new record"""
        schema_name = args.get("schema_name")
        table_name = args.get("table_name")
        data = args.get("data", {})
        
        if not data:
            content = "❌ No data provided for record creation"
            return {"content": [{"type": "text", "text": content}], "isError": True}
        
        columns = list(data.keys())
        values = list(data.values())
        placeholders = ", ".join(["%s"] * len(values))
        
        sql = f"INSERT INTO {schema_name}.{table_name} ({', '.join(columns)}) VALUES ({placeholders}) RETURNING id"
        
        data = {
            "sql": sql,
            "parameters": values,
            "readonly": False
        }
        
        result = await self._make_request("/query", method="POST", data=data)
        
        if "error" in result:
            content = f"❌ Failed to create record:\n{result['error']}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
        
        rows = result.get('rows', [])
        new_id = rows[0][0] if rows else "Unknown"
        
        content = f"✅ Record created successfully:\n\n"
        content += f"Table: {schema_name}.{table_name}\n"
        content += f"New ID: {new_id}\n"
        content += f"Data: {args['data']}"
        
        return {"content": [{"type": "text", "text": content}]}
    
    async def update_record(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """Update an existing record"""
        schema_name = args.get("schema_name")
        table_name = args.get("table_name")
        record_id = args.get("record_id")
        data = args.get("data", {})
        
        if not data:
            content = "❌ No data provided for record update"
            return {"content": [{"type": "text", "text": content}], "isError": True}
        
        set_clause = ", ".join([f"{col} = %s" for col in data.keys()])
        sql = f"UPDATE {schema_name}.{table_name} SET {set_clause} WHERE id = %s"
        
        values = list(data.values()) + [record_id]
        
        data = {
            "sql": sql,
            "parameters": values,
            "readonly": False
        }
        
        result = await self._make_request("/query", method="POST", data=data)
        
        if "error" in result:
            content = f"❌ Failed to update record:\n{result['error']}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
        
        affected_rows = result.get('affected_rows', 0)
        
        if affected_rows == 0:
            content = f"❌ Record not found: ID {record_id} in {schema_name}.{table_name}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
        
        content = f"✅ Record updated successfully:\n\n"
        content += f"Table: {schema_name}.{table_name}\n"
        content += f"Record ID: {record_id}\n"
        content += f"Updated data: {args['data']}\n"
        content += f"Rows affected: {affected_rows}"
        
        return {"content": [{"type": "text", "text": content}]}
    
    async def delete_record(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """Delete a record"""
        schema_name = args.get("schema_name")
        table_name = args.get("table_name")
        record_id = args.get("record_id")
        
        sql = f"DELETE FROM {schema_name}.{table_name} WHERE id = %s"
        
        data = {
            "sql": sql,
            "parameters": [record_id],
            "readonly": False
        }
        
        result = await self._make_request("/query", method="POST", data=data)
        
        if "error" in result:
            content = f"❌ Failed to delete record:\n{result['error']}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
        
        affected_rows = result.get('affected_rows', 0)
        
        if affected_rows == 0:
            content = f"❌ Record not found: ID {record_id} in {schema_name}.{table_name}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
        
        content = f"✅ Record deleted successfully:\n\n"
        content += f"Table: {schema_name}.{table_name}\n"
        content += f"Record ID: {record_id}\n"
        content += f"Rows affected: {affected_rows}"
        
        return {"content": [{"type": "text", "text": content}]}

    async def upsert_record(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """Upsert (Insert or Update) a record in a table"""
        schema_name = args.get("schema_name")
        table_name = args.get("table_name")
        record_id = args.get("record_id")
        data = args.get("data", {})

        if not data:
            content = "❌ No data provided for upsert"
            return {"content": [{"type": "text", "text": content}], "isError": True}

        # Use the PATCH endpoint for upsert
        endpoint = f"/crud/{schema_name}/{table_name}/{record_id}"
        
        result = await self._make_request(endpoint, method="PATCH", data={"data": data})

        if "error" in result:
            content = f"❌ Failed to upsert record:\n{result['error']}"
            return {"content": [{"type": "text", "text": content}], "isError": True}

        record = result.get('record', {})
        record_id_result = record.get('id', record_id)

        content = f"✅ Record upserted successfully:\n\n"
        content += f"Table: {schema_name}.{table_name}\n"
        content += f"Record ID: {record_id_result}\n"
        content += f"Data: {data}\n"
        content += f"Operation: {'Updated' if result.get('updated', False) else 'Inserted'}"

        return {"content": [{"type": "text", "text": content}]}


class PostgreSQLMCPServer(BaseMCPServer):
    """PostgreSQL MCP Server implementation"""
    
    def __init__(self):
        super().__init__("postgresql-mcp-server", "1.0.0")
        self.postgres_tools = None
    
    def register_server_tools(self):
        """Register PostgreSQL-specific tools"""
        # Initialize PostgreSQL tools
        self.postgres_tools = PostgreSQLTools(self.config)
        
        # Register tools
        postgres_tools = self.postgres_tools.get_tools()
        for tool_name, tool_def in postgres_tools.items():
            self.tools[tool_name] = tool_def
            self.tool_handlers[tool_name] = getattr(self.postgres_tools, tool_name)
