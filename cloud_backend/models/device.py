"""
Device Data Models

SQLAlchemy models and Pydantic schemas for device management.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Float, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Device(Base):
    """SQLAlchemy model for devices."""
    
    __tablename__ = "devices"
    
    device_id = Column(String(100), primary_key=True, index=True)
    location = Column(String(255), nullable=True)
    battery_capacity_kwh = Column(Float, nullable=True)
    max_charge_rate_kw = Column(Float, nullable=True)
    max_discharge_rate_kw = Column(Float, nullable=True)
    status = Column(String(50), default="offline")
    last_seen = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DeviceModel(BaseModel):
    """Pydantic model for device information."""
    device_id: str
    location: Optional[str] = None
    battery_capacity_kwh: Optional[float] = None
    max_charge_rate_kw: Optional[float] = None
    max_discharge_rate_kw: Optional[float] = None
    status: str = "offline"
    last_seen: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
