"""
Device Service

Business logic for device management including registration,
status tracking, and acknowledgement processing.
"""

import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cloud_backend.config.database import get_db
from cloud_backend.models.device import Device

logger = logging.getLogger(__name__)


class DeviceService:
    """Service for managing devices."""
    
    async def register_device(
        self,
        device_id: str,
        location: Optional[str] = None,
        battery_capacity_kwh: Optional[float] = None,
        max_charge_rate_kw: Optional[float] = None,
        max_discharge_rate_kw: Optional[float] = None
    ) -> Device:
        """
        Register a new device.
        
        Args:
            device_id: Unique device identifier
            location: Device location
            battery_capacity_kwh: Battery capacity in kWh
            max_charge_rate_kw: Maximum charge rate in kW
            max_discharge_rate_kw: Maximum discharge rate in kW
        
        Returns:
            Device object
        
        Raises:
            ValueError: If device already exists
        """
        async for session in get_db():
            existing = await session.get(Device, device_id)
            
            if existing:
                raise ValueError(f"Device {device_id} already exists")
            
            device = Device(
                device_id=device_id,
                location=location,
                battery_capacity_kwh=battery_capacity_kwh,
                max_charge_rate_kw=max_charge_rate_kw,
                max_discharge_rate_kw=max_discharge_rate_kw,
                status="offline"
            )
            
            session.add(device)
            await session.commit()
            await session.refresh(device)
            
            logger.info(f"Registered device {device_id}")
            return device
    
    async def get_device(self, device_id: str) -> Optional[Device]:
        """
        Get device information.
        
        Args:
            device_id: Device identifier
        
        Returns:
            Device object or None if not found
        """
        async for session in get_db():
            device = await session.get(Device, device_id)
            return device
    
    async def update_device_status(
        self,
        device_id: str,
        status: str
    ) -> Optional[Device]:
        """
        Update device status.
        
        Args:
            device_id: Device identifier
            status: New status (online, offline, maintenance)
        
        Returns:
            Updated device object or None if not found
        """
        async for session in get_db():
            device = await session.get(Device, device_id)
            
            if device:
                device.status = status
                device.updated_at = datetime.utcnow()
                await session.commit()
                await session.refresh(device)
                
                logger.info(f"Updated device {device_id} status to {status}")
            
            return device
    
    async def update_last_seen(self, device_id: str):
        """
        Update device last seen timestamp.
        
        Args:
            device_id: Device identifier
        """
        async for session in get_db():
            device = await session.get(Device, device_id)
            
            if device:
                device.last_seen = datetime.utcnow()
                device.status = "online"
                await session.commit()
    
    async def process_acknowledgement(
        self,
        device_id: str,
        schedule_entry_index: int,
        execution_time: str,
        status: str,
        actual_rate_kw: Optional[float] = None,
        error_message: Optional[str] = None
    ):
        """
        Process device execution acknowledgement.
        
        Args:
            device_id: Device identifier
            schedule_entry_index: Index of executed schedule entry
            execution_time: ISO8601 timestamp of execution
            status: Execution status (success or failed)
            actual_rate_kw: Actual rate achieved
            error_message: Error message if failed
        """
        await self.update_last_seen(device_id)
        
        logger.info(
            f"Processed acknowledgement from {device_id}: "
            f"entry={schedule_entry_index}, status={status}"
        )
        
        if status == "failed":
            logger.warning(
                f"Device {device_id} execution failed: {error_message}"
            )


    async def list_devices(
        self,
        limit: int = 100,
        offset: int = 0,
        status_filter: Optional[str] = None
    ) -> List[Device]:
        """
        List devices with pagination and optional filtering.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            status_filter: Optional status filter
        
        Returns:
            List of device objects
        """
        async for session in get_db():
            stmt = select(Device)
            
            if status_filter:
                stmt = stmt.where(Device.status == status_filter)
            
            stmt = stmt.order_by(
                Device.created_at.desc()
            ).limit(limit).offset(offset)
            
            result = await session.execute(stmt)
            devices = result.scalars().all()
            
            return list(devices)
