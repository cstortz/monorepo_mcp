#!/usr/bin/env python3
"""
PostgreSQL MCP Server - Main entry point
"""

import asyncio
import argparse
import logging
import os
import signal
import sys
import yaml
from pathlib import Path

from ..mcp_core import ServerConfig, setup_logging
from .server import PostgresMCPServer


async def main():
    """Main entry point for the Database MCP Server"""
    parser = argparse.ArgumentParser(description='PostgreSQL MCP Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=3003, help='Port to bind to')
    parser.add_argument('--ssl-cert', help='SSL certificate file')
    parser.add_argument('--ssl-key', help='SSL private key file')
    parser.add_argument('--auth-token', help='Authentication token')
    parser.add_argument('--no-auth', action='store_true', help='Disable authentication')
    parser.add_argument('--max-connections', type=int, default=50, help='Maximum connections')
    parser.add_argument('--rate-limit', type=int, default=100, help='Rate limit (requests per minute)')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--database-url', help='Database service URL (defaults to DATABASE_WS_URL env var)')
    
    args = parser.parse_args()
    
    # Setup logging
    global logger
    logger = setup_logging(args.log_level)
    
    # Load configuration from file if provided
    config_data = {}
    if args.config and os.path.exists(args.config):
        try:
            with open(args.config, 'r') as f:
                config_data = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {args.config}")
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
            sys.exit(1)
    
    # Create configuration
    config = ServerConfig(
        host=config_data.get('server', {}).get('host', args.host),
        port=config_data.get('server', {}).get('port', args.port),
        ssl_cert=args.ssl_cert or config_data.get('server', {}).get('ssl_cert'),
        ssl_key=args.ssl_key or config_data.get('server', {}).get('ssl_key'),
        auth_enabled=not args.no_auth and config_data.get('security', {}).get('auth_enabled', True),
        auth_token=args.auth_token or os.getenv('MCP_AUTH_TOKEN') or config_data.get('security', {}).get('auth_token'),
        max_connections=args.max_connections or config_data.get('limits', {}).get('max_connections', 50),
        rate_limit_requests=args.rate_limit or config_data.get('rate_limiting', {}).get('requests_per_minute', 100),
        database_ws_url=args.database_url or os.getenv('DATABASE_WS_URL') or config_data.get('database', {}).get('ws_url', 'http://localhost:8000')
    )
    
    # Validate configuration
    if config.auth_enabled and not config.auth_token:
        logger.error("Authentication enabled but no token provided. Set MCP_AUTH_TOKEN env var or use --auth-token")
        sys.exit(1)
    
    if config.ssl_cert and not config.ssl_key:
        logger.error("SSL certificate provided but no private key")
        sys.exit(1)
    
    # Create and start server
    server_instance = PostgresMCPServer(config)
    server = await server_instance.start_server()
    
    # Graceful shutdown handling
    def signal_handler():
        logger.info("Received shutdown signal")
        server.close()
    
    for sig in [signal.SIGTERM, signal.SIGINT]:
        asyncio.get_event_loop().add_signal_handler(sig, signal_handler)
    
    try:
        async with server:
            await server.serve_forever()
    except asyncio.CancelledError:
        logger.info("Server cancelled")
    finally:
        await server.wait_closed()
        logger.info("PostgreSQL MCP Server stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


