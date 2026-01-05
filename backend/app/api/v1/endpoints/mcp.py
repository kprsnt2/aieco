"""
AIEco - MCP (Model Context Protocol) Endpoints
Extensible tool system for file, shell, and code execution
"""

from typing import Any, Dict, List, Optional
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
import structlog

from app.api.v1.deps import get_current_user
from app.models.user import User

logger = structlog.get_logger()
router = APIRouter()


class ToolCategory(str, Enum):
    FILESYSTEM = "filesystem"
    SHELL = "shell"
    CODE = "code"
    DATABASE = "database"
    HTTP = "http"


class ToolInfo(BaseModel):
    name: str
    description: str
    category: ToolCategory
    parameters: Dict[str, Any]
    returns: str


class ToolExecuteRequest(BaseModel):
    tool: str = Field(..., description="Tool name to execute")
    parameters: Dict[str, Any] = Field(default={}, description="Tool parameters")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tool": "filesystem.read_file",
                "parameters": {"path": "/path/to/file.txt"}
            }
        }


class ToolExecuteResponse(BaseModel):
    tool: str
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time_ms: int


# ===== MCP Tools Registry =====

MCP_TOOLS: Dict[str, ToolInfo] = {
    # Filesystem tools
    "filesystem.list_directory": ToolInfo(
        name="filesystem.list_directory",
        description="List contents of a directory",
        category=ToolCategory.FILESYSTEM,
        parameters={"path": "string", "recursive": "boolean (optional)"},
        returns="List of files and directories"
    ),
    "filesystem.read_file": ToolInfo(
        name="filesystem.read_file",
        description="Read contents of a file",
        category=ToolCategory.FILESYSTEM,
        parameters={"path": "string", "encoding": "string (optional)"},
        returns="File contents as string"
    ),
    "filesystem.write_file": ToolInfo(
        name="filesystem.write_file",
        description="Write contents to a file",
        category=ToolCategory.FILESYSTEM,
        parameters={"path": "string", "content": "string", "append": "boolean (optional)"},
        returns="Success status"
    ),
    "filesystem.search": ToolInfo(
        name="filesystem.search",
        description="Search for files matching a pattern",
        category=ToolCategory.FILESYSTEM,
        parameters={"pattern": "string", "path": "string (optional)", "type": "file|directory (optional)"},
        returns="List of matching paths"
    ),
    
    # Shell tools
    "shell.execute": ToolInfo(
        name="shell.execute",
        description="Execute a shell command (sandboxed)",
        category=ToolCategory.SHELL,
        parameters={"command": "string", "cwd": "string (optional)", "timeout": "int (optional)"},
        returns="Command output"
    ),
    
    # Code tools
    "code.execute_python": ToolInfo(
        name="code.execute_python",
        description="Execute Python code in a sandboxed environment",
        category=ToolCategory.CODE,
        parameters={"code": "string", "timeout": "int (optional)"},
        returns="Execution result"
    ),
    "code.analyze": ToolInfo(
        name="code.analyze",
        description="Analyze code for issues and suggestions",
        category=ToolCategory.CODE,
        parameters={"code": "string", "language": "string"},
        returns="Analysis results"
    ),
    
    # HTTP tools
    "http.fetch": ToolInfo(
        name="http.fetch",
        description="Make an HTTP request",
        category=ToolCategory.HTTP,
        parameters={"url": "string", "method": "GET|POST|PUT|DELETE", "headers": "object (optional)", "body": "string (optional)"},
        returns="HTTP response"
    ),
    
    # Database tools
    "database.query": ToolInfo(
        name="database.query",
        description="Execute a database query",
        category=ToolCategory.DATABASE,
        parameters={"query": "string", "database": "string (optional)"},
        returns="Query results"
    )
}


# ===== Endpoints =====

@router.get("/tools", response_model=List[ToolInfo])
async def list_tools(
    category: Optional[ToolCategory] = None,
    current_user: User = Depends(get_current_user)
):
    """List all available MCP tools"""
    tools = list(MCP_TOOLS.values())
    
    if category:
        tools = [t for t in tools if t.category == category]
    
    return tools


@router.post("/execute", response_model=ToolExecuteResponse)
async def execute_tool(
    request: ToolExecuteRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Execute an MCP tool.
    
    Tools are sandboxed and have rate limits applied.
    """
    import time
    
    if request.tool not in MCP_TOOLS:
        raise HTTPException(
            status_code=404,
            detail=f"Tool not found: {request.tool}"
        )
    
    logger.info(
        "🔧 Tool execution",
        user_id=current_user.id,
        tool=request.tool
    )
    
    start_time = time.time()
    
    try:
        # Route to appropriate handler
        result = await _execute_tool(request.tool, request.parameters)
        
        return ToolExecuteResponse(
            tool=request.tool,
            success=True,
            result=result,
            execution_time_ms=int((time.time() - start_time) * 1000)
        )
    
    except Exception as e:
        logger.error("❌ Tool execution failed", tool=request.tool, error=str(e))
        return ToolExecuteResponse(
            tool=request.tool,
            success=False,
            result=None,
            error=str(e),
            execution_time_ms=int((time.time() - start_time) * 1000)
        )


async def _execute_tool(tool_name: str, params: Dict[str, Any]) -> Any:
    """Route and execute a tool"""
    from app.services.mcp import tools as mcp_tools
    
    category, action = tool_name.split(".", 1)
    
    if category == "filesystem":
        return await mcp_tools.filesystem.execute(action, params)
    elif category == "shell":
        return await mcp_tools.shell.execute(action, params)
    elif category == "code":
        return await mcp_tools.code.execute(action, params)
    elif category == "http":
        return await mcp_tools.http.execute(action, params)
    elif category == "database":
        return await mcp_tools.database.execute(action, params)
    else:
        raise ValueError(f"Unknown tool category: {category}")


@router.get("/tools/{tool_name}", response_model=ToolInfo)
async def get_tool_info(
    tool_name: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a specific tool"""
    if tool_name not in MCP_TOOLS:
        raise HTTPException(status_code=404, detail="Tool not found")
    return MCP_TOOLS[tool_name]


# ===== MCP Protocol Endpoint =====

@router.post("/protocol")
async def mcp_protocol_handler(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    MCP protocol handler for tool discovery and execution.
    
    This endpoint implements the MCP specification for compatibility
    with Claude Code, OpenCode, and other MCP clients.
    """
    method = request.get("method")
    params = request.get("params", {})
    
    if method == "tools/list":
        return {
            "tools": [
                {
                    "name": t.name,
                    "description": t.description,
                    "inputSchema": {
                        "type": "object",
                        "properties": t.parameters
                    }
                }
                for t in MCP_TOOLS.values()
            ]
        }
    
    elif method == "tools/call":
        tool_name = params.get("name")
        tool_params = params.get("arguments", {})
        
        result = await _execute_tool(tool_name, tool_params)
        return {"content": [{"type": "text", "text": str(result)}]}
    
    elif method == "resources/list":
        return {"resources": []}
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown method: {method}")
