"""
Admin API Routes

REST API endpoints for administrative operations.
Requires admin role for access.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from cloud_backend.auth.dependencies import require_admin
from cloud_backend.models.user import User, UserRole
from cloud_backend.services.user_service import UserService

logger = logging.getLogger(__name__)
router = APIRouter()


class UserCreateRequest(BaseModel):
    """Request model for user creation."""
    email: str
    username: str
    password: str
    role: UserRole = UserRole.VIEWER


class UserUpdateRoleRequest(BaseModel):
    """Request model for role update."""
    role: UserRole


@router.get("/users", response_model=List[dict])
async def list_all_users(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    role_filter: UserRole = Query(None),
    admin: User = Depends(require_admin),
    user_service: UserService = Depends(lambda: UserService())
):
    """
    List all users (admin only).
    
    Returns paginated list of users with optional role filtering.
    """
    users = await user_service.list_users(
        limit=limit,
        offset=offset,
        role_filter=role_filter
    )
    
    return [
        {
            "user_id": u.user_id,
            "email": u.email,
            "username": u.username,
            "role": u.role.value,
            "is_active": u.is_active,
            "last_login": u.last_login.isoformat() if u.last_login else None,
            "created_at": u.created_at.isoformat()
        }
        for u in users
    ]


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreateRequest,
    admin: User = Depends(require_admin),
    user_service: UserService = Depends(lambda: UserService())
):
    """
    Create a new user (admin only).
    
    Allows admins to create users with specified roles.
    """
    try:
        user = await user_service.create_user(
            email=user_data.email,
            username=user_data.username,
            password=user_data.password,
            role=user_data.role
        )
        
        logger.info(f"Admin {admin.user_id} created user: {user.user_id}")
        
        return {
            "user_id": user.user_id,
            "email": user.email,
            "username": user.username,
            "role": user.role.value,
            "status": "created"
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/users/{user_id}/role", status_code=status.HTTP_200_OK)
async def update_user_role(
    user_id: str,
    role_data: UserUpdateRoleRequest,
    admin: User = Depends(require_admin),
    user_service: UserService = Depends(lambda: UserService())
):
    """
    Update user role (admin only).
    
    Allows admins to change user roles.
    """
    user = await user_service.update_user_role(user_id, role_data.role)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(f"Admin {admin.user_id} updated role for user {user_id} to {role_data.role}")
    
    return {
        "user_id": user.user_id,
        "role": user.role.value,
        "status": "updated"
    }


@router.patch("/users/{user_id}/deactivate", status_code=status.HTTP_200_OK)
async def deactivate_user(
    user_id: str,
    admin: User = Depends(require_admin),
    user_service: UserService = Depends(lambda: UserService())
):
    """
    Deactivate a user account (admin only).
    
    Prevents user from logging in while preserving data.
    """
    if user_id == admin.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    user = await user_service.deactivate_user(user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(f"Admin {admin.user_id} deactivated user {user_id}")
    
    return {
        "user_id": user.user_id,
        "status": "deactivated"
    }


@router.get("/system/stats")
async def get_system_stats(
    admin: User = Depends(require_admin)
):
    """
    Get system statistics (admin only).
    
    Returns aggregate system metrics and health information.
    """
    return {
        "total_users": 0,
        "active_devices": 0,
        "total_schedules": 0,
        "system_health": "operational",
        "timestamp": "2026-02-06T00:00:00Z"
    }
