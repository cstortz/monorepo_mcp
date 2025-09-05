"""
MCP REST API Server

This module provides MCP tools for interacting with REST APIs,
specifically the resume generation API.
"""

from .server import RestAPIMCPServer
from .tools import RestAPITools

__all__ = ["RestAPIMCPServer", "RestAPITools"]
__version__ = "1.0.0"
