"""
Rate limiting functionality for MCP servers
"""

import time
from collections import defaultdict, deque
from typing import Dict


class RateLimiter:
    """Rate limiter for client requests"""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.clients: Dict[str, deque] = defaultdict(deque)

    def is_allowed(self, client_ip: str) -> bool:
        """Check if a client request is allowed"""
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
