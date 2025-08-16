"""
Admin tools for Monorepo MCP Server

These tools provide system information, metrics, and health checks.
"""

import os
import platform
import psutil
from typing import Dict, Any
from datetime import datetime, timezone
from ..security import ClientSession
from ..metrics import MetricsCollector


class AdminTools:
    """Admin tools that are available in all MCP servers"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
    
    def get_tools(self) -> Dict[str, Any]:
        """Get the admin tools definitions"""
        return {
            "get_system_info": {
                "name": "get_system_info",
                "description": "Get comprehensive system information and server status",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "echo": {
                "name": "echo",
                "description": "Echo a message with client metadata and timestamps",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Message to echo"
                        }
                    },
                    "required": ["message"]
                }
            },
            "get_metrics": {
                "name": "get_metrics",
                "description": "Get server performance metrics and statistics",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "health_check": {
                "name": "health_check",
                "description": "Perform a comprehensive health check of the server",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
    
    async def get_system_info(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """Get comprehensive system information"""
        cpu_info = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get network interfaces
        network_info = []
        for interface, addresses in psutil.net_if_addrs().items():
            for addr in addresses:
                if addr.family == psutil.AF_INET:  # IPv4
                    network_info.append(f"{interface}: {addr.address}")
        
        content = f"""🖥️  System Information:

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

🌐 Network:
- Interfaces: {', '.join(network_info[:5])}  # Showing first 5

📊 Server Status:
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
    
    async def echo(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """Echo a message with metadata"""
        message = args.get("message", "")
        timestamp = datetime.now().isoformat()
        
        response = f"""📢 Echo Response:
Message: {message}
Timestamp: {timestamp}
Client IP: {session.ip_address}
Request Count: {session.request_count}"""

        return {"content": [{"type": "text", "text": response}]}
    
    async def get_metrics(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """Get server performance metrics"""
        metrics = self.metrics.get_summary()
        
        # Format metrics for display
        content = f"""📊 Server Metrics Dashboard:

🕐 Server Info:
- Start Time: {metrics['server_info']['start_time']}
- Uptime: {metrics['server_info']['uptime_formatted']}
- Platform: {metrics['server_info']['platform']}
- Python: {metrics['server_info']['python_version']}

📈 Request Metrics:
- Total Requests: {metrics['request_metrics']['total_requests']}
- Errors: {metrics['request_metrics']['error_count']}
- Success Rate: {metrics['request_metrics']['success_rate_percent']}%
- Active Connections: {metrics['request_metrics']['active_connections']}

💻 System Metrics:
- CPU Usage: {metrics['system_metrics']['current']['cpu_percent']}%
- Memory Usage: {metrics['system_metrics']['current']['memory_percent']}%
- Disk Usage: {metrics['system_metrics']['current']['disk_percent']}%

🛠️ Tool Performance:"""
        
        # Add tool metrics
        for tool_name, tool_metrics in metrics['tool_metrics'].items():
            content += f"""
- {tool_name}:
  - Calls: {tool_metrics['count']}
  - Success Rate: {tool_metrics['success_rate']}%
  - Avg Response: {tool_metrics['avg_response_time']}s
  - Min/Max: {tool_metrics['min_response_time']}s / {tool_metrics['max_response_time']}s"""
        
        if metrics['request_metrics']['recent_requests']:
            content += "\n\n🕒 Recent Requests:"
            for req in metrics['request_metrics']['recent_requests'][-5:]:  # Last 5
                status = "✅" if req['success'] else "❌"
                content += f"\n{status} {req['tool']}: {req['response_time']}s"
        
        return {"content": [{"type": "text", "text": content}]}
    
    async def health_check(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health_status = {
            'overall': 'healthy',
            'checks': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Check system resources
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            health_status['checks']['cpu'] = {
                'status': 'healthy' if cpu_percent < 90 else 'warning',
                'value': f"{cpu_percent}%",
                'threshold': '90%'
            }
            
            health_status['checks']['memory'] = {
                'status': 'healthy' if memory.percent < 90 else 'warning',
                'value': f"{memory.percent}%",
                'threshold': '90%'
            }
            
            health_status['checks']['disk'] = {
                'status': 'healthy' if disk.percent < 90 else 'warning',
                'value': f"{disk.percent}%",
                'threshold': '90%'
            }
            
        except Exception as e:
            health_status['checks']['system_resources'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # Check server metrics
        try:
            metrics = self.metrics.get_summary()
            success_rate = metrics['request_metrics']['success_rate_percent']
            
            health_status['checks']['success_rate'] = {
                'status': 'healthy' if success_rate > 95 else 'warning',
                'value': f"{success_rate}%",
                'threshold': '95%'
            }
            
        except Exception as e:
            health_status['checks']['metrics'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # Check process health
        try:
            process = psutil.Process()
            health_status['checks']['process'] = {
                'status': 'healthy',
                'pid': process.pid,
                'memory_mb': round(process.memory_info().rss / (1024 * 1024), 2)
            }
        except Exception as e:
            health_status['checks']['process'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # Determine overall status
        if any(check['status'] == 'error' for check in health_status['checks'].values()):
            health_status['overall'] = 'unhealthy'
        elif any(check['status'] == 'warning' for check in health_status['checks'].values()):
            health_status['overall'] = 'degraded'
        
        # Format response
        status_emoji = {
            'healthy': '✅',
            'degraded': '⚠️',
            'unhealthy': '❌'
        }
        
        content = f"""🏥 Health Check Results:

Overall Status: {status_emoji[health_status['overall']]} {health_status['overall'].upper()}
Timestamp: {health_status['timestamp']}

Detailed Checks:"""
        
        for check_name, check_data in health_status['checks'].items():
            status_icon = status_emoji.get(check_data['status'], '❓')
            if 'error' in check_data:
                content += f"\n{status_icon} {check_name}: ERROR - {check_data['error']}"
            else:
                content += f"\n{status_icon} {check_name}: {check_data.get('value', 'OK')}"
        
        return {"content": [{"type": "text", "text": content}]}
