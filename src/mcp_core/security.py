"""
Security management for MCP servers
"""

import hmac
import logging
from collections import defaultdict
from typing import Set

from .config import ServerConfig

logger = logging.getLogger(__name__)


class SecurityManager:
    """Security manager for authentication and IP filtering"""

    def __init__(self, config: ServerConfig):
        self.config = config
        self.blocked_ips: Set[str] = set()
        self.failed_attempts = defaultdict(int)

    def verify_token(self, token: str) -> bool:
        """Verify authentication token"""
        if not self.config.auth_enabled or not self.config.auth_token:
            return True
        return hmac.compare_digest(token, self.config.auth_token)

    def is_ip_allowed(self, ip: str) -> bool:
        """Check if IP is allowed to connect"""
        if ip in self.blocked_ips:
            return False
        if self.config.allowed_ips and ip not in self.config.allowed_ips:
            return False
        return True

    def record_failed_attempt(self, ip: str):
        """Record a failed authentication attempt"""
        self.failed_attempts[ip] += 1
        if self.failed_attempts[ip] >= 5:  # Block after 5 failed attempts
            self.blocked_ips.add(ip)
            logger.warning(f"IP {ip} blocked due to repeated failed attempts")
