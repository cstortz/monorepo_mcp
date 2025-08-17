"""
Logging configuration for MCP servers
"""

import json
import logging
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        if hasattr(record, 'client_ip'):
            log_entry['client_ip'] = record.client_ip
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        return json.dumps(log_entry)


def setup_logging(log_level: str = "INFO", log_file: str = "mcp_server.log"):
    """Setup logging configuration"""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # File handler with JSON formatting
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    # Console handler with standard formatting
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    )
    logger.addHandler(console_handler)
    
    return logger


