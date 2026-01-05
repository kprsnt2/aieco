"""AIEco - User Models"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class User(BaseModel):
    id: str
    email: EmailStr
    name: Optional[str] = None
    role: str = "user"
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# SQLAlchemy models would be defined here
# For now using Pydantic only
UserModel = None  # Placeholder for SQLAlchemy model
ApiKeyModel = None  # Placeholder
