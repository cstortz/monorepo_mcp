"""
REST API Tools for MCP server
"""

import aiohttp
import logging
import json
import base64
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class RestAPITools:
    """Tools for interacting with REST APIs"""

    def __init__(self, resume_api_url: str):
        self.resume_api_url = resume_api_url.rstrip("/")
        self.session = None

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

                # Handle different content types
                content_type = response.headers.get("content-type", "")

                if "application/json" in content_type:
                    return await response.json()
                elif (
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    in content_type
                ):
                    # Handle file download
                    file_data = await response.read()
                    file_b64 = base64.b64encode(file_data).decode("utf-8")
                    return {
                        "success": True,
                        "file_data": file_b64,
                        "filename": "resume.docx",
                        "content_type": content_type,
                    }
                else:
                    # Handle text responses
                    text = await response.text()
                    return {"success": True, "data": text, "content_type": content_type}

        except aiohttp.ClientError as e:
            logger.error(f"HTTP request error: {e}")
            return {"error": True, "message": f"HTTP request failed: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"error": True, "message": f"Unexpected error: {str(e)}"}

    async def generate_resume(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a resume using the resume API"""
        try:
            logger.info("Generating resume...")

            # Validate required fields
            required_fields = ["contact_info", "summary", "skills", "experience"]
            for field in required_fields:
                if field not in resume_data:
                    return {
                        "error": True,
                        "message": f"Missing required field: {field}",
                    }

            # Make API request to store-resume endpoint (which works)
            result = await self._make_request(
                "POST",
                "/store-resume",
                json=resume_data,
                headers={"Content-Type": "application/json"},
            )

            if result.get("error"):
                return result

            # Extract resume ID and download the file
            resume_id = result.get("resume_id")
            if resume_id:
                # Download the generated resume
                download_result = await self._make_request(
                    "GET", f"/resumes/{resume_id}"
                )
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
            else:
                return {"error": True, "message": "No resume ID returned from API"}

        except Exception as e:
            logger.error(f"Error generating resume: {e}")
            return {"error": True, "message": f"Error generating resume: {str(e)}"}

    async def list_resumes(self) -> Dict[str, Any]:
        """List all generated resumes"""
        try:
            logger.info("Listing resumes...")

            result = await self._make_request("GET", "/resumes")

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

            result = await self._make_request("GET", f"/resumes/{resume_id}")

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

            result = await self._make_request("DELETE", f"/resumes/{resume_id}")

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
        """Get information about the resume API"""
        try:
            logger.info("Getting resume API info...")

            # Try to get API documentation or health check
            result = await self._make_request("GET", "/docs")

            if result.get("error"):
                # Try alternative endpoints
                result = await self._make_request("GET", "/health")
                if result.get("error"):
                    result = await self._make_request("GET", "/")

            return {
                "success": True,
                "api_url": self.resume_api_url,
                "available_endpoints": [
                    "POST /store-resume",
                    "GET /resumes",
                    "GET /resumes/{resume_id}",
                    "DELETE /resumes/{resume_id}",
                ],
                "api_info": (
                    result if not result.get("error") else "API info not available"
                ),
            }

        except Exception as e:
            logger.error(f"Error getting API info: {e}")
            return {"error": True, "message": f"Error getting API info: {str(e)}"}

    async def close(self):
        """Close the HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
