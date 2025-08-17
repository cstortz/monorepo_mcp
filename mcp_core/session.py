"""
Client session management for MCP servers
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ClientSession:
    """Client session information"""
    client_id: str
    ip_address: str
    connected_at: datetime
    last_activity: datetime
    request_count: int = 0
    authenticated: bool = False
    user_agent: Optional[str] = None


