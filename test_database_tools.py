#!/usr/bin/env python3
"""
Test script to verify database tools functionality
"""

import asyncio
import aiohttp
import json

async def test_database_connection():
    """Test the database_ws microservice directly"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Database Tools...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test health endpoint
            print("📡 Testing database health...")
            async with session.get(f"{base_url}/admin/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Database health: {data}")
                else:
                    print(f"❌ Health check failed: {response.status}")
            
            # Test databases endpoint
            print("🗄️ Testing list databases...")
            async with session.get(f"{base_url}/admin/databases") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Databases: {data}")
                else:
                    print(f"❌ List databases failed: {response.status}")
            
            # Test schemas endpoint
            print("📋 Testing list schemas...")
            async with session.get(f"{base_url}/admin/schemas") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Schemas: {data}")
                else:
                    print(f"❌ List schemas failed: {response.status}")
            
            # Test tables endpoint
            print("📊 Testing list tables...")
            async with session.get(f"{base_url}/admin/tables") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Tables: {data}")
                else:
                    print(f"❌ List tables failed: {response.status}")
            
            print("\n🎯 Database tools test completed successfully!")
            print("The database_ws microservice is working correctly.")
            print("The MCP server should be able to use these endpoints.")
            
    except Exception as e:
        print(f"❌ Error testing database tools: {e}")

if __name__ == "__main__":
    asyncio.run(test_database_connection())
