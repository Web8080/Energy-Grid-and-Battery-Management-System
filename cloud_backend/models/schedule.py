"""
Schedule Data Models

SQLAlchemy models and Pydantic schemas for battery schedules.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, JSON, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Schedule(Base):
    """SQLAlchemy model for battery schedules."""
    
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), nullable=False, index=True)
    schedule = Column(JSON, nullable=False)
    source = Column(String(100), nullable=True)
    priority = Column(Integer, default=1)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ScheduleEntry(BaseModel):
    """Pydantic model for a single schedule entry."""
    start_time: str
    end_time: str
    mode: int
    rate_kw: float


class ScheduleModel(BaseModel):
    """Pydantic model for complete schedule."""
    device_id: str
    schedule: List[dict]
    source: Optional[str] = None
    priority: int = 1
    status: str = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
