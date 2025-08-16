"""
Security utilities for Monorepo MCP Server
"""

import hashlib
import hmac
import secrets
import time
import ipaddress
from typing import Dict, Any, Optional, Set
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime


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


class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.clients = defaultdict(deque)
    
    def is_allowed(self, client_ip: str) -> bool:
        """Check if client is within rate limits"""
        now = time.time()
        client_requests = self.clients[client_ip]
        
        # Remove old requests outside the window
        while client_requests and client_requests[0] < now - self.window_seconds:
            client_requests.popleft()
        
        # Check if client has exceeded the limit
        if len(client_requests) >= self.max_requests:
            return False
        
        # Add current request
        client_requests.append(now)
        return True
    
    def get_remaining_requests(self, client_ip: str) -> int:
        """Get remaining requests for a client"""
        now = time.time()
        client_requests = self.clients[client_ip]
        
        # Remove old requests outside the window
        while client_requests and client_requests[0] < now - self.window_seconds:
            client_requests.popleft()
        
        return max(0, self.max_requests - len(client_requests))


class IPFilter:
    """IP address filtering"""
    
    def __init__(self, allowed_ips: Optional[Set[str]] = None):
        self.allowed_ips = allowed_ips or set()
        self.blocked_ips = set()
        self.failed_attempts = defaultdict(int)
        self.max_failed_attempts = 5
    
    def is_allowed(self, ip_address: str) -> bool:
        """Check if IP address is allowed"""
        # Check if IP is blocked
        if ip_address in self.blocked_ips:
            return False
        
        # If no allowed IPs specified, allow all
        if not self.allowed_ips:
            return True
        
        # Check if IP is in allowed list
        for allowed_ip in self.allowed_ips:
            try:
                if ipaddress.ip_address(ip_address) in ipaddress.ip_network(allowed_ip):
                    return True
            except ValueError:
                # Invalid IP format, skip
                continue
        
        return False
    
    def record_failed_attempt(self, ip_address: str):
        """Record a failed authentication attempt"""
        self.failed_attempts[ip_address] += 1
        
        if self.failed_attempts[ip_address] >= self.max_failed_attempts:
            self.blocked_ips.add(ip_address)
    
    def is_blocked(self, ip_address: str) -> bool:
        """Check if IP is blocked"""
        return ip_address in self.blocked_ips


class Authenticator:
    """Authentication handler"""
    
    def __init__(self, auth_token: Optional[str] = None):
        self.auth_token = auth_token
        self.sessions = {}
    
    def verify_token(self, token: str) -> bool:
        """Verify authentication token"""
        if not self.auth_token:
            return True  # No auth required
        
        return hmac.compare_digest(token, self.auth_token)
    
    def create_session(self, client_id: str, ip_address: str, user_agent: Optional[str] = None) -> ClientSession:
        """Create a new client session"""
        session = ClientSession(
            client_id=client_id,
            ip_address=ip_address,
            connected_at=datetime.now(),
            last_activity=datetime.now(),
            user_agent=user_agent
        )
        self.sessions[client_id] = session
        return session
    
    def get_session(self, client_id: str) -> Optional[ClientSession]:
        """Get client session"""
        return self.sessions.get(client_id)
    
    def update_session(self, client_id: str):
        """Update session activity"""
        if client_id in self.sessions:
            self.sessions[client_id].last_activity = datetime.now()
            self.sessions[client_id].request_count += 1
    
    def remove_session(self, client_id: str):
        """Remove client session"""
        if client_id in self.sessions:
            del self.sessions[client_id]
    
    def cleanup_expired_sessions(self, max_age_hours: int = 24):
        """Clean up expired sessions"""
        cutoff = datetime.now().replace(hour=datetime.now().hour - max_age_hours)
        expired = [
            client_id for client_id, session in self.sessions.items()
            if session.last_activity < cutoff
        ]
        for client_id in expired:
            self.remove_session(client_id)


class SecurityManager:
    """Main security manager that coordinates all security components"""
    
    def __init__(self, config):
        self.config = config
        self.rate_limiter = RateLimiter(
            config.rate_limit_requests,
            config.rate_limit_window
        )
        self.ip_filter = IPFilter(config.allowed_ips)
        self.authenticator = Authenticator(config.auth_token)
    
    def check_access(self, ip_address: str, token: Optional[str] = None) -> Dict[str, Any]:
        """Check if client has access to the server"""
        result = {
            'allowed': True,
            'reason': None,
            'rate_limited': False,
            'ip_blocked': False,
            'auth_failed': False
        }
        
        # Check IP filtering
        if not self.ip_filter.is_allowed(ip_address):
            result['allowed'] = False
            result['reason'] = 'IP address not allowed'
            result['ip_blocked'] = True
            return result
        
        # Check if IP is blocked due to failed attempts
        if self.ip_filter.is_blocked(ip_address):
            result['allowed'] = False
            result['reason'] = 'IP address blocked due to failed attempts'
            result['ip_blocked'] = True
            return result
        
        # Check rate limiting
        if not self.rate_limiter.is_allowed(ip_address):
            result['allowed'] = False
            result['reason'] = 'Rate limit exceeded'
            result['rate_limited'] = True
            return result
        
        # Check authentication if enabled
        if self.config.auth_enabled:
            if not token:
                result['allowed'] = False
                result['reason'] = 'Authentication token required'
                result['auth_failed'] = True
                self.ip_filter.record_failed_attempt(ip_address)
                return result
            
            if not self.authenticator.verify_token(token):
                result['allowed'] = False
                result['reason'] = 'Invalid authentication token'
                result['auth_failed'] = True
                self.ip_filter.record_failed_attempt(ip_address)
                return result
        
        return result
    
    def create_session(self, client_id: str, ip_address: str, user_agent: Optional[str] = None) -> ClientSession:
        """Create a new client session"""
        return self.authenticator.create_session(client_id, ip_address, user_agent)
    
    def get_session(self, client_id: str) -> Optional[ClientSession]:
        """Get client session"""
        return self.authenticator.get_session(client_id)
    
    def update_session(self, client_id: str):
        """Update session activity"""
        self.authenticator.update_session(client_id)
    
    def get_remaining_requests(self, ip_address: str) -> int:
        """Get remaining requests for an IP"""
        return self.rate_limiter.get_remaining_requests(ip_address)
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        self.authenticator.cleanup_expired_sessions()
