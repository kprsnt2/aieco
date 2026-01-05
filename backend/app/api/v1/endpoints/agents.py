"""
AIEco - LangGraph Agents Endpoints
Multi-agent system with code, research, and custom agents
"""

from typing import Any, Dict, List, Optional
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import structlog

from app.api.v1.deps import get_current_user, get_llm_client
from app.core.llm import LLMClient
from app.models.user import User

logger = structlog.get_logger()
router = APIRouter()


class AgentType(str, Enum):
    CODE = "code"
    RESEARCH = "research"
    FILE = "file"
    CUSTOM = "custom"


class AgentRunRequest(BaseModel):
    agent: AgentType = Field(..., description="Agent type to run")
    task: str = Field(..., description="Task description")
    context: Optional[Dict[str, Any]] = Field(default={}, description="Additional context")
    tools: Optional[List[str]] = Field(default=None, description="Specific tools to enable")
    max_iterations: int = Field(default=10, ge=1, le=50)
    stream: bool = Field(default=False)
    
    class Config:
        json_schema_extra = {
            "example": {
                "agent": "code",
                "task": "Create a Python function that calculates fibonacci numbers",
                "stream": True
            }
        }


class AgentStep(BaseModel):
    step: int
    action: str
    tool: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    observation: Optional[str] = None
    thought: Optional[str] = None


class AgentRunResponse(BaseModel):
    agent: str
    task: str
    result: str
    steps: List[AgentStep] = []
    tools_used: List[str] = []
    iterations: int
    status: str


class AgentInfo(BaseModel):
    name: str
    description: str
    available_tools: List[str]


# ===== Endpoints =====

@router.post("/run", response_model=AgentRunResponse)
async def run_agent(
    request: AgentRunRequest,
    current_user: User = Depends(get_current_user),
    llm_client: LLMClient = Depends(get_llm_client)
):
    """
    Run an AI agent to complete a task.
    
    Available agents:
    - **code**: Write, debug, and refactor code
    - **research**: Search and summarize information
    - **file**: File and project management
    - **custom**: User-defined agent
    """
    from app.services.agents.orchestrator import AgentOrchestrator
    
    logger.info(
        "🤖 Agent run",
        user_id=current_user.id,
        agent=request.agent,
        task=request.task[:100]
    )
    
    if request.stream:
        return StreamingResponse(
            stream_agent_run(request, llm_client, current_user),
            media_type="text/event-stream"
        )
    
    try:
        orchestrator = AgentOrchestrator(llm_client)
        result = await orchestrator.run(
            agent_type=request.agent,
            task=request.task,
            context=request.context,
            tools=request.tools,
            max_iterations=request.max_iterations
        )
        
        return AgentRunResponse(
            agent=request.agent,
            task=request.task,
            result=result["output"],
            steps=result.get("steps", []),
            tools_used=result.get("tools_used", []),
            iterations=result.get("iterations", 0),
            status="completed"
        )
    
    except Exception as e:
        logger.error("❌ Agent run failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Agent failed: {str(e)}")


async def stream_agent_run(request, llm_client, current_user):
    """Stream agent execution steps"""
    import json
    from app.services.agents.orchestrator import AgentOrchestrator
    
    orchestrator = AgentOrchestrator(llm_client)
    
    async for step in orchestrator.stream_run(
        agent_type=request.agent,
        task=request.task,
        context=request.context,
        tools=request.tools,
        max_iterations=request.max_iterations
    ):
        yield f"data: {json.dumps(step)}\n\n"
    
    yield "data: [DONE]\n\n"


@router.get("/list", response_model=List[AgentInfo])
async def list_agents(
    current_user: User = Depends(get_current_user)
):
    """List available agents and their capabilities"""
    return [
        AgentInfo(
            name="code",
            description="Expert coding agent for writing, debugging, and refactoring code",
            available_tools=["execute_code", "read_file", "write_file", "search_code", "run_tests"]
        ),
        AgentInfo(
            name="research",
            description="Research agent for searching and summarizing information",
            available_tools=["web_search", "read_url", "summarize", "extract_info"]
        ),
        AgentInfo(
            name="file",
            description="File management agent for organizing and manipulating files",
            available_tools=["list_files", "read_file", "write_file", "move_file", "delete_file"]
        ),
        AgentInfo(
            name="custom",
            description="Customizable agent with user-defined tools",
            available_tools=["*"]
        )
    ]


@router.get("/history")
async def get_agent_history(
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Get recent agent runs for the current user"""
    # TODO: Implement database query for agent history
    return {"runs": [], "total": 0}


@router.post("/stop/{run_id}")
async def stop_agent_run(
    run_id: str,
    current_user: User = Depends(get_current_user)
):
    """Stop a running agent"""
    # TODO: Implement run cancellation
    return {"status": "stopped", "run_id": run_id}
