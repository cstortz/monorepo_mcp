"""
Metrics collection for MCP servers
"""

import psutil
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Dict, Any


class MetricsCollector:
    """Collect and track server metrics"""

    def __init__(self):
        self.start_time = datetime.now(timezone.utc)
        self.request_count = 0
        self.error_count = 0
        self.active_connections = 0
        self.tool_usage = defaultdict(int)
        self.response_times = deque(maxlen=1000)

    def record_request(self, tool_name: str, response_time: float, success: bool):
        """Record a request with its metrics"""
        self.request_count += 1
        if not success:
            self.error_count += 1
        self.tool_usage[tool_name] += 1
        self.response_times.append(response_time)

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        uptime = datetime.now(timezone.utc) - self.start_time
        avg_response_time = (
            sum(self.response_times) / len(self.response_times)
            if self.response_times
            else 0
        )

        return {
            "uptime_seconds": uptime.total_seconds(),
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "error_rate": self.error_count / max(self.request_count, 1),
            "active_connections": self.active_connections,
            "average_response_time_ms": avg_response_time * 1000,
            "tool_usage": dict(self.tool_usage),
            "system": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage("/").percent,
            },
        }
