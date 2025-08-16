#!/usr/bin/env python3
"""
Script to create a new MCP server from template

Usage: python create_server.py <server_name> <database_type> <port>
Example: python create_server.py mongodb_server mongodb 3005
"""

import os
import sys
import shutil
from pathlib import Path


def create_server(server_name: str, database_type: str, port: int):
    """Create a new server from template"""
    
    # Get the monorepo root directory
    monorepo_root = Path(__file__).parent.parent.parent
    template_dir = monorepo_root / "shared" / "templates" / "server_template"
    servers_dir = monorepo_root / "servers"
    new_server_dir = servers_dir / server_name
    
    # Check if server already exists
    if new_server_dir.exists():
        print(f"❌ Server '{server_name}' already exists at {new_server_dir}")
        return False
    
    # Create server directory
    new_server_dir.mkdir(parents=True, exist_ok=True)
    tests_dir = new_server_dir / "tests"
    tests_dir.mkdir(exist_ok=True)
    
    print(f"📁 Creating server directory: {new_server_dir}")
    
    # Copy template files
    template_files = [
        "__init__.py",
        "config.yaml",
        "server.py",
        "start.py"
    ]
    
    for file_name in template_files:
        template_file = template_dir / file_name
        new_file = new_server_dir / file_name
        
        if template_file.exists():
            # Read template content
            with open(template_file, 'r') as f:
                content = f.read()
            
            # Replace placeholders
            content = content.replace("your_database_type", database_type)
            content = content.replace("your_server_name", server_name)
            content = content.replace("your-database-mcp-server", f"{server_name}-mcp-server")
            content = content.replace("YourDatabase", database_type.title())
            content = content.replace("YourDatabaseTools", f"{database_type.title()}Tools")
            content = content.replace("YourDatabaseMCPServer", f"{database_type.title()}MCPServer")
            content = content.replace("your_database_tools", f"{database_type}_tools")
            content = content.replace("your_database", database_type)
            content = content.replace("3004", str(port))
            content = content.replace("27017", str(get_default_port(database_type)))
            content = content.replace("your_database_name", database_type)
            content = content.replace("your_username", database_type)
            content = content.replace("YOUR_DB_PASSWORD", f"{database_type.upper()}_PASSWORD")
            content = content.replace("your_server_mcp_server.log", f"{server_name}_mcp_server.log")
            content = content.replace("Your Database", database_type.title())
            content = content.replace("Your custom tool", f"{database_type.title()} custom tool")
            
            # Write new file
            with open(new_file, 'w') as f:
                f.write(content)
            
            print(f"✅ Created {file_name}")
    
    # Create __init__.py for tests directory
    tests_init = tests_dir / "__init__.py"
    tests_init.write_text('"""Tests for {} MCP Server"""\n'.format(database_type.title()))
    
    # Create basic test file
    test_file = tests_dir / f"test_{server_name}.py"
    test_content = f'''"""
Tests for {database_type.title()} MCP Server
"""

import pytest
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock

# Add the core module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from servers.{server_name}.server import {database_type.title()}MCPServer, {database_type.title()}Tools
from core.security import ClientSession
from datetime import datetime


class Test{database_type.title()}Tools:
    """Test {database_type.title()} tools functionality"""
    
    @pytest.fixture
    def {database_type}_tools(self):
        """Create {database_type.title()} tools instance"""
        return {database_type.title()}Tools("http://localhost:8000")
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock client session"""
        return ClientSession(
            client_id="test_client",
            ip_address="127.0.0.1",
            connected_at=datetime.now(),
            last_activity=datetime.now()
        )
    
    def test_get_tools(self, {database_type}_tools):
        """Test that all tools are properly defined"""
        tools = {database_type}_tools.get_tools()
        
        expected_tools = ["database_health"]
        for tool_name in expected_tools:
            assert tool_name in tools
            assert "name" in tools[tool_name]
            assert "description" in tools[tool_name]
            assert "inputSchema" in tools[tool_name]


class Test{database_type.title()}MCPServer:
    """Test {database_type.title()} MCP Server functionality"""
    
    @pytest.fixture
    def server(self):
        """Create {database_type.title()} MCP server instance"""
        return {database_type.title()}MCPServer()
    
    def test_server_initialization(self, server):
        """Test server initialization"""
        assert server.server_name == "{server_name}-mcp-server"
        assert server.server_version == "1.0.0"
        assert server.{database_type}_tools is None
    
    def test_register_server_tools(self, server):
        """Test server tools registration"""
        # Tools should be empty before registration
        assert len(server.tools) == 0
        
        # Register tools
        server.register_server_tools()
        
        # Should have admin tools, file tools, and {database_type.title()} tools
        assert len(server.tools) > 0
        
        # Check for {database_type.title()}-specific tools
        {database_type}_tools = ["database_health"]
        
        for tool_name in {database_type}_tools:
            assert tool_name in server.tools
            assert tool_name in server.tool_handlers


if __name__ == "__main__":
    pytest.main([__file__])
'''
    
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    print(f"✅ Created test file: {test_file}")
    
    # Create README for the server
    readme_file = new_server_dir / "README.md"
    readme_content = f"""# {database_type.title()} MCP Server

This is the {database_type.title()} MCP server implementation for the monorepo.

## Features

- Database health monitoring
- Custom {database_type.title()} tools
- Admin tools (system info, metrics, health checks)
- File tools (list files, read files)
- Security features (authentication, rate limiting, IP filtering)

## Configuration

Edit `config.yaml` to configure:
- Server host and port
- Database connection settings
- Security settings
- Rate limiting
- Logging

## Usage

1. Install dependencies:
   ```bash
   pip install -r ../../requirements.txt
   ```

2. Set environment variables:
   ```bash
   export MCP_AUTH_TOKEN="your-auth-token"
   export {database_type.upper()}_PASSWORD="your-database-password"
   ```

3. Start the server:
   ```bash
   python start.py
   ```

## Testing

Run tests:
```bash
python -m pytest tests/
```

## Tools

### Admin Tools (Available in all servers)
- `get_system_info` - Get system information
- `echo` - Echo a message
- `get_metrics` - Get server metrics
- `health_check` - Perform health check

### File Tools (Available in all servers)
- `list_files` - List files in directory
- `read_file` - Read file contents

### {database_type.title()} Tools
- `database_health` - Check {database_type.title()} service health
- Add your custom tools here
"""
    
    with open(readme_file, 'w') as f:
        f.write(readme_content)
    
    print(f"✅ Created README: {readme_file}")
    
    print(f"\n🎉 Successfully created {database_type.title()} MCP server!")
    print(f"📁 Server directory: {new_server_dir}")
    print(f"🔧 Server name: {server_name}")
    print(f"🌐 Port: {port}")
    print(f"🗄️ Database type: {database_type}")
    
    print(f"\n📝 Next steps:")
    print(f"1. Edit {new_server_dir}/config.yaml to configure your database")
    print(f"2. Add your custom tools to {new_server_dir}/server.py")
    print(f"3. Set up your database service")
    print(f"4. Test the server: cd {new_server_dir} && python start.py")
    
    return True


def get_default_port(database_type: str) -> int:
    """Get default port for database type"""
    default_ports = {
        "mongodb": 27017,
        "elasticsearch": 9200,
        "cassandra": 9042,
        "neo4j": 7687,
        "influxdb": 8086,
        "couchdb": 5984,
        "dynamodb": 8000,
        "sqlite": 0,  # No port for SQLite
        "postgresql": 5432,
        "mysql": 3306,
        "redis": 6379
    }
    
    return default_ports.get(database_type.lower(), 27017)


def main():
    """Main function"""
    if len(sys.argv) != 4:
        print("Usage: python create_server.py <server_name> <database_type> <port>")
        print("Example: python create_server.py mongodb_server mongodb 3005")
        sys.exit(1)
    
    server_name = sys.argv[1]
    database_type = sys.argv[2]
    port = int(sys.argv[3])
    
    # Validate port
    if not (1 <= port <= 65535):
        print("❌ Port must be between 1 and 65535")
        sys.exit(1)
    
    # Create server
    success = create_server(server_name, database_type, port)
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
