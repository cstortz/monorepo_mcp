#!/usr/bin/env python3
"""
Start Filesystem MCP Server
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_core import ServerConfig, setup_logging
from mcp_filesystem.server import FilesystemMCPServer


async def main():
    """Start the Filesystem MCP Server"""
    # Setup logging
    logger = setup_logging("INFO", "filesystem_mcp_server.log")
    
    # Create configuration
    config = ServerConfig(
        host="0.0.0.0",
        port=3004,
        auth_enabled=True,
        auth_token=os.getenv('MCP_AUTH_TOKEN', '6b649d2159b61bf69f0a05fd9fe03bd8ead6f8414271b69149bce3fcd1326aec'),
        max_connections=50,
        rate_limit_requests=100
    )
    
    # Create and start server
    server_instance = FilesystemMCPServer(config, base_path="/home/cstortz/repos")
    server = await server_instance.start_server()
    
    logger.info("Filesystem MCP Server started successfully")
    
    try:
        async with server:
            await server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    finally:
        await server.wait_closed()
        logger.info("Filesystem MCP Server stopped")


if __name__ == "__main__":
    asyncio.run(main())


