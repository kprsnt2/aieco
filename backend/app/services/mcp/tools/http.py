"""AIEco - HTTP MCP Tools"""
import httpx
from typing import Any, Dict


async def execute(action: str, params: Dict[str, Any]) -> Any:
    if action == "fetch":
        return await fetch(
            params["url"],
            params.get("method", "GET"),
            params.get("headers", {}),
            params.get("body")
        )
    raise ValueError(f"Unknown HTTP action: {action}")


async def fetch(url: str, method: str = "GET", headers: Dict = None, body: str = None) -> Dict:
    """Make HTTP request"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.request(method, url, headers=headers, content=body)
        return {
            "status": response.status_code,
            "headers": dict(response.headers),
            "body": response.text[:10000]  # Limit response size
        }
