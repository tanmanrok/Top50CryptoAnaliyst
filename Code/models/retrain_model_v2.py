"""
Phase F: Model Retraining Scheduler
Periodically retrain Ridge model with new Bitcoin data to keep predictions current.
Runs weekly to incorporate latest market data into the model.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import logging
import pickle
import json
from datetime import datetime, timedelta
from typing import Dict, Tuple
import subprocess

# Add parent Code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.db_connection import engine
from sqlalchemy import text
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelRetrainingScheduler:
    """
    Retrain Ridge model with latest Bitcoin data.
    
    Workflow:
    1. Load latest data from database (includes new data since last training)
    2. Prepare features and targets with proper temporal split
    3. Train new Ridge model on expanded dataset
    4. Validate model performance against test set
    5. If performance is maintained, backup old model and replace with new
    6. Log retraining results for auditing
    """
    
    def __init__(self, data_dir: str = 'data/model_data', 
                 model_dir: str = 'models', crypto: str = 'bitcoin'):
        """
        Initialize retraining scheduler.
        
        Args:
            data_dir: Directory for train/test CSVs
            model_dir: Directory for model artifacts
            crypto: Cryptocurrency name
        """
        self.data_dir = Path(data_dir)
        self.model_dir = Path(model_dir)
        self.crypto = crypto.lower()
        self.engine = engine
        
        # Data
        self.df_full = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        
        # Models
        self.model_old = None
        self.model_new = None
        self.scaler_X = None
        self.scaler_y = None
        
        # Metrics
        self.metrics_old = None
        self.metrics_new = None
        
        logger.info(f"ModelRetrainingScheduler initialized for {self.crypto}")
    
    def fetch_latest_data(self) -> bool:
        """
        Fetch all latest Bitcoin data from database.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Fetching latest Bitcoin data from database...")
        
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
            ORDER BY timestamp ASC
            """
            
            with self.engine.begin() as conn:
                self.df_full = pd.read_sql(text(query), conn, params={'crypto': self.crypto})
            
            if self.df_full.empty:
                logger.error("No data found in database")
                return False
            
            # Convert timestamp to datetime
            self.df_full['timestamp'] = pd.to_datetime(self.df_full['timestamp'])
            
            logger.info(f"✓ Loaded {len(self.df_full)} total records from database")
            logger.info(f"  Date range: {self.df_full['timestamp'].min().date()} to {self.df_full['timestamp'].max().date()}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to fetch data: {e}")
            return False
    
    def prepare_train_test_split(self, train_ratio: float = 0.8) -> bool:
        """
        Prepare training and test sets with proper temporal ordering.
        
        Args:
            train_ratio: Fraction for training
        
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Preparing {train_ratio:.0%}/{1-train_ratio:.0%} train/test split...")
        
        try:
            # Sort by timestamp
            self.df_full = self.df_full.sort_values('timestamp').reset_index(drop=True)
            
            # Create target (next day's close)
            self.df_full['target'] = self.df_full['close'].shift(-1)
            self.df_full = self.df_full.iloc[:-1]  # Drop last row
            
            # Drop NaN rows
            initial_rows = len(self.df_full)
            self.df_full = self.df_full.dropna()
            dropped = initial_rows - len(self.df_full)
            logger.info(f"  Dropped {dropped} NaN rows from indicators")
            
            # Temporal split (no shuffle)
            split_idx = int(len(self.df_full) * train_ratio)
            df_train = self.df_full.iloc[:split_idx]
            df_test = self.df_full.iloc[split_idx:]
            
            # Extract features and targets
            feature_cols = [col for col in self.df_full.columns 
                          if col not in ['timestamp', 'close', 'target', 'trend_up']]
            
            self.X_train = df_train[feature_cols].values
            self.X_test = df_test[feature_cols].values
            self.y_train = df_train['target'].values
            self.y_test = df_test['target'].values
            
            logger.info(f"✓ Train/test split created:")
            logger.info(f"  Train: {len(self.X_train)} samples ({df_train['timestamp'].min().date()} to {df_train['timestamp'].max().date()})")
            logger.info(f"  Test:  {len(self.X_test)} samples ({df_test['timestamp'].min().date()} to {df_test['timestamp'].max().date()})")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to prepare split: {e}")
            return False
    
    def train_new_model(self) -> bool:
        """
        Train new Ridge model on updated dataset.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Training new Ridge model...")
        
        try:
            # Scale data
            self.scaler_X = StandardScaler()
            X_train_scaled = self.scaler_X.fit_transform(self.X_train)
            X_test_scaled = self.scaler_X.transform(self.X_test)
            
            self.scaler_y = StandardScaler()
            y_train_scaled = self.scaler_y.fit_transform(self.y_train.reshape(-1, 1)).flatten()
            y_test_scaled = self.scaler_y.transform(self.y_test.reshape(-1, 1)).flatten()
            
            # Train Ridge
            self.model_new = Ridge(alpha=0.001)
            self.model_new.fit(X_train_scaled, y_train_scaled)
            
            # Evaluate
            y_pred_test = self.model_new.predict(X_test_scaled)
            r2 = r2_score(y_test_scaled, y_pred_test)
            rmse = np.sqrt(mean_squared_error(y_test_scaled, y_pred_test))
            mae = mean_absolute_error(y_test_scaled, y_pred_test)
            mape = np.mean(np.abs((y_test_scaled - y_pred_test) / y_test_scaled)) * 100
            
            self.metrics_new = {
                'r2_score': r2,
                'rmse': rmse,
                'mae': mae,
                'mape': mape,
                'n_samples': len(self.X_train) + len(self.X_test),
                'training_date': datetime.now().isoformat()
            }
            
            logger.info(f"✓ Model trained successfully:")
            logger.info(f"  R²: {r2:.6f} ({r2*100:.2f}%)")
            logger.info(f"  RMSE: {rmse:.6f}")
            logger.info(f"  MAE: {mae:.6f}")
            logger.info(f"  MAPE: {mape:.2f}%")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to train model: {e}")
            return False
    
    def load_old_model_metrics(self) -> bool:
        """
        Load old model's performance metrics for comparison.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Loading old model metrics...")
        
        try:
            metadata_file = self.model_dir / f'v2_final_Ridge_{self.crypto}_metadata.json'
            
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            self.metrics_old = {
                'r2_score': metadata.get('r2_score', 0.0),
                'rmse': metadata.get('rmse', float('inf')),
                'mape': metadata.get('mape', float('inf'))
            }
            
            logger.info(f"✓ Old model metrics loaded:")
            logger.info(f"  R²: {self.metrics_old['r2_score']:.6f}")
            logger.info(f"  RMSE: {self.metrics_old['rmse']:.6f}")
            logger.info(f"  MAPE: {self.metrics_old['mape']:.2f}%")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to load old metrics: {e}")
            return False
    
    def compare_and_decide(self, r2_threshold: float = 0.98) -> bool:
        """
        Compare new model with old model and decide whether to replace.
        
        Args:
            r2_threshold: Minimum R² for accepting new model
        
        Returns:
            True if new model should replace old, False otherwise
        """
        logger.info("\nComparing new model with old model...")
        
        r2_new = self.metrics_new['r2_score']
        r2_old = self.metrics_old['r2_score']
        
        logger.info(f"  R² improvement: {r2_old:.6f} → {r2_new:.6f} ({(r2_new-r2_old)*100:+.2f}pp)")
        
        # Decision criteria
        if r2_new < r2_threshold:
            logger.warning(f"  ❌ New model R² ({r2_new:.4f}) below threshold ({r2_threshold:.4f})")
            return False
        
        if r2_new < r2_old - 0.01:  # Allow up to 1% degradation due to new data volatility
            logger.warning(f"  ⚠️ New model R² degraded by >{1}%")
            return False
        
        logger.info(f"  ✅ New model meets quality criteria")
        return True
    
    def backup_and_replace_model(self) -> bool:
        """
        Backup old model and replace with new one.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Backing up old model and replacing with new...")
        
        try:
            # Backup old model artifacts
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            for suffix in ['', '_scaler_X', '_scaler_y', '_metadata.json']:
                old_file = self.model_dir / f'v2_final_Ridge_{self.crypto}{suffix}'
                backup_file = self.model_dir / f'v2_final_Ridge_{self.crypto}{suffix}.backup_{timestamp}'
                
                if old_file.exists():
                    import shutil
                    shutil.copy2(old_file, backup_file)
            
            logger.info(f"✓ Old model backed up with timestamp: {timestamp}")
            
            # Save new model artifacts
            model_file = self.model_dir / f'v2_final_Ridge_{self.crypto}.pkl'
            with open(model_file, 'wb') as f:
                pickle.dump(self.model_new, f)
            
            scaler_X_file = self.model_dir / f'v2_final_scaler_X_{self.crypto}.pkl'
            with open(scaler_X_file, 'wb') as f:
                pickle.dump(self.scaler_X, f)
            
            scaler_y_file = self.model_dir / f'v2_final_scaler_y_{self.crypto}.pkl'
            with open(scaler_y_file, 'wb') as f:
                pickle.dump(self.scaler_y, f)
            
            metadata_file = self.model_dir / f'v2_final_Ridge_{self.crypto}_metadata.json'
            with open(metadata_file, 'w') as f:
                json.dump(self.metrics_new, f, indent=2)
            
            logger.info(f"✓ New model saved successfully")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to backup/replace model: {e}")
            return False
    
    def retrain_and_validate(self) -> bool:
        """
        Execute full retraining pipeline.
        
        Returns:
            True if retraining successful and model replaced, False otherwise
        """
        logger.info("\n" + "=" * 80)
        logger.info("MODEL V2 RETRAINING PIPELINE")
        logger.info("=" * 80)
        
        # Step 1: Fetch latest data
        if not self.fetch_latest_data():
            logger.error("Failed to fetch data")
            return False
        
        # Step 2: Prepare train/test
        if not self.prepare_train_test_split():
            logger.error("Failed to prepare split")
            return False
        
        # Step 3: Train new model
        if not self.train_new_model():
            logger.error("Failed to train model")
            return False
        
        # Step 4: Load old metrics
        if not self.load_old_model_metrics():
            logger.warning("Could not load old model metrics")
        
        # Step 5: Compare and decide
        if self.metrics_old and not self.compare_and_decide():
            logger.warning("New model does not meet quality criteria - keeping old model")
            return False
        
        # Step 6: Backup and replace
        if not self.backup_and_replace_model():
            logger.error("Failed to backup/replace model")
            return False
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ Retraining pipeline complete! Model updated successfully.")
        logger.info("=" * 80 + "\n")
        
        return True


def main():
    """Main entry point for retraining scheduler."""
    scheduler = ModelRetrainingScheduler(
        data_dir='data/model_data',
        model_dir='models',
        crypto='bitcoin'
    )
    
    success = scheduler.retrain_and_validate()
    return 0 if success else 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
