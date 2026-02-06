"""
Schedule Management API Routes

REST API endpoints for creating, retrieving, updating, and deleting
battery schedules. Handles schedule validation and distribution to devices.
"""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, validator

from cloud_backend.auth.dependencies import require_operator_or_admin
from cloud_backend.models.schedule import Schedule, ScheduleEntry
from cloud_backend.models.user import User
from cloud_backend.services.schedule_service import ScheduleService
from cloud_backend.utils.input_sanitizer import sanitize_device_id, validate_schedule_entry_input
from cloud_backend.utils.validation import ScheduleValidator

logger = logging.getLogger(__name__)
router = APIRouter()


class ScheduleEntryRequest(BaseModel):
    """Request model for a single schedule entry."""
    start_time: str = Field(..., description="ISO8601 start timestamp")
    end_time: str = Field(..., description="ISO8601 end timestamp")
    mode: int = Field(..., description="1 for discharge, 2 for charge")
    rate_kw: float = Field(..., ge=0, le=1000, description="Rate in kW")
    
    @validator("mode")
    def validate_mode(cls, v):
        if v not in [1, 2]:
            raise ValueError("mode must be 1 (discharge) or 2 (charge)")
        return v


class ScheduleRequest(BaseModel):
    """Request model for creating a schedule."""
    device_id: str = Field(..., description="Device identifier")
    schedule: List[ScheduleEntryRequest] = Field(..., description="List of schedule entries")
    source: Optional[str] = Field(None, description="Source of the schedule")
    priority: Optional[int] = Field(1, ge=1, le=10, description="Schedule priority")


class ScheduleResponse(BaseModel):
    """Response model for schedule retrieval."""
    device_id: str
    schedule: List[dict]
    created_at: datetime
    updated_at: datetime
    status: str
    
    class Config:
        from_attributes = True


def get_schedule_service() -> ScheduleService:
    """Dependency injection for schedule service."""
    return ScheduleService()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=dict)
async def create_schedule(
    schedule_request: ScheduleRequest,
    current_user: User = Depends(require_operator_or_admin),
    service: ScheduleService = Depends(get_schedule_service)
):
    """
    Create a new battery schedule for a device.
    
    Validates the schedule and stores it for distribution to the device.
    """
    device_id = sanitize_device_id(schedule_request.device_id)
    logger.info(f"User {current_user.user_id} creating schedule for device {device_id}")
    
    try:
        schedule_dicts = [
            validate_schedule_entry_input(entry.dict()) 
            for entry in schedule_request.schedule
        ]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid schedule entry: {str(e)}"
        )
    
    validator = ScheduleValidator()
    
    is_valid, errors = validator.validate_schedule(
        schedule_dicts,
        schedule_request.device_id
    )
    
    if not is_valid:
        logger.warning(
            f"Invalid schedule for {schedule_request.device_id}: {errors}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": errors, "device_id": schedule_request.device_id}
        )
    
    try:
        schedule = await service.create_schedule(
            device_id=device_id,
            schedule_entries=schedule_dicts,
            source=schedule_request.source,
            priority=schedule_request.priority
        )
        
        logger.info(f"Schedule created for {schedule_request.device_id}")
        
        return {
            "device_id": schedule.device_id,
            "schedule_id": schedule.id,
            "status": "created",
            "entries_count": len(schedule.schedule)
        }
    
    except Exception as e:
        logger.error(f"Failed to create schedule: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create schedule"
        )


@router.get("/{device_id}", response_model=ScheduleResponse)
async def get_schedule(
    device_id: str,
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    current_user: User = Depends(require_operator_or_admin),
    service: ScheduleService = Depends(get_schedule_service)
):
    """
    Retrieve the current schedule for a device.
    
    Returns the most recent schedule for the device, optionally filtered by date.
    """
    device_id = sanitize_device_id(device_id)
    logger.info(f"User {current_user.user_id} retrieving schedule for device {device_id}")
    
    try:
        schedule = await service.get_schedule(device_id, date)
        
        if schedule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No schedule found for device {device_id}"
            )
        
        return ScheduleResponse(
            device_id=schedule.device_id,
            schedule=schedule.schedule,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at,
            status=schedule.status
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve schedule: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve schedule"
        )


@router.put("/{device_id}", response_model=dict)
async def update_schedule(
    device_id: str,
    schedule_request: ScheduleRequest,
    current_user: User = Depends(require_operator_or_admin),
    service: ScheduleService = Depends(get_schedule_service)
):
    """
    Update an existing schedule for a device.
    
    Replaces the current schedule with the new one after validation.
    """
    logger.info(f"Updating schedule for device {device_id}")
    
    if schedule_request.device_id != device_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="device_id in URL and body must match"
        )
    
    validator = ScheduleValidator()
    schedule_dicts = [entry.dict() for entry in schedule_request.schedule]
    
    is_valid, errors = validator.validate_schedule(
        schedule_dicts,
        device_id
    )
    
    if not is_valid:
        logger.warning(f"Invalid schedule update for {device_id}: {errors}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": errors, "device_id": device_id}
        )
    
    try:
        schedule = await service.update_schedule(
            device_id=device_id,
            schedule_entries=schedule_dicts,
            source=schedule_request.source,
            priority=schedule_request.priority
        )
        
        logger.info(f"Schedule updated for {device_id}")
        
        return {
            "device_id": schedule.device_id,
            "schedule_id": schedule.id,
            "status": "updated",
            "entries_count": len(schedule.schedule)
        }
    
    except Exception as e:
        logger.error(f"Failed to update schedule: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update schedule"
        )


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    device_id: str,
    current_user: User = Depends(require_operator_or_admin),
    service: ScheduleService = Depends(get_schedule_service)
):
    """
    Delete the schedule for a device.
    
    Removes the schedule from the system. Device will need to request
    a new schedule or use a fallback schedule.
    """
    logger.info(f"Deleting schedule for device {device_id}")
    
    try:
        await service.delete_schedule(device_id)
        logger.info(f"Schedule deleted for {device_id}")
    
    except Exception as e:
        logger.error(f"Failed to delete schedule: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete schedule"
        )


@router.get("", response_model=List[ScheduleResponse])
async def list_schedules(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    device_id: Optional[str] = Query(None),
    current_user: User = Depends(require_operator_or_admin),
    service: ScheduleService = Depends(get_schedule_service)
):
    """
    List schedules with optional filtering.
    
    Returns a paginated list of schedules, optionally filtered by device_id.
    """
    logger.info(f"Listing schedules: limit={limit}, offset={offset}")
    
    try:
        schedules = await service.list_schedules(
            limit=limit,
            offset=offset,
            device_id=device_id
        )
        
        return [
            ScheduleResponse(
                device_id=s.device_id,
                schedule=s.schedule,
                created_at=s.created_at,
                updated_at=s.updated_at,
                status=s.status
            )
            for s in schedules
        ]
    
    except Exception as e:
        logger.error(f"Failed to list schedules: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list schedules"
        )
