"""
MCP REST API Server implementation
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Set

try:
    from ..mcp_core import (
        BaseMCPServer,
        ServerConfig,
        ClientSession,
        EndpointRegistryClient,
        resolve_registry_url,
    )
except ImportError:
    from mcp_core import (
        BaseMCPServer,
        ServerConfig,
        ClientSession,
        EndpointRegistryClient,
        resolve_registry_url,
    )
from .tools import RestAPITools

logger = logging.getLogger(__name__)

CUSTOM_HANDLERS: Set[str] = {"generate_resume", "download_resume", "get_resume_api_info"}


class RestAPIMCPServer(BaseMCPServer):
    """MCP server for REST API interactions"""

    def __init__(self, config: ServerConfig):
        super().__init__(config)
        self.registry_url = resolve_registry_url(
            config.resume_api_registry_url,
            config.resume_api_url,
        )
        self.registry_client: Optional[EndpointRegistryClient] = None
        if self.registry_url:
            self.registry_client = EndpointRegistryClient(self.registry_url)
        self.tools_instance = RestAPITools(
            config.resume_api_url,
            registry=self.registry_client,
            registry_url=self.registry_url,
        )
        self.server = None
        self.tools = self._fallback_tools()

    def _fallback_tools(self) -> Dict[str, Dict[str, Any]]:
        """Static tool definitions used when registry is unavailable."""
        return {
            "generate_resume": {
                "name": "generate_resume",
                "description": "Generate a Word document resume from JSON data",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "contact_info": {
                            "type": "object",
                            "description": "Contact information for the resume",
                            "properties": {
                                "name": {"type": "string"},
                                "location": {"type": "string"},
                                "phone": {"type": "string"},
                                "email": {"type": "string"},
                                "linkedin": {"type": "string"},
                                "medium": {"type": "string"},
                            },
                            "required": ["name", "email"],
                        },
                        "summary": {"type": "string", "description": "Professional summary"},
                        "skills": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of skills",
                        },
                        "experience": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "Work experience entries",
                        },
                        "education": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "Education entries",
                        },
                    },
                    "required": ["contact_info", "summary", "skills", "experience"],
                },
            },
            "list_resumes": {
                "name": "list_resumes",
                "description": "List all generated resumes",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
            },
            "download_resume": {
                "name": "download_resume",
                "description": "Download a specific resume by ID",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "resume_id": {
                            "type": "string",
                            "description": "ID of the resume to download",
                        }
                    },
                    "required": ["resume_id"],
                },
            },
            "delete_resume": {
                "name": "delete_resume",
                "description": "Delete a specific resume by ID",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "resume_id": {
                            "type": "string",
                            "description": "ID of the resume to delete",
                        }
                    },
                    "required": ["resume_id"],
                },
            },
            "get_resume_api_info": {
                "name": "get_resume_api_info",
                "description": "Get information about the resume API from the endpoint registry",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
            },
        }

    async def _load_registry_tools(self) -> None:
        """Fetch registry and merge tool descriptors."""
        if not self.registry_client:
            logger.warning("No registry URL configured; using fallback tool definitions")
            return

        loaded = await self.registry_client.load()
        if not loaded:
            logger.warning(
                "Registry fetch failed for %s; using fallback tool definitions",
                self.registry_url,
            )
            return

        registry_tools = self.registry_client.to_mcp_tools_dict()
        merged = dict(registry_tools)
        merged["get_resume_api_info"] = self._fallback_tools()["get_resume_api_info"]
        self.tools = merged
        logger.info(
            "Registry loaded from %s: %d tools exposed",
            self.registry_url,
            len(self.tools),
        )

    async def _handle_client_communication(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        session: ClientSession,
    ):
        """Handle JSON-RPC communication with client"""
        buffer = ""

        while True:
            try:
                data = await reader.read(4096)
                if not data:
                    break

                buffer += data.decode("utf-8")

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()

                    if not line:
                        continue

                    try:
                        request = json.loads(line)
                        response = await self._handle_request(request, session)

                        if response and "id" in request:
                            response_line = json.dumps(response) + "\n"
                            writer.write(response_line.encode("utf-8"))
                            await writer.drain()

                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON: {e}")
                        if "id" in request:
                            error_response = {
                                "jsonrpc": "2.0",
                                "id": request.get("id"),
                                "error": {
                                    "code": -32700,
                                    "message": "Parse error",
                                    "data": str(e),
                                },
                            }
                            error_line = json.dumps(error_response) + "\n"
                            writer.write(error_line.encode("utf-8"))
                            await writer.drain()

            except Exception as e:
                logger.error(f"Error in client communication: {e}")
                break

    async def _handle_request(
        self, request: Dict[str, Any], session: ClientSession
    ) -> Optional[Dict[str, Any]]:
        """Handle individual JSON-RPC request"""
        try:
            session.last_activity = asyncio.get_event_loop().time()

            request_id = request.get("id")
            method = request.get("method")
            params = request.get("params", {})

            try:
                result = await self._process_request(method, params)
                success = True
            except Exception as e:
                logger.error(f"Error processing request {method}: {e}")
                result = {"error": {"code": -32603, "message": str(e)}}
                success = False

            response_time = asyncio.get_event_loop().time() - session.last_activity
            self.metrics.record_request(method, response_time, success)

            if request_id is None:
                return None

            response = {"jsonrpc": "2.0", "id": request_id}

            if isinstance(result, dict) and "error" in result:
                response["error"] = result["error"]
            else:
                response["result"] = result

            return response

        except Exception as e:
            logger.error(f"Request handling error: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {"code": -32603, "message": "Internal error", "data": str(e)},
            }

    async def _process_request(
        self, method: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process MCP protocol requests"""
        if method == "initialize":
            return {
                "protocolVersion": "2025-06-18",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "REST API MCP Server", "version": "1.0.0"},
            }
        elif method == "tools/list":
            return {"tools": list(self.tools.values())}
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name not in self.tools:
                raise ValueError(f"Unknown tool: {tool_name}")

            result = await self._execute_tool(tool_name, arguments)

            return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
        elif method == "resources/list":
            return {"resources": []}
        elif method == "prompts/list":
            return {"prompts": []}
        elif method == "notifications/initialized":
            return {}
        else:
            raise ValueError(f"Unknown method: {method}")

    async def _execute_tool(
        self, tool_name: str, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a specific tool"""
        if tool_name == "generate_resume":
            return await self.tools_instance.generate_resume(args)
        if tool_name == "download_resume":
            return await self.tools_instance.download_resume(args.get("resume_id"))
        if tool_name == "get_resume_api_info":
            return await self.tools_instance.get_resume_api_info()
        if tool_name == "list_resumes":
            return await self.tools_instance.list_resumes()
        if tool_name == "delete_resume":
            return await self.tools_instance.delete_resume(args.get("resume_id"))
        if tool_name in CUSTOM_HANDLERS:
            raise ValueError(f"Unhandled custom tool: {tool_name}")
        return await self.tools_instance._invoke_registry_tool(tool_name, args)

    async def start(self):
        """Start the MCP server"""
        await self._load_registry_tools()
        self.server = await self.start_server()

        try:
            async with self.server:
                await self.server.serve_forever()
        except KeyboardInterrupt:
            logger.info("Shutting down server...")
        finally:
            if self.server:
                self.server.close()
                await self.server.wait_closed()
