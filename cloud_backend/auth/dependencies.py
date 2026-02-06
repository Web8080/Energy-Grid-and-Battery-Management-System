"""
Authentication Dependencies

FastAPI dependencies for authentication and authorization.
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from cloud_backend.auth.security import decode_token
from cloud_backend.models.user import User, UserRole
from cloud_backend.services.user_service import UserService

logger = logging.getLogger(__name__)
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_service: UserService = Depends(lambda: UserService())
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer token credentials
        user_service: User service dependency
    
    Returns:
        Current user object
    
    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    
    payload = decode_token(token, token_type="access")
    
    if payload is None:
        logger.warning("Invalid or expired access token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: Optional[str] = payload.get("sub")
    
    if user_id is None:
        logger.warning("Token missing user ID")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await user_service.get_user_by_id(user_id)
    
    if user is None:
        logger.warning(f"User not found: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        logger.warning(f"Inactive user attempted access: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (alias for get_current_user).
    
    Args:
        current_user: Current user from get_current_user
    
    Returns:
        Current active user
    """
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Require admin role for endpoint access.
    
    Args:
        current_user: Current user from get_current_user
    
    Returns:
        Current user if admin
    
    Raises:
        HTTPException: If user is not admin
    """
    if current_user.role != UserRole.ADMIN:
        logger.warning(
            f"Non-admin user attempted admin access: {current_user.user_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user


async def require_operator_or_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Require operator or admin role for endpoint access.
    
    Args:
        current_user: Current user from get_current_user
    
    Returns:
        Current user if operator or admin
    
    Raises:
        HTTPException: If user lacks required role
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.OPERATOR]:
        logger.warning(
            f"User without operator role attempted access: {current_user.user_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operator or admin access required"
        )
    
    return current_user
