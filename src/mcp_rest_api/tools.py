"""
REST API Tools for MCP server
"""

import aiohttp
import logging
import base64
from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from mcp_core.registry_client import EndpointRegistryClient

logger = logging.getLogger(__name__)

# Hardcoded fallbacks when registry is unavailable or missing a tool
FALLBACK_HTTP: Dict[str, Dict[str, str]] = {
    "store_resume": {"method": "POST", "path": "/store-resume"},
    "list_resumes": {"method": "GET", "path": "/resumes"},
    "download_resume": {"method": "GET", "path": "/resumes/{resume_id}"},
    "delete_resume": {"method": "DELETE", "path": "/resumes/{resume_id}"},
    "generate_resume": {"method": "POST", "path": "/generate-resume"},
}


class RestAPITools:
    """Tools for interacting with REST APIs"""

    def __init__(
        self,
        resume_api_url: str,
        registry: Optional["EndpointRegistryClient"] = None,
        registry_url: Optional[str] = None,
    ):
        self.resume_api_url = resume_api_url.rstrip("/")
        self.registry = registry
        self.registry_url = registry_url
        self.session = None

    def _resolve_http(
        self, tool_name: str, **path_params: Any
    ) -> tuple[str, str]:
        """Return (method, path) from registry or fallback."""
        if self.registry and self.registry.loaded:
            method = self.registry.get_http_method(tool_name)
            path = self.registry.resolve_path(tool_name, **path_params)
            if method and path:
                return method, path

        fallback = FALLBACK_HTTP.get(tool_name)
        if not fallback:
            raise ValueError(f"No HTTP mapping for tool: {tool_name}")

        path = fallback["path"]
        for key, value in path_params.items():
            if value is not None:
                path = path.replace(f"{{{key}}}", str(value))
        return fallback["method"], path

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def _make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request to the resume API"""
        session = await self._get_session()
        url = f"{self.resume_api_url}{endpoint}"

        try:
            async with session.request(method, url, **kwargs) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    logger.error(
                        f"API request failed: {response.status} - {error_text}"
                    )
                    return {
                        "error": True,
                        "status_code": response.status,
                        "message": f"API request failed: {error_text}",
                    }

                content_type = response.headers.get("content-type", "")

                if "application/json" in content_type:
                    return await response.json()
                elif (
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    in content_type
                ):
                    file_data = await response.read()
                    file_b64 = base64.b64encode(file_data).decode("utf-8")
                    return {
                        "success": True,
                        "file_data": file_b64,
                        "filename": "resume.docx",
                        "content_type": content_type,
                    }
                else:
                    text = await response.text()
                    return {"success": True, "data": text, "content_type": content_type}

        except aiohttp.ClientError as e:
            logger.error(f"HTTP request error: {e}")
            return {"error": True, "message": f"HTTP request failed: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"error": True, "message": f"Unexpected error: {str(e)}"}

    async def _invoke_registry_tool(
        self, tool_name: str, args: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generic HTTP invocation for registry-backed tools."""
        args = args or {}
        path_params = {
            k: args.get(k)
            for k in ("resume_id",)
            if args.get(k) is not None
        }
        method, path = self._resolve_http(tool_name, **path_params)
        kwargs: Dict[str, Any] = {}
        if method in ("POST", "PUT", "PATCH"):
            kwargs["json"] = args
            kwargs["headers"] = {"Content-Type": "application/json"}
        return await self._make_request(method, path, **kwargs)

    async def generate_resume(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a resume using the resume API"""
        try:
            logger.info("Generating resume...")

            required_fields = ["contact_info", "summary", "skills", "experience"]
            for field in required_fields:
                if field not in resume_data:
                    return {
                        "error": True,
                        "message": f"Missing required field: {field}",
                    }

            store_method, store_path = self._resolve_http("store_resume")
            result = await self._make_request(
                store_method,
                store_path,
                json=resume_data,
                headers={"Content-Type": "application/json"},
            )

            if result.get("error"):
                return result

            resume_id = result.get("resume_id")
            if resume_id:
                dl_method, dl_path = self._resolve_http(
                    "download_resume", resume_id=resume_id
                )
                download_result = await self._make_request(dl_method, dl_path)
                if download_result.get("error"):
                    return download_result

                return {
                    "success": True,
                    "message": "Resume generated and stored successfully",
                    "resume_id": resume_id,
                    "filename": result.get("filename", "resume.docx"),
                    "download_url": result.get("download_url"),
                    "file_data": download_result.get("file_data"),
                    "metadata": {
                        "resume_name": result.get("resume_name"),
                        "created_at": result.get("created_at"),
                        "file_size": result.get("file_size"),
                    },
                }
            return {"error": True, "message": "No resume ID returned from API"}

        except Exception as e:
            logger.error(f"Error generating resume: {e}")
            return {"error": True, "message": f"Error generating resume: {str(e)}"}

    async def list_resumes(self) -> Dict[str, Any]:
        """List all generated resumes"""
        try:
            logger.info("Listing resumes...")
            method, path = self._resolve_http("list_resumes")
            result = await self._make_request(method, path)

            if result.get("error"):
                return result

            return {
                "success": True,
                "resumes": result.get("resumes", []),
                "count": result.get("count", 0),
            }

        except Exception as e:
            logger.error(f"Error listing resumes: {e}")
            return {"error": True, "message": f"Error listing resumes: {str(e)}"}

    async def download_resume(self, resume_id: str) -> Dict[str, Any]:
        """Download a specific resume"""
        try:
            if not resume_id:
                return {"error": True, "message": "Resume ID is required"}

            logger.info(f"Downloading resume: {resume_id}")
            method, path = self._resolve_http("download_resume", resume_id=resume_id)
            result = await self._make_request(method, path)

            if result.get("error"):
                return result

            return {
                "success": True,
                "message": "Resume downloaded successfully",
                "file_data": result.get("file_data"),
                "filename": result.get("filename", f"resume_{resume_id}.docx"),
            }

        except Exception as e:
            logger.error(f"Error downloading resume: {e}")
            return {"error": True, "message": f"Error downloading resume: {str(e)}"}

    async def delete_resume(self, resume_id: str) -> Dict[str, Any]:
        """Delete a specific resume"""
        try:
            if not resume_id:
                return {"error": True, "message": "Resume ID is required"}

            logger.info(f"Deleting resume: {resume_id}")
            method, path = self._resolve_http("delete_resume", resume_id=resume_id)
            result = await self._make_request(method, path)

            if result.get("error"):
                return result

            return {
                "success": True,
                "message": result.get("message", "Resume deleted successfully"),
            }

        except Exception as e:
            logger.error(f"Error deleting resume: {e}")
            return {"error": True, "message": f"Error deleting resume: {str(e)}"}

    async def get_resume_api_info(self) -> Dict[str, Any]:
        """Get information about the resume API from the endpoint registry."""
        try:
            logger.info("Getting resume API info from endpoint registry...")

            if self.registry and self.registry.loaded and self.registry.raw_data:
                registry = self.registry.raw_data
                tools = registry.get("tools", [])
                return {
                    "success": True,
                    "api_url": self.resume_api_url,
                    "registry_url": self.registry_url or f"{self.resume_api_url}/registry/mcp",
                    "mcp_registry_url": self.registry_url or f"{self.resume_api_url}/registry/mcp",
                    "available_endpoints": [
                        f"{t['http']['method']} {t['http']['path']}" for t in tools
                    ],
                    "tools": tools,
                    "workflows": registry.get("workflows", []),
                    "integration_notes": registry.get("integration_notes", {}),
                    "discovery": registry.get("discovery", {}),
                }

            registry = await self._make_request("GET", "/registry/mcp")
            if not registry.get("error"):
                tools = registry.get("tools", [])
                return {
                    "success": True,
                    "api_url": self.resume_api_url,
                    "registry_url": f"{self.resume_api_url}/registry",
                    "mcp_registry_url": f"{self.resume_api_url}/registry/mcp",
                    "available_endpoints": [
                        f"{t['http']['method']} {t['http']['path']}" for t in tools
                    ],
                    "tools": tools,
                    "workflows": registry.get("workflows", []),
                    "integration_notes": registry.get("integration_notes", {}),
                    "discovery": registry.get("discovery", {}),
                }

            logger.warning("MCP registry unavailable, falling back to /")
            fallback = await self._make_request("GET", "/")
            if fallback.get("error"):
                fallback = await self._make_request("GET", "/health")

            return {
                "success": not fallback.get("error"),
                "api_url": self.resume_api_url,
                "registry_url": f"{self.resume_api_url}/registry",
                "available_endpoints": list(fallback.get("endpoints", {}).keys())
                if isinstance(fallback.get("endpoints"), dict)
                else [],
                "api_info": fallback if not fallback.get("error") else "API info not available",
            }

        except Exception as e:
            logger.error(f"Error getting API info: {e}")
            return {"error": True, "message": f"Error getting API info: {str(e)}"}

    async def close(self):
        """Close the HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
