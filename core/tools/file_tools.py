"""
File tools for Monorepo MCP Server

These tools provide secure file operations with path validation and size limits.
"""

import os
import stat
from pathlib import Path
from typing import Dict, Any, List
from ..security import ClientSession


class FileTools:
    """File operation tools with security features"""
    
    def __init__(self, max_file_size: int = 1048576):
        self.max_file_size = max_file_size
    
    def get_tools(self) -> Dict[str, Any]:
        """Get the file tools definitions"""
        return {
            "list_files": {
                "name": "list_files",
                "description": "List files in a directory with detailed information",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Directory path to list"
                        },
                        "include_hidden": {
                            "type": "boolean",
                            "description": "Include hidden files",
                            "default": False
                        }
                    },
                    "required": []
                }
            },
            "read_file": {
                "name": "read_file",
                "description": "Read contents of a text file safely",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "File path to read"
                        },
                        "encoding": {
                            "type": "string",
                            "description": "File encoding",
                            "default": "utf-8"
                        },
                        "max_size": {
                            "type": "integer",
                            "description": "Maximum file size in bytes",
                            "default": 1048576
                        }
                    },
                    "required": ["path"]
                }
            }
        }
    
    def _validate_path(self, path: str) -> Path:
        """Validate and resolve a file path safely"""
        try:
            # Convert to Path object
            file_path = Path(path)
            
            # Resolve to absolute path
            abs_path = file_path.resolve()
            
            # Get current working directory
            cwd = Path.cwd().resolve()
            
            # Security check: ensure path is within current working directory
            if not str(abs_path).startswith(str(cwd)):
                raise ValueError(f"Path {path} is outside the allowed directory")
            
            return abs_path
            
        except Exception as e:
            raise ValueError(f"Invalid path {path}: {str(e)}")
    
    def _get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get detailed file information"""
        try:
            stat_info = file_path.stat()
            
            # Determine file type
            if file_path.is_dir():
                file_type = "directory"
            elif file_path.is_file():
                file_type = "file"
            elif file_path.is_symlink():
                file_type = "symlink"
            else:
                file_type = "other"
            
            # Get permissions
            mode = stat_info.st_mode
            permissions = ""
            permissions += "r" if mode & stat.S_IRUSR else "-"
            permissions += "w" if mode & stat.S_IWUSR else "-"
            permissions += "x" if mode & stat.S_IXUSR else "-"
            permissions += "r" if mode & stat.S_IRGRP else "-"
            permissions += "w" if mode & stat.S_IWGRP else "-"
            permissions += "x" if mode & stat.S_IXGRP else "-"
            permissions += "r" if mode & stat.S_IROTH else "-"
            permissions += "w" if mode & stat.S_IWOTH else "-"
            permissions += "x" if mode & stat.S_IXOTH else "-"
            
            return {
                "name": file_path.name,
                "type": file_type,
                "size": stat_info.st_size if file_path.is_file() else None,
                "permissions": permissions,
                "modified": stat_info.st_mtime,
                "owner": stat_info.st_uid,
                "group": stat_info.st_gid,
                "is_hidden": file_path.name.startswith('.')
            }
            
        except Exception as e:
            return {
                "name": file_path.name,
                "type": "error",
                "error": str(e)
            }
    
    async def list_files(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """List files in a directory with detailed information"""
        try:
            path = args.get("path", ".")
            include_hidden = args.get("include_hidden", False)
            
            # Validate path
            dir_path = self._validate_path(path)
            
            # Check if it's a directory
            if not dir_path.is_dir():
                return {
                    "content": [{"type": "text", "text": f"❌ Error: {path} is not a directory"}],
                    "isError": True
                }
            
            # List files
            files = []
            try:
                for item in dir_path.iterdir():
                    file_info = self._get_file_info(item)
                    
                    # Skip hidden files if not requested
                    if file_info.get("is_hidden", False) and not include_hidden:
                        continue
                    
                    files.append(file_info)
            except PermissionError:
                return {
                    "content": [{"type": "text", "text": f"❌ Error: Permission denied accessing {path}"}],
                    "isError": True
                }
            
            # Sort files: directories first, then by name
            files.sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))
            
            # Format output
            content = f"""📁 Directory Listing: {path}

