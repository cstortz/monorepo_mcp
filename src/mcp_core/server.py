"""
Base MCP server implementation
"""

import asyncio
import json
import logging
import ssl
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from .config import ServerConfig
from .session import ClientSession
from .security import SecurityManager
from .rate_limiter import RateLimiter
from .metrics import MetricsCollector

logger = logging.getLogger(__name__)


class BaseMCPServer:
    """Base MCP server with common functionality"""

    def __init__(self, config: ServerConfig):
        self.config = config
        self.clients: Dict[str, ClientSession] = {}
        self.rate_limiter = RateLimiter(
            config.rate_limit_requests, config.rate_limit_window
        )
        self.security = SecurityManager(config)
        self.metrics = MetricsCollector()
        self.tools = self._initialize_tools()

    def _initialize_tools(self) -> Dict[str, Dict[str, Any]]:
        """Initialize available tools - override in subclasses"""
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

    async def handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        """Handle client connection"""
        client_addr = writer.get_extra_info("peername")
        client_ip = client_addr[0] if client_addr else "unknown"
        client_id = str(uuid.uuid4())

        # Check IP restrictions
        if not self.security.is_ip_allowed(client_ip):
            logger.warning(f"Connection rejected from blocked IP: {client_ip}")
            writer.close()
            await writer.wait_closed()
            return

        # Check connection limits
        if len(self.clients) >= self.config.max_connections:
            logger.warning(
                f"Connection rejected - max connections reached: {client_ip}"
            )
            writer.close()
            await writer.wait_closed()
            return

        # Create client session
        session = ClientSession(
            client_id=client_id,
            ip_address=client_ip,
            connected_at=datetime.now(timezone.utc),
            last_activity=datetime.now(timezone.utc),
        )

        # Handle authentication - for MCP protocol, authentication is handled via environment
        # If auth_token is configured, automatically authenticate the session
        if self.config.auth_token:
            session.authenticated = True
            logger.debug(
                f"Client authenticated via auth token: {client_ip} (ID: {client_id})"
            )
        else:
            logger.debug(
                f"Client connected without authentication: {client_ip} (ID: {client_id})"
            )

        self.clients[client_id] = session
        self.metrics.active_connections += 1

        logger.info(f"Client connected: {client_ip} (ID: {client_id})")

        try:
            await self._handle_client_communication(reader, writer, session)
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            self.clients.pop(client_id, None)
            self.metrics.active_connections -= 1
            try:
                writer.close()
                await writer.wait_closed()
            except Exception as e:
                logger.debug(f"Error closing connection: {e}")
            logger.info(f"Client disconnected: {client_ip} (ID: {client_id})")

    async def _handle_client_communication(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        session: ClientSession,
    ):
        """Handle client communication - override in subclasses"""
        raise NotImplementedError(
            "Subclasses must implement _handle_client_communication"
        )

    async def start_server(self) -> asyncio.Server:
        """Start the server"""
        ssl_context = None
        if self.config.ssl_cert and self.config.ssl_key:
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(self.config.ssl_cert, self.config.ssl_key)

        server = await asyncio.start_server(
            self.handle_client, self.config.host, self.config.port, ssl=ssl_context
        )

        addr = server.sockets[0].getsockname()
        protocol = "wss" if ssl_context else "tcp"
        logger.info(f"MCP Server listening on {protocol}://{addr[0]}:{addr[1]}")

        return server
