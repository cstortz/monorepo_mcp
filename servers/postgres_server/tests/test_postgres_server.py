"""
Tests for PostgreSQL MCP Server
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock

# Add the core module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from servers.postgres_server.server import PostgreSQLMCPServer, PostgreSQLTools
from core.security import ClientSession
from core.config import ServerConfig
from datetime import datetime


class TestPostgreSQLTools:
    """Test PostgreSQL tools functionality"""
    
    @pytest.fixture
    def postgres_tools(self):
        """Create PostgreSQL tools instance"""
        config = ServerConfig(
            database_service_url="http://localhost:8000",
            database_service_timeout=30,
            database_service_retry_attempts=3
        )
        return PostgreSQLTools(config)
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock client session"""
        return ClientSession(
            client_id="test_client",
            ip_address="127.0.0.1",
            connected_at=datetime.now(),
            last_activity=datetime.now()
        )
    
    @pytest.mark.asyncio
    async def test_database_health_success(self, postgres_tools, mock_session):
        """Test successful database health check"""
        mock_response = {
            "status": "healthy",
            "version": "15.1",
            "uptime": "2 days",
            "active_connections": 5,
            "max_connections": 100
        }
        
        with patch.object(postgres_tools, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await postgres_tools.database_health({}, mock_session)
            
            assert not result.get("isError", False)
            assert "✅ PostgreSQL Health Check" in result["content"][0]["text"]
            assert "Status: healthy" in result["content"][0]["text"]
            mock_request.assert_called_once_with("/admin/health")
    
    @pytest.mark.asyncio
    async def test_database_health_failure(self, postgres_tools, mock_session):
        """Test database health check failure"""
        mock_response = {"error": "Connection failed"}
        
        with patch.object(postgres_tools, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await postgres_tools.database_health({}, mock_session)
            
            assert result.get("isError", False)
            assert "❌ PostgreSQL Health Check Failed" in result["content"][0]["text"]
    
    @pytest.mark.asyncio
    async def test_list_databases_success(self, postgres_tools, mock_session):
        """Test successful database listing"""
        mock_response = {
            "databases": [
                {"name": "test_db", "size": "1MB", "tables": 10},
                {"name": "prod_db", "size": "100MB", "tables": 50}
            ]
        }
        
        with patch.object(postgres_tools, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await postgres_tools.list_databases({}, mock_session)
            
            assert not result.get("isError", False)
            assert "🗄️ PostgreSQL Databases (2)" in result["content"][0]["text"]
            assert "test_db" in result["content"][0]["text"]
            assert "prod_db" in result["content"][0]["text"]
    
    @pytest.mark.asyncio
    async def test_execute_sql_success(self, postgres_tools, mock_session):
        """Test successful SQL execution"""
        mock_response = {
            "rows": [["1", "John"], ["2", "Jane"]],
            "columns": ["id", "name"],
            "row_count": 2
        }
        
        with patch.object(postgres_tools, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await postgres_tools.execute_sql({"sql": "SELECT * FROM users"}, mock_session)
            
            assert not result.get("isError", False)
            assert "✅ SQL Query Results" in result["content"][0]["text"]
            assert "Rows returned: 2" in result["content"][0]["text"]
            mock_request.assert_called_once_with("/query", method="POST", data={
                "sql": "SELECT * FROM users",
                "parameters": {},
                "readonly": True
            })
    
    @pytest.mark.asyncio
    async def test_execute_sql_failure(self, postgres_tools, mock_session):
        """Test SQL execution failure"""
        mock_response = {"error": "Syntax error"}
        
        with patch.object(postgres_tools, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await postgres_tools.execute_sql({"sql": "INVALID SQL"}, mock_session)
            
            assert result.get("isError", False)
            assert "❌ SQL execution failed" in result["content"][0]["text"]
    
    @pytest.mark.asyncio
    async def test_create_record_success(self, postgres_tools, mock_session):
        """Test successful record creation"""
        mock_response = {
            "rows": [["123"]],
            "affected_rows": 1
        }
        
        with patch.object(postgres_tools, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await postgres_tools.create_record({
                "schema_name": "public",
                "table_name": "users",
                "data": {"name": "John", "email": "john@example.com"}
            }, mock_session)
            
            assert not result.get("isError", False)
            assert "✅ Record created successfully" in result["content"][0]["text"]
            assert "New ID: 123" in result["content"][0]["text"]
    
    def test_get_tools(self, postgres_tools):
        """Test that all tools are properly defined"""
        tools = postgres_tools.get_tools()
        
        expected_tools = [
            "database_health", "list_databases", "list_schemas", "list_tables",
            "execute_sql", "execute_write_sql", "read_records", "read_record",
            "create_record", "update_record", "delete_record"
        ]
        
        for tool_name in expected_tools:
            assert tool_name in tools
            assert "name" in tools[tool_name]
            assert "description" in tools[tool_name]
            assert "inputSchema" in tools[tool_name]


class TestPostgreSQLMCPServer:
    """Test PostgreSQL MCP Server functionality"""
    
    @pytest.fixture
    def server(self):
        """Create PostgreSQL MCP server instance"""
        server = PostgreSQLMCPServer()
        # Set up a mock configuration
        server.config = ServerConfig(
            database_service_url="http://localhost:8000",
            database_service_timeout=30,
            database_service_retry_attempts=3
        )
        return server
    
    def test_server_initialization(self, server):
        """Test server initialization"""
        assert server.server_name == "postgresql-mcp-server"
        assert server.server_version == "1.0.0"
        assert server.postgres_tools is None
    
    def test_register_server_tools(self, server):
        """Test server tools registration"""
        # Tools should be empty before registration
        assert len(server.tools) == 0
        
        # Register tools
        server.register_server_tools()
        
        # Should have admin tools, file tools, and PostgreSQL tools
        assert len(server.tools) > 0
        
        # Check for PostgreSQL-specific tools
        postgres_tools = [
            "database_health", "list_databases", "list_schemas", "list_tables",
            "execute_sql", "execute_write_sql", "read_records", "read_record",
            "create_record", "update_record", "delete_record"
        ]
        
        for tool_name in postgres_tools:
            assert tool_name in server.tools
            assert tool_name in server.tool_handlers
    
    def test_admin_tools_included(self, server):
        """Test that admin tools are included"""
        # Mock the components that would be set up in setup_components
        from core.metrics import MetricsCollector
        from core.tools import AdminTools, FileTools
        
        server.metrics = MetricsCollector()
        server.admin_tools = AdminTools(server.metrics)
        server.file_tools = FileTools()
        
        # Register all tools
        server._register_admin_tools()
        server._register_file_tools()
        server.register_server_tools()
        
        admin_tools = ["get_system_info", "echo", "get_metrics", "health_check"]
        for tool_name in admin_tools:
            assert tool_name in server.tools
    
    def test_file_tools_included(self, server):
        """Test that file tools are included"""
        # Mock the components that would be set up in setup_components
        from core.metrics import MetricsCollector
        from core.tools import AdminTools, FileTools
        
        server.metrics = MetricsCollector()
        server.admin_tools = AdminTools(server.metrics)
        server.file_tools = FileTools()
        
        # Register all tools
        server._register_admin_tools()
        server._register_file_tools()
        server.register_server_tools()
        
        file_tools = ["list_files", "read_file"]
        for tool_name in file_tools:
            assert tool_name in server.tools


if __name__ == "__main__":
    pytest.main([__file__])
