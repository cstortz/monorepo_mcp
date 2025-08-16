#!/usr/bin/env python3
"""
Endpoint Validation Script

This script validates that all endpoints from the database_ws service
are properly implemented in the PostgreSQL MCP server.
"""

import asyncio
import aiohttp
import sys
import os
from pathlib import Path
from typing import Dict, List, Any

# Add the core module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.config import ConfigManager
from servers.postgres_server.server import PostgreSQLTools, PostgreSQLMCPServer


# Database WS endpoints from the service
DATABASE_WS_ENDPOINTS = {
    # Root endpoint
    "GET /": "Root endpoint - API information",
    
    # Admin endpoints
    "GET /admin/health": "Health check endpoint",
    "GET /admin/test-connection": "Test database connection",
    "GET /admin/db-info": "Get database information",
    "GET /admin/databases": "List all databases",
    "GET /admin/schemas": "List all schemas",
    "GET /admin/tables": "List all tables",
    "GET /admin/tables/{schema_name}": "List tables in specific schema",
    
    # CRUD endpoints
    "POST /crud/raw-sql": "Execute raw SQL (read-only)",
    "POST /crud/raw-sql/write": "Execute raw SQL (write operations)",
    "GET /crud/{schema_name}/{table_name}": "Read records from table",
    "GET /crud/{schema_name}/{table_name}/{record_id}": "Read specific record",
    "POST /crud/{schema_name}/{table_name}": "Create new record",
    "PUT /crud/{schema_name}/{table_name}/{record_id}": "Update record",
    "DELETE /crud/{schema_name}/{table_name}/{record_id}": "Delete record",
    "PATCH /crud/{schema_name}/{table_name}/{record_id}": "Upsert record"
}

# MCP Server tools mapping to database_ws endpoints
MCP_TOOLS_MAPPING = {
    "database_health": "GET /admin/health",
    "database_info": "GET /admin/db-info",
    "test_connection": "GET /admin/test-connection",
    "list_databases": "GET /admin/databases", 
    "list_schemas": "GET /admin/schemas",
    "list_tables": "GET /admin/tables",  # Also supports GET /admin/tables/{schema_name}
    "execute_sql": "POST /crud/raw-sql",
    "execute_write_sql": "POST /crud/raw-sql/write",
    "read_records": "GET /crud/{schema_name}/{table_name}",
    "read_record": "GET /crud/{schema_name}/{table_name}/{record_id}",
    "create_record": "POST /crud/{schema_name}/{table_name}",
    "update_record": "PUT /crud/{schema_name}/{table_name}/{record_id}",
    "delete_record": "DELETE /crud/{schema_name}/{table_name}/{record_id}",
    "upsert_record": "PATCH /crud/{schema_name}/{table_name}/{record_id}"
}

# Missing endpoints that don't have direct MCP tool equivalents
MISSING_ENDPOINTS = [
    "GET /"
]


async def test_database_ws_endpoints():
    """Test all database_ws endpoints directly"""
    base_url = "http://dev01.int.stortz.tech:8000"
    
    print("🔍 Testing Database WS Endpoints Directly")
    print("=" * 50)
    
    results = {}
    
    async with aiohttp.ClientSession() as session:
        # Test root endpoint
        try:
            async with session.get(f"{base_url}/") as response:
                results["GET /"] = {
                    "status": response.status,
                    "available": response.status == 200,
                    "response": await response.json() if response.status == 200 else None
                }
                print(f"✅ GET / - Status: {response.status}")
        except Exception as e:
            results["GET /"] = {"status": "error", "available": False, "error": str(e)}
            print(f"❌ GET / - Error: {e}")
        
        # Test admin endpoints
        admin_endpoints = [
            "/admin/health",
            "/admin/test-connection", 
            "/admin/db-info",
            "/admin/databases",
            "/admin/schemas",
            "/admin/tables"
        ]
        
        for endpoint in admin_endpoints:
            try:
                async with session.get(f"{base_url}{endpoint}") as response:
                    results[f"GET {endpoint}"] = {
                        "status": response.status,
                        "available": response.status == 200,
                        "response": await response.json() if response.status == 200 else None
                    }
                    print(f"✅ GET {endpoint} - Status: {response.status}")
            except Exception as e:
                results[f"GET {endpoint}"] = {"status": "error", "available": False, "error": str(e)}
                print(f"❌ GET {endpoint} - Error: {e}")
    
    return results


