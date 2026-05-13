"""
Phase 2.5 - Phase A: Data Preparation for Model v2
Loads Bitcoin features from database, implements target shifting (Features[t] → Close[t+1]),
creates temporal train/test split with no data leakage verification.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Tuple, Dict, List
import logging

# Add parent Code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.db_connection import engine
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataPreparerV2:
    """
    Prepare Bitcoin data for Model v2 (next-day prediction)
    
    Model v2 Approach:
    - Features from Day N (OHLCV + technical indicators)
    - Target: Close price on Day N+1
    - No data leakage (proper temporal validation)
    
    This prevents the data leakage issue from v1 where same-day indicators
    predicted same-day prices (unrealistic for live trading).
    """
    
    def __init__(self, cryptocurrency: str = 'bitcoin', lookback_days: int = 500):
        """
        Initialize data preparer.
        
        Args:
            cryptocurrency: Name of crypto in database (e.g., 'bitcoin')
            lookback_days: Maximum days to load (for memory efficiency)
        """
        self.cryptocurrency = cryptocurrency.lower()
        self.lookback_days = lookback_days
        self.engine = engine
        self.df = None
        self.df_train = None
        self.df_test = None
        
        logger.info(f"DataPreparerV2 initialized for {self.cryptocurrency}")
    
    def load_data(self) -> pd.DataFrame:
        """
        Load Bitcoin price and feature data from computed_features table.
        
        Returns:
            DataFrame with all features sorted by timestamp
        """
        logger.info(f"Loading data for {self.cryptocurrency}...")
        
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
            day_of_week, month, trend_up
        FROM computed_features
        WHERE cryptocurrency = :crypto
        ORDER BY timestamp ASC
        """
        
        try:
            with self.engine.begin() as conn:
                self.df = pd.read_sql(text(query), conn, params={'crypto': self.cryptocurrency})
            
            if self.df.empty:
                raise ValueError(f"No data found for {self.cryptocurrency}")
            
            # Convert timestamp to datetime if needed
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
            
            logger.info(f"✓ Loaded {len(self.df)} records for {self.cryptocurrency}")
            logger.info(f"  Date range: {self.df['timestamp'].min()} to {self.df['timestamp'].max()}")
            
            return self.df
        
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            raise
    
    def create_target_variable(self) -> pd.DataFrame:
        """
        Implement target shifting: next day's close becomes the target.
        
        Steps:
        1. Sort by timestamp (ascending)
        2. Shift close price backward by 1 row (next day's close)
        3. Drop last row (no forward-looking target)
        4. Drop rows with NaN targets
        
        Returns:
            DataFrame with 'target' column (next day's close)
        
        No Data Leakage: Features[t] uses only data up to Day N, predicts Close[N+1]
        """
        if self.df is None:
            raise ValueError("Call load_data() first")
        
        logger.info("Creating target variable (next day's close)...")
        
        # Ensure sorted by timestamp
        self.df = self.df.sort_values('timestamp').reset_index(drop=True)
        
        # Shift close backward to get next day's close
        # shift(-1) moves row up, so row[i] gets row[i+1]'s value
        self.df['target'] = self.df['close'].shift(-1)
        
        # Drop last row (no next day to predict)
        self.df = self.df.iloc[:-1].copy()
        
        # Drop any NaN targets (shouldn't happen after shift, but be safe)
        initial_rows = len(self.df)
        self.df = self.df.dropna(subset=['target'])
        dropped = initial_rows - len(self.df)
        
        logger.info(f"✓ Target variable created ({len(self.df)} rows, dropped {dropped} NaN)")
        logger.info(f"  Target range: {self.df['target'].min():.2f} to {self.df['target'].max():.2f}")
        
        return self.df
    
    def create_temporal_split(self, train_ratio: float = 0.8) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Create temporal train/test split (NO random shuffle).
        
        Args:
            train_ratio: Fraction for training (default 0.8 = 80/20 split)
        
        Returns:
            Tuple of (train_df, test_df) both sorted by timestamp
        
        Temporal Split Rationale:
        - Training: Earlier 80% of data (past)
        - Testing: Later 20% of data (future)
        - Simulates real-world scenario: train on history, predict future
        - Prevents data leakage from future prices affecting model training
        """
        if self.df is None or 'target' not in self.df.columns:
            raise ValueError("Call create_target_variable() first")
        
        logger.info(f"Creating temporal train/test split ({train_ratio:.0%}/{1-train_ratio:.0%})...")
        
        split_idx = int(len(self.df) * train_ratio)
        
        self.df_train = self.df.iloc[:split_idx].copy()
        self.df_test = self.df.iloc[split_idx:].copy()
        
        logger.info(f"✓ Temporal split created (before NaN removal):")
        logger.info(f"  Training: {len(self.df_train)} rows")
        logger.info(f"  Testing: {len(self.df_test)} rows")
        
        return self.df_train, self.df_test
    
    def drop_nan_rows(self) -> None:
        """
        Drop rows with NaN values in features (indicators need lookback periods).
        
        Technical indicators like SMA_50 need 50 prior candles, so early data is NaN.
        This is normal and expected - we simply start training after all indicators
        are computed.
        """
        if self.df_train is None or self.df_test is None:
            raise ValueError("Call create_temporal_split() first")
        
        logger.info("Dropping rows with NaN values in features...")
        
        # Count rows before
        train_len_before = len(self.df_train)
        test_len_before = len(self.df_test)
        
        # Drop NaN rows
        self.df_train = self.df_train.dropna()
        self.df_test = self.df_test.dropna()
        
        # Calculate dropped counts
        train_dropped = train_len_before - len(self.df_train)
        test_dropped = test_len_before - len(self.df_test)
        
        # Log results
        logger.info(f"✓ NaN rows dropped:")
        logger.info(f"  Training: {train_len_before} rows → {len(self.df_train)} clean rows (dropped {train_dropped})")
        logger.info(f"  Testing: {test_len_before} rows → {len(self.df_test)} clean rows (dropped {test_dropped})")
        logger.info(f"  Training date range: {self.df_train['timestamp'].min()} to {self.df_train['timestamp'].max()}")
    
    def verify_no_data_leakage(self) -> Dict[str, bool]:
        """
        Verify no data leakage between training and test sets.
        
        Checks:
        1. Train/test don't overlap temporally
        2. Test dates are after training dates
        3. No NaN values in features or target
        4. Features and targets are valid numbers
        
        Returns:
            Dictionary with validation results
        """
        if self.df_train is None or self.df_test is None:
            raise ValueError("Call create_temporal_split() first")
        
        logger.info("Verifying no data leakage...")
        
        results = {}
        
        # Check 1: Temporal ordering
        train_max_date = self.df_train['timestamp'].max()
        test_min_date = self.df_test['timestamp'].min()
        results['temporal_ordering'] = test_min_date > train_max_date
        logger.info(f"  ✓ Temporal ordering: {results['temporal_ordering']}")
        logger.info(f"    Train ends: {train_max_date}, Test starts: {test_min_date}")
        
        # Check 2: No overlap
        results['no_overlap'] = len(set(self.df_train['timestamp']) & set(self.df_test['timestamp'])) == 0
        logger.info(f"  ✓ No temporal overlap: {results['no_overlap']}")
        
        # Check 3: NaN values in training set
        train_nans = self.df_train.isna().sum().sum()
        results['train_no_nans'] = train_nans == 0
        logger.info(f"  ✓ Train NaN count: {train_nans} (valid: {results['train_no_nans']})")
        
        # Check 4: NaN values in test set
        test_nans = self.df_test.isna().sum().sum()
        results['test_no_nans'] = test_nans == 0
        logger.info(f"  ✓ Test NaN count: {test_nans} (valid: {results['test_no_nans']})")
        
        # Check 5: Targets are valid (finite) numbers
        results['train_targets_valid'] = np.all(np.isfinite(self.df_train['target']))
        results['test_targets_valid'] = np.all(np.isfinite(self.df_test['target']))
        logger.info(f"  ✓ Train targets valid: {results['train_targets_valid']}")
        logger.info(f"  ✓ Test targets valid: {results['test_targets_valid']}")
        
        # Check 6: Features are valid (finite) numbers
        feature_cols = [col for col in self.df_train.columns 
                       if col not in ['timestamp', 'close', 'target', 'trend_up']]
        train_features_valid = np.all(np.isfinite(self.df_train[feature_cols]))
        test_features_valid = np.all(np.isfinite(self.df_test[feature_cols]))
        results['train_features_valid'] = train_features_valid
        results['test_features_valid'] = test_features_valid
        logger.info(f"  ✓ Train features valid: {train_features_valid}")
        logger.info(f"  ✓ Test features valid: {test_features_valid}")
        
        # Overall result
        results['all_valid'] = all(results.values())
        logger.info(f"\n  Overall: {'✅ PASS' if results['all_valid'] else '❌ FAIL'}")
        
        return results
    
    def prepare(self, train_ratio: float = 0.8) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
        """
        Execute full data preparation pipeline.
        
        Args:
            train_ratio: Fraction for training (default 0.8)
        
        Returns:
            Tuple of (train_df, test_df, validation_results)
        """
        logger.info("=" * 60)
        logger.info("MODEL V2 DATA PREPARATION")
        logger.info("=" * 60)
        
        # Step 1: Load data
        self.load_data()
        
        # Step 2: Create target variable
        self.create_target_variable()
        
        # Step 3: Create train/test split
        self.create_temporal_split(train_ratio)
        
        # Step 4: Drop NaN rows from indicators needing lookback periods
        self.drop_nan_rows()
        
        # Step 5: Verify no leakage
        validation = self.verify_no_data_leakage()
        
        logger.info("=" * 60)
        logger.info(f"✅ Data preparation complete!")
        logger.info(f"  Train set: {len(self.df_train)} samples")
        logger.info(f"  Test set: {len(self.df_test)} samples")
        logger.info(f"  Validation: {'PASS' if validation['all_valid'] else 'FAIL'}")
        logger.info("=" * 60)
        
        return self.df_train, self.df_test, validation
    
    def get_feature_columns(self) -> List[str]:
        """Get list of feature column names (excluding target/metadata)."""
        exclude = {'timestamp', 'close', 'target', 'trend_up'}
        return [col for col in self.df.columns if col not in exclude]
    
    def save_to_csv(self, output_dir: str = 'data/model_data'):
        """
        Save train/test splits to CSV for inspection.
        
        Args:
            output_dir: Directory to save CSV files
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        train_file = output_path / f'{self.cryptocurrency}_train_v2.csv'
        test_file = output_path / f'{self.cryptocurrency}_test_v2.csv'
        
        self.df_train.to_csv(train_file, index=False)
        self.df_test.to_csv(test_file, index=False)
        
        logger.info(f"✓ Saved training data to {train_file}")
        logger.info(f"✓ Saved test data to {test_file}")


