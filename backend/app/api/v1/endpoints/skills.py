"""
AIEco - Skills API Endpoints
Manage and use skills in the system
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
import structlog

from app.api.v1.deps import get_current_user
from app.models.user import User
from app.services.skills import SkillLoader, get_skill_registry

logger = structlog.get_logger()
router = APIRouter()


class SkillInfo(BaseModel):
    name: str
    description: str
    version: str
    author: Optional[str] = None
    tags: List[str] = []


class SkillDetail(SkillInfo):
    instructions: str
    examples: List[str] = []
    guidelines: List[str] = []
    tools: List[str] = []


class ActivateSkillRequest(BaseModel):
    skill_name: str = Field(..., description="Name of skill to activate")


class SkillPromptResponse(BaseModel):
    prompt: str
    active_skills: List[str]


# ===== Endpoints =====

@router.get("/list", response_model=List[SkillInfo])
async def list_skills(
    tag: Optional[str] = Query(None, description="Filter by tag"),
    current_user: User = Depends(get_current_user)
):
    """
    List all available skills.
    
    Skills are loaded from the skills/ directory and can be filtered by tag.
    """
    registry = get_skill_registry()
    all_skills = registry.list_all_skills()
    
    if tag:
        all_skills = [s for s in all_skills if tag in s.get("tags", [])]
    
    return all_skills


@router.get("/{skill_name}", response_model=SkillDetail)
async def get_skill(
    skill_name: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a specific skill"""
    registry = get_skill_registry()
    skill = registry._loader.get_skill(skill_name)
    
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill not found: {skill_name}")
    
    return SkillDetail(
        name=skill.name,
        description=skill.description,
        version=skill.version,
        author=skill.author,
        tags=skill.tags or [],
        instructions=skill.instructions,
        examples=skill.examples or [],
        guidelines=skill.guidelines or [],
        tools=skill.tools or []
    )


@router.post("/activate")
async def activate_skill(
    request: ActivateSkillRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Activate a skill for the current session.
    
    Active skills influence agent behavior and responses.
    """
    registry = get_skill_registry()
    
    if registry.activate_skill(request.skill_name):
        logger.info(f"✅ Skill activated: {request.skill_name}", user_id=current_user.id)
        return {
            "status": "activated",
            "skill": request.skill_name,
            "active_skills": registry.list_active_skills()
        }
    else:
        raise HTTPException(status_code=404, detail=f"Skill not found: {request.skill_name}")


@router.post("/deactivate")
async def deactivate_skill(
    request: ActivateSkillRequest,
    current_user: User = Depends(get_current_user)
):
    """Deactivate a skill"""
    registry = get_skill_registry()
    
    if registry.deactivate_skill(request.skill_name):
        return {
            "status": "deactivated",
            "skill": request.skill_name,
            "active_skills": registry.list_active_skills()
        }
    else:
        raise HTTPException(status_code=404, detail=f"Skill not active: {request.skill_name}")


@router.get("/active/list")
async def list_active_skills(
    current_user: User = Depends(get_current_user)
):
    """List currently active skills"""
    registry = get_skill_registry()
    return {"active_skills": registry.list_active_skills()}


@router.get("/active/prompt", response_model=SkillPromptResponse)
async def get_active_skills_prompt(
    current_user: User = Depends(get_current_user)
):
    """
    Get the combined prompt from all active skills.
    
    This prompt can be injected into agent system prompts.
    """
    registry = get_skill_registry()
    return SkillPromptResponse(
        prompt=registry.get_active_skills_prompt(),
        active_skills=registry.list_active_skills()
    )


@router.post("/reload")
async def reload_skills(
    current_user: User = Depends(get_current_user)
):
    """
    Reload all skills from disk.
    
    Useful after adding or modifying skill files.
    """
    registry = get_skill_registry()
    registry._loader._reload_needed = True
    skills = registry._loader.load_all_skills()
    
    return {
        "status": "reloaded",
        "skill_count": len(skills),
        "skills": list(skills.keys())
    }
