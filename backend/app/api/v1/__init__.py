"""
AIEco Backend - API v1 Router
Aggregates all API endpoints
"""

from fastapi import APIRouter

from app.api.v1.endpoints import chat, rag, agents, mcp, models, auth, admin, skills, public

router = APIRouter()

# ===== PUBLIC ENDPOINTS (No Auth) =====
router.include_router(
    public.router,
    prefix="/public",
    tags=["Public (No Auth)"]
)

# Authentication
router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

# Chat completions (OpenAI-compatible)
router.include_router(
    chat.router,
    prefix="/chat",
    tags=["Chat"]
)

# RAG pipeline
router.include_router(
    rag.router,
    prefix="/rag",
    tags=["RAG"]
)

# AI Agents
router.include_router(
    agents.router,
    prefix="/agents",
    tags=["Agents"]
)

# Skills
router.include_router(
    skills.router,
    prefix="/skills",
    tags=["Skills"]
)

# MCP Tools
router.include_router(
    mcp.router,
    prefix="/mcp",
    tags=["MCP Tools"]
)

# Model management
router.include_router(
    models.router,
    prefix="/models",
    tags=["Models"]
)

# Admin & metrics
router.include_router(
    admin.router,
    prefix="/admin",
    tags=["Admin"]
)

