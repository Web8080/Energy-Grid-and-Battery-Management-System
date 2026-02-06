"""
ML Model Serving

Serves ML models for schedule optimization predictions.
Handles model loading, feature computation, and prediction serving.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ml_pipeline.training.train_model import ScheduleOptimizationModel

logger = logging.getLogger(__name__)


class ModelServer:
    """
    Server for ML model predictions.
    
    Manages model lifecycle and serves predictions for schedule optimization.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize model server.
        
        Args:
            model_path: Path to model file (loads latest if None)
        """
        self.model: Optional[ScheduleOptimizationModel] = None
        self.model_version: str = "unknown"
        self.model_path: Optional[str] = model_path
        self.loaded_at: Optional[datetime] = None
    
    def load_model(self, model_path: Optional[str] = None):
        """
        Load model from disk.
        
        Args:
            model_path: Path to model file
        """
        if model_path is None:
            model_path = self.model_path or self._find_latest_model()
        
        if model_path is None:
            raise ValueError("No model path provided and no model found")
        
        self.model = ScheduleOptimizationModel.load(model_path)
        self.model_path = model_path
        self.model_version = Path(model_path).stem
        self.loaded_at = datetime.utcnow()
        
        logger.info(f"Model loaded: {model_path}, version: {self.model_version}")
    
    def predict_optimal_schedule(
        self,
        device_id: str,
        historical_prices: Optional[pd.DataFrame] = None,
        historical_demand: Optional[pd.DataFrame] = None,
        device_history: Optional[pd.DataFrame] = None
    ) -> List[Dict]:
        """
        Predict optimal schedule for a device.
        
        Args:
            device_id: Device identifier
            historical_prices: Historical energy prices
            historical_demand: Historical demand data
            device_history: Device usage history
        
        Returns:
            List of optimized schedule entries
        """
        if self.model is None:
            raise ValueError("Model not loaded")
        
        try:
            features = self.model.prepare_features(
                historical_prices,
                historical_demand,
                device_history
            )
            
            predictions = self.model.predict(features)
            
            schedule = self._predictions_to_schedule(predictions)
            
            logger.info(f"Generated optimized schedule for {device_id}")
            return schedule
        
        except Exception as e:
            logger.error(f"Prediction failed for {device_id}: {e}", exc_info=True)
            raise
    
    def _predictions_to_schedule(self, predictions: np.ndarray) -> List[Dict]:
        """
        Convert predictions to schedule format.
        
        Args:
            predictions: Model predictions
        
        Returns:
            List of schedule entries
        """
        schedule = []
        base_time = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        
        for i, pred in enumerate(predictions[:48]):
            start_time = base_time + pd.Timedelta(minutes=30 * i)
            end_time = start_time + pd.Timedelta(minutes=30)
            
            mode = 1 if pred > 0 else 2
            rate_kw = abs(pred)
            
            schedule.append({
                "start_time": start_time.isoformat() + "Z",
                "end_time": end_time.isoformat() + "Z",
                "mode": mode,
                "rate_kw": min(rate_kw, 1000.0)
            })
        
        return schedule
    
    def _find_latest_model(self) -> Optional[str]:
        """Find the latest model file."""
        model_dir = Path("ml_pipeline/models")
        
        if not model_dir.exists():
            return None
        
        model_files = list(model_dir.glob("*.pkl"))
        
        if not model_files:
            return None
        
        latest = max(model_files, key=lambda p: p.stat().st_mtime)
        return str(latest)
    
    def get_status(self) -> Dict:
        """Get model server status."""
        return {
            "model_loaded": self.model is not None,
            "model_version": self.model_version,
            "model_path": self.model_path,
            "loaded_at": self.loaded_at.isoformat() if self.loaded_at else None
        }


def main():
    """Example usage."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    server = ModelServer()
    
    try:
        server.load_model()
        print(f"Model status: {server.get_status()}")
    except ValueError as e:
        print(f"Failed to load model: {e}")


if __name__ == "__main__":
    main()
