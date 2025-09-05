#!/usr/bin/env python3
"""
Entry point for the MCP REST API server
"""

import asyncio
import argparse
import os
import sys
import logging
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_core import ServerConfig, setup_logging
from mcp_rest_api.server import RestAPIMCPServer

async def main():
    """Main entry point for the MCP REST API server"""
    parser = argparse.ArgumentParser(description="MCP REST API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=3004, help="Port to bind to")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    parser.add_argument("--auth-token", help="Authentication token")
    parser.add_argument("--no-auth", action="store_true", help="Disable authentication")
    parser.add_argument("--resume-api-url", help="Resume API URL (defaults to RESUME_API_URL env var)")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Configuration priority: CLI arg → Environment var → Default
    resume_api_url = args.resume_api_url or os.getenv('RESUME_API_URL', 'http://dev01.int.stortz.tech:8002')
    auth_token = args.auth_token or os.getenv('MCP_AUTH_TOKEN')
    
    if args.no_auth:
        auth_token = None
    
    # Create server configuration
    config = ServerConfig(
        host=args.host,
        port=args.port,
        auth_token=auth_token,
        resume_api_url=resume_api_url
    )
    
    # Create and start server
    server = RestAPIMCPServer(config)
    
    try:
        logger.info(f"Starting MCP REST API server on {args.host}:{args.port}")
        logger.info(f"Resume API URL: {resume_api_url}")
        await server.start()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
