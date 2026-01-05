"""
AIEco - Remaining API Endpoints
Auth, Models, and Admin endpoints
"""

# ===== auth.py =====
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

router = APIRouter()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login with email and password"""
    from app.core.auth import verify_password, create_access_token
    from app.core.database import get_db_session
    from sqlalchemy import select
    
    # TODO: Implement actual user lookup
    # For demo, accept any credentials
    token = create_access_token(user_id="demo-user", email=request.email)
    return TokenResponse(access_token=token, expires_in=604800)

@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest):
    """Register a new user"""
    from app.core.auth import hash_password, create_access_token
    
    # TODO: Implement actual user creation
    token = create_access_token(user_id="new-user", email=request.email)
    return TokenResponse(access_token=token, expires_in=604800)

@router.post("/api-keys")
async def create_api_key():
    """Create a new API key"""
    from app.core.auth import generate_api_key
    key = generate_api_key()
    return {"api_key": key, "note": "Save this key, it won't be shown again"}
