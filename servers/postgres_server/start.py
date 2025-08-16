#!/usr/bin/env python3
"""
PostgreSQL MCP Server Startup Script

This script starts the PostgreSQL MCP server with proper configuration and signal handling.
"""

import asyncio
import signal
import sys
import os
from pathlib import Path

# Add the core module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from servers.postgres_server.server import PostgreSQLMCPServer


async def main():
    """Main function to start the PostgreSQL MCP server"""
    # Get the directory of this script
    script_dir = Path(__file__).parent
    config_path = script_dir / "config.yaml"
    
    # Create server instance
    server = PostgreSQLMCPServer()
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}, shutting down...")
        server.stop_server()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        print("🚀 Starting PostgreSQL MCP Server...")
        print(f"📁 Config path: {config_path}")
        print(f"🔧 Server name: {server.server_name}")
        print(f"📦 Version: {server.server_version}")
        
        # Start the server
        await server.start_server(str(config_path))
        
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
