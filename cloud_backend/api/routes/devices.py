"""
Device Management API Routes

REST API endpoints for device registration, status tracking, and
acknowledgement processing.
"""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from cloud_backend.models.device import Device
from cloud_backend.services.device_service import DeviceService

logger = logging.getLogger(__name__)
router = APIRouter()


class DeviceRequest(BaseModel):
    """Request model for device registration."""
    device_id: str = Field(..., description="Unique device identifier")
    location: Optional[str] = Field(None, description="Device location")
    battery_capacity_kwh: Optional[float] = Field(None, ge=0, description="Battery capacity in kWh")
    max_charge_rate_kw: Optional[float] = Field(None, ge=0, description="Maximum charge rate in kW")
    max_discharge_rate_kw: Optional[float] = Field(None, ge=0, description="Maximum discharge rate in kW")


class DeviceResponse(BaseModel):
    """Response model for device information."""
    device_id: str
    location: Optional[str]
    battery_capacity_kwh: Optional[float]
    max_charge_rate_kw: Optional[float]
    max_discharge_rate_kw: Optional[float]
    status: str
    last_seen: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AcknowledgementRequest(BaseModel):
    """Request model for device execution acknowledgement."""
    device_id: str = Field(..., description="Device identifier")
    schedule_entry_index: int = Field(..., description="Index of executed schedule entry")
    execution_time: str = Field(..., description="ISO8601 timestamp of execution")
    status: str = Field(..., description="Execution status: success or failed")
    actual_rate_kw: Optional[float] = Field(None, description="Actual rate achieved")
    error_message: Optional[str] = Field(None, description="Error message if failed")


def get_device_service() -> DeviceService:
    """Dependency injection for device service."""
    return DeviceService()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=DeviceResponse)
async def register_device(
    device_request: DeviceRequest,
    service: DeviceService = Depends(get_device_service)
):
    """
    Register a new device in the system.
    
    Creates device metadata record for tracking and management.
    """
    logger.info(f"Registering device {device_request.device_id}")
    
    try:
        device = await service.register_device(
            device_id=device_request.device_id,
            location=device_request.location,
            battery_capacity_kwh=device_request.battery_capacity_kwh,
            max_charge_rate_kw=device_request.max_charge_rate_kw,
            max_discharge_rate_kw=device_request.max_discharge_rate_kw
        )
        
        logger.info(f"Device {device_request.device_id} registered successfully")
        
        return DeviceResponse(
            device_id=device.device_id,
            location=device.location,
            battery_capacity_kwh=device.battery_capacity_kwh,
            max_charge_rate_kw=device.max_charge_rate_kw,
            max_discharge_rate_kw=device.max_discharge_rate_kw,
            status=device.status,
            last_seen=device.last_seen,
            created_at=device.created_at,
            updated_at=device.updated_at
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to register device: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register device"
        )


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: str,
    service: DeviceService = Depends(get_device_service)
):
    """
    Retrieve device information.
    
    Returns device metadata and current status.
    """
    logger.info(f"Retrieving device {device_id}")
    
    try:
        device = await service.get_device(device_id)
        
        if device is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device {device_id} not found"
            )
        
        return DeviceResponse(
            device_id=device.device_id,
            location=device.location,
            battery_capacity_kwh=device.battery_capacity_kwh,
            max_charge_rate_kw=device.max_charge_rate_kw,
            max_discharge_rate_kw=device.max_discharge_rate_kw,
            status=device.status,
            last_seen=device.last_seen,
            created_at=device.created_at,
            updated_at=device.updated_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve device: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve device"
        )


@router.post("/{device_id}/acknowledgements", status_code=status.HTTP_202_ACCEPTED)
async def submit_acknowledgement(
    device_id: str,
    ack_request: AcknowledgementRequest,
    service: DeviceService = Depends(get_device_service)
):
    """
    Submit execution acknowledgement from a device.
    
    Records the result of a command execution for monitoring and analytics.
    """
    logger.info(
        f"Received acknowledgement from {device_id} for entry {ack_request.schedule_entry_index}"
    )
    
    if ack_request.device_id != device_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="device_id in URL and body must match"
        )
    
    try:
        await service.process_acknowledgement(
            device_id=device_id,
            schedule_entry_index=ack_request.schedule_entry_index,
            execution_time=ack_request.execution_time,
            status=ack_request.status,
            actual_rate_kw=ack_request.actual_rate_kw,
            error_message=ack_request.error_message
        )
        
        logger.info(f"Acknowledgement processed for {device_id}")
        
        return {
            "status": "accepted",
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to process acknowledgement: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process acknowledgement"
        )


@router.get("", response_model=List[DeviceResponse])
async def list_devices(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    service: DeviceService = Depends(get_device_service)
):
    """
    List devices with optional filtering.
    
    Returns a paginated list of devices, optionally filtered by status.
    """
    logger.info(f"Listing devices: limit={limit}, offset={offset}, status={status_filter}")
    
    try:
        devices = await service.list_devices(
            limit=limit,
            offset=offset,
            status_filter=status_filter
        )
        
        return [
            DeviceResponse(
                device_id=d.device_id,
                location=d.location,
                battery_capacity_kwh=d.battery_capacity_kwh,
                max_charge_rate_kw=d.max_charge_rate_kw,
                max_discharge_rate_kw=d.max_discharge_rate_kw,
                status=d.status,
                last_seen=d.last_seen,
                created_at=d.created_at,
                updated_at=d.updated_at
            )
            for d in devices
        ]
    
    except Exception as e:
        logger.error(f"Failed to list devices: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list devices"
        )


@router.patch("/{device_id}/status", response_model=DeviceResponse)
async def update_device_status(
    device_id: str,
    new_status: str = Query(..., description="New status: online, offline, maintenance"),
    service: DeviceService = Depends(get_device_service)
):
    """
    Update device status.
    
    Manually update device status for administrative purposes.
    """
    logger.info(f"Updating status for device {device_id} to {new_status}")
    
    valid_statuses = {"online", "offline", "maintenance"}
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Status must be one of: {', '.join(valid_statuses)}"
        )
    
    try:
        device = await service.update_device_status(device_id, new_status)
        
        if device is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device {device_id} not found"
            )
        
        return DeviceResponse(
            device_id=device.device_id,
            location=device.location,
            battery_capacity_kwh=device.battery_capacity_kwh,
            max_charge_rate_kw=device.max_charge_rate_kw,
            max_discharge_rate_kw=device.max_discharge_rate_kw,
            status=device.status,
            last_seen=device.last_seen,
            created_at=device.created_at,
            updated_at=device.updated_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update device status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update device status"
        )
