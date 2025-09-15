"""
Configuration management for MCP servers
"""

from dataclasses import dataclass
from typing import Optional, Set


@dataclass
class ServerConfig:
    """Configuration for MCP servers"""

    host: str = "0.0.0.0"
    port: int = 3001
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    auth_enabled: bool = True
    auth_token: Optional[str] = None
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    max_connections: int = 50
    request_timeout: int = 300
    allowed_ips: Optional[Set[str]] = None
    metrics_enabled: bool = True
    database_ws_url: str = None
    resume_api_url: str = None
