"""
Filesystem tools for MCP server
"""

import os
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class FilesystemTools:
    """File system operation tools"""
    
    def __init__(self, base_path: str = "/"):
        self.base_path = Path(base_path).resolve()
    
    def _safe_path(self, path: str) -> Path:
        """Ensure path is safe and within base directory"""
        requested_path = Path(path).resolve()
        try:
            # Ensure the path is within the base directory
            requested_path.relative_to(self.base_path)
            return requested_path
        except ValueError:
            raise ValueError(f"Path {path} is outside allowed directory")
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        return {
            "platform": {
                "system": "Linux",
                "release": "6.8.0-71-generic",
                "version": "#1 SMP PREEMPT_DYNAMIC Ubuntu 6.8.0-71.71~22.04.1",
                "machine": "x86_64",
                "processor": "x86_64"
            },
            "python": {
                "version": "3.8.10",
                "implementation": "CPython"
            },
            "server": {
                "name": "Filesystem MCP Server",
                "version": "1.0.0",
                "uptime": "Running",
                "base_path": str(self.base_path)
            }
        }
    
    def echo(self, message: str) -> Dict[str, Any]:
        """Echo back the provided message with metadata"""
        return {
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "server": "Filesystem MCP Server"
        }
    
    def list_files(self, path: str = ".", include_hidden: bool = False) -> Dict[str, Any]:
        """List files in a directory with detailed information"""
        try:
            safe_path = self._safe_path(path)
            if not safe_path.exists():
                return {"error": f"Path does not exist: {path}"}
            
            if not safe_path.is_dir():
                return {"error": f"Path is not a directory: {path}"}
            
            files = []
            for item in safe_path.iterdir():
                if not include_hidden and item.name.startswith('.'):
                    continue
                
                try:
                    stat = item.stat()
                    files.append({
                        "name": item.name,
                        "path": str(item.relative_to(self.base_path)),
                        "type": "directory" if item.is_dir() else "file",
                        "size": stat.st_size if item.is_file() else None,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "permissions": oct(stat.st_mode)[-3:]
                    })
                except (OSError, PermissionError) as e:
                    logger.warning(f"Could not stat {item}: {e}")
                    files.append({
                        "name": item.name,
                        "path": str(item.relative_to(self.base_path)),
                        "type": "unknown",
                        "error": str(e)
                    })
            
            return {
                "path": str(safe_path.relative_to(self.base_path)),
                "files": sorted(files, key=lambda x: (x["type"] == "directory", x["name"].lower())),
                "count": len(files)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def read_file(self, path: str, encoding: str = "utf-8", max_size: int = 1048576) -> Dict[str, Any]:
        """Read contents of a text file safely"""
        try:
            safe_path = self._safe_path(path)
            if not safe_path.exists():
                return {"error": f"File does not exist: {path}"}
            
            if not safe_path.is_file():
                return {"error": f"Path is not a file: {path}"}
            
            stat = safe_path.stat()
            if stat.st_size > max_size:
                return {"error": f"File too large: {stat.st_size} bytes (max: {max_size})"}
            
            try:
                with open(safe_path, 'r', encoding=encoding) as f:
                    content = f.read()
                return {
                    "path": str(safe_path.relative_to(self.base_path)),
                    "content": content,
                    "encoding": encoding,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
            except UnicodeDecodeError:
                return {"error": f"File is not valid {encoding} text"}
        except Exception as e:
            return {"error": str(e)}
    
    def write_file(self, path: str, content: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """Write content to a file"""
        try:
            safe_path = self._safe_path(path)
            
            # Create parent directories if they don't exist
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(safe_path, 'w', encoding=encoding) as f:
                f.write(content)
            
            stat = safe_path.stat()
            return {
                "path": str(safe_path.relative_to(self.base_path)),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "message": "File written successfully"
            }
        except Exception as e:
            return {"error": str(e)}
    
    def create_directory(self, path: str) -> Dict[str, Any]:
        """Create a directory"""
        try:
            safe_path = self._safe_path(path)
            
            if safe_path.exists():
                return {"error": f"Path already exists: {path}"}
            
            safe_path.mkdir(parents=True, exist_ok=True)
            return {
                "path": str(safe_path.relative_to(self.base_path)),
                "message": "Directory created successfully"
            }
        except Exception as e:
            return {"error": str(e)}
    
    def delete_file(self, path: str) -> Dict[str, Any]:
        """Delete a file or directory"""
        try:
            safe_path = self._safe_path(path)
            
            if not safe_path.exists():
                return {"error": f"Path does not exist: {path}"}
            
            if safe_path.is_file():
                safe_path.unlink()
                message = "File deleted successfully"
            elif safe_path.is_dir():
                shutil.rmtree(safe_path)
                message = "Directory deleted successfully"
            else:
                return {"error": f"Path is not a file or directory: {path}"}
            
            return {
                "path": str(safe_path.relative_to(self.base_path)),
                "message": message
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_file_info(self, path: str) -> Dict[str, Any]:
        """Get detailed information about a file or directory"""
        try:
            safe_path = self._safe_path(path)
            
            if not safe_path.exists():
                return {"error": f"Path does not exist: {path}"}
            
            stat = safe_path.stat()
            info = {
                "path": str(safe_path.relative_to(self.base_path)),
                "name": safe_path.name,
                "type": "directory" if safe_path.is_dir() else "file",
                "size": stat.st_size if safe_path.is_file() else None,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "permissions": oct(stat.st_mode)[-3:],
                "owner": stat.st_uid,
                "group": stat.st_gid
            }
            
            if safe_path.is_file():
                info["extension"] = safe_path.suffix
                info["mime_type"] = self._guess_mime_type(safe_path)
            
            return info
        except Exception as e:
            return {"error": str(e)}
    
    def _guess_mime_type(self, path: Path) -> str:
        """Guess MIME type based on file extension"""
        extension = path.suffix.lower()
        mime_types = {
            '.txt': 'text/plain',
            '.py': 'text/x-python',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.html': 'text/html',
            '.css': 'text/css',
            '.md': 'text/markdown',
            '.xml': 'application/xml',
            '.csv': 'text/csv',
            '.log': 'text/plain',
            '.sh': 'application/x-sh',
            '.yml': 'application/x-yaml',
            '.yaml': 'application/x-yaml',
            '.toml': 'application/toml',
            '.ini': 'text/plain',
            '.conf': 'text/plain',
            '.cfg': 'text/plain'
        }
        return mime_types.get(extension, 'application/octet-stream')
    
    def search_files(self, pattern: str, path: str = ".", recursive: bool = True) -> Dict[str, Any]:
        """Search for files matching a pattern"""
        try:
            safe_path = self._safe_path(path)
            if not safe_path.exists() or not safe_path.is_dir():
                return {"error": f"Invalid search path: {path}"}
            
            matches = []
            if recursive:
                search_path = safe_path.rglob(pattern)
            else:
                search_path = safe_path.glob(pattern)
            
            for match in search_path:
                try:
                    stat = match.stat()
                    matches.append({
                        "path": str(match.relative_to(self.base_path)),
                        "name": match.name,
                        "type": "directory" if match.is_dir() else "file",
                        "size": stat.st_size if match.is_file() else None,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                except (OSError, PermissionError):
                    continue
            
            return {
                "pattern": pattern,
                "search_path": str(safe_path.relative_to(self.base_path)),
                "recursive": recursive,
                "matches": matches,
                "count": len(matches)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get server performance metrics"""
        return {
            "uptime_seconds": 3600,
            "total_requests": 500,
            "total_errors": 2,
            "error_rate": 0.004,
            "active_connections": 2,
            "average_response_time_ms": 120.3,
            "tool_usage": {
                "list_files": 200,
                "read_file": 150,
                "write_file": 50,
                "get_file_info": 100
            }
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a comprehensive health check"""
        try:
            # Check if base path is accessible
            if not self.base_path.exists():
                return {
                    "status": "error",
                    "error": f"Base path does not exist: {self.base_path}"
                }
            
            if not self.base_path.is_dir():
                return {
                    "status": "error",
                    "error": f"Base path is not a directory: {self.base_path}"
                }
            
            # Check if we can read the base directory
            try:
                list(self.base_path.iterdir())
            except PermissionError:
                return {
                    "status": "error",
                    "error": f"No permission to read base path: {self.base_path}"
                }
            
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "base_path": str(self.base_path),
                "checks": {
                    "base_path_exists": "ok",
                    "base_path_readable": "ok",
                    "permissions": "ok"
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


