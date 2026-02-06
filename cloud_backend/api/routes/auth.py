"""
Authentication API Routes

REST API endpoints for user authentication, registration, and token management.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from cloud_backend.auth.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    sanitize_input,
    validate_redirect_url,
)
from cloud_backend.config.settings import get_settings
from cloud_backend.models.user import TokenResponse, UserLogin, UserResponse
from cloud_backend.services.user_service import UserService

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()
security = HTTPBearer()


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(
    login_data: UserLogin,
    user_service: UserService = Depends(lambda: UserService())
):
    """
    Authenticate user and return JWT tokens.
    
    Returns access token (7-day expiration) and refresh token (30-day expiration).
    """
    sanitized_username = sanitize_input(login_data.username)
    
    user = await user_service.authenticate_user(
        username=sanitized_username,
        password=login_data.password
    )
    
    if user is None:
        logger.warning(f"Failed login attempt for username: {sanitized_username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    access_token = create_access_token(data={"sub": user.user_id, "role": user.role.value})
    refresh_token = create_refresh_token(data={"sub": user.user_id})
    
    logger.info(f"User logged in: {user.user_id} ({user.username})")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=604800
    )


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_service: UserService = Depends(lambda: UserService())
):
    """
    Refresh access token using refresh token.
    
    Validates refresh token and returns new access and refresh tokens.
    """
    refresh_token = credentials.credentials
    
    payload = decode_token(refresh_token, token_type="refresh")
    
    if payload is None:
        logger.warning("Invalid or expired refresh token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    user_id = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    user = await user_service.get_user_by_id(user_id)
    
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    new_access_token = create_access_token(
        data={"sub": user.user_id, "role": user.role.value}
    )
    new_refresh_token = create_refresh_token(data={"sub": user.user_id})
    
    logger.info(f"Token refreshed for user: {user.user_id}")
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=604800
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout():
    """
    Logout endpoint.
    
    In a stateless JWT system, logout is handled client-side by discarding tokens.
    This endpoint exists for API consistency and can be extended for token blacklisting.
    """
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user = Depends(lambda: None)
):
    """
    Get current user information.
    
    Requires authentication via get_current_user dependency.
    Note: This requires proper dependency injection setup in main.py
    """
    from cloud_backend.auth.dependencies import get_current_user
    
    user = await get_current_user()
    
    return UserResponse(
        user_id=user.user_id,
        email=user.email,
        username=user.username,
        role=user.role,
        is_active=user.is_active,
        last_login=user.last_login,
        created_at=user.created_at
    )


@router.get("/validate-redirect")
async def validate_redirect(
    url: str,
    allowed_domains: Optional[list] = None
):
    """
    Validate redirect URL to prevent open redirect vulnerabilities.
    
    Args:
        url: Redirect URL to validate
        allowed_domains: List of allowed domains (from settings if not provided)
    
    Returns:
        Validation result
    """
    if allowed_domains is None:
        allowed_domains = settings.CORS_ORIGINS if settings.CORS_ORIGINS != ["*"] else []
    
    is_valid = validate_redirect_url(url, allowed_domains)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid redirect URL"
        )
    
    return {"valid": True, "url": url}
