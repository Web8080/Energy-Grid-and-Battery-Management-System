"""
Health Check API Routes

Endpoints for monitoring system health and readiness.
Used by load balancers, monitoring systems, and deployment pipelines.
"""

import logging
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status

from cloud_backend.config.database import check_db_connection
from cloud_backend.config.settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


@router.get("")
async def health_check() -> Dict[str, str]:
    """
    Basic health check endpoint.
    
    Returns 200 if the service is running. Does not check dependencies.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "energy-grid-api"
    }


@router.get("/ready")
async def readiness_check() -> Dict[str, str]:
    """
    Readiness check endpoint.
    
    Returns 200 if the service is ready to accept traffic.
    Checks database connectivity.
    """
    try:
        db_healthy = await check_db_connection()
        
        if not db_healthy:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection failed"
            )
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected",
            "service": "energy-grid-api"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )


@router.get("/live")
async def liveness_check() -> Dict[str, str]:
    """
    Liveness check endpoint.
    
    Returns 200 if the service process is alive.
    Used by Kubernetes liveness probes.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "energy-grid-api"
    }
