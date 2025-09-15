"""
Database MCP Server implementation
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional

from ..mcp_core import BaseMCPServer, ServerConfig, ClientSession
from .tools import PostgresTools

logger = logging.getLogger(__name__)


class PostgresMCPServer(BaseMCPServer):
    """PostgreSQL MCP Server with full MCP protocol support"""

    def __init__(self, config: ServerConfig):
        super().__init__(config)
        logger.debug(
            f"Initializing PostgresMCPServer with database_ws_url: {config.database_ws_url}"
        )
        self.database_tools = PostgresTools(config.database_ws_url)
        self.tools = self._initialize_tools()
        logger.debug(f"PostgresMCPServer initialized with {len(self.tools)} tools")

    def _initialize_tools(self) -> Dict[str, Dict[str, Any]]:
        """Initialize database-specific tools"""
        return {
            "get_system_info": {
                "name": "get_system_info",
                "description": "Get comprehensive system information",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
            },
            "echo": {
                "name": "echo",
                "description": "Echo back the provided message with metadata",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Message to echo back",
                        }
                    },
                    "required": ["message"],
                },
            },
            "list_files": {
                "name": "list_files",
                "description": "List files in a directory with detailed information",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Directory path to list",
                        },
                        "include_hidden": {
                            "type": "boolean",
                            "description": "Include hidden files",
                            "default": False,
                        },
                    },
                    "required": [],
                },
            },
            "read_file": {
                "name": "read_file",
                "description": "Read contents of a text file safely",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path to read"},
                        "encoding": {
                            "type": "string",
                            "description": "File encoding",
                            "default": "utf-8",
                        },
                        "max_size": {
                            "type": "integer",
                            "description": "Maximum file size in bytes",
                            "default": 1048576,
                        },
                    },
                    "required": ["path"],
                },
            },
            "get_metrics": {
                "name": "get_metrics",
                "description": "Get server performance metrics",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
            },
            "health_check": {
                "name": "health_check",
                "description": "Perform a comprehensive health check",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
            },
            "database_health": {
                "name": "database_health",
                "description": "Check PostgreSQL database service health and connection",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
            },
            "list_databases": {
                "name": "list_databases",
                "description": "List all available PostgreSQL databases",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
            },
            "list_schemas": {
                "name": "list_schemas",
                "description": "List all schemas in the PostgreSQL database",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
            },
            "list_tables": {
                "name": "list_tables",
                "description": "List all tables in the PostgreSQL database or specific schema",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "schema_name": {
                            "type": "string",
                            "description": "Schema name to list tables for (optional)",
                        }
                    },
                    "required": [],
                },
            },
            "execute_prepared_sql": {
                "name": "execute_prepared_sql",
                "description": "Execute a prepared SQL statement with advanced validation and caching",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": "SQL query to execute",
                        },
                        "parameters": {
                            "type": "object",
                            "description": "Query parameters (optional)",
                        },
                        "operation_type": {
                            "type": "string",
                            "description": "Operation type: 'read' or 'write'",
                            "default": "read",
                        },
                    },
                    "required": ["sql"],
                },
            },
            "execute_prepared_select": {
                "name": "execute_prepared_select",
                "description": "Execute a prepared SELECT statement with validation",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": "SELECT query to execute",
                        },
                        "parameters": {
                            "type": "object",
                            "description": "Query parameters (optional)",
                        },
                    },
                    "required": ["sql"],
                },
            },
            "execute_prepared_insert": {
                "name": "execute_prepared_insert",
                "description": "Execute a prepared INSERT statement with validation",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": "INSERT query to execute",
                        },
                        "parameters": {
                            "type": "object",
                            "description": "Query parameters (optional)",
                        },
                    },
                    "required": ["sql"],
                },
            },
            "execute_prepared_update": {
                "name": "execute_prepared_update",
                "description": "Execute a prepared UPDATE statement with validation",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": "UPDATE query to execute",
                        },
                        "parameters": {
                            "type": "object",
                            "description": "Query parameters (optional)",
                        },
                    },
                    "required": ["sql"],
                },
            },
            "execute_prepared_delete": {
                "name": "execute_prepared_delete",
                "description": "Execute a prepared DELETE statement with validation",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": "DELETE query to execute",
                        },
                        "parameters": {
                            "type": "object",
                            "description": "Query parameters (optional)",
                        },
                    },
                    "required": ["sql"],
                },
            },
            "validate_prepared_sql": {
                "name": "validate_prepared_sql",
                "description": "Validate a prepared SQL statement without executing it",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": "SQL query to validate",
                        },
                        "parameters": {
                            "type": "object",
                            "description": "Query parameters (optional)",
                        },
                        "operation_type": {
                            "type": "string",
                            "description": "Operation type: 'read' or 'write'",
                            "default": "read",
                        },
                    },
                    "required": ["sql"],
                },
            },
            "get_prepared_statements": {
                "name": "get_prepared_statements",
                "description": "Get information about cached prepared statements",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
            },
            "clear_prepared_statements": {
                "name": "clear_prepared_statements",
                "description": "Clear all cached prepared statements",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
            },
            "clear_specific_prepared_statement": {
                "name": "clear_specific_prepared_statement",
                "description": "Clear a specific prepared statement by name",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "statement_name": {
                            "type": "string",
                            "description": "Name of the prepared statement to clear",
                        }
                    },
                    "required": ["statement_name"],
                },
            },
        }

    async def _handle_client_communication(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        session: ClientSession,
    ):
        """Handle MCP protocol communication with client"""
        try:
            while True:
                # Read request
                line = await reader.readline()
                if not line:
                    break

                line = line.decode("utf-8").strip()
                if not line:
                    continue

                # Parse JSON-RPC request
                try:
                    request = json.loads(line)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON request: {e}")
                    continue

                # Extract request details
                request_id = request.get("id")
                method = request.get("method")
                params = request.get("params", {})

                # Update session activity
                session.last_activity = time.time()
                session.request_count += 1

                # Check rate limiting
                if not self.rate_limiter.is_allowed(session.ip_address):
                    response = {
                        "jsonrpc": "2.0",
                        "error": {"code": -32000, "message": "Rate limit exceeded"},
                    }
                    if request_id is not None:
                        response["id"] = request_id
                    writer.write((json.dumps(response) + "\n").encode("utf-8"))
                    await writer.drain()
                    continue

                # Handle authentication
                if method != "initialize":
                    auth_header = params.get("headers", {}).get("authorization")
                    if auth_header and auth_header.startswith("Bearer "):
                        token = auth_header[7:]
                        if not self.security.verify_token(token):
                            self.security.record_failed_attempt(session.ip_address)
                            response = {
                                "jsonrpc": "2.0",
                                "error": {
                                    "code": -32001,
                                    "message": "Authentication failed",
                                },
                            }
                            if request_id is not None:
                                response["id"] = request_id
                            writer.write((json.dumps(response) + "\n").encode("utf-8"))
                            await writer.drain()
                            continue
                        session.authenticated = True

                # Process request
                start_time = time.time()
                try:
                    result = await self._process_request(method, params)
                    success = True
                except Exception as e:
                    logger.error(f"Error processing request {method}: {e}")
                    result = {"error": {"code": -32603, "message": str(e)}}
                    success = False

                # Record metrics
                response_time = time.time() - start_time
                self.metrics.record_request(method, response_time, success)

                # Don't send response for notifications (requests without id)
                if request_id is None:
                    continue

                # Send response
                response = {"jsonrpc": "2.0", "id": request_id}

                # Check if result contains an error
                if isinstance(result, dict) and "error" in result:
                    response["error"] = result["error"]
                else:
                    response["result"] = result
                writer.write((json.dumps(response) + "\n").encode("utf-8"))
                await writer.drain()

        except Exception as e:
            logger.error(f"Communication error: {e}")
        finally:
            await self.database_tools.close()

    async def _process_request(
        self, method: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process MCP protocol requests"""
        if method == "initialize":
            return {
                "protocolVersion": "2025-06-18",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "PostgreSQL MCP Server", "version": "1.0.0"},
            }
        elif method == "tools/list":
            return {"tools": list(self.tools.values())}
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name not in self.tools:
                raise ValueError(f"Unknown tool: {tool_name}")

            # Call the appropriate tool method
            tool_method = getattr(self.database_tools, tool_name, None)
            if not tool_method:
                raise ValueError(f"Tool {tool_name} not implemented")

            # Call the tool method with arguments
            if asyncio.iscoroutinefunction(tool_method):
                result = await tool_method(**arguments)
            else:
                result = tool_method(**arguments)

            return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
        elif method == "resources/list":
            # Return empty resources list
            return {"resources": []}
        elif method == "prompts/list":
            # Return empty prompts list
            return {"prompts": []}
        elif method == "notifications/initialized":
            # Acknowledge initialization notification
            return {}
        else:
            raise ValueError(f"Unknown method: {method}")
