"""
ML Model Training Pipeline

Trains models for battery schedule optimization using historical
energy price and demand data.
"""

import logging
import pickle
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)


class ScheduleOptimizationModel:
    """
    ML model for predicting optimal battery schedules.
    
    Uses historical energy prices and demand patterns to predict
    optimal charge/discharge times.
    """
    
    def __init__(self):
        """Initialize the model."""
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.feature_names: List[str] = []
        self.trained = False
    
    def prepare_features(
        self,
        historical_prices: pd.DataFrame,
        historical_demand: pd.DataFrame,
        device_history: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        Prepare features for training.
        
        Args:
            historical_prices: Historical energy prices
            historical_demand: Historical demand data
            device_history: Optional device usage history
        
        Returns:
            DataFrame with features
        """
        features = []
        
        if historical_prices is not None and len(historical_prices) > 0:
            features.append(historical_prices["price"].values)
            features.append(historical_prices["price"].rolling(24).mean().values)
            features.append(historical_prices["price"].rolling(168).mean().values)
        
        if historical_demand is not None and len(historical_demand) > 0:
            features.append(historical_demand["demand"].values)
            features.append(historical_demand["demand"].rolling(24).mean().values)
        
        if device_history is not None and len(device_history) > 0:
            features.append(device_history["usage"].values)
        
        if not features:
            raise ValueError("No features available for training")
        
        feature_df = pd.DataFrame(np.column_stack(features))
        self.feature_names = [f"feature_{i}" for i in range(feature_df.shape[1])]
        feature_df.columns = self.feature_names
        
        return feature_df
    
    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        test_size: float = 0.2
    ) -> Dict[str, float]:
        """
        Train the model.
        
        Args:
            X: Feature matrix
            y: Target values (optimal rates)
            test_size: Proportion of data for testing
        
        Returns:
            Dictionary with evaluation metrics
        """
        logger.info(f"Training model on {len(X)} samples")
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        self.model.fit(X_train, y_train)
        
        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)
        
        metrics = {
            "train_mae": mean_absolute_error(y_train, y_pred_train),
            "train_rmse": np.sqrt(mean_squared_error(y_train, y_pred_train)),
            "train_r2": r2_score(y_train, y_pred_train),
            "test_mae": mean_absolute_error(y_test, y_pred_test),
            "test_rmse": np.sqrt(mean_squared_error(y_test, y_pred_test)),
            "test_r2": r2_score(y_test, y_pred_test)
        }
        
        logger.info(f"Model training completed: {metrics}")
        self.trained = True
        
        return metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions.
        
        Args:
            X: Feature matrix
        
        Returns:
            Predictions array
        """
        if not self.trained:
            raise ValueError("Model not trained")
        
        return self.model.predict(X)
    
    def save(self, path: str):
        """
        Save model to disk.
        
        Args:
            path: Path to save model
        """
        model_data = {
            "model": self.model,
            "feature_names": self.feature_names,
            "trained": self.trained,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "wb") as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Model saved to {path}")
    
    @classmethod
    def load(cls, path: str) -> "ScheduleOptimizationModel":
        """
        Load model from disk.
        
        Args:
            path: Path to model file
        
        Returns:
            Loaded model instance
        """
        with open(path, "rb") as f:
            model_data = pickle.load(f)
        
        instance = cls()
        instance.model = model_data["model"]
        instance.feature_names = model_data["feature_names"]
        instance.trained = model_data["trained"]
        
        logger.info(f"Model loaded from {path}")
        return instance


def main():
    """Example training script."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    model = ScheduleOptimizationModel()
    
    historical_prices = pd.DataFrame({
        "price": np.random.randn(1000) * 10 + 50,
        "timestamp": pd.date_range("2024-01-01", periods=1000, freq="H")
    })
    
    historical_demand = pd.DataFrame({
        "demand": np.random.randn(1000) * 100 + 500,
        "timestamp": pd.date_range("2024-01-01", periods=1000, freq="H")
    })
    
    X = model.prepare_features(historical_prices, historical_demand)
    y = pd.Series(np.random.randn(len(X)) * 20 + 100)
    
    metrics = model.train(X, y)
    print(f"Training metrics: {metrics}")
    
    model.save("ml_pipeline/models/optimization_model.pkl")


if __name__ == "__main__":
    main()
