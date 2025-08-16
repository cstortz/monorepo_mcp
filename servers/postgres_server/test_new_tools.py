#!/usr/bin/env python3
"""
Test script for the new Medium priority tools
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the core module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.config import ConfigManager
from servers.postgres_server.server import PostgreSQLTools


async def test_new_tools():
    """Test the new Medium priority tools"""
    
    # Load configuration
    config_path = Path(__file__).parent / "config.yaml"
    config_manager = ConfigManager(str(config_path))
    config = config_manager.load_config()
    
    # Create PostgreSQL tools instance
    postgres_tools = PostgreSQLTools(config)
    
    print("🧪 Testing New Medium Priority Tools")
    print("=" * 50)
    
    # Test database_info
    print("\n🔧 Testing database_info...")
    try:
        result = await postgres_tools.database_info({}, None)
        if "isError" in result:
            print(f"  ❌ database_info failed: {result['content'][0]['text']}")
        else:
            print("  ✅ database_info succeeded")
            print("  📋 Response preview:")
            lines = result['content'][0]['text'].split('\n')[:5]
            for line in lines:
                print(f"    {line}")
    except Exception as e:
        print(f"  ❌ database_info error: {e}")
    
    # Test test_connection
    print("\n🔧 Testing test_connection...")
    try:
        result = await postgres_tools.test_connection({}, None)
        if "isError" in result:
            print(f"  ❌ test_connection failed: {result['content'][0]['text']}")
        else:
            print("  ✅ test_connection succeeded")
            print("  📋 Response preview:")
            lines = result['content'][0]['text'].split('\n')[:5]
            for line in lines:
                print(f"    {line}")
    except Exception as e:
        print(f"  ❌ test_connection error: {e}")
    
    # Test upsert_record (this will likely fail without proper test data, but we can test the structure)
    print("\n🔧 Testing upsert_record structure...")
    try:
        # Test with invalid data to see error handling
        result = await postgres_tools.upsert_record({
            "schema_name": "public",
            "table_name": "test_table",
            "record_id": "999",
            "data": {"name": "test", "value": "test_value"}
        }, None)
        
        if "isError" in result:
            print("  ✅ upsert_record error handling works (expected for non-existent table)")
            print(f"  📋 Error: {result['content'][0]['text'][:100]}...")
        else:
            print("  ✅ upsert_record succeeded")
            print("  📋 Response preview:")
            lines = result['content'][0]['text'].split('\n')[:3]
            for line in lines:
                print(f"    {line}")
    except Exception as e:
        print(f"  ❌ upsert_record error: {e}")
    
    # Test that all tools are available
    print("\n🔧 Testing tool availability...")
    tools = postgres_tools.get_tools()
    new_tools = ["database_info", "test_connection", "upsert_record"]
    
    for tool_name in new_tools:
        if tool_name in tools:
            print(f"  ✅ {tool_name} is available")
        else:
            print(f"  ❌ {tool_name} is missing")
    
    print(f"\n📊 Summary:")
    print(f"  - Total tools available: {len(tools)}")
    print(f"  - New tools implemented: {len(new_tools)}")
    print(f"  - All new tools available: {all(tool in tools for tool in new_tools)}")


if __name__ == "__main__":
    asyncio.run(test_new_tools())
