"""
Schedule Service

Business logic for schedule management including CRUD operations,
caching, and distribution coordination.
"""

import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from cloud_backend.config.database import get_db
from cloud_backend.models.schedule import Schedule

logger = logging.getLogger(__name__)


class ScheduleService:
    """Service for managing battery schedules."""
    
    async def create_schedule(
        self,
        device_id: str,
        schedule_entries: List[dict],
        source: Optional[str] = None,
        priority: int = 1
    ) -> Schedule:
        """
        Create a new schedule for a device.
        
        Args:
            device_id: Device identifier
            schedule_entries: List of schedule entry dictionaries
            source: Source of the schedule
            priority: Schedule priority (1-10)
        
        Returns:
            Created schedule object
        """
        async for session in get_db():
            schedule = Schedule(
                device_id=device_id,
                schedule=schedule_entries,
                source=source,
                priority=priority,
                status="active"
            )
            
            session.add(schedule)
            await session.commit()
            await session.refresh(schedule)
            
            logger.info(f"Created schedule for device {device_id}")
            return schedule
    
    async def get_schedule(
        self,
        device_id: str,
        date: Optional[str] = None
    ) -> Optional[Schedule]:
        """
        Get the current schedule for a device.
        
        Args:
            device_id: Device identifier
            date: Optional date filter
        
        Returns:
            Schedule object or None if not found
        """
        async for session in get_db():
            stmt = select(Schedule).where(
                Schedule.device_id == device_id,
                Schedule.status == "active"
            ).order_by(Schedule.priority.desc(), Schedule.created_at.desc())
            
            result = await session.execute(stmt)
            schedule = result.scalar_one_or_none()
            
            return schedule
    
    async def update_schedule(
        self,
        device_id: str,
        schedule_entries: List[dict],
        source: Optional[str] = None,
        priority: int = 1
    ) -> Schedule:
        """
        Update an existing schedule for a device.
        
        Deactivates old schedule and creates a new one.
        
        Args:
            device_id: Device identifier
            schedule_entries: List of schedule entry dictionaries
            source: Source of the schedule
            priority: Schedule priority
        
        Returns:
            Updated schedule object
        """
        async for session in get_db():
            stmt = select(Schedule).where(
                Schedule.device_id == device_id,
                Schedule.status == "active"
            )
            
            result = await session.execute(stmt)
            old_schedule = result.scalar_one_or_none()
            
            if old_schedule:
                old_schedule.status = "inactive"
            
            new_schedule = Schedule(
                device_id=device_id,
                schedule=schedule_entries,
                source=source,
                priority=priority,
                status="active"
            )
            
            session.add(new_schedule)
            await session.commit()
            await session.refresh(new_schedule)
            
            logger.info(f"Updated schedule for device {device_id}")
            return new_schedule
    
    async def delete_schedule(self, device_id: str):
        """
        Delete (deactivate) schedule for a device.
        
        Args:
            device_id: Device identifier
        """
        async for session in get_db():
            stmt = select(Schedule).where(
                Schedule.device_id == device_id,
                Schedule.status == "active"
            )
            
            result = await session.execute(stmt)
            schedule = result.scalar_one_or_none()
            
            if schedule:
                schedule.status = "inactive"
                await session.commit()
                logger.info(f"Deleted schedule for device {device_id}")
    
    async def list_schedules(
        self,
        limit: int = 100,
        offset: int = 0,
        device_id: Optional[str] = None
    ) -> List[Schedule]:
        """
        List schedules with pagination and optional filtering.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            device_id: Optional device ID filter
        
        Returns:
            List of schedule objects
        """
        async for session in get_db():
            stmt = select(Schedule).where(
                Schedule.status == "active"
            )
            
            if device_id:
                stmt = stmt.where(Schedule.device_id == device_id)
            
            stmt = stmt.order_by(
                Schedule.created_at.desc()
            ).limit(limit).offset(offset)
            
            result = await session.execute(stmt)
            schedules = result.scalars().all()
            
            return list(schedules)
