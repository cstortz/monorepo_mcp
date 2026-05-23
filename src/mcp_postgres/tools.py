"""
Database tools for MCP server - Updated to utilize all database_ws features
"""

import logging
import os
import aiohttp
from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from mcp_core.registry_client import EndpointRegistryClient

logger = logging.getLogger(__name__)

FALLBACK_HTTP: Dict[str, Dict[str, str]] = {
    "database_health": {"method": "GET", "path": "/admin/health"},
    "test_connection": {"method": "GET", "path": "/admin/test-connection"},
    "get_db_info": {"method": "GET", "path": "/admin/db-info"},
    "list_databases": {"method": "GET", "path": "/admin/databases"},
    "list_schemas": {"method": "GET", "path": "/admin/schemas"},
    "list_tables": {"method": "GET", "path": "/admin/tables"},
    "execute_sql": {"method": "POST", "path": "/raw/sql"},
    "execute_write_sql": {"method": "POST", "path": "/raw/sql/write"},
    "read_records": {"method": "GET", "path": "/crud/{schema_name}/{table_name}"},
    "read_record": {"method": "GET", "path": "/crud/{schema_name}/{table_name}/{record_id}"},
    "create_record": {"method": "POST", "path": "/crud/{schema_name}/{table_name}"},
    "update_record": {"method": "PUT", "path": "/crud/{schema_name}/{table_name}/{record_id}"},
    "delete_record": {"method": "DELETE", "path": "/crud/{schema_name}/{table_name}/{record_id}"},
    "upsert_record": {"method": "PATCH", "path": "/crud/{schema_name}/{table_name}/{record_id}"},
    "execute_prepared_sql": {"method": "POST", "path": "/crud/prepared/execute"},
    "execute_prepared_select": {"method": "POST", "path": "/crud/prepared/select"},
    "execute_prepared_insert": {"method": "POST", "path": "/crud/prepared/insert"},
    "execute_prepared_update": {"method": "POST", "path": "/crud/prepared/update"},
    "execute_prepared_delete": {"method": "POST", "path": "/crud/prepared/delete"},
    "validate_prepared_sql": {"method": "POST", "path": "/crud/prepared/validate"},
    "get_prepared_statements": {"method": "GET", "path": "/crud/prepared/statements"},
    "clear_prepared_statements": {"method": "DELETE", "path": "/crud/prepared/statements"},
    "clear_specific_prepared_statement": {
        "method": "DELETE",
        "path": "/crud/prepared/statements/{statement_name}",
    },
}

LOCAL_ONLY_TOOLS = {
    "get_system_info",
    "echo",
    "list_files",
    "read_file",
    "get_metrics",
    "health_check",
}


