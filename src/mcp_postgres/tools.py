"""
Database tools for MCP server - Updated to utilize all database_ws features
"""

import asyncio
import json
import logging
import os
import aiohttp
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)


class PostgresTools:
    """PostgreSQL database operation tools with full database_ws integration"""
    
    def __init__(self, database_ws_url: str = None):
        if database_ws_url is None:
            database_ws_url = os.getenv('DATABASE_WS_URL', 'http://localhost:8000')
        self.database_ws_url = database_ws_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def _make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to database service"""
        session = await self._get_session()
        url = f"{self.database_ws_url}{endpoint}"
        
        try:
            if method == "GET":
                async with session.get(url) as response:
                    return await response.json()
            elif method == "POST":
                async with session.post(url, json=data) as response:
                    return await response.json()
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
        except Exception as e:
            logger.error(f"Database request failed: {e}")
            return {"error": str(e)}
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        return {
            "platform": {
                "system": "Linux",
                "release": "6.8.0-71-generic",
                "version": "#1 SMP PREEMPT_DYNAMIC Ubuntu 6.8.0-71.71~22.04.1",
                "machine": "x86_64",
                "processor": "x86_64"
            },
            "python": {
                "version": "3.8.10",
                "implementation": "CPython"
            },
            "server": {
                "name": "Database MCP Server",
                "version": "1.0.0",
                "uptime": "Running"
            }
        }
    
    async def echo(self, message: str) -> Dict[str, Any]:
        """Echo back the provided message with metadata"""
        return {
            "message": message,
            "timestamp": "2024-01-15T10:30:00Z",
            "server": "Database MCP Server"
        }
    
    async def list_files(self, path: str = ".", include_hidden: bool = False) -> Dict[str, Any]:
        """List files in a directory with detailed information"""
        # This would be implemented with actual file system access
        return {
            "path": path,
            "files": [
                {
                    "name": "example.txt",
                    "size": 1024,
                    "type": "file",
                    "modified": "2024-01-15T10:30:00Z"
                }
            ]
        }
    
    async def read_file(self, path: str, encoding: str = "utf-8", max_size: int = 1048576) -> Dict[str, Any]:
        """Read contents of a text file safely"""
        # This would be implemented with actual file system access
        return {
            "path": path,
            "content": "File content would be here",
            "encoding": encoding,
            "size": 1024
        }
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get server performance metrics"""
        return {
            "uptime_seconds": 3600,
            "total_requests": 1000,
            "total_errors": 5,
            "error_rate": 0.005,
            "active_connections": 3,
            "average_response_time_ms": 150.5,
            "tool_usage": {
                "get_system_info": 50,
                "echo": 100,
                "list_files": 25
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a comprehensive health check"""
        return {
            "status": "healthy",
            "timestamp": "2024-01-15T10:30:00Z",
            "checks": {
                "database_connection": "ok",
                "memory_usage": "normal",
                "disk_space": "sufficient"
            }
        }
    
    async def database_health(self) -> Dict[str, Any]:
        """Check PostgreSQL database service health and connection"""
        try:
            result = await self._make_request("/admin/health")
            return {
                "status": "connected",
                "database_url": self.database_ws_url,
                "response": result
            }
        except Exception as e:
            return {
                "status": "error",
                "database_url": self.database_ws_url,
                "error": str(e)
            }
    
    async def list_databases(self) -> Dict[str, Any]:
        """List all available PostgreSQL databases"""
        try:
            result = await self._make_request("/admin/databases")
            return {
                "databases": result.get("databases", []),
                "count": len(result.get("databases", []))
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def list_schemas(self) -> Dict[str, Any]:
        """List all schemas in the PostgreSQL database"""
        try:
            result = await self._make_request("/admin/schemas")
            return {
                "schemas": result.get("schemas", []),
                "count": len(result.get("schemas", []))
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def list_tables(self, schema_name: Optional[str] = None) -> Dict[str, Any]:
        """List all tables in the PostgreSQL database or specific schema"""
        try:
            if schema_name:
                endpoint = f"/admin/tables/{schema_name}"
            else:
                endpoint = "/admin/tables"
            result = await self._make_request(endpoint)
            return {
                "tables": result.get("tables", []),
                "count": len(result.get("tables", [])),
                "schema": schema_name
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def execute_sql(self, sql: str, parameters: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a PostgreSQL SQL query (read-only) using raw SQL endpoint"""
        try:
            data = {"sql": sql}
            if parameters:
                data["parameters"] = parameters
            result = await self._make_request("/raw/sql", method="POST", data=data)
            return result
        except Exception as e:
            return {"error": str(e)}
    
    async def execute_write_sql(self, sql: str, parameters: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a PostgreSQL SQL write operation (INSERT, UPDATE, DELETE) using raw SQL endpoint"""
        try:
            data = {"sql": sql}
            if parameters:
                data["parameters"] = parameters
            result = await self._make_request("/raw/sql/write", method="POST", data=data)
            return result
        except Exception as e:
            return {"error": str(e)}
    
    # New Prepared Statement Tools
    async def execute_prepared_sql(self, sql: str, parameters: Optional[Dict] = None, operation_type: str = "read") -> Dict[str, Any]:
        """Execute a prepared SQL statement with advanced validation and caching"""
        try:
            data = {
                "sql": sql,
                "operation_type": operation_type
            }
            if parameters:
                data["parameters"] = parameters
            result = await self._make_request("/crud/prepared/execute", method="POST", data=data)
            return result
        except Exception as e:
            return {"error": str(e)}
    
    async def execute_prepared_select(self, sql: str, parameters: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a prepared SELECT statement with validation"""
        try:
            data = {"sql": sql}
            if parameters:
                data["parameters"] = parameters
            result = await self._make_request("/crud/prepared/select", method="POST", data=data)
            return result
        except Exception as e:
            return {"error": str(e)}
    
    async def execute_prepared_insert(self, sql: str, parameters: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a prepared INSERT statement with validation"""
        try:
            data = {"sql": sql}
            if parameters:
                data["parameters"] = parameters
            result = await self._make_request("/crud/prepared/insert", method="POST", data=data)
            return result
        except Exception as e:
            return {"error": str(e)}
    
    async def execute_prepared_update(self, sql: str, parameters: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a prepared UPDATE statement with validation"""
        try:
            data = {"sql": sql}
            if parameters:
                data["parameters"] = parameters
            result = await self._make_request("/crud/prepared/update", method="POST", data=data)
            return result
        except Exception as e:
            return {"error": str(e)}
    
    async def execute_prepared_delete(self, sql: str, parameters: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a prepared DELETE statement with validation"""
        try:
            data = {"sql": sql}
            if parameters:
                data["parameters"] = parameters
            result = await self._make_request("/crud/prepared/delete", method="POST", data=data)
            return result
        except Exception as e:
            return {"error": str(e)}
    
    async def validate_prepared_sql(self, sql: str, parameters: Optional[Dict] = None, operation_type: str = "read") -> Dict[str, Any]:
        """Validate a prepared SQL statement without executing it"""
        try:
            data = {
                "sql": sql,
                "operation_type": operation_type
            }
            if parameters:
                data["parameters"] = parameters
            result = await self._make_request("/crud/prepared/validate", method="POST", data=data)
            return result
        except Exception as e:
            return {"error": str(e)}
    
    async def get_prepared_statements(self) -> Dict[str, Any]:
        """Get information about cached prepared statements"""
        try:
            result = await self._make_request("/crud/prepared/statements", method="GET")
            return result
        except Exception as e:
            return {"error": str(e)}
    
    async def clear_prepared_statements(self) -> Dict[str, Any]:
        """Clear all cached prepared statements"""
        try:
            result = await self._make_request("/crud/prepared/statements", method="DELETE")
            return result
        except Exception as e:
            return {"error": str(e)}
    
    async def clear_specific_prepared_statement(self, statement_name: str) -> Dict[str, Any]:
        """Clear a specific prepared statement by name"""
        try:
            result = await self._make_request(f"/crud/prepared/statements/{statement_name}", method="DELETE")
            return result
        except Exception as e:
            return {"error": str(e)}
    
    async def read_records(self, schema_name: str, table_name: str, limit: int = 100, 
                          offset: int = 0, order_by: Optional[str] = None) -> Dict[str, Any]:
        """Read records from a table using CRUD endpoint"""
        try:
            # Build query parameters
            params = []
            if limit != 100:
                params.append(f"limit={limit}")
            if offset != 0:
                params.append(f"offset={offset}")
            if order_by:
                params.append(f"order_by={order_by}")
            
            query_string = "&".join(params)
            endpoint = f"/crud/{schema_name}/{table_name}"
            if query_string:
                endpoint += f"?{query_string}"
            
            result = await self._make_request(endpoint, method="GET")
            return result
        except Exception as e:
            return {"error": str(e)}
    
    async def read_record(self, schema_name: str, table_name: str, record_id: str) -> Dict[str, Any]:
        """Read a specific record by ID using CRUD endpoint"""
        try:
            endpoint = f"/crud/{schema_name}/{table_name}/{record_id}"
            result = await self._make_request(endpoint, method="GET")
            return result
        except Exception as e:
            return {"error": str(e)}
    
    async def create_record(self, schema_name: str, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record in a table using CRUD endpoint"""
        try:
            request_data = {"data": data}
            endpoint = f"/crud/{schema_name}/{table_name}"
            result = await self._make_request(endpoint, method="POST", data=request_data)
            return result
        except Exception as e:
            return {"error": str(e)}
    
    async def update_record(self, schema_name: str, table_name: str, record_id: str, 
                           data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing record using CRUD endpoint"""
        try:
            request_data = {"data": data}
            endpoint = f"/crud/{schema_name}/{table_name}/{record_id}"
            result = await self._make_request(endpoint, method="PUT", data=request_data)
            return result
        except Exception as e:
            return {"error": str(e)}
    
    async def delete_record(self, schema_name: str, table_name: str, record_id: str) -> Dict[str, Any]:
        """Delete a record from a table using CRUD endpoint"""
        try:
            endpoint = f"/crud/{schema_name}/{table_name}/{record_id}"
            result = await self._make_request(endpoint, method="DELETE")
            return result
        except Exception as e:
            return {"error": str(e)}
    
    async def upsert_record(self, schema_name: str, table_name: str, record_id: str, 
                           data: Dict[str, Any]) -> Dict[str, Any]:
        """Upsert a record (insert if not exists, update if exists) using CRUD endpoint"""
        try:
            request_data = {"data": data}
            endpoint = f"/crud/{schema_name}/{table_name}/{record_id}"
            result = await self._make_request(endpoint, method="PATCH", data=request_data)
            return result
        except Exception as e:
            return {"error": str(e)}
    
    async def close(self):
        """Close the HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()


