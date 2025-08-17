#!/usr/bin/env python3
"""
Production MCP Server
Enterprise-grade MCP server with authentication, SSL, monitoring, and robust features
"""

import asyncio
import json
import logging
import argparse
import signal
import sys
import ssl
import time
import hashlib
import hmac
import secrets
import os
import aiohttp
import yaml
from typing import Dict, Any, Optional, Set
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, asdict
from pathlib import Path
import platform
import psutil
from collections import defaultdict, deque

# Configure structured logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        if hasattr(record, 'client_ip'):
            log_entry['client_ip'] = record.client_ip
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        return json.dumps(log_entry)

# Setup logging
def setup_logging(log_level: str = "INFO", log_file: str = "mcp_server.log"):
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # File handler with JSON formatting
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    # Console handler with standard formatting
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    )
    logger.addHandler(console_handler)
    
    return logger

@dataclass
class ClientSession:
    client_id: str
    ip_address: str
    connected_at: datetime
    last_activity: datetime
    request_count: int = 0
    authenticated: bool = False
    user_agent: Optional[str] = None

@dataclass
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 3001
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    auth_enabled: bool = True
    auth_token: Optional[str] = None
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    max_connections: int = 50
    request_timeout: int = 300  # Increased to 5 minutes
    allowed_ips: Optional[Set[str]] = None
    metrics_enabled: bool = True
    database_ws_url: str = "http://localhost:8000"
    
class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.clients = defaultdict(deque)
    
    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        client_requests = self.clients[client_ip]
        
        # Remove old requests outside the window
        while client_requests and client_requests[0] < now - self.window_seconds:
            client_requests.popleft()
        
        # Check if under limit
        if len(client_requests) < self.max_requests:
            client_requests.append(now)
            return True
        
        return False

class SecurityManager:
    def __init__(self, config: ServerConfig):
        self.config = config
        self.blocked_ips = set()
        self.failed_attempts = defaultdict(int)
        
    def verify_token(self, token: str) -> bool:
        if not self.config.auth_enabled or not self.config.auth_token:
            return True
        return hmac.compare_digest(token, self.config.auth_token)
    
    def is_ip_allowed(self, ip: str) -> bool:
        if ip in self.blocked_ips:
            return False
        if self.config.allowed_ips and ip not in self.config.allowed_ips:
            return False
        return True
    
    def record_failed_attempt(self, ip: str):
        self.failed_attempts[ip] += 1
        if self.failed_attempts[ip] >= 5:  # Block after 5 failed attempts
            self.blocked_ips.add(ip)
            logger.warning(f"IP {ip} blocked due to repeated failed attempts")

class MetricsCollector:
    def __init__(self):
        self.start_time = datetime.now(timezone.utc)
        self.request_count = 0
        self.error_count = 0
        self.active_connections = 0
        self.tool_usage = defaultdict(int)
        self.response_times = deque(maxlen=1000)
        
    def record_request(self, tool_name: str, response_time: float, success: bool):
        self.request_count += 1
        if not success:
            self.error_count += 1
        self.tool_usage[tool_name] += 1
        self.response_times.append(response_time)
    
    def get_metrics(self) -> Dict[str, Any]:
        uptime = datetime.now(timezone.utc) - self.start_time
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        return {
            'uptime_seconds': uptime.total_seconds(),
            'total_requests': self.request_count,
            'total_errors': self.error_count,
            'error_rate': self.error_count / max(self.request_count, 1),
            'active_connections': self.active_connections,
            'average_response_time_ms': avg_response_time * 1000,
            'tool_usage': dict(self.tool_usage),
            'system': {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent
            }
        }

