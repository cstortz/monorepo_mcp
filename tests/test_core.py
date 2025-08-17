"""
Tests for mcp_core components
"""

import pytest
from src.mcp_core import ServerConfig, setup_logging, RateLimiter, SecurityManager


def test_server_config():
    """Test ServerConfig creation and defaults"""
    config = ServerConfig()
    assert config.host == "0.0.0.0"
    assert config.port == 3001
    assert config.auth_enabled is True
    assert config.max_connections == 50


def test_rate_limiter():
    """Test RateLimiter functionality"""
    limiter = RateLimiter(max_requests=2, window_seconds=60)
    
    # Should allow first two requests
    assert limiter.is_allowed("127.0.0.1") is True
    assert limiter.is_allowed("127.0.0.1") is True
    
    # Should block third request
    assert limiter.is_allowed("127.0.0.1") is False


def test_security_manager():
    """Test SecurityManager functionality"""
    config = ServerConfig(auth_token="test-token")
    security = SecurityManager(config)
    
    # Test token verification
    assert security.verify_token("test-token") is True
    assert security.verify_token("wrong-token") is False
    
    # Test IP allowlisting
    assert security.is_ip_allowed("127.0.0.1") is True
