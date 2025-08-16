"""
Redis MCP Server Implementation

This module provides a Redis-specific MCP server with database tools.
"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional
import sys
import os

# Add the core module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.base_server import BaseMCPServer
from core.security import ClientSession


class RedisTools:
    """Redis-specific tools"""
    
    def __init__(self, database_url: str = "http://localhost:8000"):
        self.database_url = database_url
    
    def get_tools(self) -> Dict[str, Any]:
        """Get Redis tools definitions"""
        return {
            "redis_health": {
                "name": "redis_health",
                "description": "Check Redis service health and connection",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "redis_keys": {
                "name": "redis_keys",
                "description": "List keys in Redis with pattern matching",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Key pattern to match (e.g., 'user:*')",
                            "default": "*"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of keys to return",
                            "default": 100
                        }
                    },
                    "required": []
                }
            },
            "redis_get": {
                "name": "redis_get",
                "description": "Get value for a Redis key",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "key": {
                            "type": "string",
                            "description": "Redis key to get"
                        }
                    },
                    "required": ["key"]
                }
            },
            "redis_set": {
                "name": "redis_set",
                "description": "Set value for a Redis key",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "key": {
                            "type": "string",
                            "description": "Redis key to set"
                        },
                        "value": {
                            "type": "string",
                            "description": "Value to set"
                        },
                        "expire": {
                            "type": "integer",
                            "description": "Expiration time in seconds (optional)"
                        }
                    },
                    "required": ["key", "value"]
                }
            },
            "redis_delete": {
                "name": "redis_delete",
                "description": "Delete a Redis key",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "key": {
                            "type": "string",
                            "description": "Redis key to delete"
                        }
                    },
                    "required": ["key"]
                }
            },
            "redis_scan": {
                "name": "redis_scan",
                "description": "Scan Redis keys with pattern matching",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Key pattern to match",
                            "default": "*"
                        },
                        "count": {
                            "type": "integer",
                            "description": "Number of keys to scan per iteration",
                            "default": 10
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of keys to return",
                            "default": 100
                        }
                    },
                    "required": []
                }
            }
        }
    
    async def _make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to the database service"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.database_url}{endpoint}"
                
                if method == "GET":
                    async with session.get(url) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            return {"error": f"HTTP {response.status}: {await response.text()}"}
                elif method == "POST":
                    async with session.post(url, json=data) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            return {"error": f"HTTP {response.status}: {await response.text()}"}
                else:
                    return {"error": f"Unsupported method: {method}"}
                    
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}
    
    async def redis_health(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """Check Redis service health"""
        result = await self._make_request("/admin/health")
        
        if "error" in result:
            content = f"❌ Redis Health Check Failed:\n{result['error']}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
        
        content = f"""✅ Redis Health Check:

