"""
MCP REST API Server implementation
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional

try:
    from ..mcp_core import BaseMCPServer, ServerConfig, ClientSession
except ImportError:
    from mcp_core import BaseMCPServer, ServerConfig, ClientSession
from .tools import RestAPITools

logger = logging.getLogger(__name__)


class RestAPIMCPServer(BaseMCPServer):
    """MCP server for REST API interactions"""
    
    def __init__(self, config: ServerConfig):
        super().__init__(config)
        self.tools_instance = RestAPITools(config.resume_api_url)
        self.server = None
        # Override tools with our REST API tools
        self.tools = self._initialize_tools()
        
    def _initialize_tools(self) -> Dict[str, Dict[str, Any]]:
        """Initialize REST API tools"""
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
                                "medium": {"type": "string"}
                            },
                            "required": ["name", "email"]
                        },
                        "summary": {
                            "type": "string",
                            "description": "Professional summary"
                        },
                        "skills": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of skills"
                        },
                        "experience": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "company": {"type": "string"},
                                    "location": {"type": "string"},
                                    "duration": {"type": "string"},
                                    "title": {"type": "string"},
                                    "summary": {"type": "string"},
                                    "accomplishments": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                },
                                "required": ["company", "title", "summary"]
                            },
                            "description": "Work experience entries"
                        },
                        "education": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "institution": {"type": "string"},
                                    "degree": {"type": "string"},
                                    "field": {"type": "string"},
                                    "graduation_year": {"type": "string"}
                                },
                                "required": ["institution", "degree"]
                            },
                            "description": "Education entries"
                        }
                    },
                    "required": ["contact_info", "summary", "skills", "experience"]
                }
            },
            "list_resumes": {
                "name": "list_resumes",
                "description": "List all generated resumes",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "download_resume": {
                "name": "download_resume",
                "description": "Download a specific resume by ID",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "resume_id": {
                            "type": "string",
                            "description": "ID of the resume to download"
                        }
                    },
                    "required": ["resume_id"]
                }
            },
            "delete_resume": {
                "name": "delete_resume",
                "description": "Delete a specific resume by ID",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "resume_id": {
                            "type": "string",
                            "description": "ID of the resume to delete"
                        }
                    },
                    "required": ["resume_id"]
                }
            },
            "get_resume_api_info": {
                "name": "get_resume_api_info",
                "description": "Get information about the resume API",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
    
    async def _handle_client_communication(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, session: ClientSession):
        """Handle JSON-RPC communication with client"""
        buffer = ""
        
        while True:
            try:
                # Read data from client
                data = await reader.read(4096)
                if not data:
                    break
                
                buffer += data.decode('utf-8')
                
                # Process complete JSON-RPC messages
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    
                    if not line:
                        continue
                    
                    try:
                        request = json.loads(line)
                        response = await self._handle_request(request, session)
                        
                        # Send response if request_id is present (not a notification)
                        if response and 'id' in request:
                            response_line = json.dumps(response) + '\n'
                            writer.write(response_line.encode('utf-8'))
                            await writer.drain()
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON: {e}")
                        if 'id' in request:
                            error_response = {
                                "jsonrpc": "2.0",
                                "id": request.get('id'),
                                "error": {
                                    "code": -32700,
                                    "message": "Parse error",
                                    "data": str(e)
                                }
                            }
                            error_line = json.dumps(error_response) + '\n'
                            writer.write(error_line.encode('utf-8'))
                            await writer.drain()
                            
            except Exception as e:
                logger.error(f"Error in client communication: {e}")
                break
    
    async def _handle_request(self, request: Dict[str, Any], session: ClientSession) -> Optional[Dict[str, Any]]:
        """Handle individual JSON-RPC request"""
        try:
            # Update session activity
            session.last_activity = asyncio.get_event_loop().time()
            
            # Extract request details
            request_id = request.get('id')
            method = request.get('method')
            params = request.get('params', {})
            
            # Handle authentication
            if self.config.auth_token:
                auth_header = request.get('auth', {}).get('token')
                if auth_header != self.config.auth_token:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32001,
                            "message": "Authentication failed"
                        }
                    }
            
            # Process request
            try:
                result = await self._process_request(method, params)
                success = True
            except Exception as e:
                logger.error(f"Error processing request {method}: {e}")
                result = {
                    'error': {
                        'code': -32603,
                        'message': str(e)
                    }
                }
                success = False
            
            # Record metrics
            response_time = asyncio.get_event_loop().time() - session.last_activity
            self.metrics.record_request(method, response_time, success)
            
            # Don't send response for notifications (requests without id)
            if request_id is None:
                return None
            
            # Send response
            response = {
                'jsonrpc': '2.0',
                'id': request_id
            }
            
            # Check if result contains an error
            if isinstance(result, dict) and 'error' in result:
                response['error'] = result['error']
            else:
                response['result'] = result
            
            return response
                
        except Exception as e:
            logger.error(f"Request handling error: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get('id'),
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": str(e)
                }
            }
    
    async def _process_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Process MCP protocol requests"""
        if method == 'initialize':
            return {
                'protocolVersion': '2025-06-18',
                'capabilities': {
                    'tools': {}
                },
                'serverInfo': {
                    'name': 'REST API MCP Server',
                    'version': '1.0.0'
                }
            }
        elif method == 'tools/list':
            return {
                'tools': list(self.tools.values())
            }
        elif method == 'tools/call':
            tool_name = params.get('name')
            arguments = params.get('arguments', {})
            
            if tool_name not in self.tools:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            # Execute tool
            result = await self._execute_tool(tool_name, arguments)
            
            return {
                'content': [
                    {
                        'type': 'text',
                        'text': json.dumps(result, indent=2)
                    }
                ]
            }
        elif method == 'resources/list':
            # Return empty resources list
            return {'resources': []}
        elif method == 'prompts/list':
            # Return empty prompts list
            return {'prompts': []}
        elif method == 'notifications/initialized':
            # Acknowledge initialization notification
            return {}
        else:
            raise ValueError(f"Unknown method: {method}")
    
    async def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific tool"""
        if tool_name == "generate_resume":
            return await self.tools_instance.generate_resume(args)
        elif tool_name == "list_resumes":
            return await self.tools_instance.list_resumes()
        elif tool_name == "download_resume":
            return await self.tools_instance.download_resume(args.get('resume_id'))
        elif tool_name == "delete_resume":
            return await self.tools_instance.delete_resume(args.get('resume_id'))
        elif tool_name == "get_resume_api_info":
            return await self.tools_instance.get_resume_api_info()
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def start(self):
        """Start the MCP server"""
        self.server = await self.start_server()
        
        try:
            # Keep the server running
            async with self.server:
                await self.server.serve_forever()
        except KeyboardInterrupt:
            logger.info("Shutting down server...")
        finally:
            if self.server:
                self.server.close()
                await self.server.wait_closed()