async def test_mcp_server_tools():
    """Test MCP server tools and their corresponding endpoints"""
    print("\n🔧 Testing MCP Server Tools")
    print("=" * 50)
    
    # Load configuration
    config_path = Path(__file__).parent / "config.yaml"
    config_manager = ConfigManager(str(config_path))
    config = config_manager.load_config()
    
    # Create PostgreSQL tools instance
    postgres_tools = PostgreSQLTools(config)
    
    # Get all available tools
    tools = postgres_tools.get_tools()
    
    print(f"📋 Available MCP Tools ({len(tools)}):")
    for tool_name in sorted(tools.keys()):
        print(f"  - {tool_name}")
    
    # Check mapping
    print(f"\n🔗 MCP Tools to Database WS Endpoints Mapping:")
    for tool_name, endpoint in MCP_TOOLS_MAPPING.items():
        if tool_name in tools:
            print(f"  ✅ {tool_name} → {endpoint}")
        else:
            print(f"  ❌ {tool_name} → {endpoint} (MISSING)")
    
    return tools


def analyze_coverage():
    """Analyze endpoint coverage"""
    print("\n📊 Endpoint Coverage Analysis")
    print("=" * 50)
    
    # Count endpoints
    total_endpoints = len(DATABASE_WS_ENDPOINTS)
    mapped_endpoints = len(MCP_TOOLS_MAPPING)
    missing_endpoints = len(MISSING_ENDPOINTS)
    
    print(f"📈 Coverage Statistics:")
    print(f"  - Total Database WS Endpoints: {total_endpoints}")
    print(f"  - Mapped to MCP Tools: {mapped_endpoints}")
    print(f"  - Missing from MCP Tools: {missing_endpoints}")
    print(f"  - Coverage: {(mapped_endpoints/total_endpoints)*100:.1f}%")
    
    print(f"\n❌ Missing Endpoints:")
    for endpoint in MISSING_ENDPOINTS:
        print(f"  - {endpoint}: {DATABASE_WS_ENDPOINTS[endpoint]}")
    
    print(f"\n💡 Recommendations:")
    if missing_endpoints > 0:
        print(f"  - Consider adding MCP tools for missing endpoints")
        print(f"  - Some endpoints may be internal/admin only")
    else:
        print(f"  - All endpoints are covered! 🎉")


async def test_mcp_server_functionality():
    """Test actual MCP server functionality"""
    print("\n🧪 Testing MCP Server Functionality")
    print("=" * 50)
    
    # Load configuration
    config_path = Path(__file__).parent / "config.yaml"
    config_manager = ConfigManager(str(config_path))
    config = config_manager.load_config()
    
    # Create PostgreSQL tools instance
    postgres_tools = PostgreSQLTools(config)
    
    # Test a few key tools
    test_cases = [
        ("database_health", {}),
        ("list_databases", {}),
        ("list_schemas", {}),
    ]
    
    for tool_name, args in test_cases:
        try:
            print(f"🔧 Testing {tool_name}...")
            result = await postgres_tools.__getattribute__(tool_name)(args, None)
            
            if "isError" in result and result["isError"]:
                print(f"  ❌ {tool_name} failed: {result['content'][0]['text']}")
            else:
                print(f"  ✅ {tool_name} succeeded")
                
        except Exception as e:
            print(f"  ❌ {tool_name} error: {e}")


async def main():
    """Main validation function"""
    print("🔍 PostgreSQL MCP Server Endpoint Validation")
    print("=" * 60)
    print(f"🎯 Target Database Service: http://dev01.int.stortz.tech:8000")
    print(f"📁 MCP Server: {Path(__file__).parent}")
    print()
    
    # Test database_ws endpoints directly
    db_ws_results = await test_database_ws_endpoints()
    
    # Test MCP server tools
    mcp_tools = await test_mcp_server_tools()
    
    # Analyze coverage
    analyze_coverage()
    
    # Test MCP server functionality
    await test_mcp_server_functionality()
    
    # Summary
    print("\n📋 Validation Summary")
    print("=" * 50)
    
    available_endpoints = sum(1 for result in db_ws_results.values() if result.get("available", False))
    total_endpoints = len(db_ws_results)
    
    print(f"✅ Database WS Endpoints Available: {available_endpoints}/{total_endpoints}")
    print(f"✅ MCP Tools Implemented: {len(mcp_tools)}")
    print(f"✅ MCP Tools Mapped to Endpoints: {len(MCP_TOOLS_MAPPING)}")
    
    if available_endpoints == total_endpoints and len(mcp_tools) >= len(MCP_TOOLS_MAPPING):
        print("\n🎉 All endpoints are properly implemented and accessible!")
    else:
        print("\n⚠️  Some endpoints may need attention.")
    
    print(f"\n📚 For detailed endpoint documentation, see:")
    print(f"   - Database WS: /home/cstortz/repos/database_ws/README.md")
    print(f"   - MCP Server: {Path(__file__).parent}/README.md")


if __name__ == "__main__":
    asyncio.run(main())
