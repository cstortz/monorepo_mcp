"""
MySQL MCP Server Implementation

This module provides a MySQL-specific MCP server with database tools.
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


class MySQLTools:
    """MySQL-specific tools"""
    
    def __init__(self, database_url: str = "http://localhost:8000"):
        self.database_url = database_url
    
    def get_tools(self) -> Dict[str, Any]:
        """Get MySQL tools definitions"""
        return {
            "database_health": {
                "name": "database_health",
                "description": "Check MySQL service health and connection",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "list_databases": {
                "name": "list_databases",
                "description": "List all available MySQL databases",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "list_schemas": {
                "name": "list_schemas",
                "description": "List all schemas in the MySQL database",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "list_tables": {
                "name": "list_tables",
                "description": "List all tables in the MySQL database or specific schema",
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
                "description": "Execute a MySQL SQL query (read-only)",
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
                "description": "Execute a MySQL SQL write operation (INSERT, UPDATE, DELETE)",
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
                "description": "Read records from a MySQL table",
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
                "description": "Read a specific record by ID from a MySQL table",
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
                "description": "Create a new record in a MySQL table",
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
                "description": "Update an existing record in a MySQL table",
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
                "description": "Delete a record from a MySQL table",
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
            }
        }
    
    async def _make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to the database service"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.database_url}{endpoint}"
                
                if method == "GET":
                    async with session.get(url) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            return {"error": f"HTTP {response.status}: {await response.text()}"}
                elif method == "POST":
                    async with session.post(url, json=data) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            return {"error": f"HTTP {response.status}: {await response.text()}"}
                else:
                    return {"error": f"Unsupported method: {method}"}
                    
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}
    
    async def database_health(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """Check MySQL service health"""
        result = await self._make_request("/admin/health")
        
        if "error" in result:
            content = f"❌ MySQL Health Check Failed:\n{result['error']}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
        
        content = f"""✅ MySQL Health Check:

Status: {result.get('status', 'Unknown')}
Version: {result.get('version', 'Unknown')}
Uptime: {result.get('uptime', 'Unknown')}
Active Connections: {result.get('active_connections', 'Unknown')}
Max Connections: {result.get('max_connections', 'Unknown')}"""
        
        return {"content": [{"type": "text", "text": content}]}
    
    async def list_databases(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """List all MySQL databases"""
        result = await self._make_request("/admin/databases")
        
        if "error" in result:
            content = f"❌ Failed to list databases:\n{result['error']}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
        
        databases = result.get('databases', [])
        content = f"🗄️ MySQL Databases ({len(databases)}):\n\n"
        
        for db in databases:
            content += f"📁 {db.get('name', 'Unknown')}\n"
            content += f"   Size: {db.get('size', 'Unknown')}\n"
            content += f"   Tables: {db.get('tables', 'Unknown')}\n\n"
        
        return {"content": [{"type": "text", "text": content}]}
    
    async def list_schemas(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """List all schemas in MySQL"""
        result = await self._make_request("/admin/schemas")
        
        if "error" in result:
            content = f"❌ Failed to list schemas:\n{result['error']}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
        
        schemas = result.get('schemas', [])
        content = f"📋 MySQL Schemas ({len(schemas)}):\n\n"
        
        for schema in schemas:
            content += f"📁 {schema.get('name', 'Unknown')}\n"
            content += f"   Tables: {schema.get('tables', 'Unknown')}\n"
            content += f"   Owner: {schema.get('owner', 'Unknown')}\n\n"
        
        return {"content": [{"type": "text", "text": content}]}
    
    async def list_tables(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """List tables in MySQL"""
        schema_name = args.get("schema_name")
        endpoint = f"/admin/tables"
        if schema_name:
            endpoint += f"?schema={schema_name}"
        
        result = await self._make_request(endpoint)
        
        if "error" in result:
            content = f"❌ Failed to list tables:\n{result['error']}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
        
        tables = result.get('tables', [])
        schema_text = f" in schema '{schema_name}'" if schema_name else ""
        content = f"📊 MySQL Tables{schema_text} ({len(tables)}):\n\n"
        
        for table in tables:
            content += f"📋 {table.get('name', 'Unknown')}\n"
            content += f"   Schema: {table.get('schema', 'Unknown')}\n"
            content += f"   Rows: {table.get('rows', 'Unknown')}\n"
            content += f"   Size: {table.get('size', 'Unknown')}\n\n"
        
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
        
        sql = f"INSERT INTO {schema_name}.{table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        
        data = {
            "sql": sql,
            "parameters": values,
            "readonly": False
        }
        
        result = await self._make_request("/query", method="POST", data=data)
        
        if "error" in result:
            content = f"❌ Failed to create record:\n{result['error']}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
        
        affected_rows = result.get('affected_rows', 0)
        last_insert_id = result.get('last_insert_id', 'Unknown')
        
        content = f"✅ Record created successfully:\n\n"
        content += f"Table: {schema_name}.{table_name}\n"
        content += f"Last Insert ID: {last_insert_id}\n"
        content += f"Rows affected: {affected_rows}\n"
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


class MySQLMCPServer(BaseMCPServer):
    """MySQL MCP Server implementation"""
    
    def __init__(self):
        super().__init__("mysql-mcp-server", "1.0.0")
        self.mysql_tools = None
    
    def register_server_tools(self):
        """Register MySQL-specific tools"""
        # Initialize MySQL tools
        self.mysql_tools = MySQLTools()
        
        # Register tools
        mysql_tools = self.mysql_tools.get_tools()
        for tool_name, tool_def in mysql_tools.items():
            self.tools[tool_name] = tool_def
            self.tool_handlers[tool_name] = getattr(self.mysql_tools, tool_name)
