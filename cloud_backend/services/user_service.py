"""
User Service

Business logic for user management including authentication, authorization,
and user CRUD operations.
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cloud_backend.auth.security import hash_password, verify_password
from cloud_backend.config.database import get_db
from cloud_backend.models.user import User, UserRole

logger = logging.getLogger(__name__)


class UserService:
    """Service for managing users and authentication."""
    
    async def create_user(
        self,
        email: str,
        username: str,
        password: str,
        role: UserRole = UserRole.VIEWER
    ) -> User:
        """
        Create a new user.
        
        Args:
            email: User email address
            username: Username
            password: Plain text password
            role: User role
        
        Returns:
            Created user object
        
        Raises:
            ValueError: If user already exists
        """
        async for session in get_db():
            existing_email = await session.execute(
                select(User).where(User.email == email)
            )
            if existing_email.scalar_one_or_none():
                raise ValueError("User with this email already exists")
            
            existing_username = await session.execute(
                select(User).where(User.username == username)
            )
            if existing_username.scalar_one_or_none():
                raise ValueError("User with this username already exists")
            
            user_id = str(uuid.uuid4())
            hashed_password = hash_password(password)
            
            user = User(
                user_id=user_id,
                email=email,
                username=username,
                hashed_password=hashed_password,
                role=role,
                is_active=True
            )
            
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            logger.info(f"Created user: {user_id} ({username})")
            return user
    
    async def authenticate_user(
        self,
        username: str,
        password: str
    ) -> Optional[User]:
        """
        Authenticate a user by username and password.
        
        Args:
            username: Username
            password: Plain text password
        
        Returns:
            User object if authenticated, None otherwise
        """
        async for session in get_db():
            result = await session.execute(
                select(User).where(User.username == username)
            )
            user = result.scalar_one_or_none()
            
            if user is None:
                logger.warning(f"Authentication failed: user not found: {username}")
                return None
            
            if not verify_password(password, user.hashed_password):
                logger.warning(f"Authentication failed: invalid password for {username}")
                return None
            
            if not user.is_active:
                logger.warning(f"Authentication failed: inactive user {username}")
                return None
            
            user.last_login = datetime.utcnow()
            await session.commit()
            
            logger.info(f"User authenticated: {user.user_id} ({username})")
            return user
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User identifier
        
        Returns:
            User object or None if not found
        """
        async for session in get_db():
            user = await session.get(User, user_id)
            return user
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            username: Username
        
        Returns:
            User object or None if not found
        """
        async for session in get_db():
            result = await session.execute(
                select(User).where(User.username == username)
            )
            return result.scalar_one_or_none()
    
    async def update_user_role(
        self,
        user_id: str,
        new_role: UserRole
    ) -> Optional[User]:
        """
        Update user role (admin only).
        
        Args:
            user_id: User identifier
            new_role: New role
        
        Returns:
            Updated user object or None if not found
        """
        async for session in get_db():
            user = await session.get(User, user_id)
            
            if user:
                user.role = new_role
                user.updated_at = datetime.utcnow()
                await session.commit()
                await session.refresh(user)
                
                logger.info(f"Updated user role: {user_id} -> {new_role}")
            
            return user
    
    async def deactivate_user(self, user_id: str) -> Optional[User]:
        """
        Deactivate a user account.
        
        Args:
            user_id: User identifier
        
        Returns:
            Updated user object or None if not found
        """
        async for session in get_db():
            user = await session.get(User, user_id)
            
            if user:
                user.is_active = False
                user.updated_at = datetime.utcnow()
                await session.commit()
                await session.refresh(user)
                
                logger.info(f"Deactivated user: {user_id}")
            
            return user
    
    async def list_users(
        self,
        limit: int = 100,
        offset: int = 0,
        role_filter: Optional[UserRole] = None
    ) -> List[User]:
        """
        List users with pagination and optional filtering.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            role_filter: Optional role filter
        
        Returns:
            List of user objects
        """
        async for session in get_db():
            stmt = select(User)
            
            if role_filter:
                stmt = stmt.where(User.role == role_filter)
            
            stmt = stmt.order_by(User.created_at.desc()).limit(limit).offset(offset)
            
            result = await session.execute(stmt)
            users = result.scalars().all()
            
            return list(users)
