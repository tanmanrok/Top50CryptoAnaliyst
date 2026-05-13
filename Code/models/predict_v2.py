"""
Phase 2.5 - Phase F: Production Prediction Service for Model v2
Load trained Ridge model and generate daily Bitcoin next-day price predictions.

Workflow:
1. Load final model, scalers, and metadata from Phase D artifacts
2. Fetch latest Bitcoin features from database
3. Generate prediction for next day's close price
4. Store prediction with confidence metrics in database
5. Log all predictions for auditing and analysis
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import logging
import pickle
import json
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional

# Add parent Code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.db_connection import engine
from sqlalchemy import text, Column, Float, DateTime, String, Integer, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database ORM
Base = declarative_base()


class BitcoinPredictionV2(Base):
    """ORM model for storing Model v2 predictions."""
    __tablename__ = 'bitcoin_predictions_v2'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    prediction_date = Column(DateTime, nullable=False)  # When prediction was made
    target_date = Column(DateTime, nullable=False)      # What date is being predicted
    predicted_price = Column(Float, nullable=False)     # Predicted close price
    confidence_interval_lower = Column(Float)           # 95% CI lower bound (scaled)
    confidence_interval_upper = Column(Float)           # 95% CI upper bound (scaled)
    model_version = Column(String(50), default='v2_ridge')
    input_features_hash = Column(String(64))            # Hash of input features for traceability
    status = Column(String(20), default='pending')      # pending, confirmed, failed
    actual_price = Column(Float)                        # Filled in after market close
    prediction_error = Column(Float)                    # |predicted - actual| / actual
    
    def __repr__(self):
        return f"<Prediction: {self.target_date.date()} pred={self.predicted_price:.2f}>"


class PredictionServiceV2:
    """
    Production prediction service for Model v2.
    
    Generates daily Bitcoin next-day price predictions using the final Ridge model
    trained on all available historical data.
    """
    
    def __init__(self, model_dir: str = 'models', crypto: str = 'bitcoin'):
        """
        Initialize prediction service.
        
        Args:
            model_dir: Directory containing trained model artifacts
            crypto: Cryptocurrency name (e.g., 'bitcoin')
        """
        self.model_dir = Path(model_dir)
        self.crypto = crypto.lower()
        self.engine = engine
        
        # Model artifacts
        self.model = None
        self.scaler_X = None
        self.scaler_y = None
        self.metadata = None
        self.feature_cols = None
        
        # Prediction state
        self.latest_features = None
        self.latest_timestamp = None
        self.prediction = None
        
        logger.info(f"PredictionServiceV2 initialized for {self.crypto}")
    
    def load_model_artifacts(self) -> bool:
        """
        Load trained model, scalers, and metadata from Phase D.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Loading model artifacts...")
        
        try:
            # Model file
            model_file = self.model_dir / f'v2_final_Ridge_{self.crypto}.pkl'
            if not model_file.exists():
                logger.error(f"Model file not found: {model_file}")
                return False
            
            with open(model_file, 'rb') as f:
                self.model = pickle.load(f)
            logger.info(f"✓ Model loaded: {model_file.name}")
            
            # Feature scaler
            scaler_X_file = self.model_dir / f'v2_final_scaler_X_{self.crypto}.pkl'
            if not scaler_X_file.exists():
                logger.error(f"Feature scaler not found: {scaler_X_file}")
                return False
            
            with open(scaler_X_file, 'rb') as f:
                self.scaler_X = pickle.load(f)
            logger.info(f"✓ Feature scaler loaded: {scaler_X_file.name}")
            
            # Target scaler
            scaler_y_file = self.model_dir / f'v2_final_scaler_y_{self.crypto}.pkl'
            if not scaler_y_file.exists():
                logger.error(f"Target scaler not found: {scaler_y_file}")
                return False
            
            with open(scaler_y_file, 'rb') as f:
                self.scaler_y = pickle.load(f)
            logger.info(f"✓ Target scaler loaded: {scaler_y_file.name}")
            
            # Metadata
            metadata_file = self.model_dir / f'v2_final_Ridge_{self.crypto}_metadata.json'
            if not metadata_file.exists():
                logger.error(f"Metadata file not found: {metadata_file}")
                return False
            
            with open(metadata_file, 'r') as f:
                self.metadata = json.load(f)
            logger.info(f"✓ Metadata loaded: {metadata_file.name}")
            logger.info(f"  Model R²: {self.metadata.get('r2_score', 'N/A')}")
            logger.info(f"  Trained on {self.metadata.get('n_samples', 'N/A')} samples")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to load model artifacts: {e}")
            return False
    
    def fetch_latest_features(self) -> bool:
        """
        Fetch latest Bitcoin features from database (most recent day).
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Fetching latest Bitcoin features from database...")
        
        try:
            query = f"""
            SELECT 
                timestamp,
                open, high, low, close, volume,
                sma_5, sma_10, sma_20, sma_50,
                ema_12, ema_26,
                macd, macd_signal, macd_diff,
                rsi_14,
                bb_upper_20, bb_middle_20, bb_lower_20,
                roc_12, momentum_10, atr_14,
                daily_return, weekly_return, monthly_return,
                volatility_7, volatility_30,
                day_of_week, month
            FROM computed_features
            WHERE cryptocurrency = :crypto
            ORDER BY timestamp DESC
            LIMIT 1
            """
            
            with self.engine.begin() as conn:
                result = pd.read_sql(text(query), conn, params={'crypto': self.crypto})
            
            if result.empty:
                logger.error("No data found in database")
                return False
            
            self.latest_features = result.iloc[0]
            self.latest_timestamp = pd.to_datetime(self.latest_features['timestamp'])
            
            logger.info(f"✓ Latest features loaded for {self.latest_timestamp.date()}")
            logger.info(f"  Close price: ${self.latest_features['close']:.2f}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to fetch latest features: {e}")
            return False
    
    def prepare_features(self) -> Optional[np.ndarray]:
        """
        Prepare features for model prediction (scale and arrange).
        
        Returns:
            Scaled feature array or None if error
        """
        logger.info("Preparing features for prediction...")
        
        try:
            if self.latest_features is None:
                logger.error("Latest features not loaded")
                return None
            
            # Feature columns (same as used in training)
            feature_cols = [col for col in self.latest_features.index 
                          if col not in ['timestamp', 'close', 'trend_up']]
            
            # Extract feature values
            X = self.latest_features[feature_cols].values.reshape(1, -1)
            
            # Scale features using trained scaler
            X_scaled = self.scaler_X.transform(X)
            
            logger.info(f"✓ Features prepared: {X_scaled.shape[0]} sample(s), {X_scaled.shape[1]} features")
            
            return X_scaled
        
        except Exception as e:
            logger.error(f"Failed to prepare features: {e}")
            return None
    
    def make_prediction(self, X_scaled: np.ndarray) -> Optional[float]:
        """
        Generate next-day price prediction using trained model.
        
        Args:
            X_scaled: Scaled feature array
        
        Returns:
            Predicted price (unscaled) or None if error
        """
        logger.info("Generating next-day price prediction...")
        
        try:
            if self.model is None:
                logger.error("Model not loaded")
                return None
            
            # Predict in scaled space
            y_pred_scaled = self.model.predict(X_scaled)[0]
            
            # Unscale to get actual price
            y_pred = self.scaler_y.inverse_transform([[y_pred_scaled]])[0, 0]
            
            # Calculate confidence interval (approximate)
            # Using residual std dev from training
            residual_std = self.metadata.get('residual_std', 0.1)
            confidence_margin = 1.96 * residual_std  # 95% CI
            
            ci_lower = y_pred - confidence_margin
            ci_upper = y_pred + confidence_margin
            
            logger.info(f"✓ Prediction generated:")
            logger.info(f"  Predicted close (tomorrow): ${y_pred:.2f}")
            logger.info(f"  95% CI: [${ci_lower:.2f}, ${ci_upper:.2f}]")
            logger.info(f"  Expected change: {((y_pred / self.latest_features['close']) - 1) * 100:+.2f}%")
            
            self.prediction = {
                'predicted_price': y_pred,
                'ci_lower': ci_lower,
                'ci_upper': ci_upper,
                'predicted_timestamp': self.latest_timestamp + timedelta(days=1)
            }
            
            return y_pred
        
        except Exception as e:
            logger.error(f"Failed to generate prediction: {e}")
            return None
    
    def store_prediction(self) -> bool:
        """
        Store prediction in database.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Storing prediction in database...")
        
        try:
            if self.prediction is None:
                logger.error("No prediction generated yet")
                return False
            
            # Create ORM session
            Session = sessionmaker(bind=self.engine)
            session = Session()
            
            # Create prediction record (convert numpy types to Python types)
            pred_record = BitcoinPredictionV2(
                prediction_date=datetime.now(),
                target_date=self.prediction['predicted_timestamp'],
                predicted_price=float(self.prediction['predicted_price']),
                confidence_interval_lower=float(self.prediction['ci_lower']),
                confidence_interval_upper=float(self.prediction['ci_upper']),
                model_version='v2_ridge',
                status='pending'
            )
            
            # Add and commit
            session.add(pred_record)
            session.commit()
            
            logger.info(f"✓ Prediction stored (ID: {pred_record.id})")
            
            session.close()
            return True
        
        except Exception as e:
            logger.error(f"Failed to store prediction: {e}")
            return False
    
    def predict_tomorrow(self) -> Optional[Dict]:
        """
        Execute full prediction pipeline for tomorrow's Bitcoin price.
        
        Returns:
            Dictionary with prediction details or None if error
        """
        logger.info("\n" + "=" * 80)
        logger.info("BITCOIN NEXT-DAY PRICE PREDICTION - MODEL V2")
        logger.info("=" * 80)
        
        # Step 1: Load model
        if not self.load_model_artifacts():
            logger.error("Failed to load model artifacts")
            return None
        
        # Step 2: Fetch latest features
        if not self.fetch_latest_features():
            logger.error("Failed to fetch latest features")
            return None
        
        # Step 3: Prepare features
        X_scaled = self.prepare_features()
        if X_scaled is None:
            logger.error("Failed to prepare features")
            return None
        
        # Step 4: Make prediction
        predicted_price = self.make_prediction(X_scaled)
        if predicted_price is None:
            logger.error("Failed to generate prediction")
            return None
        
        # Step 5: Store prediction
        if not self.store_prediction():
            logger.warning("Failed to store prediction (non-critical)")
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ Prediction pipeline complete!")
        logger.info("=" * 80 + "\n")
        
        return self.prediction


def main():
    """Main entry point for prediction service."""
    logger.info("\n")
    logger.info("=" * 80)
    logger.info("BITCOIN MODEL V2 PRODUCTION PREDICTION SERVICE")
    logger.info("=" * 80)
    
    # Initialize service
    service = PredictionServiceV2(model_dir='models', crypto='bitcoin')
    
    # Run prediction
    result = service.predict_tomorrow()
    
    if result:
        logger.info("\n" + "=" * 80)
        logger.info("PREDICTION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Current date: {service.latest_timestamp.date()}")
        logger.info(f"Target date: {result['predicted_timestamp'].date()}")
        logger.info(f"Predicted price: ${result['predicted_price']:.2f}")
        logger.info(f"95% Confidence interval: [${result['ci_lower']:.2f}, ${result['ci_upper']:.2f}]")
        logger.info("=" * 80 + "\n")
        return 0
    else:
        logger.error("\n❌ Prediction failed. Check logs for details.\n")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
