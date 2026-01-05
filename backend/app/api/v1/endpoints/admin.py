"""AIEco - Admin endpoints"""
from fastapi import APIRouter, Depends
from app.core.auth import get_admin_user

router = APIRouter()

@router.get("/metrics")
async def get_metrics(admin = Depends(get_admin_user)):
    """Get system metrics"""
    return {
        "requests_total": 0,
        "tokens_used": 0,
        "active_users": 0,
        "uptime_seconds": 0
    }

@router.get("/usage")
async def get_usage(admin = Depends(get_admin_user)):
    """Get usage statistics"""
    return {"daily": [], "weekly": [], "monthly": []}
