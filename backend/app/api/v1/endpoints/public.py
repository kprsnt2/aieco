"""
AIEco - Public Chat Endpoints (No Auth Required)
For local development and testing without authentication
"""

import time
import uuid
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import structlog

from app.core.llm import get_llm_client, LLMClient

logger = structlog.get_logger()
router = APIRouter()


# ===== Request/Response Models =====

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role: system, user, assistant")
    content: str = Field(..., description="Message content")


class PublicChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="List of messages")
    model: str = Field(default="local-model", description="Model to use")
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=2048, description="Max tokens")
    
    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {"role": "user", "content": "Hello!"}
                ]
            }
        }


class ChatResponse(BaseModel):
    id: str
    content: str
    model: str
    tokens_used: int


# ===== Public Endpoints (No Auth) =====

@router.post("/chat", response_model=ChatResponse)
async def public_chat(request: PublicChatRequest):
    """
    Public chat endpoint - NO AUTHENTICATION REQUIRED.
    
    For local development and testing.
    Connects to LMStudio/Ollama running locally.
    """
    request_id = str(uuid.uuid4())[:8]
    
    logger.info(
        "💬 Public chat request",
        request_id=request_id,
        model=request.model,
        message_count=len(request.messages)
    )
    
    try:
        llm_client = get_llm_client()
        
        response = await llm_client.chat_completion(
            messages=[m.model_dump() for m in request.messages],
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        content = response["choices"][0]["message"]["content"]
        tokens = response.get("usage", {}).get("total_tokens", 0)
        
        logger.info("✅ Chat response", request_id=request_id, tokens=tokens)
        
        return ChatResponse(
            id=f"chat-{request_id}",
            content=content,
            model=request.model,
            tokens_used=tokens
        )
    
    except Exception as e:
        logger.error("❌ Chat failed", error=str(e), request_id=request_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test")
async def test_connection():
    """
    Test the LLM connection.
    Returns info about the connected model server.
    """
    from app.config import settings
    
    try:
        llm_client = get_llm_client()
        models = await llm_client.list_models()
        
        return {
            "status": "connected",
            "backend": settings.local_backend,
            "base_url": settings.llm_base_url,
            "models": [m.get("id", "unknown") for m in models]
        }
    except Exception as e:
        return {
            "status": "error",
            "backend": settings.local_backend,
            "base_url": settings.llm_base_url,
            "error": str(e)
        }


@router.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "service": "aieco-public"}