def run_unit_tests():
    """Run unit tests to verify data preparation logic."""
    logger.info("\n" + "=" * 60)
    logger.info("RUNNING UNIT TESTS")
    logger.info("=" * 60)
    
    test_results = {}
    
    try:
        # Test 1: Load data
        logger.info("\n[TEST 1] Loading Bitcoin data...")
        preparer = DataPreparerV2('bitcoin')
        df = preparer.load_data()
        test_results['test_load_data'] = len(df) > 0 and 'close' in df.columns
        logger.info(f"  {'✅ PASS' if test_results['test_load_data'] else '❌ FAIL'}")
        
        # Test 2: Target creation
        logger.info("\n[TEST 2] Creating target variable...")
        df_with_target = preparer.create_target_variable()
        has_target = 'target' in df_with_target.columns
        target_matches = len(df_with_target) < len(df)  # Should drop 1 row
        test_results['test_target_creation'] = has_target and target_matches
        logger.info(f"  {'✅ PASS' if test_results['test_target_creation'] else '❌ FAIL'}")
        
        # Test 3: Temporal split
        logger.info("\n[TEST 3] Creating temporal train/test split...")
        train, test = preparer.create_temporal_split(0.8)
        split_correct = len(train) + len(test) == len(df_with_target)
        ratio_correct = len(train) / (len(train) + len(test)) >= 0.79
        test_results['test_temporal_split'] = split_correct and ratio_correct
        logger.info(f"  {'✅ PASS' if test_results['test_temporal_split'] else '❌ FAIL'}")
        
        # Test 3.5: Drop NaN rows
        logger.info("\n[TEST 3.5] Dropping NaN rows from indicators...")
        preparer.drop_nan_rows()
        test_results['test_drop_nans'] = len(preparer.df_train) > 0 and len(preparer.df_test) > 0
        logger.info(f"  {'✅ PASS' if test_results['test_drop_nans'] else '❌ FAIL'}")
        
        # Test 4: No data leakage
        logger.info("\n[TEST 4] Verifying no data leakage...")
        validation = preparer.verify_no_data_leakage()
        test_results['test_no_leakage'] = validation['all_valid']
        logger.info(f"  {'✅ PASS' if test_results['test_no_leakage'] else '❌ FAIL'}")
        
        # Test 5: Feature columns
        logger.info("\n[TEST 5] Checking feature columns...")
        features = preparer.get_feature_columns()
        test_results['test_feature_columns'] = len(features) >= 25  # Should have ~28 indicators
        logger.info(f"  ✓ Found {len(features)} feature columns")
        logger.info(f"  {'✅ PASS' if test_results['test_feature_columns'] else '❌ FAIL'}")
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        test_results['error'] = str(e)
    
    # Summary
    logger.info("\n" + "=" * 60)
    passed = sum(1 for v in test_results.values() if v is True)
    total = len(test_results)
    logger.info(f"TESTS PASSED: {passed}/{total}")
    logger.info("=" * 60 + "\n")
    
    return all(v is True for k, v in test_results.items() if k != 'error')


if __name__ == "__main__":
    # Run unit tests
    all_passed = run_unit_tests()
    
    if all_passed:
        # Run full data preparation
        logger.info("\n" + "=" * 60)
        logger.info("EXECUTING FULL DATA PREPARATION")
        logger.info("=" * 60 + "\n")
        
        preparer = DataPreparerV2('bitcoin')
        train_df, test_df, validation = preparer.prepare(train_ratio=0.8)
        
        # Save to CSV
        preparer.save_to_csv('data/model_data')
        
        logger.info("\n✅ Phase A Complete!")
        logger.info(f"Next: Phase B - Model Training (train_model_v2.py)")
    else:
        logger.error("\n❌ Unit tests failed. Please fix issues before proceeding.")
        sys.exit(1)