Status: {result.get('status', 'Unknown')}
Version: {result.get('version', 'Unknown')}
Uptime: {result.get('uptime', 'Unknown')}
Connected Clients: {result.get('connected_clients', 'Unknown')}
Used Memory: {result.get('used_memory', 'Unknown')}
Total Keys: {result.get('total_keys', 'Unknown')}"""
        
        return {"content": [{"type": "text", "text": content}]}
    
    async def redis_keys(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """List Redis keys with pattern matching"""
        pattern = args.get("pattern", "*")
        limit = args.get("limit", 100)
        
        data = {
            "command": "KEYS",
            "args": [pattern],
            "limit": limit
        }
        
        result = await self._make_request("/redis/command", method="POST", data=data)
        
        if "error" in result:
            content = f"❌ Failed to list keys:\n{result['error']}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
        
        keys = result.get('result', [])
        content = f"🔑 Redis Keys (pattern: {pattern}):\n\n"
        content += f"Found {len(keys)} keys:\n\n"
        
        for key in keys[:limit]:
            content += f"• {key}\n"
        
        if len(keys) > limit:
            content += f"\n... and {len(keys) - limit} more keys"
        
        return {"content": [{"type": "text", "text": content}]}
    
    async def redis_get(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """Get value for a Redis key"""
        key = args.get("key")
        
        data = {
            "command": "GET",
            "args": [key]
        }
        
        result = await self._make_request("/redis/command", method="POST", data=data)
        
        if "error" in result:
            content = f"❌ Failed to get key '{key}':\n{result['error']}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
        
        value = result.get('result')
        
        if value is None:
            content = f"❌ Key '{key}' not found in Redis"
            return {"content": [{"type": "text", "text": content}], "isError": True}
        
        content = f"📖 Redis Key: {key}\n\n"
        content += f"Value:\n{value}\n\n"
        content += f"Type: {type(value).__name__}\n"
        content += f"Length: {len(str(value))} characters"
        
        return {"content": [{"type": "text", "text": content}]}
    
    async def redis_set(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """Set value for a Redis key"""
        key = args.get("key")
        value = args.get("value")
        expire = args.get("expire")
        
        data = {
            "command": "SET",
            "args": [key, value]
        }
        
        if expire:
            data["args"].extend(["EX", expire])
        
        result = await self._make_request("/redis/command", method="POST", data=data)
        
        if "error" in result:
            content = f"❌ Failed to set key '{key}':\n{result['error']}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
        
        content = f"✅ Redis Key Set Successfully:\n\n"
        content += f"Key: {key}\n"
        content += f"Value: {value}\n"
        if expire:
            content += f"Expiration: {expire} seconds\n"
        content += f"Result: {result.get('result', 'OK')}"
        
        return {"content": [{"type": "text", "text": content}]}
    
    async def redis_delete(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """Delete a Redis key"""
        key = args.get("key")
        
        data = {
            "command": "DEL",
            "args": [key]
        }
        
        result = await self._make_request("/redis/command", method="POST", data=data)
        
        if "error" in result:
            content = f"❌ Failed to delete key '{key}':\n{result['error']}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
        
        deleted_count = result.get('result', 0)
        
        if deleted_count == 0:
            content = f"❌ Key '{key}' not found in Redis"
            return {"content": [{"type": "text", "text": content}], "isError": True}
        
        content = f"✅ Redis Key Deleted Successfully:\n\n"
        content += f"Key: {key}\n"
        content += f"Keys deleted: {deleted_count}"
        
        return {"content": [{"type": "text", "text": content}]}
    
    async def redis_scan(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """Scan Redis keys with pattern matching"""
        pattern = args.get("pattern", "*")
        count = args.get("count", 10)
        limit = args.get("limit", 100)
        
        data = {
            "command": "SCAN",
            "args": [0, "MATCH", pattern, "COUNT", count]
        }
        
        result = await self._make_request("/redis/command", method="POST", data=data)
        
        if "error" in result:
            content = f"❌ Failed to scan keys:\n{result['error']}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
        
        scan_result = result.get('result', [])
        if isinstance(scan_result, list) and len(scan_result) >= 2:
            cursor = scan_result[0]
            keys = scan_result[1][:limit]
        else:
            cursor = 0
            keys = []
        
        content = f"🔍 Redis Key Scan Results:\n\n"
        content += f"Pattern: {pattern}\n"
        content += f"Cursor: {cursor}\n"
        content += f"Keys found: {len(keys)}\n\n"
        
        if keys:
            content += "Keys:\n"
            for key in keys:
                content += f"• {key}\n"
        else:
            content += "No keys found matching the pattern"
        
        return {"content": [{"type": "text", "text": content}]}


class RedisMCPServer(BaseMCPServer):
    """Redis MCP Server implementation"""
    
    def __init__(self):
        super().__init__("redis-mcp-server", "1.0.0")
        self.redis_tools = None
    
    def register_server_tools(self):
        """Register Redis-specific tools"""
        # Initialize Redis tools
        self.redis_tools = RedisTools()
        
        # Register tools
        redis_tools = self.redis_tools.get_tools()
        for tool_name, tool_def in redis_tools.items():
            self.tools[tool_name] = tool_def
            self.tool_handlers[tool_name] = getattr(self.redis_tools, tool_name)
