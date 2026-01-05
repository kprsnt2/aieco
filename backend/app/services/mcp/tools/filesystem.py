"""AIEco - Filesystem MCP Tools"""

import os
from pathlib import Path
from typing import Any, Dict, List
import aiofiles
import aiofiles.os


async def execute(action: str, params: Dict[str, Any]) -> Any:
    """Execute filesystem tool actions"""
    
    if action == "list_directory":
        return await list_directory(params.get("path", "."), params.get("recursive", False))
    elif action == "read_file":
        return await read_file(params["path"], params.get("encoding", "utf-8"))
    elif action == "write_file":
        return await write_file(params["path"], params["content"], params.get("append", False))
    elif action == "search":
        return await search_files(params["pattern"], params.get("path", "."))
    else:
        raise ValueError(f"Unknown filesystem action: {action}")


async def list_directory(path: str, recursive: bool = False) -> List[Dict[str, Any]]:
    """List directory contents"""
    results = []
    base_path = Path(path)
    
    if recursive:
        for item in base_path.rglob("*"):
            results.append({
                "name": item.name,
                "path": str(item),
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None
            })
    else:
        for item in base_path.iterdir():
            results.append({
                "name": item.name,
                "path": str(item),
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None
            })
    
    return results


async def read_file(path: str, encoding: str = "utf-8") -> str:
    """Read file contents"""
    async with aiofiles.open(path, mode="r", encoding=encoding) as f:
        return await f.read()


async def write_file(path: str, content: str, append: bool = False) -> Dict[str, Any]:
    """Write content to file"""
    mode = "a" if append else "w"
    async with aiofiles.open(path, mode=mode, encoding="utf-8") as f:
        await f.write(content)
    return {"success": True, "path": path, "bytes_written": len(content)}


async def search_files(pattern: str, path: str = ".") -> List[str]:
    """Search for files matching pattern"""
    results = []
    base_path = Path(path)
    
    for item in base_path.rglob(pattern):
        results.append(str(item))
    
    return results
