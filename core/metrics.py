"""
Metrics collection for Monorepo MCP Server
"""

import time
import psutil
import platform
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections import defaultdict, deque


@dataclass
class RequestMetrics:
    """Metrics for a single request"""
    tool_name: str
    response_time: float
    success: bool
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class MetricsCollector:
    """Collects and manages server metrics"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.start_time = datetime.now(timezone.utc)
        self.request_count = 0
        self.error_count = 0
        self.active_connections = 0
        self.request_history = deque(maxlen=max_history)
        self.tool_metrics = defaultdict(lambda: {
            'count': 0,
            'errors': 0,
            'total_time': 0.0,
            'avg_time': 0.0,
            'min_time': float('inf'),
            'max_time': 0.0
        })
        self.system_history = deque(maxlen=100)  # Keep last 100 system snapshots
    
    def record_request(self, tool_name: str, response_time: float, success: bool):
        """Record a tool request"""
        self.request_count += 1
        if not success:
            self.error_count += 1
        
        # Record request metrics
        request_metric = RequestMetrics(
            tool_name=tool_name,
            response_time=response_time,
            success=success
        )
        self.request_history.append(request_metric)
        
        # Update tool-specific metrics
        tool_metric = self.tool_metrics[tool_name]
        tool_metric['count'] += 1
        tool_metric['total_time'] += response_time
        tool_metric['avg_time'] = tool_metric['total_time'] / tool_metric['count']
        tool_metric['min_time'] = min(tool_metric['min_time'], response_time)
        tool_metric['max_time'] = max(tool_metric['max_time'], response_time)
        
        if not success:
            tool_metric['errors'] += 1
    
    def record_connection_change(self, delta: int):
        """Record a change in active connections"""
        self.active_connections = max(0, self.active_connections + delta)
    
    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_gb=memory.used / (1024**3),
                memory_total_gb=memory.total / (1024**3),
                disk_percent=disk.percent,
                disk_used_gb=disk.used / (1024**3),
                disk_total_gb=disk.total / (1024**3)
            )
            
            self.system_history.append(metrics)
            return metrics
            
        except Exception:
            # Return default metrics if collection fails
            return SystemMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_gb=0.0,
                memory_total_gb=0.0,
                disk_percent=0.0,
                disk_used_gb=0.0,
                disk_total_gb=0.0
            )
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics"""
        current_system = self.collect_system_metrics()
        
        # Calculate uptime
        uptime = datetime.now(timezone.utc) - self.start_time
        
        # Calculate success rate
        success_rate = 0.0
        if self.request_count > 0:
            success_rate = ((self.request_count - self.error_count) / self.request_count) * 100
        
        # Get recent requests (last 10)
        recent_requests = list(self.request_history)[-10:] if self.request_history else []
        
        # Get system history (last 10 snapshots)
        system_history = list(self.system_history)[-10:] if self.system_history else []
        
        return {
            'server_info': {
                'start_time': self.start_time.isoformat(),
                'uptime_seconds': uptime.total_seconds(),
                'uptime_formatted': str(uptime).split('.')[0],  # Remove microseconds
                'platform': platform.system(),
                'python_version': platform.python_version()
            },
            'request_metrics': {
                'total_requests': self.request_count,
                'error_count': self.error_count,
                'success_rate_percent': round(success_rate, 2),
                'active_connections': self.active_connections,
                'recent_requests': [
                    {
                        'tool': req.tool_name,
                        'response_time': round(req.response_time, 3),
                        'success': req.success,
                        'timestamp': req.timestamp.isoformat()
                    }
                    for req in recent_requests
                ]
            },
            'tool_metrics': {
                tool_name: {
                    'count': metrics['count'],
                    'errors': metrics['errors'],
                    'success_rate': round(((metrics['count'] - metrics['errors']) / metrics['count']) * 100, 2) if metrics['count'] > 0 else 0.0,
                    'avg_response_time': round(metrics['avg_time'], 3),
                    'min_response_time': round(metrics['min_time'], 3) if metrics['min_time'] != float('inf') else 0.0,
                    'max_response_time': round(metrics['max_time'], 3)
                }
                for tool_name, metrics in self.tool_metrics.items()
            },
            'system_metrics': {
                'current': {
                    'cpu_percent': round(current_system.cpu_percent, 2),
                    'memory_percent': round(current_system.memory_percent, 2),
                    'memory_used_gb': round(current_system.memory_used_gb, 2),
                    'memory_total_gb': round(current_system.memory_total_gb, 2),
                    'disk_percent': round(current_system.disk_percent, 2),
                    'disk_used_gb': round(current_system.disk_used_gb, 2),
                    'disk_total_gb': round(current_system.disk_total_gb, 2),
                    'timestamp': current_system.timestamp.isoformat()
                },
                'history': [
                    {
                        'cpu_percent': round(metrics.cpu_percent, 2),
                        'memory_percent': round(metrics.memory_percent, 2),
                        'disk_percent': round(metrics.disk_percent, 2),
                        'timestamp': metrics.timestamp.isoformat()
                    }
                    for metrics in system_history
                ]
            }
        }
    
    def get_tool_metrics(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific tool"""
        if tool_name not in self.tool_metrics:
            return None
        
        metrics = self.tool_metrics[tool_name]
        return {
            'tool_name': tool_name,
            'count': metrics['count'],
            'errors': metrics['errors'],
            'success_rate': round(((metrics['count'] - metrics['errors']) / metrics['count']) * 100, 2) if metrics['count'] > 0 else 0.0,
            'avg_response_time': round(metrics['avg_time'], 3),
            'min_response_time': round(metrics['min_time'], 3) if metrics['min_time'] != float('inf') else 0.0,
            'max_response_time': round(metrics['max_time'], 3)
        }
    
    def reset_metrics(self):
        """Reset all metrics (useful for testing)"""
        self.request_count = 0
        self.error_count = 0
        self.active_connections = 0
        self.request_history.clear()
        self.tool_metrics.clear()
        self.system_history.clear()
        self.start_time = datetime.now(timezone.utc)
