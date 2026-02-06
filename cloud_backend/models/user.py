"""
User Data Models

SQLAlchemy models and Pydantic schemas for user management and authentication.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr
from sqlalchemy import Boolean, Column, DateTime, Enum as SQLEnum, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"
    DEVICE = "device"


class User(Base):
    """SQLAlchemy model for users."""
    
    __tablename__ = "users"
    
    user_id = Column(String(100), primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.VIEWER)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserCreate(BaseModel):
    """Pydantic model for user creation."""
    email: EmailStr
    username: str
    password: str
    role: UserRole = UserRole.VIEWER


class UserResponse(BaseModel):
    """Pydantic model for user response."""
    user_id: str
    email: str
    username: str
    role: UserRole
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Pydantic model for user login."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Pydantic model for token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 604800
