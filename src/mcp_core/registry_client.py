"""
Endpoint registry client for MCP servers.

Fetches machine-readable tool catalogs from backend services
(e.g. GET /registry/mcp) and exposes HTTP path/method resolution.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import aiohttp

logger = logging.getLogger(__name__)


def resolve_registry_url(
    registry_url: Optional[str],
    service_url: Optional[str],
    registry_path: str = "/registry/mcp",
) -> Optional[str]:
    """Resolve registry URL from explicit env/CLI or service base URL."""
    if registry_url:
        return registry_url.rstrip("/")
    if service_url:
        return f"{service_url.rstrip('/')}{registry_path}"
    return None


class EndpointRegistryClient:
    """Client for fetching and querying MCP endpoint registries."""

    def __init__(self, registry_url: str):
        self.registry_url = registry_url.rstrip("/")
        self._data: Optional[Dict[str, Any]] = None
        self._tools_by_name: Dict[str, Dict[str, Any]] = {}
        self._loaded = False

    @property
    def loaded(self) -> bool:
        return self._loaded

    @property
    def service_base_url(self) -> Optional[str]:
        if not self._data:
            return None
        discovery = self._data.get("discovery") or {}
        for key in ("health", "registry", "registry_mcp"):
            url = discovery.get(key)
            if url:
                parsed = urlparse(url)
                if parsed.scheme and parsed.netloc:
                    return f"{parsed.scheme}://{parsed.netloc}"
        parsed = urlparse(self.registry_url)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
        return None

    async def load(self) -> bool:
        """Fetch and cache the registry document."""
        timeout = aiohttp.ClientTimeout(total=30)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.registry_url) as response:
                    if response.status >= 400:
                        body = await response.text()
                        logger.warning(
                            "Registry fetch failed: %s %s - %s",
                            response.status,
                            self.registry_url,
                            body,
                        )
                        return False
                    self._data = await response.json()
        except aiohttp.ClientError as exc:
            logger.warning("Registry fetch error for %s: %s", self.registry_url, exc)
            return False
        except Exception as exc:
            logger.warning("Unexpected registry fetch error for %s: %s", self.registry_url, exc)
            return False

        self._tools_by_name = {}
        for tool in self._data.get("tools", []):
            name = tool.get("name")
            if name:
                self._tools_by_name[name] = tool

        self._loaded = True
        logger.info(
            "Loaded endpoint registry from %s (%d tools)",
            self.registry_url,
            len(self._tools_by_name),
        )
        return True

    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        return self._tools_by_name.get(name)

    def resolve_path(self, tool_name: str, **path_params: Any) -> Optional[str]:
        """Return HTTP path for a tool, substituting path parameters."""
        tool = self.get_tool(tool_name)
        if not tool:
            return None
        http = tool.get("http") or {}
        path = http.get("path")
        if not path:
            return None
        resolved = path
        for key, value in path_params.items():
            if value is not None:
                resolved = resolved.replace(f"{{{key}}}", str(value))
        return resolved

    def get_http_method(self, tool_name: str) -> Optional[str]:
        tool = self.get_tool(tool_name)
        if not tool:
            return None
        return (tool.get("http") or {}).get("method")

    def to_mcp_tools(self) -> List[Dict[str, Any]]:
        """Build MCP tools/list descriptors from registry entries."""
        tools: List[Dict[str, Any]] = []
        for entry in self._data.get("tools", []) if self._data else []:
            name = entry.get("name")
            if not name:
                continue
            tools.append(
                {
                    "name": name,
                    "description": entry.get("description", name),
                    "inputSchema": entry.get("inputSchema")
                    or {"type": "object", "properties": {}},
                }
            )
        return tools

    def to_mcp_tools_dict(self) -> Dict[str, Dict[str, Any]]:
        return {tool["name"]: tool for tool in self.to_mcp_tools()}

    @property
    def raw_data(self) -> Optional[Dict[str, Any]]:
        return self._data
