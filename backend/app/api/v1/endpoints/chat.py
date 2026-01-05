"""
AIEco - Chat Endpoints (OpenAI-Compatible)
Provides chat completions API matching OpenAI's spec
"""

import time
import uuid
from typing import AsyncGenerator, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import structlog

from app.api.v1.deps import get_current_user, get_llm_client
from app.core.llm import LLMClient
from app.core.observability import trace_llm_call
from app.models.user import User

logger = structlog.get_logger()
router = APIRouter()


# ===== Request/Response Models =====

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role: system, user, assistant, or tool")
    content: str = Field(..., description="Message content")
    name: Optional[str] = Field(None, description="Name for the message author")
    tool_calls: Optional[List[dict]] = Field(None, description="Tool calls made by assistant")
    tool_call_id: Optional[str] = Field(None, description="ID of the tool call this message responds to")


class ChatCompletionRequest(BaseModel):
    model: str = Field(default="glm-4.7", description="Model to use")
    messages: List[ChatMessage] = Field(..., description="List of messages")
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=4096, description="Max tokens to generate")
    stream: bool = Field(default=False, description="Enable streaming")
    top_p: float = Field(default=1.0, ge=0, le=1)
    frequency_penalty: float = Field(default=0, ge=-2, le=2)
    presence_penalty: float = Field(default=0, ge=-2, le=2)
    stop: Optional[List[str]] = Field(None, description="Stop sequences")
    tools: Optional[List[dict]] = Field(None, description="Available tools")
    tool_choice: Optional[str] = Field(None, description="Tool choice strategy")
    
    class Config:
        json_schema_extra = {
            "example": {
                "model": "glm-4.7",
                "messages": [
                    {"role": "system", "content": "You are a helpful coding assistant."},
                    {"role": "user", "content": "Write a Python function to sort a list"}
                ],
                "temperature": 0.7,
                "stream": True
            }
        }


class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str


class ChatCompletionUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: ChatCompletionUsage


# ===== Endpoints =====

@router.post("/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    request: ChatCompletionRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    llm_client: LLMClient = Depends(get_llm_client)
):
    """
    Create a chat completion (OpenAI-compatible).
    
    Supports both streaming and non-streaming responses.
    """
    request_id = str(uuid.uuid4())
    
    logger.info(
        "💬 Chat completion request",
        request_id=request_id,
        user_id=current_user.id,
        model=request.model,
        stream=request.stream,
        message_count=len(request.messages)
    )
    
    # If streaming, return SSE response
    if request.stream:
        return StreamingResponse(
            stream_chat_completion(request, llm_client, request_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Request-ID": request_id
            }
        )
    
    # Non-streaming response
    try:
        with trace_llm_call(
            name="chat_completion",
            model=request.model,
            user_id=str(current_user.id)
        ) as trace:
            response = await llm_client.chat_completion(
                messages=[m.model_dump() for m in request.messages],
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                tools=request.tools,
                tool_choice=request.tool_choice
            )
            
            trace.update(
                output=response["choices"][0]["message"]["content"],
                usage=response.get("usage", {})
            )
        
        return ChatCompletionResponse(
            id=f"chatcmpl-{request_id}",
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(**response["choices"][0]["message"]),
                    finish_reason=response["choices"][0].get("finish_reason", "stop")
                )
            ],
            usage=ChatCompletionUsage(
                prompt_tokens=response.get("usage", {}).get("prompt_tokens", 0),
                completion_tokens=response.get("usage", {}).get("completion_tokens", 0),
                total_tokens=response.get("usage", {}).get("total_tokens", 0)
            )
        )
    
    except Exception as e:
        logger.error("❌ Chat completion failed", error=str(e), request_id=request_id)
        raise HTTPException(status_code=500, detail=f"Chat completion failed: {str(e)}")


async def stream_chat_completion(
    request: ChatCompletionRequest,
    llm_client: LLMClient,
    request_id: str
) -> AsyncGenerator[str, None]:
    """Stream chat completion chunks as SSE events"""
    import json
    
    try:
        async for chunk in llm_client.stream_chat_completion(
            messages=[m.model_dump() for m in request.messages],
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            tools=request.tools
        ):
            # Format as SSE
            data = {
                "id": f"chatcmpl-{request_id}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "delta": chunk.get("delta", {}),
                    "finish_reason": chunk.get("finish_reason")
                }]
            }
            yield f"data: {json.dumps(data)}\n\n"
        
        # Send done message
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error("❌ Stream error", error=str(e), request_id=request_id)
        error_data = {"error": {"message": str(e), "type": "server_error"}}
        yield f"data: {json.dumps(error_data)}\n\n"


@router.get("/models")
async def list_chat_models(
    current_user: User = Depends(get_current_user),
    llm_client: LLMClient = Depends(get_llm_client)
):
    """List available chat models"""
    models = await llm_client.list_models()
    return {"models": models}
