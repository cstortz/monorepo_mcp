"""
Configuration management for Monorepo MCP Server
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Set
from dataclasses import dataclass, field


@dataclass
class ServerConfig:
    """Configuration for an MCP server"""
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
    log_level: str = "INFO"
    log_file: str = "mcp_server.log"
    log_format: str = "json"
    max_file_size: int = 1048576
    # Database service configuration
    database_service_url: str = "http://localhost:8000"
    database_service_timeout: int = 30
    database_service_retry_attempts: int = 3


class ConfigManager:
    """Manages configuration loading and validation"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.config = ServerConfig()
    
    def load_config(self, config_path: Optional[str] = None) -> ServerConfig:
        """Load configuration from file and environment variables"""
        if config_path:
            self.config_path = config_path
        
        # Load from file if exists
        if self.config_path and Path(self.config_path).exists():
            with open(self.config_path, 'r') as f:
                file_config = yaml.safe_load(f)
                self._apply_file_config(file_config)
        
        # Override with environment variables
        self._apply_env_config()
        
        return self.config
    
    def _apply_file_config(self, file_config: Dict[str, Any]):
        """Apply configuration from file"""
        if 'server' in file_config:
            server_config = file_config['server']
            if 'host' in server_config:
                self.config.host = server_config['host']
            if 'port' in server_config:
                self.config.port = server_config['port']
            if 'ssl_cert' in server_config:
                self.config.ssl_cert = server_config['ssl_cert']
            if 'ssl_key' in server_config:
                self.config.ssl_key = server_config['ssl_key']
        
        if 'security' in file_config:
            security_config = file_config['security']
            if 'auth_enabled' in security_config:
                self.config.auth_enabled = security_config['auth_enabled']
            if 'auth_token' in security_config:
                self.config.auth_token = security_config['auth_token']
            if 'allowed_ips' in security_config:
                self.config.allowed_ips = set(security_config['allowed_ips'])
        
        if 'rate_limiting' in file_config:
            rate_config = file_config['rate_limiting']
            if 'requests_per_minute' in rate_config:
                self.config.rate_limit_requests = rate_config['requests_per_minute']
            if 'window_seconds' in rate_config:
                self.config.rate_limit_window = rate_config['window_seconds']
        
        if 'limits' in file_config:
            limits_config = file_config['limits']
            if 'max_connections' in limits_config:
                self.config.max_connections = limits_config['max_connections']
            if 'request_timeout' in limits_config:
                self.config.request_timeout = limits_config['request_timeout']
            if 'max_file_size' in limits_config:
                self.config.max_file_size = limits_config['max_file_size']
        
        if 'logging' in file_config:
            log_config = file_config['logging']
            if 'level' in log_config:
                self.config.log_level = log_config['level']
            if 'file' in log_config:
                self.config.log_file = log_config['file']
            if 'format' in log_config:
                self.config.log_format = log_config['format']
        
        if 'database_service' in file_config:
            db_service_config = file_config['database_service']
            if 'url' in db_service_config:
                self.config.database_service_url = db_service_config['url']
            if 'timeout' in db_service_config:
                self.config.database_service_timeout = db_service_config['timeout']
            if 'retry_attempts' in db_service_config:
                self.config.database_service_retry_attempts = db_service_config['retry_attempts']
    
    def _apply_env_config(self):
        """Apply configuration from environment variables"""
        # Server settings
        if os.getenv('MCP_HOST'):
            self.config.host = os.getenv('MCP_HOST')
        if os.getenv('MCP_PORT'):
            self.config.port = int(os.getenv('MCP_PORT'))
        
        # SSL settings
        if os.getenv('MCP_SSL_CERT'):
            self.config.ssl_cert = os.getenv('MCP_SSL_CERT')
        if os.getenv('MCP_SSL_KEY'):
            self.config.ssl_key = os.getenv('MCP_SSL_KEY')
        
        # Security settings
        if os.getenv('MCP_AUTH_ENABLED'):
            self.config.auth_enabled = os.getenv('MCP_AUTH_ENABLED').lower() == 'true'
        if os.getenv('MCP_AUTH_TOKEN'):
            self.config.auth_token = os.getenv('MCP_AUTH_TOKEN')
        
        # Rate limiting
        if os.getenv('MCP_RATE_LIMIT_REQUESTS'):
            self.config.rate_limit_requests = int(os.getenv('MCP_RATE_LIMIT_REQUESTS'))
        if os.getenv('MCP_RATE_LIMIT_WINDOW'):
            self.config.rate_limit_window = int(os.getenv('MCP_RATE_LIMIT_WINDOW'))
        
        # Limits
        if os.getenv('MCP_MAX_CONNECTIONS'):
            self.config.max_connections = int(os.getenv('MCP_MAX_CONNECTIONS'))
        if os.getenv('MCP_REQUEST_TIMEOUT'):
            self.config.request_timeout = int(os.getenv('MCP_REQUEST_TIMEOUT'))
        
        # Logging
        if os.getenv('MCP_LOG_LEVEL'):
            self.config.log_level = os.getenv('MCP_LOG_LEVEL')
        if os.getenv('MCP_LOG_FILE'):
            self.config.log_file = os.getenv('MCP_LOG_FILE')
        
        # Database service settings
        if os.getenv('MCP_DATABASE_SERVICE_URL'):
            self.config.database_service_url = os.getenv('MCP_DATABASE_SERVICE_URL')
        if os.getenv('MCP_DATABASE_SERVICE_TIMEOUT'):
            self.config.database_service_timeout = int(os.getenv('MCP_DATABASE_SERVICE_TIMEOUT'))
        if os.getenv('MCP_DATABASE_SERVICE_RETRY_ATTEMPTS'):
            self.config.database_service_retry_attempts = int(os.getenv('MCP_DATABASE_SERVICE_RETRY_ATTEMPTS'))
    
    def validate_config(self) -> bool:
        """Validate the current configuration"""
        errors = []
        
        # Check required fields
        if not self.config.host:
            errors.append("Host is required")
        
        if not (1 <= self.config.port <= 65535):
            errors.append("Port must be between 1 and 65535")
        
        if self.config.auth_enabled and not self.config.auth_token:
            errors.append("Auth token is required when authentication is enabled")
        
        if self.config.ssl_cert and not self.config.ssl_key:
            errors.append("SSL key is required when SSL cert is provided")
        
        if self.config.ssl_key and not self.config.ssl_cert:
            errors.append("SSL cert is required when SSL key is provided")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
        
        return True
    
    def get_config(self) -> ServerConfig:
        """Get the current configuration"""
        return self.config
