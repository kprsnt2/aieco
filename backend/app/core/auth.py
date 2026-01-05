"""
AIEco - Authentication System
JWT + API Key authentication with role-based access
"""

from datetime import datetime, timedelta
from typing import Optional
import secrets

from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import structlog

from app.config import settings

logger = structlog.get_logger()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name=settings.api_key_header, auto_error=False)


class TokenData(BaseModel):
    """JWT token payload"""
    user_id: str
    email: str
    role: str = "user"
    exp: datetime


class Token(BaseModel):
    """Token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(
    user_id: str,
    email: str,
    role: str = "user",
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expiry_minutes)
    
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return token


def decode_token(token: str) -> TokenData:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        return TokenData(
            user_id=payload["sub"],
            email=payload["email"],
            role=payload.get("role", "user"),
            exp=datetime.fromtimestamp(payload["exp"])
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )


def generate_api_key() -> str:
    """Generate a new API key"""
    return f"aie_{secrets.token_urlsafe(32)}"


async def get_current_user(
    bearer_token: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    api_key: Optional[str] = Security(api_key_header)
):
    """
    Get current authenticated user from JWT or API key.
    
    Priority:
    1. Bearer token (JWT)
    2. X-API-Key header
    """
    from app.models.user import User
    from app.core.database import get_db_session
    
    # Try Bearer token first
    if bearer_token:
        token_data = decode_token(bearer_token.credentials)
        
        # Get user from database
        async with get_db_session() as session:
            from sqlalchemy import select
            from app.models.user import UserModel
            
            result = await session.execute(
                select(UserModel).where(UserModel.id == token_data.user_id)
            )
            user_model = result.scalar_one_or_none()
            
            if not user_model:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            return User.from_orm(user_model)
    
    # Try API key
    if api_key:
        async with get_db_session() as session:
            from sqlalchemy import select
            from app.models.user import ApiKeyModel, UserModel
            
            result = await session.execute(
                select(ApiKeyModel).where(
                    ApiKeyModel.key_hash == hash_api_key(api_key),
                    ApiKeyModel.is_active == True
                )
            )
            api_key_model = result.scalar_one_or_none()
            
            if not api_key_model:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key"
                )
            
            # Update last used
            api_key_model.last_used_at = datetime.utcnow()
            await session.commit()
            
            # Get associated user
            result = await session.execute(
                select(UserModel).where(UserModel.id == api_key_model.user_id)
            )
            user_model = result.scalar_one()
            
            return User.from_orm(user_model)
    
    # No authentication provided
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"}
    )


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage"""
    import hashlib
    return hashlib.sha256(api_key.encode()).hexdigest()


async def get_admin_user(
    current_user = Depends(get_current_user)
):
    """Require admin role"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