Total items: {len(files)}"""

            if files:
                content += "\n\n"
                for file_info in files:
                    if "error" in file_info:
                        content += f"❌ {file_info['name']}: {file_info['error']}\n"
                        continue
                    
                    # File type icon
                    type_icon = {
                        "directory": "📁",
                        "file": "📄",
                        "symlink": "🔗",
                        "other": "❓"
                    }.get(file_info["type"], "❓")
                    
                    # Size formatting
                    size_str = ""
                    if file_info["size"] is not None:
                        size_bytes = file_info["size"]
                        if size_bytes < 1024:
                            size_str = f"{size_bytes}B"
                        elif size_bytes < 1024**2:
                            size_str = f"{size_bytes/1024:.1f}KB"
                        elif size_bytes < 1024**3:
                            size_str = f"{size_bytes/(1024**2):.1f}MB"
                        else:
                            size_str = f"{size_bytes/(1024**3):.1f}GB"
                    
                    # Hidden file indicator
                    hidden_indicator = " (hidden)" if file_info.get("is_hidden", False) else ""
                    
                    content += f"{type_icon} {file_info['name']}{hidden_indicator}\n"
                    content += f"   Type: {file_info['type']}\n"
                    if size_str:
                        content += f"   Size: {size_str}\n"
                    content += f"   Permissions: {file_info['permissions']}\n"
                    content += f"   Modified: {file_info['modified']}\n\n"
            else:
                content += "\n\n📭 Directory is empty"
            
            return {"content": [{"type": "text", "text": content}]}
            
        except ValueError as e:
            return {
                "content": [{"type": "text", "text": f"❌ Error: {str(e)}"}],
                "isError": True
            }
        except Exception as e:
            return {
                "content": [{"type": "text", "text": f"❌ Unexpected error: {str(e)}"}],
                "isError": True
            }
    
    async def read_file(self, args: Dict[str, Any], session: ClientSession) -> Dict[str, Any]:
        """Read contents of a text file safely"""
        try:
            path = args.get("path")
            encoding = args.get("encoding", "utf-8")
            max_size = args.get("max_size", self.max_file_size)
            
            # Validate path
            file_path = self._validate_path(path)
            
            # Check if it's a file
            if not file_path.is_file():
                return {
                    "content": [{"type": "text", "text": f"❌ Error: {path} is not a file"}],
                    "isError": True
                }
            
            # Check file size
            try:
                file_size = file_path.stat().st_size
                if file_size > max_size:
                    return {
                        "content": [{"type": "text", "text": f"❌ Error: File size ({file_size} bytes) exceeds maximum allowed size ({max_size} bytes)"}],
                        "isError": True
                    }
            except OSError as e:
                return {
                    "content": [{"type": "text", "text": f"❌ Error: Cannot access file size: {str(e)}"}],
                    "isError": True
                }
            
            # Read file content
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
            except UnicodeDecodeError:
                return {
                    "content": [{"type": "text", "text": f"❌ Error: Cannot decode file with encoding '{encoding}'. Try a different encoding."}],
                    "isError": True
                }
            except PermissionError:
                return {
                    "content": [{"type": "text", "text": f"❌ Error: Permission denied reading {path}"}],
                    "isError": True
                }
            except Exception as e:
                return {
                    "content": [{"type": "text", "text": f"❌ Error reading file: {str(e)}"}],
                    "isError": True
                }
            
            # Format response
            file_info = self._get_file_info(file_path)
            response = f"""📄 File Contents: {path}

📊 File Information:
- Size: {file_size} bytes
- Encoding: {encoding}
- Permissions: {file_info['permissions']}
- Modified: {file_info['modified']}

📝 Content:
{'-' * 50}
{content}
{'-' * 50}"""
            
            return {"content": [{"type": "text", "text": response}]}
            
        except ValueError as e:
            return {
                "content": [{"type": "text", "text": f"❌ Error: {str(e)}"}],
                "isError": True
            }
        except Exception as e:
            return {
                "content": [{"type": "text", "text": f"❌ Unexpected error: {str(e)}"}],
                "isError": True
            }