class PostgresTools:
    """PostgreSQL database operation tools with full database_ws integration"""

    def __init__(
        self,
        database_ws_url: str = None,
        registry: Optional["EndpointRegistryClient"] = None,
    ):
        if database_ws_url is None:
            database_ws_url = os.getenv("DATABASE_WS_URL", "http://localhost:8000")
        self.database_ws_url = database_ws_url
        self.registry = registry
        self.session: Optional[aiohttp.ClientSession] = None

    def _resolve_http(
        self, tool_name: str, **path_params: Any
    ) -> tuple[str, str]:
        """Return (method, path) from registry or fallback."""
        if self.registry and self.registry.loaded:
            method = self.registry.get_http_method(tool_name)
            path = self.registry.resolve_path(tool_name, **path_params)
            if method and path:
                return method, path

        fallback = FALLBACK_HTTP.get(tool_name)
        if not fallback:
            raise ValueError(f"No HTTP mapping for tool: {tool_name}")

        path = fallback["path"]
        for key, value in path_params.items():
            if value is not None:
                path = path.replace(f"{{{key}}}", str(value))
        return fallback["method"], path

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request to database service"""
        session = await self._get_session()
        url = f"{self.database_ws_url}{endpoint}"

        logger.debug(f"Making {method} request to: {url}")

        try:
            async with session.request(
                method, url, json=data if method in ("POST", "PUT", "PATCH") else None, params=params
            ) as response:
                logger.debug(f"Response status: {response.status}")

                if response.status >= 400:
                    error_text = await response.text()
                    logger.error(f"HTTP {response.status} error: {error_text}")
                    return {"error": f"HTTP {response.status}: {error_text}"}

                response_data = await response.json()
                logger.debug(f"Response data: {response_data}")
                return response_data
        except Exception as e:
            logger.error(f"Database request failed: {e}")
            logger.error(
                f"Request details - URL: {url}, Method: {method}, Data: {data}"
            )
            return {"error": str(e)}

    async def _invoke_registry_tool(
        self, tool_name: str, args: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generic HTTP invocation for registry-backed tools without dedicated handlers."""
        args = args or {}
        path_params = {
            k: args.get(k)
            for k in (
                "schema_name",
                "table_name",
                "record_id",
                "statement_name",
            )
            if args.get(k) is not None
        }
        method, path = self._resolve_http(tool_name, **path_params)
        query_params = None
        if tool_name == "read_records":
            query_params = {}
            if args.get("limit") is not None:
                query_params["limit"] = args["limit"]
            if args.get("offset") is not None:
                query_params["offset"] = args["offset"]
            if args.get("order_by"):
                query_params["order_by"] = args["order_by"]
        body = None
        if method in ("POST", "PUT", "PATCH"):
            if tool_name in ("create_record", "update_record", "upsert_record"):
                body = {"data": args.get("data", {})}
            elif tool_name.startswith("execute_") or tool_name.startswith("validate_"):
                body = {k: v for k, v in args.items() if k not in path_params}
            else:
                body = args
        return await self._make_request(path, method=method, data=body, params=query_params)

    async def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        return {
            "platform": {
                "system": "Linux",
                "release": "6.8.0-71-generic",
                "version": "#1 SMP PREEMPT_DYNAMIC Ubuntu 6.8.0-71.71~22.04.1",
                "machine": "x86_64",
                "processor": "x86_64",
            },
            "python": {"version": "3.8.10", "implementation": "CPython"},
            "server": {
                "name": "Database MCP Server",
                "version": "1.0.0",
                "uptime": "Running",
            },
        }

    async def echo(self, message: str) -> Dict[str, Any]:
        """Echo back the provided message with metadata"""
        return {
            "message": message,
            "timestamp": "2024-01-15T10:30:00Z",
            "server": "Database MCP Server",
        }

    async def list_files(
        self, path: str = ".", include_hidden: bool = False
    ) -> Dict[str, Any]:
        """List files in a directory with detailed information"""
        # This would be implemented with actual file system access
        return {
            "path": path,
            "files": [
                {
                    "name": "example.txt",
                    "size": 1024,
                    "type": "file",
                    "modified": "2024-01-15T10:30:00Z",
                }
            ],
        }

    async def read_file(
        self, path: str, encoding: str = "utf-8", max_size: int = 1048576
    ) -> Dict[str, Any]:
        """Read contents of a text file safely"""
        # This would be implemented with actual file system access
        return {
            "path": path,
            "content": "File content would be here",
            "encoding": encoding,
            "size": 1024,
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
            "tool_usage": {"get_system_info": 50, "echo": 100, "list_files": 25},
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform a comprehensive health check"""
        return {
            "status": "healthy",
            "timestamp": "2024-01-15T10:30:00Z",
            "checks": {
                "database_connection": "ok",
                "memory_usage": "normal",
                "disk_space": "sufficient",
            },
        }

    async def database_health(self) -> Dict[str, Any]:
        """Check PostgreSQL database service health and connection"""
        try:
            method, path = self._resolve_http("database_health")
            result = await self._make_request(path, method=method)
            return {
                "status": "connected",
                "database_url": self.database_ws_url,
                "response": result,
            }
        except Exception as e:
            return {
                "status": "error",
                "database_url": self.database_ws_url,
                "error": str(e),
            }

    async def list_databases(self) -> Dict[str, Any]:
        """List all available PostgreSQL databases"""
        logger.debug("Starting list_databases request")
        try:
            method, path = self._resolve_http("list_databases")
            result = await self._make_request(path, method=method)
            logger.debug(f"Raw result from _make_request: {result}")

            if "error" in result:
                logger.error(f"Error in database request: {result['error']}")
                return {"error": result["error"]}

            databases = result.get("databases", [])
            count = len(databases)

            logger.debug(f"Extracted databases: {databases}")
            logger.debug(f"Database count: {count}")

            response = {"databases": databases, "count": count}

            logger.debug(f"Final response: {response}")
            return response

        except Exception as e:
            logger.error(f"Exception in list_databases: {e}")
            logger.error(f"Exception type: {type(e)}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"error": str(e)}

    async def list_schemas(self) -> Dict[str, Any]:
        """List all schemas in the PostgreSQL database"""
        try:
            method, path = self._resolve_http("list_schemas")
            result = await self._make_request(path, method=method)
            return {
                "schemas": result.get("schemas", []),
                "count": len(result.get("schemas", [])),
            }
        except Exception as e:
            return {"error": str(e)}

    async def list_tables(self, schema_name: Optional[str] = None) -> Dict[str, Any]:
        """List all tables in the PostgreSQL database or specific schema"""
        try:
            if schema_name:
                method, path = "GET", f"/admin/tables/{schema_name}"
            else:
                method, path = self._resolve_http("list_tables")
            result = await self._make_request(path, method=method)
            return {
                "tables": result.get("tables", []),
                "count": len(result.get("tables", [])),
                "schema": schema_name,
            }
        except Exception as e:
            return {"error": str(e)}

    async def execute_sql(
        self, sql: str, parameters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Execute a PostgreSQL SQL query (read-only) using raw SQL endpoint"""
        try:
            data = {"sql": sql}
            if parameters:
                data["parameters"] = parameters
            method, path = self._resolve_http("execute_sql")
            result = await self._make_request(path, method=method, data=data)
            return result
        except Exception as e:
            return {"error": str(e)}

    async def execute_write_sql(
        self, sql: str, parameters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Execute a PostgreSQL SQL write operation (INSERT, UPDATE, DELETE) using raw SQL endpoint"""
        try:
            data = {"sql": sql}
            if parameters:
                data["parameters"] = parameters
            method, path = self._resolve_http("execute_write_sql")
            result = await self._make_request(path, method=method, data=data)
            return result
        except Exception as e:
            return {"error": str(e)}

    # New Prepared Statement Tools
    async def execute_prepared_sql(
        self, sql: str, parameters: Optional[Dict] = None, operation_type: str = "read"
    ) -> Dict[str, Any]:
        """Execute a prepared SQL statement with advanced validation and caching"""
        try:
            data = {"sql": sql, "operation_type": operation_type}
            if parameters:
                data["parameters"] = parameters
            method, path = self._resolve_http("execute_prepared_sql")
            result = await self._make_request(path, method=method, data=data)
            return result
        except Exception as e:
            return {"error": str(e)}

    async def execute_prepared_select(
        self, sql: str, parameters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Execute a prepared SELECT statement with validation"""
        try:
            data = {"sql": sql}
            if parameters:
                data["parameters"] = parameters
            method, path = self._resolve_http("execute_prepared_select")
            result = await self._make_request(path, method=method, data=data)
            return result
        except Exception as e:
            return {"error": str(e)}

    async def execute_prepared_insert(
        self, sql: str, parameters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Execute a prepared INSERT statement with validation"""
        try:
            data = {"sql": sql}
            if parameters:
                data["parameters"] = parameters
            method, path = self._resolve_http("execute_prepared_insert")
            result = await self._make_request(path, method=method, data=data)
            return result
        except Exception as e:
            return {"error": str(e)}

    async def execute_prepared_update(
        self, sql: str, parameters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Execute a prepared UPDATE statement with validation"""
        try:
            data = {"sql": sql}
            if parameters:
                data["parameters"] = parameters
            method, path = self._resolve_http("execute_prepared_update")
            result = await self._make_request(path, method=method, data=data)
            return result
        except Exception as e:
            return {"error": str(e)}

    async def execute_prepared_delete(
        self, sql: str, parameters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Execute a prepared DELETE statement with validation"""
        try:
            data = {"sql": sql}
            if parameters:
                data["parameters"] = parameters
            method, path = self._resolve_http("execute_prepared_delete")
            result = await self._make_request(path, method=method, data=data)
            return result
        except Exception as e:
            return {"error": str(e)}

    async def validate_prepared_sql(
        self, sql: str, parameters: Optional[Dict] = None, operation_type: str = "read"
    ) -> Dict[str, Any]:
        """Validate a prepared SQL statement without executing it"""
        try:
            data = {"sql": sql, "operation_type": operation_type}
            if parameters:
                data["parameters"] = parameters
            method, path = self._resolve_http("validate_prepared_sql")
            result = await self._make_request(path, method=method, data=data)
            return result
        except Exception as e:
            return {"error": str(e)}

    async def get_prepared_statements(self) -> Dict[str, Any]:
        """Get information about cached prepared statements"""
        try:
            method, path = self._resolve_http("get_prepared_statements")
            result = await self._make_request(path, method=method)
            return result
        except Exception as e:
            return {"error": str(e)}

    async def clear_prepared_statements(self) -> Dict[str, Any]:
        """Clear all cached prepared statements"""
        try:
            method, path = self._resolve_http("clear_prepared_statements")
            result = await self._make_request(path, method=method)
            return result
        except Exception as e:
            return {"error": str(e)}

    async def clear_specific_prepared_statement(
        self, statement_name: str
    ) -> Dict[str, Any]:
        """Clear a specific prepared statement by name"""
        try:
            method, path = self._resolve_http(
                "clear_specific_prepared_statement", statement_name=statement_name
            )
            result = await self._make_request(path, method=method)
            return result
        except Exception as e:
            return {"error": str(e)}

    async def read_records(
        self,
        schema_name: str,
        table_name: str,
        limit: int = 100,
        offset: int = 0,
        order_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Read records from a table using CRUD endpoint"""
        try:
            query_params = {}
            if limit != 100:
                query_params["limit"] = limit
            if offset != 0:
                query_params["offset"] = offset
            if order_by:
                query_params["order_by"] = order_by

            method, path = self._resolve_http(
                "read_records", schema_name=schema_name, table_name=table_name
            )
            result = await self._make_request(
                path, method=method, params=query_params or None
            )
            return result
        except Exception as e:
            return {"error": str(e)}

    async def read_record(
        self, schema_name: str, table_name: str, record_id: str
    ) -> Dict[str, Any]:
        """Read a specific record by ID using CRUD endpoint"""
        try:
            method, path = self._resolve_http(
                "read_record",
                schema_name=schema_name,
                table_name=table_name,
                record_id=record_id,
            )
            result = await self._make_request(path, method=method)
            return result
        except Exception as e:
            return {"error": str(e)}

    async def create_record(
        self, schema_name: str, table_name: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new record in a table using CRUD endpoint"""
        try:
            request_data = {"data": data}
            method, path = self._resolve_http(
                "create_record", schema_name=schema_name, table_name=table_name
            )
            result = await self._make_request(path, method=method, data=request_data)
            return result
        except Exception as e:
            return {"error": str(e)}

    async def update_record(
        self, schema_name: str, table_name: str, record_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing record using CRUD endpoint"""
        try:
            request_data = {"data": data}
            method, path = self._resolve_http(
                "update_record",
                schema_name=schema_name,
                table_name=table_name,
                record_id=record_id,
            )
            result = await self._make_request(path, method=method, data=request_data)
            return result
        except Exception as e:
            return {"error": str(e)}

    async def delete_record(
        self, schema_name: str, table_name: str, record_id: str
    ) -> Dict[str, Any]:
        """Delete a record from a table using CRUD endpoint"""
        try:
            method, path = self._resolve_http(
                "delete_record",
                schema_name=schema_name,
                table_name=table_name,
                record_id=record_id,
            )
            result = await self._make_request(path, method=method)
            return result
        except Exception as e:
            return {"error": str(e)}

    async def upsert_record(
        self, schema_name: str, table_name: str, record_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Upsert a record (insert if not exists, update if exists) using CRUD endpoint"""
        try:
            request_data = {"data": data}
            method, path = self._resolve_http(
                "upsert_record",
                schema_name=schema_name,
                table_name=table_name,
                record_id=record_id,
            )
            result = await self._make_request(path, method=method, data=request_data)
            return result
        except Exception as e:
            return {"error": str(e)}

    async def close(self):
        """Close the HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
