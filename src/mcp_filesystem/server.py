"""
Filesystem MCP Server implementation
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional

from ..mcp_core import BaseMCPServer, ServerConfig, ClientSession
from .tools import FilesystemTools

logger = logging.getLogger(__name__)


class FilesystemMCPServer(BaseMCPServer):
    """Filesystem MCP Server with full MCP protocol support"""

    def __init__(self, config: ServerConfig, base_path: str = "/"):
        super().__init__(config)
        self.filesystem_tools = FilesystemTools(base_path)
        self.tools = self._initialize_tools()

    def _initialize_tools(self) -> Dict[str, Dict[str, Any]]:
        """Initialize filesystem-specific tools"""
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
                            "default": ".",
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
            "write_file": {
                "name": "write_file",
                "description": "Write content to a file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path to write"},
                        "content": {
                            "type": "string",
                            "description": "Content to write",
                        },
                        "encoding": {
                            "type": "string",
                            "description": "File encoding",
                            "default": "utf-8",
                        },
                    },
                    "required": ["path", "content"],
                },
            },
            "create_directory": {
                "name": "create_directory",
                "description": "Create a directory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Directory path to create",
                        }
                    },
                    "required": ["path"],
                },
            },
            "delete_file": {
                "name": "delete_file",
                "description": "Delete a file or directory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to delete"}
                    },
                    "required": ["path"],
                },
            },
            "get_file_info": {
                "name": "get_file_info",
                "description": "Get detailed information about a file or directory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to get info for",
                        }
                    },
                    "required": ["path"],
                },
            },
            "search_files": {
                "name": "search_files",
                "description": "Search for files matching a pattern",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "File pattern to search for (e.g., *.txt)",
                        },
                        "path": {
                            "type": "string",
                            "description": "Directory to search in",
                            "default": ".",
                        },
                        "recursive": {
                            "type": "boolean",
                            "description": "Search recursively in subdirectories",
                            "default": True,
                        },
                    },
                    "required": ["pattern"],
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
                        "id": request_id,
                        "error": {"code": -32000, "message": "Rate limit exceeded"},
                    }
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
                                "id": request_id,
                                "error": {
                                    "code": -32001,
                                    "message": "Authentication failed",
                                },
                            }
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

                # Send response
                response = {"jsonrpc": "2.0", "id": request_id, "result": result}
                writer.write((json.dumps(response) + "\n").encode("utf-8"))
                await writer.drain()

        except Exception as e:
            logger.error(f"Communication error: {e}")

    async def _process_request(
        self, method: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process MCP protocol requests"""
        if method == "initialize":
            return {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "Filesystem MCP Server", "version": "1.0.0"},
            }
        elif method == "tools/list":
            return {"tools": list(self.tools.values())}
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name not in self.tools:
                raise ValueError(f"Unknown tool: {tool_name}")

            # Call the appropriate tool method
            tool_method = getattr(self.filesystem_tools, tool_name, None)
            if not tool_method:
                raise ValueError(f"Tool {tool_name} not implemented")

            # Call the tool method with arguments
            if asyncio.iscoroutinefunction(tool_method):
                result = await tool_method(**arguments)
            else:
                result = tool_method(**arguments)

            return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
        else:
            raise ValueError(f"Unknown method: {method}")
