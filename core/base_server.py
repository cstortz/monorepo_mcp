"""
Base MCP Server for Monorepo

This module provides the base class for all MCP servers in the monorepo.
"""

import asyncio
import json
import logging
import signal
import sys
import ssl
import time
from typing import Dict, Any, Optional
from datetime import datetime
import aiohttp

from .config import ConfigManager, ServerConfig
from .security import SecurityManager, ClientSession
from .metrics import MetricsCollector
from .tools import AdminTools, FileTools


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        if hasattr(record, 'client_ip'):
            log_entry['client_ip'] = record.client_ip
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        return json.dumps(log_entry)


class BaseMCPServer:
    """Base class for all MCP servers in the monorepo"""
    
    def __init__(self, server_name: str, server_version: str = "1.0.0"):
        self.server_name = server_name
        self.server_version = server_version
        self.config_manager = ConfigManager()
        self.config = None
        self.security_manager = None
        self.metrics = None
        self.admin_tools = None
        self.file_tools = None
        self.logger = None
        self.server = None
        self.running = False
        
        # Tools registry - will be populated by subclasses
        self.tools = {}
        self.tool_handlers = {}
    
    def setup_logging(self, config: ServerConfig):
        """Setup logging configuration"""
        self.logger = logging.getLogger()
        self.logger.setLevel(getattr(logging, config.log_level.upper()))
        
        # Clear existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler with JSON formatting
        if config.log_format == "json":
            file_handler = logging.FileHandler(config.log_file)
            file_handler.setFormatter(JSONFormatter())
            self.logger.addHandler(file_handler)
        else:
            file_handler = logging.FileHandler(config.log_file)
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            )
            self.logger.addHandler(file_handler)
        
        # Console handler with standard formatting
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(console_handler)
        
        return self.logger
    
    def setup_components(self, config: ServerConfig):
        """Setup server components"""
        # Setup security manager
        self.security_manager = SecurityManager(config)
        
        # Setup metrics collector
        self.metrics = MetricsCollector()
        
        # Setup admin tools
        self.admin_tools = AdminTools(self.metrics)
        
        # Setup file tools
        self.file_tools = FileTools(config.max_file_size)
        
        # Register admin tools
        self._register_admin_tools()
        
        # Register file tools
        self._register_file_tools()
        
        # Allow subclasses to register their own tools
        self.register_server_tools()
    
    def _register_admin_tools(self):
        """Register admin tools"""
        admin_tools = self.admin_tools.get_tools()
        for tool_name, tool_def in admin_tools.items():
            self.tools[tool_name] = tool_def
            self.tool_handlers[tool_name] = getattr(self.admin_tools, tool_name)
    
    def _register_file_tools(self):
        """Register file tools"""
        file_tools = self.file_tools.get_tools()
        for tool_name, tool_def in file_tools.items():
            self.tools[tool_name] = tool_def
            self.tool_handlers[tool_name] = getattr(self.file_tools, tool_name)
    
    def register_server_tools(self):
        """Register server-specific tools - to be implemented by subclasses"""
        pass
    
    def get_tools(self) -> Dict[str, Any]:
        """Get all available tools"""
        return self.tools
    
    async def handle_initialize(self, params: Dict[str, Any], client_session: ClientSession) -> Dict[str, Any]:
        """Handle client initialization"""
        self.logger.info("Client initialized", extra={'client_ip': client_session.ip_address})
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": self.server_name,
                "version": self.server_version,
                "description": f"Monorepo MCP server: {self.server_name}"
            }
        }
    
    async def handle_list_tools(self, params: Dict[str, Any], client_session: ClientSession) -> Dict[str, Any]:
        """Handle tool listing request"""
        return {"tools": list(self.tools.values())}
    
    async def handle_call_tool(self, params: Dict[str, Any], client_session: ClientSession) -> Dict[str, Any]:
        """Handle tool call request"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        start_time = time.time()
        
        try:
            if tool_name in self.tool_handlers:
                handler = self.tool_handlers[tool_name]
                result = await handler(arguments, client_session)
            else:
                result = {
                    "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
                    "isError": True
                }
            
            response_time = time.time() - start_time
            self.metrics.record_request(tool_name, response_time, not result.get("isError", False))
            
            return result
            
        except Exception as e:
            response_time = time.time() - start_time
            self.metrics.record_request(tool_name, response_time, False)
            self.logger.error(f"Tool execution error: {e}", extra={'client_ip': client_session.ip_address})
            return {
                "content": [{"type": "text", "text": f"Internal error: {str(e)}"}],
                "isError": True
            }
    
    async def handle_request(self, request: Dict[str, Any], client_ip: str, auth_token: Optional[str] = None) -> Dict[str, Any]:
        """Handle incoming MCP request"""
        # Check access
        access_check = self.security_manager.check_access(client_ip, auth_token)
        if not access_check['allowed']:
            return {
                "error": {
                    "code": -32001,
                    "message": access_check['reason']
                }
            }
        
        # Extract request details
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        # Create or get client session
        client_id = params.get("client_id", f"client_{client_ip}")
        client_session = self.security_manager.get_session(client_id)
        if not client_session:
            client_session = self.security_manager.create_session(client_id, client_ip)
        
        # Update session activity
        self.security_manager.update_session(client_id)
        
        # Handle request based on method
        try:
            if method == "initialize":
                result = await self.handle_initialize(params, client_session)
            elif method == "tools/list":
                result = await self.handle_list_tools(params, client_session)
            elif method == "tools/call":
                result = await self.handle_call_tool(params, client_session)
            else:
                result = {
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
        except Exception as e:
            self.logger.error(f"Request handling error: {e}", extra={'client_ip': client_ip})
            result = {
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
        
        # Add request ID if provided
        if request_id is not None:
            result["id"] = request_id
        
        return result
    
    async def start_server(self, config_path: Optional[str] = None):
        """Start the MCP server"""
        try:
            # Load configuration
            self.config = self.config_manager.load_config(config_path)
            self.config_manager.validate_config()
            
            # Setup logging
            self.setup_logging(self.config)
            self.logger.info(f"Starting {self.server_name} MCP server...")
            
            # Setup components
            self.setup_components(self.config)
            
            # Create SSL context if needed
            ssl_context = None
            if self.config.ssl_cert and self.config.ssl_key:
                ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                ssl_context.load_cert_chain(self.config.ssl_cert, self.config.ssl_key)
                self.logger.info("SSL/TLS enabled")
            
            # Create server
            self.server = await asyncio.start_server(
                self._handle_client,
                self.config.host,
                self.config.port,
                ssl=ssl_context,
                limit=1024 * 1024  # 1MB limit
            )
            
            self.running = True
            self.logger.info(f"{self.server_name} MCP server started on {self.config.host}:{self.config.port}")
            
            # Start cleanup task
            asyncio.create_task(self._cleanup_task())
            
            # Keep server running
            async with self.server:
                await self.server.serve_forever()
                
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            raise
    
    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle client connection"""
        client_addr = writer.get_extra_info('peername')
        client_ip = client_addr[0] if client_addr else "unknown"
        
        self.metrics.record_connection_change(1)
        self.logger.info(f"Client connected from {client_ip}")
        
        try:
            while self.running:
                # Read request
                data = await reader.read(1024 * 1024)  # 1MB limit
                if not data:
                    break
                
                try:
                    request = json.loads(data.decode('utf-8'))
                except json.JSONDecodeError as e:
                    self.logger.error(f"Invalid JSON from {client_ip}: {e}")
                    break
                
                # Extract auth token from headers or request
                auth_token = None
                if self.config.auth_enabled:
                    # In a real implementation, you'd extract this from headers
                    # For now, we'll assume it's in the request
                    auth_token = request.get("auth_token")
                
                # Handle request
                response = await self.handle_request(request, client_ip, auth_token)
                
                # Send response
                response_data = json.dumps(response).encode('utf-8')
                writer.write(response_data)
                await writer.drain()
                
        except Exception as e:
            self.logger.error(f"Error handling client {client_ip}: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
            self.metrics.record_connection_change(-1)
            self.logger.info(f"Client {client_ip} disconnected")
    
    async def _cleanup_task(self):
        """Periodic cleanup task"""
        while self.running:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                self.security_manager.cleanup_expired_sessions()
            except Exception as e:
                self.logger.error(f"Cleanup task error: {e}")
    
    def stop_server(self):
        """Stop the server"""
        self.running = False
        if self.server:
            self.server.close()
        self.logger.info(f"{self.server_name} MCP server stopped")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop_server()
        sys.exit(0)
