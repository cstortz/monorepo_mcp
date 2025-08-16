"""
Tests for core components
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add the core module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.config import ConfigManager, ServerConfig
from core.security import SecurityManager, RateLimiter, IPFilter, Authenticator
from core.metrics import MetricsCollector
from core.tools import AdminTools, FileTools


class TestConfigManager:
    """Test configuration management"""
    
    def test_default_config(self):
        """Test default configuration"""
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        assert config.host == "0.0.0.0"
        assert config.port == 3001
        assert config.auth_enabled is True
        assert config.rate_limit_requests == 100
        assert config.rate_limit_window == 60
    
    def test_config_validation(self):
        """Test configuration validation"""
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Set auth token for valid config
        config.auth_token = "test-token"
        
        # Valid config should pass
        assert config_manager.validate_config() is True
        
        # Invalid port should fail
        config.port = 70000
        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            config_manager.validate_config()
        
        # Reset port
        config.port = 3001
        
        # Auth enabled without token should fail
        config.auth_enabled = True
        config.auth_token = None
        with pytest.raises(ValueError, match="Auth token is required when authentication is enabled"):
            config_manager.validate_config()


class TestRateLimiter:
    """Test rate limiting functionality"""
    
    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization"""
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        assert limiter.max_requests == 10
        assert limiter.window_seconds == 60
    
    def test_rate_limiter_allowed(self):
        """Test rate limiter allows requests within limits"""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        
        # First 3 requests should be allowed
        assert limiter.is_allowed("127.0.0.1") is True
        assert limiter.is_allowed("127.0.0.1") is True
        assert limiter.is_allowed("127.0.0.1") is True
        
        # 4th request should be blocked
        assert limiter.is_allowed("127.0.0.1") is False
    
    def test_rate_limiter_remaining_requests(self):
        """Test remaining requests calculation"""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        # No requests made yet
        assert limiter.get_remaining_requests("127.0.0.1") == 5
        
        # Make 2 requests
        limiter.is_allowed("127.0.0.1")
        limiter.is_allowed("127.0.0.1")
        
        assert limiter.get_remaining_requests("127.0.0.1") == 3


class TestIPFilter:
    """Test IP filtering functionality"""
    
    def test_ip_filter_no_restrictions(self):
        """Test IP filter with no restrictions"""
        ip_filter = IPFilter()
        assert ip_filter.is_allowed("127.0.0.1") is True
        assert ip_filter.is_allowed("192.168.1.1") is True
    
    def test_ip_filter_with_allowed_ips(self):
        """Test IP filter with allowed IPs"""
        allowed_ips = {"127.0.0.0/8", "192.168.1.0/24"}
        ip_filter = IPFilter(allowed_ips)
        
        assert ip_filter.is_allowed("127.0.0.1") is True
        assert ip_filter.is_allowed("192.168.1.100") is True
        assert ip_filter.is_allowed("10.0.0.1") is False
    
    def test_ip_filter_blocking(self):
        """Test IP blocking functionality"""
        ip_filter = IPFilter()
        
        # IP should not be blocked initially
        assert ip_filter.is_blocked("127.0.0.1") is False
        
        # Record failed attempts
        for _ in range(5):
            ip_filter.record_failed_attempt("127.0.0.1")
        
        # IP should now be blocked
        assert ip_filter.is_blocked("127.0.0.1") is True
        assert ip_filter.is_allowed("127.0.0.1") is False


class TestAuthenticator:
    """Test authentication functionality"""
    
    def test_authenticator_no_token(self):
        """Test authenticator with no token required"""
        auth = Authenticator()
        assert auth.verify_token("any_token") is True
    
    def test_authenticator_with_token(self):
        """Test authenticator with token verification"""
        auth = Authenticator("secret_token")
        assert auth.verify_token("secret_token") is True
        assert auth.verify_token("wrong_token") is False
    
    def test_session_management(self):
        """Test session management"""
        auth = Authenticator()
        
        # Create session
        session = auth.create_session("client1", "127.0.0.1")
        assert session.client_id == "client1"
        assert session.ip_address == "127.0.0.1"
        assert session.authenticated is False
        
        # Get session
        retrieved_session = auth.get_session("client1")
        assert retrieved_session is not None
        assert retrieved_session.client_id == "client1"
        
        # Update session
        auth.update_session("client1")
        updated_session = auth.get_session("client1")
        assert updated_session.request_count == 1
        
        # Remove session
        auth.remove_session("client1")
        assert auth.get_session("client1") is None


class TestMetricsCollector:
    """Test metrics collection"""
    
    def test_metrics_initialization(self):
        """Test metrics collector initialization"""
        metrics = MetricsCollector()
        assert metrics.request_count == 0
        assert metrics.error_count == 0
        assert metrics.active_connections == 0
    
    def test_record_request(self):
        """Test recording requests"""
        metrics = MetricsCollector()
        
        # Record successful request
        metrics.record_request("test_tool", 1.5, True)
        assert metrics.request_count == 1
        assert metrics.error_count == 0
        
        # Record failed request
        metrics.record_request("test_tool", 0.5, False)
        assert metrics.request_count == 2
        assert metrics.error_count == 1
    
    def test_connection_tracking(self):
        """Test connection tracking"""
        metrics = MetricsCollector()
        
        assert metrics.active_connections == 0
        
        # Add connections
        metrics.record_connection_change(1)
        metrics.record_connection_change(1)
        assert metrics.active_connections == 2
        
        # Remove connections
        metrics.record_connection_change(-1)
        assert metrics.active_connections == 1
        
        # Ensure it doesn't go below 0
        metrics.record_connection_change(-5)
        assert metrics.active_connections == 0
    
    def test_get_summary(self):
        """Test getting metrics summary"""
        metrics = MetricsCollector()
        
        # Record some data
        metrics.record_request("tool1", 1.0, True)
        metrics.record_request("tool2", 2.0, False)
        metrics.record_connection_change(1)
        
        summary = metrics.get_summary()
        
        assert summary['request_metrics']['total_requests'] == 2
        assert summary['request_metrics']['error_count'] == 1
        assert summary['request_metrics']['success_rate_percent'] == 50.0
        assert summary['request_metrics']['active_connections'] == 1


class TestAdminTools:
    """Test admin tools functionality"""
    
    def test_admin_tools_initialization(self):
        """Test admin tools initialization"""
        metrics = MetricsCollector()
        admin_tools = AdminTools(metrics)
        assert admin_tools.metrics == metrics
    
    def test_get_tools(self):
        """Test admin tools definitions"""
        metrics = MetricsCollector()
        admin_tools = AdminTools(metrics)
        tools = admin_tools.get_tools()
        
        expected_tools = ["get_system_info", "echo", "get_metrics", "health_check"]
        for tool_name in expected_tools:
            assert tool_name in tools
            assert "name" in tools[tool_name]
            assert "description" in tools[tool_name]
            assert "inputSchema" in tools[tool_name]


class TestFileTools:
    """Test file tools functionality"""
    
    def test_file_tools_initialization(self):
        """Test file tools initialization"""
        file_tools = FileTools(max_file_size=1024)
        assert file_tools.max_file_size == 1024
    
    def test_get_tools(self):
        """Test file tools definitions"""
        file_tools = FileTools()
        tools = file_tools.get_tools()
        
        expected_tools = ["list_files", "read_file"]
        for tool_name in expected_tools:
            assert tool_name in tools
            assert "name" in tools[tool_name]
            assert "description" in tools[tool_name]
            assert "inputSchema" in tools[tool_name]


if __name__ == "__main__":
    pytest.main([__file__])