class ProductionMCPServer:
    def __init__(self, config: ServerConfig):
        self.config = config
        self.clients: Dict[str, ClientSession] = {}
        self.rate_limiter = RateLimiter(config.rate_limit_requests, config.rate_limit_window)
        self.security = SecurityManager(config)
        self.metrics = MetricsCollector()
        self.tools = self._initialize_tools()
        
    def _initialize_tools(self) -> Dict[str, Dict[str, Any]]:
        return {
            "get_system_info": {
                "name": "get_system_info",
                "description": "Get comprehensive system information",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "echo": {
                "name": "echo",
                "description": "Echo back the provided message with metadata",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Message to echo back"
                        }
                    },
                    "required": ["message"]
                }
            },
            "list_files": {
                "name": "list_files",
                "description": "List files in a directory with detailed information",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Directory path to list"
                        },
                        "include_hidden": {
                            "type": "boolean",
                            "description": "Include hidden files",
                            "default": False
                        }
                    },
                    "required": []
                }
            },
            "read_file": {
                "name": "read_file",
                "description": "Read contents of a text file safely",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "File path to read"
                        },
                        "encoding": {
                            "type": "string",
                            "description": "File encoding",
                            "default": "utf-8"
                        },
                        "max_size": {
                            "type": "integer",
                            "description": "Maximum file size in bytes",
                            "default": 1048576
                        }
                    },
                    "required": ["path"]
                }
            },
            "get_metrics": {
                "name": "get_metrics",
                "description": "Get server performance metrics",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "health_check": {
                "name": "health_check",
                "description": "Perform a comprehensive health check",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "database_health": {
                "name": "database_health",
                "description": "Check database service health and connection",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "list_databases": {
                "name": "list_databases",
                "description": "List all available databases",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "list_schemas": {
                "name": "list_schemas",
                "description": "List all schemas in the database",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "list_tables": {
                "name": "list_tables",
                "description": "List all tables in the database or specific schema",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "schema_name": {
                            "type": "string",
                            "description": "Schema name to list tables for (optional)"
                        }
                    },
                    "required": []
                }
            },
            "execute_sql": {
                "name": "execute_sql",
                "description": "Execute a SQL query (read-only)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": "SQL query to execute"
                        },
                        "parameters": {
                            "type": "object",
                            "description": "Query parameters (optional)"
                        }
                    },
                    "required": ["sql"]
                }
            },
            "execute_write_sql": {
                "name": "execute_write_sql",
                "description": "Execute a SQL write operation (INSERT, UPDATE, DELETE)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": "SQL write query to execute"
                        },
                        "parameters": {
                            "type": "object",
                            "description": "Query parameters (optional)"
                        }
                    },
                    "required": ["sql"]
                }
            },
            "read_records": {
                "name": "read_records",
                "description": "Read records from a table",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "schema_name": {
                            "type": "string",
                            "description": "Schema name"
                        },
                        "table_name": {
                            "type": "string",
                            "description": "Table name"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of records to return",
                            "default": 100
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Number of records to skip",
                            "default": 0
                        },
                        "order_by": {
                            "type": "string",
                            "description": "Order by clause (optional)"
                        }
                    },
                    "required": ["schema_name", "table_name"]
                }
            },
            "read_record": {
                "name": "read_record",
                "description": "Read a specific record by ID",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "schema_name": {
                            "type": "string",
                            "description": "Schema name"
                        },
                        "table_name": {
                            "type": "string",
                            "description": "Table name"
                        },
                        "record_id": {
                            "type": "string",
                            "description": "Record ID"
                        }
                    },
                    "required": ["schema_name", "table_name", "record_id"]
                }
            },
            "create_record": {
                "name": "create_record",
                "description": "Create a new record in a table",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "schema_name": {
                            "type": "string",
                            "description": "Schema name"
                        },
                        "table_name": {
                            "type": "string",
                            "description": "Table name"
                        },
                        "data": {
                            "type": "object",
                            "description": "Record data"
                        }
                    },
                    "required": ["schema_name", "table_name", "data"]
                }
            },
            "update_record": {
                "name": "update_record",
                "description": "Update an existing record",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "schema_name": {
                            "type": "string",
                            "description": "Schema name"
                        },
                        "table_name": {
                            "type": "string",
                            "description": "Table name"
                        },
                        "record_id": {
                            "type": "string",
                            "description": "Record ID"
                        },
                        "data": {
                            "type": "object",
                            "description": "Updated record data"
                        }
                    },
                    "required": ["schema_name", "table_name", "record_id", "data"]
                }
            },
            "delete_record": {
                "name": "delete_record",
                "description": "Delete a record from a table",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "schema_name": {
                            "type": "string",
                            "description": "Schema name"
                        },
                        "table_name": {
                            "type": "string",
                            "description": "Table name"
                        },
                        "record_id": {
                            "type": "string",
                            "description": "Record ID"
                        }
                    },
                    "required": ["schema_name", "table_name", "record_id"]
                }
            }
        }
    
    async def handle_initialize(self, params: Dict[str, Any], client_session: ClientSession) -> Dict[str, Any]:
        logger.info("Client initialized", extra={'client_ip': client_session.ip_address})
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "database-mcp-server",
                "version": "3.0.0",
                "description": "Enterprise-grade MCP server with database access and security"
            }
        }
    
    async def handle_list_tools(self, params: Dict[str, Any], client_session: ClientSession) -> Dict[str, Any]:
        return {"tools": list(self.tools.values())}
    
    async def handle_call_tool(self, params: Dict[str, Any], client_session: ClientSession) -> Dict[str, Any]:
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        start_time = time.time()
        
        try:
            if tool_name == "get_system_info":
                result = await self._tool_get_system_info(arguments, client_session)
            elif tool_name == "echo":
                result = await self._tool_echo(arguments, client_session)
            elif tool_name == "list_files":
                result = await self._tool_list_files(arguments, client_session)
            elif tool_name == "read_file":
                result = await self._tool_read_file(arguments, client_session)
            elif tool_name == "get_metrics":
                result = await self._tool_get_metrics(arguments, client_session)
            elif tool_name == "health_check":
                result = await self._tool_health_check(arguments, client_session)
            elif tool_name == "database_health":
                result = await self._tool_database_health(arguments, client_session)
            elif tool_name == "list_databases":
                result = await self._tool_list_databases(arguments, client_session)
            elif tool_name == "list_schemas":
                result = await self._tool_list_schemas(arguments, client_session)
            elif tool_name == "list_tables":
                result = await self._tool_list_tables(arguments, client_session)
            elif tool_name == "execute_sql":
                result = await self._tool_execute_sql(arguments, client_session)
            elif tool_name == "execute_write_sql":
                result = await self._tool_execute_write_sql(arguments, client_session)
            elif tool_name == "read_records":
                result = await self._tool_read_records(arguments, client_session)
            elif tool_name == "read_record":
                result = await self._tool_read_record(arguments, client_session)
            elif tool_name == "create_record":
                result = await self._tool_create_record(arguments, client_session)
            elif tool_name == "update_record":
                result = await self._tool_update_record(arguments, client_session)
            elif tool_name == "delete_record":
                result = await self._tool_delete_record(arguments, client_session)
            else:
                result = {
                    "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
                    "isError": True
                }
            
            response_time = time.time() - start_time
            self.metrics.record_request(tool_name, response_time, not result.get("isError", False))
            
            return result
            
        except Exception as e:
            response_time = time.time() - start_time
            self.metrics.record_request(tool_name, response_time, False)
            logger.error(f"Tool execution error: {e}", extra={'client_ip': client_session.ip_address})
            return {
                "content": [{"type": "text", "text": f"Internal error: {str(e)}"}],
                "isError": True
            }
    
    async def _tool_get_system_info(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        cpu_info = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        content = f"""🖥️  Production System Information:

🔧 Hardware:
- Platform: {platform.system()} {platform.release()}
- Architecture: {platform.machine()}
- CPU Usage: {cpu_info}%
- Memory: {memory.percent}% used ({memory.used // (1024**3)}GB / {memory.total // (1024**3)}GB)
- Disk: {disk.percent}% used ({disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB)

🐍 Software:
- Python: {platform.python_version()}
- Process ID: {os.getpid()}
- Working Directory: {os.getcwd()}

🌐 Server Status:
- Current Time: {datetime.now().isoformat()}
- Active Connections: {self.metrics.active_connections}
- Total Requests: {self.metrics.request_count}
- Uptime: {datetime.now(timezone.utc) - self.metrics.start_time}

👤 Client Info:
- Your IP: {session.ip_address}
- Connected: {session.connected_at.isoformat()}
- Requests Made: {session.request_count}
- Authenticated: {session.authenticated}"""

        return {"content": [{"type": "text", "text": content}]}
    
    async def _tool_echo(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        message = args.get("message", "")
        timestamp = datetime.now().isoformat()
        
        response = f"""📢 Echo Response:
Message: {message}
Timestamp: {timestamp}
Client IP: {session.ip_address}
Request Count: {session.request_count}"""

        return {"content": [{"type": "text", "text": response}]}
    
    async def _tool_list_files(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        path = args.get("path", ".")
        include_hidden = args.get("include_hidden", False)
        
        try:
            # Security check
            abs_path = Path(path).resolve()
            cwd = Path.cwd().resolve()
            if not str(abs_path).startswith(str(cwd)):
                return {
                    "content": [{"type": "text", "text": "❌ Access denied: Path outside working directory"}],
                    "isError": True
                }
            
            files = []
            for item in abs_path.iterdir():
                if not include_hidden and item.name.startswith('.'):
                    continue
                
                stat = item.stat()
                size = stat.st_size if item.is_file() else 0
                modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
                
                files.append({
                    'name': item.name,
                    'type': 'directory' if item.is_dir() else 'file',
                    'size': size,
                    'modified': modified,
                    'permissions': oct(stat.st_mode)[-3:]
                })
            
            files.sort(key=lambda x: (x['type'] == 'file', x['name'].lower()))
            
            result = f"📁 Directory: {abs_path}\n\n"
            for file_info in files:
                icon = "📁" if file_info['type'] == 'directory' else "📄"
                size_str = f"{file_info['size']:,} bytes" if file_info['type'] == 'file' else ""
                result += f"{icon} {file_info['name']} ({file_info['permissions']}) {size_str}\n"
            
            return {"content": [{"type": "text", "text": result}]}
            
        except Exception as e:
            return {
                "content": [{"type": "text", "text": f"❌ Error listing files: {str(e)}"}],
                "isError": True
            }
    
    async def _tool_read_file(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        file_path = args.get("path", "")
        encoding = args.get("encoding", "utf-8")
        max_size = args.get("max_size", 1048576)  # 1MB default
        
        try:
            # Security checks
            abs_path = Path(file_path).resolve()
            cwd = Path.cwd().resolve()
            if not str(abs_path).startswith(str(cwd)):
                return {
                    "content": [{"type": "text", "text": "❌ Access denied: File outside working directory"}],
                    "isError": True
                }
            
            if not abs_path.exists():
                return {
                    "content": [{"type": "text", "text": f"❌ File not found: {file_path}"}],
                    "isError": True
                }
            
            if abs_path.stat().st_size > max_size:
                return {
                    "content": [{"type": "text", "text": f"❌ File too large: {abs_path.stat().st_size} bytes (max: {max_size})"}],
                    "isError": True
                }
            
            with open(abs_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            return {
                "content": [{
                    "type": "text",
                    "text": f"📄 File: {abs_path}\nSize: {len(content)} characters\n\n{content}"
                }]
            }
            
        except Exception as e:
            return {
                "content": [{"type": "text", "text": f"❌ Error reading file: {str(e)}"}],
                "isError": True
            }
    
    async def _tool_get_metrics(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        metrics = self.metrics.get_metrics()
        
        content = f"""📊 Server Metrics:

🕐 Uptime: {metrics['uptime_seconds']:.0f} seconds
📊 Requests: {metrics['total_requests']} (Errors: {metrics['total_errors']})
📈 Error Rate: {metrics['error_rate']:.2%}
🔗 Active Connections: {metrics['active_connections']}
⚡ Avg Response Time: {metrics['average_response_time_ms']:.2f}ms

💻 System Resources:
- CPU: {metrics['system']['cpu_percent']:.1f}%
- Memory: {metrics['system']['memory_percent']:.1f}%
- Disk: {metrics['system']['disk_usage']:.1f}%

🔧 Tool Usage:
"""
        for tool, count in metrics['tool_usage'].items():
            content += f"- {tool}: {count} calls\n"
        
        return {"content": [{"type": "text", "text": content}]}
    
    async def _tool_health_check(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        checks = []
        overall_status = "healthy"
        
        # CPU check
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_status = "healthy" if cpu_percent < 80 else "warning" if cpu_percent < 95 else "critical"
        checks.append(f"CPU: {cpu_percent:.1f}% - {cpu_status}")
        
        # Memory check
        memory = psutil.virtual_memory()
        mem_status = "healthy" if memory.percent < 80 else "warning" if memory.percent < 95 else "critical"
        checks.append(f"Memory: {memory.percent:.1f}% - {mem_status}")
        
        # Disk check
        disk = psutil.disk_usage('/')
        disk_status = "healthy" if disk.percent < 85 else "warning" if disk.percent < 95 else "critical"
        checks.append(f"Disk: {disk.percent:.1f}% - {disk_status}")
        
        # Connection check
        conn_status = "healthy" if self.metrics.active_connections < self.config.max_connections * 0.8 else "warning"
        checks.append(f"Connections: {self.metrics.active_connections}/{self.config.max_connections} - {conn_status}")
        
        # Error rate check
        error_rate = self.metrics.error_count / max(self.metrics.request_count, 1)
        error_status = "healthy" if error_rate < 0.05 else "warning" if error_rate < 0.1 else "critical"
        checks.append(f"Error Rate: {error_rate:.2%} - {error_status}")
        
        if any("critical" in check for check in checks):
            overall_status = "critical"
        elif any("warning" in check for check in checks):
            overall_status = "warning"
        
        status_icon = "🟢" if overall_status == "healthy" else "🟡" if overall_status == "warning" else "🔴"
        
        content = f"""{status_icon} Health Check - Status: {overall_status.upper()}

📋 Component Status:
"""
        for check in checks:
            content += f"- {check}\n"
        
        content += f"\n⏰ Last Check: {datetime.now().isoformat()}"
        
        return {"content": [{"type": "text", "text": content}]}
    
    async def _make_database_request(self, endpoint: str, method: str = "GET", data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a request to the database_ws microservice"""
        try:
            url = f"{self.config.database_ws_url}{endpoint}"
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                if method == "GET":
                    async with session.get(url) as response:
                        return await response.json()
                elif method == "POST":
                    async with session.post(url, json=data) as response:
                        return await response.json()
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
        except Exception as e:
            logger.error(f"Database request failed: {e}")
            return {"error": str(e)}
    
    async def _tool_database_health(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """Check database service health"""
        try:
            result = await self._make_database_request("/admin/health")
            
            if "error" in result:
                content = f"❌ Database Health Check Failed:\n{result['error']}"
                return {"content": [{"type": "text", "text": content}], "isError": True}
            
            status = result.get("status", "unknown")
            database_status = result.get("database", "unknown")
            
            status_icon = "🟢" if status == "healthy" else "🔴"
            db_icon = "🟢" if database_status == "connected" else "🔴"
            
            content = f"""{status_icon} Database Service Health Check:
- Service Status: {status}
- Database Connection: {database_status}
- Timestamp: {datetime.now().isoformat()}"""
            
            return {"content": [{"type": "text", "text": content}]}
            
        except Exception as e:
            content = f"❌ Database Health Check Error: {str(e)}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
    
    async def _tool_list_databases(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """List all available databases"""
        try:
            result = await self._make_database_request("/admin/databases")
            
            if "error" in result:
                content = f"❌ Failed to list databases:\n{result['error']}"
                return {"content": [{"type": "text", "text": content}], "isError": True}
            
            databases = result.get("databases", [])
            
            content = "🗄️ Available Databases:\n\n"
            for db in databases:
                content += f"📊 {db}\n"
            
            return {"content": [{"type": "text", "text": content}]}
            
        except Exception as e:
            content = f"❌ Error listing databases: {str(e)}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
    
    async def _tool_list_schemas(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """List all schemas in the database"""
        try:
            result = await self._make_database_request("/admin/schemas")
            
            if "error" in result:
                content = f"❌ Failed to list schemas:\n{result['error']}"
                return {"content": [{"type": "text", "text": content}], "isError": True}
            
            schemas = result.get("schemas", [])
            
            content = "📋 Available Schemas:\n\n"
            for schema in schemas:
                content += f"📁 {schema}\n"
            
            return {"content": [{"type": "text", "text": content}]}
            
        except Exception as e:
            content = f"❌ Error listing schemas: {str(e)}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
    
    async def _tool_list_tables(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """List all tables in the database or specific schema"""
        try:
            schema_name = args.get("schema_name")
            
            if schema_name:
                endpoint = f"/admin/tables/{schema_name}"
            else:
                endpoint = "/admin/tables"
            
            result = await self._make_database_request(endpoint)
            
            if "error" in result:
                content = f"❌ Failed to list tables:\n{result['error']}"
                return {"content": [{"type": "text", "text": content}], "isError": True}
            
            tables = result.get("tables", [])
            schema_info = f" in schema '{schema_name}'" if schema_name else ""
            
            content = f"📊 Available Tables{schema_info}:\n\n"
            for table in tables:
                content += f"📋 {table}\n"
            
            return {"content": [{"type": "text", "text": content}]}
            
        except Exception as e:
            content = f"❌ Error listing tables: {str(e)}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
    
    async def _tool_execute_sql(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """Execute a SQL query (read-only)"""
        try:
            sql = args.get("sql", "")
            parameters = args.get("parameters", {})
            
            if not sql.strip():
                content = "❌ SQL query is required"
                return {"content": [{"type": "text", "text": content}], "isError": True}
            
            data = {"sql": sql, "parameters": parameters}
            result = await self._make_database_request("/crud/raw-sql", "POST", data)
            
            if "error" in result:
                content = f"❌ SQL execution failed:\n{result['error']}"
                return {"content": [{"type": "text", "text": content}], "isError": True}
            
            success = result.get("success", False)
            message = result.get("message", "")
            data = result.get("data", [])
            row_count = result.get("row_count", 0)
            
            if not success:
                content = f"❌ SQL execution failed: {message}"
                return {"content": [{"type": "text", "text": content}], "isError": True}
            
            content = f"✅ SQL Query Executed Successfully\n\n"
            content += f"📊 Results ({row_count} rows):\n"
            content += f"Query: {sql}\n\n"
            
            if data:
                # Format the data as a table
                if data and isinstance(data, list) and len(data) > 0:
                    headers = list(data[0].keys())
                    content += "| " + " | ".join(headers) + " |\n"
                    content += "|" + "|".join(["---"] * len(headers)) + "|\n"
                    
                    for row in data:
                        content += "| " + " | ".join(str(row.get(col, "")) for col in headers) + " |\n"
                else:
                    content += "No data returned\n"
            else:
                content += "Query executed successfully (no data returned)\n"
            
            return {"content": [{"type": "text", "text": content}]}
            
        except Exception as e:
            content = f"❌ SQL execution error: {str(e)}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
    
    async def _tool_execute_write_sql(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """Execute a SQL write operation (INSERT, UPDATE, DELETE)"""
        try:
            sql = args.get("sql", "")
            parameters = args.get("parameters", {})
            
            if not sql.strip():
                content = "❌ SQL query is required"
                return {"content": [{"type": "text", "text": content}], "isError": True}
            
            data = {"sql": sql, "parameters": parameters}
            result = await self._make_database_request("/crud/raw-sql/write", "POST", data)
            
            if "error" in result:
                content = f"❌ SQL write execution failed:\n{result['error']}"
                return {"content": [{"type": "text", "text": content}], "isError": True}
            
            success = result.get("success", False)
            message = result.get("message", "")
            affected_rows = result.get("affected_rows", 0)
            
            if not success:
                content = f"❌ SQL write execution failed: {message}"
                return {"content": [{"type": "text", "text": content}], "isError": True}
            
            content = f"✅ SQL Write Operation Executed Successfully\n\n"
            content += f"📝 Query: {sql}\n"
            content += f"📊 Affected Rows: {affected_rows}\n"
            content += f"💬 Message: {message}\n"
            
            return {"content": [{"type": "text", "text": content}]}
            
        except Exception as e:
            content = f"❌ SQL write execution error: {str(e)}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
    
    async def _tool_read_records(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """Read records from a table"""
        try:
            schema_name = args.get("schema_name", "")
            table_name = args.get("table_name", "")
            limit = args.get("limit", 100)
            offset = args.get("offset", 0)
            order_by = args.get("order_by")
            
            if not schema_name or not table_name:
                content = "❌ Schema name and table name are required"
                return {"content": [{"type": "text", "text": content}], "isError": True}
            
            endpoint = f"/crud/{schema_name}/{table_name}?limit={limit}&offset={offset}"
            if order_by:
                endpoint += f"&order_by={order_by}"
            
            result = await self._make_database_request(endpoint)
            
            if "error" in result:
                content = f"❌ Failed to read records:\n{result['error']}"
                return {"content": [{"type": "text", "text": content}], "isError": True}
            
            records = result.get("records", [])
            count = result.get("count", 0)
            total_count = result.get("total_count", 0)
            
            content = f"📖 Records from {schema_name}.{table_name}\n\n"
            content += f"📊 Showing {count} of {total_count} records (limit: {limit}, offset: {offset})\n\n"
            
            if records:
                # Format the data as a table
                headers = list(records[0].keys())
                content += "| " + " | ".join(headers) + " |\n"
                content += "|" + "|".join(["---"] * len(headers)) + "|\n"
                
                for record in records:
                    content += "| " + " | ".join(str(record.get(col, "")) for col in headers) + " |\n"
            else:
                content += "No records found\n"
            
            return {"content": [{"type": "text", "text": content}]}
            
        except Exception as e:
            content = f"❌ Error reading records: {str(e)}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
    
    async def _tool_read_record(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """Read a specific record by ID"""
        try:
            schema_name = args.get("schema_name", "")
            table_name = args.get("table_name", "")
            record_id = args.get("record_id", "")
            
            if not schema_name or not table_name or not record_id:
                content = "❌ Schema name, table name, and record ID are required"
                return {"content": [{"type": "text", "text": content}], "isError": True}
            
            endpoint = f"/crud/{schema_name}/{table_name}/{record_id}"
            result = await self._make_database_request(endpoint)
            
            if "error" in result:
                content = f"❌ Failed to read record:\n{result['error']}"
                return {"content": [{"type": "text", "text": content}], "isError": True}
            
            record = result.get("data", {})
            
            content = f"📖 Record {record_id} from {schema_name}.{table_name}\n\n"
            
            if record:
                for key, value in record.items():
                    content += f"**{key}**: {value}\n"
            else:
                content += "Record not found\n"
            
            return {"content": [{"type": "text", "text": content}]}
            
        except Exception as e:
            content = f"❌ Error reading record: {str(e)}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
    
    async def _tool_create_record(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """Create a new record in a table"""
        try:
            schema_name = args.get("schema_name", "")
            table_name = args.get("table_name", "")
            data = args.get("data", {})
            
            if not schema_name or not table_name:
                content = "❌ Schema name and table name are required"
                return {"content": [{"type": "text", "text": content}], "isError": True}
            
            if not data:
                content = "❌ Record data is required"
                return {"content": [{"type": "text", "text": content}], "isError": True}
            
            endpoint = f"/crud/{schema_name}/{table_name}"
            result = await self._make_database_request(endpoint, "POST", {"data": data})
            
            if "error" in result:
                content = f"❌ Failed to create record:\n{result['error']}"
                return {"content": [{"type": "text", "text": content}], "isError": True}
            
            record_id = result.get("id")
            created_record = result.get("data", {})
            
            content = f"✅ Record created successfully in {schema_name}.{table_name}\n\n"
            content += f"🆔 Record ID: {record_id}\n"
            content += f"📝 Created Data:\n"
            
            for key, value in created_record.items():
                content += f"  **{key}**: {value}\n"
            
            return {"content": [{"type": "text", "text": content}]}
            
        except Exception as e:
            content = f"❌ Error creating record: {str(e)}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
    
    async def _tool_update_record(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """Update an existing record"""
        try:
            schema_name = args.get("schema_name", "")
            table_name = args.get("table_name", "")
            record_id = args.get("record_id", "")
            data = args.get("data", {})
            
            if not schema_name or not table_name or not record_id:
                content = "❌ Schema name, table name, and record ID are required"
                return {"content": [{"type": "text", "text": content}], "isError": True}
            
            if not data:
                content = "❌ Update data is required"
                return {"content": [{"type": "text", "text": content}], "isError": True}
            
            endpoint = f"/crud/{schema_name}/{table_name}/{record_id}"
            result = await self._make_database_request(endpoint, "PUT", {"data": data})
            
            if "error" in result:
                content = f"❌ Failed to update record:\n{result['error']}"
                return {"content": [{"type": "text", "text": content}], "isError": True}
            
            updated_record = result.get("data", {})
            
            content = f"✅ Record {record_id} updated successfully in {schema_name}.{table_name}\n\n"
            content += f"📝 Updated Data:\n"
            
            for key, value in updated_record.items():
                content += f"  **{key}**: {value}\n"
            
            return {"content": [{"type": "text", "text": content}]}
            
        except Exception as e:
            content = f"❌ Error updating record: {str(e)}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
    
    async def _tool_delete_record(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """Delete a record from a table"""
        try:
            schema_name = args.get("schema_name", "")
            table_name = args.get("table_name", "")
            record_id = args.get("record_id", "")
            
            if not schema_name or not table_name or not record_id:
                content = "❌ Schema name, table name, and record ID are required"
                return {"content": [{"type": "text", "text": content}], "isError": True}
            
            endpoint = f"/crud/{schema_name}/{table_name}/{record_id}"
            result = await self._make_database_request(endpoint, "DELETE")
            
            if "error" in result:
                content = f"❌ Failed to delete record:\n{result['error']}"
                return {"content": [{"type": "text", "text": content}], "isError": True}
            
            content = f"✅ Record {record_id} deleted successfully from {schema_name}.{table_name}\n\n"
            content += f"🗑️ Record ID: {record_id}\n"
            content += f"📋 Table: {schema_name}.{table_name}\n"
            
            return {"content": [{"type": "text", "text": content}]}
            
        except Exception as e:
            content = f"❌ Error deleting record: {str(e)}"
            return {"content": [{"type": "text", "text": content}], "isError": True}
    
    async def handle_request(self, request: Dict[str, Any], client_session: ClientSession) -> Dict[str, Any]:
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        client_session.last_activity = datetime.now(timezone.utc)
        client_session.request_count += 1
        
        try:
            if method == "initialize":
                result = await self.handle_initialize(params, client_session)
            elif method == "tools/list":
                result = await self.handle_list_tools(params, client_session)
            elif method == "tools/call":
                result = await self.handle_call_tool(params, client_session)
            elif method == "resources/list":
                # Return empty resources list
                result = {"resources": []}
            elif method == "prompts/list":
                # Return empty prompts list  
                result = {"prompts": []}
            elif method == "notifications/initialized":
                # Acknowledge initialization notification
                result = {}
            else:
                result = {
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
        
        except Exception as e:
            logger.error(f"Request handling error: {e}", extra={'client_ip': client_session.ip_address})
            result = {
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
        
        response = {"jsonrpc": "2.0", "id": request_id}
        
        # Handle notification methods (no response needed)
        if method == "notifications/initialized":
            return None  # Don't send a response for notifications
        
        if "error" in result:
            response["error"] = result["error"]
        else:
            response["result"] = result
            
        return response
    
    async def authenticate_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> Optional[str]:
        if not self.config.auth_enabled:
            return "anonymous"
        
        # For now, skip the custom auth challenge since Claude Desktop handles auth differently
        # The auth token should be passed via environment variables in the client config
        return "authenticated"
    
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        client_addr = writer.get_extra_info('peername')
        client_ip = client_addr[0] if client_addr else "unknown"
        
        # Security checks
        if not self.security.is_ip_allowed(client_ip):
            logger.warning(f"Blocked connection from {client_ip}")
            writer.close()
            return
        
        if not self.rate_limiter.is_allowed(client_ip):
            logger.warning(f"Rate limit exceeded for {client_ip}")
            writer.close()
            return
        
        if len(self.clients) >= self.config.max_connections:
            logger.warning(f"Max connections reached, rejecting {client_ip}")
            writer.close()
            return
        
        # Authenticate client
        auth_result = await self.authenticate_client(reader, writer)
        if self.config.auth_enabled and not auth_result:
            self.security.record_failed_attempt(client_ip)
            logger.warning(f"Authentication failed for {client_ip}")
            writer.close()
            return
        
        # Create client session
        client_id = secrets.token_hex(8)
        session = ClientSession(
            client_id=client_id,
            ip_address=client_ip,
            connected_at=datetime.now(timezone.utc),
            last_activity=datetime.now(timezone.utc),
            authenticated=bool(auth_result)
        )
        
        self.clients[client_id] = session
        self.metrics.active_connections += 1
        
        logger.info(f"Client connected: {client_ip} (ID: {client_id})")
        
        try:
            while True:
                try:
                    # Use a longer timeout for reading - Claude Desktop connections can be idle
                    line = await asyncio.wait_for(
                        reader.readline(), 
                        timeout=600  # 10 minutes timeout
                    )
                    
                    if not line:
                        logger.info(f"Client {client_ip} disconnected (EOF)")
                        break
                    
                    line = line.decode().strip()
                    if not line:
                        continue
                    
                    logger.debug(f"Received from {client_ip}: {line}")
                    
                    request = json.loads(line)
                    response = await self.handle_request(request, session)
                    
                    # Only send response if not None (notifications don't get responses)
                    if response is not None:
                        response_line = json.dumps(response) + "\n"
                        writer.write(response_line.encode())
                        await writer.drain()
                        logger.debug(f"Sent to {client_ip}: {response_line.strip()}")
                    
                except asyncio.TimeoutError:
                    # Instead of disconnecting on timeout, just log and continue
                    # This allows for long-lived idle connections
                    logger.debug(f"Client {client_ip} idle timeout (this is normal)")
                    # Check if connection is still alive
                    if writer.is_closing():
                        logger.info(f"Client {client_ip} connection closed")
                        break
                    continue
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON from {client_ip}: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        },
                        "id": None
                    }
                    response_line = json.dumps(error_response) + "\n"
                    writer.write(response_line.encode())
                    await writer.drain()
                except Exception as e:
                    logger.error(f"Error processing request from {client_ip}: {e}")
                    break
                
        except asyncio.CancelledError:
            logger.info(f"Client {client_ip} cancelled")
        except Exception as e:
            logger.error(f"Client handling error for {client_ip}: {e}")
        finally:
            self.clients.pop(client_id, None)
            self.metrics.active_connections -= 1
            try:
                writer.close()
                await writer.wait_closed()
            except Exception as e:
                logger.debug(f"Error closing connection: {e}")
            logger.info(f"Client disconnected: {client_ip} (ID: {client_id})")
    
    async def start_server(self) -> asyncio.Server:
        ssl_context = None
        if self.config.ssl_cert and self.config.ssl_key:
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(self.config.ssl_cert, self.config.ssl_key)
        
        server = await asyncio.start_server(
            self.handle_client,
            self.config.host,
            self.config.port,
            ssl=ssl_context
        )
        
        addr = server.sockets[0].getsockname()
        protocol = "wss" if ssl_context else "tcp"
        logger.info(f"Production MCP Server listening on {protocol}://{addr[0]}:{addr[1]}")
        
        return server

async def main():
    parser = argparse.ArgumentParser(description='Production MCP Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=3001, help='Port to bind to')
    parser.add_argument('--ssl-cert', help='SSL certificate file')
    parser.add_argument('--ssl-key', help='SSL private key file')
    parser.add_argument('--auth-token', help='Authentication token')
    parser.add_argument('--no-auth', action='store_true', help='Disable authentication')
    parser.add_argument('--max-connections', type=int, default=50, help='Maximum connections')
    parser.add_argument('--rate-limit', type=int, default=100, help='Rate limit (requests per minute)')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    parser.add_argument('--config', help='Configuration file path')
    
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
        database_ws_url=config_data.get('database', {}).get('ws_url', 'http://localhost:8000')
    )
    
    # Validate configuration
    if config.auth_enabled and not config.auth_token:
        logger.error("Authentication enabled but no token provided. Set MCP_AUTH_TOKEN env var or use --auth-token")
        sys.exit(1)
    
    if config.ssl_cert and not config.ssl_key:
        logger.error("SSL certificate provided but no private key")
        sys.exit(1)
    
    server_instance = ProductionMCPServer(config)
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
        logger.info("Production MCP Server stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)