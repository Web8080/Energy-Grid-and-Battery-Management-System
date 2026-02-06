"""
ML Optimization API Routes

REST API endpoints for ML model predictions and schedule optimization.
"""

import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from cloud_backend.services.ml_service import MLService

logger = logging.getLogger(__name__)
router = APIRouter()


class OptimizationRequest(BaseModel):
    """Request model for schedule optimization."""
    device_id: str = Field(..., description="Device identifier")
    date: Optional[str] = Field(None, description="Date in YYYY-MM-DD format")
    objective: Optional[str] = Field("cost", description="Optimization objective: cost or revenue")


class OptimizationResponse(BaseModel):
    """Response model for optimized schedule."""
    device_id: str
    optimized_schedule: List[dict]
    predicted_savings_percent: Optional[float]
    model_version: str
    prediction_timestamp: str


def get_ml_service() -> MLService:
    """Dependency injection for ML service."""
    return MLService()


@router.post("/optimize", response_model=OptimizationResponse)
async def optimize_schedule(
    request: OptimizationRequest,
    service: MLService = Depends(get_ml_service)
):
    """
    Generate an optimized schedule using ML predictions.
    
    Uses historical data and ML models to predict optimal charge/discharge
    times that minimize cost or maximize revenue.
    """
    logger.info(f"Optimizing schedule for device {request.device_id}")
    
    try:
        result = await service.optimize_schedule(
            device_id=request.device_id,
            date=request.date,
            objective=request.objective
        )
        
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No data available for device {request.device_id}"
            )
        
        return OptimizationResponse(
            device_id=result["device_id"],
            optimized_schedule=result["optimized_schedule"],
            predicted_savings_percent=result.get("predicted_savings_percent"),
            model_version=result.get("model_version", "unknown"),
            prediction_timestamp=result.get("prediction_timestamp", "")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to optimize schedule: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize schedule"
        )


@router.get("/model/status", response_model=Dict)
async def get_model_status(
    service: MLService = Depends(get_ml_service)
):
    """
    Get ML model status and performance metrics.
    
    Returns current model version, performance metrics, and health status.
    """
    logger.info("Retrieving ML model status")
    
    try:
        status_info = await service.get_model_status()
        return status_info
    
    except Exception as e:
        logger.error(f"Failed to get model status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get model status"
        )


@router.post("/model/reload", status_code=status.HTTP_202_ACCEPTED)
async def reload_model(
    model_version: Optional[str] = Query(None, description="Specific model version to load"),
    service: MLService = Depends(get_ml_service)
):
    """
    Reload ML model from storage.
    
    Forces reload of the ML model, optionally to a specific version.
    """
    logger.info(f"Reloading ML model: version={model_version}")
    
    try:
        await service.reload_model(model_version)
        return {
            "status": "accepted",
            "message": "Model reload initiated"
        }
    
    except Exception as e:
        logger.error(f"Failed to reload model: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reload model"
        )
