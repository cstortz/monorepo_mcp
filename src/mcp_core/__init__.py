"""
MCP Core - Shared components for MCP servers
"""

from .config import ServerConfig
from .registry_client import EndpointRegistryClient, resolve_registry_url
from .logging import setup_logging, JSONFormatter
from .security import SecurityManager
from .rate_limiter import RateLimiter
from .metrics import MetricsCollector
from .session import ClientSession
from .server import BaseMCPServer

__version__ = "1.0.0"
__all__ = [
    "EndpointRegistryClient",
    "resolve_registry_url",
    "ServerConfig",
    "setup_logging",
    "JSONFormatter",
    "SecurityManager",
    "RateLimiter",
    "MetricsCollector",
    "ClientSession",
    "BaseMCPServer",
]
