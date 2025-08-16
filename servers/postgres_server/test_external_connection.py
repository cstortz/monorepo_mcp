#!/usr/bin/env python3
"""
Test script to verify connection to external database service
"""

import asyncio
import aiohttp
import sys
import os
from pathlib import Path

# Add the core module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.config import ConfigManager
from servers.postgres_server.server import PostgreSQLTools


async def test_database_service_connection():
    """Test connection to the external database service"""
    
    # Load configuration
    config_path = Path(__file__).parent / "config.yaml"
    config_manager = ConfigManager(str(config_path))
    config = config_manager.load_config()  # Load the configuration first
    
    print(f"🔧 Configuration loaded from: {config_path}")
    print(f"🌐 Database service URL: {config.database_service_url}")
    
    # Create PostgreSQL tools instance
    postgres_tools = PostgreSQLTools(config)
    
    print(f"🔗 Testing connection to: {postgres_tools.database_url}")
    
    # Test health endpoint
    print("\n🏥 Testing health endpoint...")
    try:
        result = await postgres_tools.database_health({}, None)
        if "isError" in result:
            print(f"❌ Health check failed: {result['content'][0]['text']}")
            return False
        else:
            print("✅ Health check successful!")
            print(result['content'][0]['text'])
            return True
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test databases endpoint
    print("\n🗄️ Testing databases endpoint...")
    try:
        result = await postgres_tools.list_databases({}, None)
        if "isError" in result:
            print(f"❌ Database list failed: {result['content'][0]['text']}")
            return False
        else:
            print("✅ Database list successful!")
            print(result['content'][0]['text'])
            return True
    except Exception as e:
        print(f"❌ Database list error: {e}")
        return False


async def test_direct_http_connection():
    """Test direct HTTP connection to the database service"""
    url = "http://dev01.int.stortz.tech:8000"
    
    print(f"\n🌐 Testing direct HTTP connection to: {url}")
    
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Test health endpoint
            async with session.get(f"{url}/admin/health") as response:
                print(f"📊 Health endpoint status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"📋 Health response: {data}")
                    return True
                else:
                    print(f"❌ Health endpoint failed: {await response.text()}")
                    return False
    except Exception as e:
        print(f"❌ Direct connection failed: {e}")
        return False


async def main():
    """Main test function"""
    print("🧪 Testing PostgreSQL MCP Server External Database Connection")
    print("=" * 60)
    
    # Test direct HTTP connection first
    direct_success = await test_direct_http_connection()
    
    if direct_success:
        print("\n✅ Direct HTTP connection successful!")
        
        # Test through PostgreSQL tools
        tools_success = await test_database_service_connection()
        
        if tools_success:
            print("\n🎉 All tests passed! The external database service is working correctly.")
        else:
            print("\n⚠️  Direct connection works but PostgreSQL tools failed.")
    else:
        print("\n❌ Direct HTTP connection failed. Please check:")
        print("   - Network connectivity to dev01.int.stortz.tech")
        print("   - Database service is running on port 8000")
        print("   - Firewall settings")


if __name__ == "__main__":
    asyncio.run(main())
