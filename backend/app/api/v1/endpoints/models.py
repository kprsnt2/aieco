"""AIEco - Models endpoint"""
from fastapi import APIRouter, Depends
from app.api.v1.deps import get_current_user, get_llm_client

router = APIRouter()

@router.get("")
async def list_models(current_user = Depends(get_current_user), llm = Depends(get_llm_client)):
    """List available models"""
    models = await llm.list_models()
    return {"object": "list", "data": models}

@router.get("/{model_id}")
async def get_model(model_id: str, current_user = Depends(get_current_user)):
    """Get model details"""
    return {"id": model_id, "object": "model", "owned_by": "aieco"}
