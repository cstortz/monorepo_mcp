#!/usr/bin/env python3
"""
Container Health Check for Production MCP Server
"""

import socket
import json
import sys
import os

def health_check():
    try:
        host = os.getenv('HEALTH_CHECK_HOST', 'localhost')
        port = int(os.getenv('HEALTH_CHECK_PORT', '3001'))
        
        # Create socket connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))
        
        # Send health check request
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "health_check",
                "arguments": {}
            }
        }
        
        sock.send((json.dumps(request) + '\n').encode())
        response = sock.recv(4096).decode()
        sock.close()
        
        # Parse response
        result = json.loads(response)
        if 'result' in result and 'healthy' in result['result']['content'][0]['text'].lower():
            return True
        
        return False
        
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

if __name__ == "__main__":
    if health_check():
        sys.exit(0)
    else:
        sys.exit(1)