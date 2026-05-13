"""
Phase 2.5 - Phase C: Time-Series Validation for Model v2
Implement 5-fold walk-forward validation to verify Ridge model robustness
across different time periods and market conditions.

Walk-forward approach simulates real-world deployment where model is trained
on historical data and tested on future data, then retrained as new data arrives.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import logging
import warnings
from typing import Dict, List, Tuple
import pickle

# Add parent Code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TimeSeriesValidatorV2:
    """
    Perform walk-forward validation on Ridge model for Bitcoin next-day prediction.
    
    Walk-Forward Validation:
    - Simulates real deployment: train on past, test on future
    - Retrains model as new data becomes available
    - Detects performance degradation over time
    - More realistic than single 80/20 split
    
    Fold structure for 4256 total records:
    Fold 1: Train [Sep 2014 - Dec 2019] → Test [Jan 2020 - Dec 2020] (365 days)
    Fold 2: Train [Sep 2014 - Dec 2020] → Test [Jan 2021 - Dec 2021] (365 days)
    Fold 3: Train [Sep 2014 - Dec 2022] → Test [Jan 2023 - Dec 2023] (365 days)
    Fold 4: Train [Sep 2014 - Dec 2023] → Test [Jan 2024 - Dec 2024] (365 days)
    Fold 5: Train [Sep 2014 - May 2025] → Test [Jun 2025 - May 2026] (365 days)
    """
    
    def __init__(self, data_dir: str = 'data/model_data', cryptocurrency: str = 'bitcoin'):
        """
        Initialize validator.
        
        Args:
            data_dir: Directory containing train/test CSV files
            cryptocurrency: Name for file naming
        """
        self.data_dir = Path(data_dir)
        self.cryptocurrency = cryptocurrency.lower()
        
        # Data container
        self.df_full = None
        self.feature_cols = None
        
        # Results storage
        self.fold_results = {}
        self.fold_metrics = []
        
        logger.info(f"TimeSeriesValidatorV2 initialized for {self.cryptocurrency}")
    
    def load_full_data(self) -> None:
        """Load and combine train/test data to create continuous time series."""
        logger.info("Loading full data for walk-forward validation...")
        
        train_file = self.data_dir / f'{self.cryptocurrency}_train_v2.csv'
        test_file = self.data_dir / f'{self.cryptocurrency}_test_v2.csv'
        
        if not train_file.exists() or not test_file.exists():
            raise FileNotFoundError(f"Missing data files in {self.data_dir}")
        
        # Load and combine
        df_train = pd.read_csv(train_file)
        df_test = pd.read_csv(test_file)
        
        self.df_full = pd.concat([df_train, df_test], ignore_index=True)
        self.df_full['timestamp'] = pd.to_datetime(self.df_full['timestamp'], format='mixed')
        self.df_full = self.df_full.sort_values('timestamp').reset_index(drop=True)
        
        logger.info(f"✓ Loaded {len(self.df_full)} total records")
        logger.info(f"  Date range: {self.df_full['timestamp'].min()} to {self.df_full['timestamp'].max()}")
        
        # Identify feature columns (exclude metadata)
        exclude_cols = {'timestamp', 'close', 'target', 'trend_up'}
        self.feature_cols = [col for col in self.df_full.columns if col not in exclude_cols]
        
        logger.info(f"  Features: {len(self.feature_cols)} indicators")
    
    def create_walk_forward_folds(self, n_folds: int = 5, 
                                   test_size: int = 365) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """
        Create walk-forward folds.
        
        Args:
            n_folds: Number of folds
            test_size: Size of test set (in days, approximately)
        
        Returns:
            List of (train_df, test_df) tuples for each fold
        """
        logger.info(f"\nCreating {n_folds}-fold walk-forward splits...")
        
        folds = []
        total_len = len(self.df_full)
        
        # Calculate fold boundaries
        fold_size = total_len // (n_folds + 1)
        
        for fold_idx in range(n_folds):
            # Training set: everything up to fold boundary
            train_end_idx = fold_size * (fold_idx + 1)
            
            # Test set: next test_size records
            test_end_idx = min(train_end_idx + test_size, total_len)
            
            if test_end_idx > train_end_idx:
                train_df = self.df_full.iloc[:train_end_idx].copy()
                test_df = self.df_full.iloc[train_end_idx:test_end_idx].copy()
                
                folds.append((train_df, test_df))
                
                train_dates = f"{train_df['timestamp'].min().date()} to {train_df['timestamp'].max().date()}"
                test_dates = f"{test_df['timestamp'].min().date()} to {test_df['timestamp'].max().date()}"
                logger.info(f"  Fold {fold_idx+1}: Train {len(train_df):5d} [{train_dates}]")
                logger.info(f"              Test  {len(test_df):5d} [{test_dates}]")
        
        return folds
    
    def train_and_evaluate_fold(self, fold_idx: int, train_df: pd.DataFrame, 
                                test_df: pd.DataFrame) -> Dict:
        """
        Train Ridge model on fold and evaluate.
        
        Args:
            fold_idx: Fold number (1-indexed for logging)
            train_df: Training data
            test_df: Test data
        
        Returns:
            Dictionary with fold metrics
        """
        logger.info(f"\n[FOLD {fold_idx}] Training Ridge model...")
        
        # Extract features and targets
        X_train = train_df[self.feature_cols].copy()
        y_train = train_df['target'].copy()
        
        X_test = test_df[self.feature_cols].copy()
        y_test = test_df['target'].copy()
        
        # Scale data (fit on train, transform on test)
        scaler_X = StandardScaler()
        scaler_y = StandardScaler()
        
        X_train_scaled = scaler_X.fit_transform(X_train)
        X_test_scaled = scaler_X.transform(X_test)
        
        y_train_scaled = scaler_y.fit_transform(y_train.values.reshape(-1, 1)).ravel()
        y_test_scaled = scaler_y.transform(y_test.values.reshape(-1, 1)).ravel()
        
        # Train Ridge (use same alpha=0.001 as Phase B)
        model = Ridge(alpha=0.001)
        model.fit(X_train_scaled, y_train_scaled)
        
        # Predictions
        y_train_pred = model.predict(X_train_scaled)
        y_test_pred = model.predict(X_test_scaled)
        
        # Metrics on scaled data
        r2_train = r2_score(y_train_scaled, y_train_pred)
        r2_test = r2_score(y_test_scaled, y_test_pred)
        
        rmse_train = np.sqrt(mean_squared_error(y_train_scaled, y_train_pred))
        rmse_test = np.sqrt(mean_squared_error(y_test_scaled, y_test_pred))
        
        mae_test = mean_absolute_error(y_test_scaled, y_test_pred)
        
        # MAPE on unscaled data
        y_test_unscaled = scaler_y.inverse_transform(y_test_scaled.reshape(-1, 1)).ravel()
        y_test_pred_unscaled = scaler_y.inverse_transform(y_test_pred.reshape(-1, 1)).ravel()
        mape_test = np.mean(np.abs((y_test_unscaled - y_test_pred_unscaled) / y_test_unscaled)) * 100
        
        # Directional accuracy (did we predict price movement direction correctly?)
        actual_direction = np.diff(y_test_unscaled) > 0
        pred_direction = np.diff(y_test_pred_unscaled) > 0
        directional_accuracy = np.mean(actual_direction == pred_direction) * 100
        
        results = {
            'fold': fold_idx,
            'train_size': len(train_df),
            'test_size': len(test_df),
            'train_period': f"{train_df['timestamp'].min().date()} to {train_df['timestamp'].max().date()}",
            'test_period': f"{test_df['timestamp'].min().date()} to {test_df['timestamp'].max().date()}",
            'r2_train': r2_train,
            'r2_test': r2_test,
            'rmse_train': rmse_train,
            'rmse_test': rmse_test,
            'mae_test': mae_test,
            'mape_test': mape_test,
            'directional_accuracy': directional_accuracy
        }
        
        logger.info(f"  Train R²: {r2_train:.4f} | Test R²: {r2_test:.4f}")
        logger.info(f"  Test RMSE: {rmse_test:.4f} | MAE: {mae_test:.4f}")
        logger.info(f"  Test MAPE: {mape_test:.2f}% | Direction Accuracy: {directional_accuracy:.1f}%")
        
        return results
    
    def validate_all_folds(self, n_folds: int = 5) -> None:
        """
        Run walk-forward validation across all folds.
        
        Args:
            n_folds: Number of folds
        """
        logger.info("=" * 60)
        logger.info(f"WALK-FORWARD VALIDATION ({n_folds} FOLDS)")
        logger.info("=" * 60)
        
        # Create folds
        folds = self.create_walk_forward_folds(n_folds)
        
        # Train and evaluate each fold
        for fold_idx, (train_df, test_df) in enumerate(folds, 1):
            results = self.train_and_evaluate_fold(fold_idx, train_df, test_df)
            self.fold_results[fold_idx] = results
            self.fold_metrics.append(results)
    
    def print_summary(self) -> None:
        """Print summary of all folds and average metrics."""
        logger.info("\n" + "=" * 80)
        logger.info("WALK-FORWARD VALIDATION SUMMARY")
        logger.info("=" * 80)
        
        # Create summary table
        summary_data = []
        for results in self.fold_metrics:
            summary_data.append({
                'Fold': results['fold'],
                'Train R²': f"{results['r2_train']:.4f}",
                'Test R²': f"{results['r2_test']:.4f}",
                'RMSE': f"{results['rmse_test']:.4f}",
                'MAE': f"{results['mae_test']:.4f}",
                'MAPE': f"{results['mape_test']:.2f}%",
                'Dir Acc': f"{results['directional_accuracy']:.1f}%"
            })
        
        summary_df = pd.DataFrame(summary_data)
        logger.info("\n" + summary_df.to_string(index=False))
        
        # Calculate average metrics
        avg_r2_test = np.mean([r['r2_test'] for r in self.fold_metrics])
        avg_rmse_test = np.mean([r['rmse_test'] for r in self.fold_metrics])
        avg_mae_test = np.mean([r['mae_test'] for r in self.fold_metrics])
        avg_mape_test = np.mean([r['mape_test'] for r in self.fold_metrics])
        avg_dir_acc = np.mean([r['directional_accuracy'] for r in self.fold_metrics])
        
        # Standard deviations (for stability assessment)
        std_r2_test = np.std([r['r2_test'] for r in self.fold_metrics])
        std_mape_test = np.std([r['mape_test'] for r in self.fold_metrics])
        
        logger.info("\n" + "=" * 80)
        logger.info("AVERAGE METRICS ACROSS ALL FOLDS")
        logger.info("=" * 80)
        logger.info(f"  Average Test R²: {avg_r2_test:.4f} ± {std_r2_test:.4f}")
        logger.info(f"  Average RMSE:    {avg_rmse_test:.4f}")
        logger.info(f"  Average MAE:     {avg_mae_test:.4f}")
        logger.info(f"  Average MAPE:    {avg_mape_test:.2f}% ± {std_mape_test:.2f}%")
        logger.info(f"  Average Dir Acc: {avg_dir_acc:.1f}%")
        logger.info("=" * 80)
        
        # Performance stability assessment
        logger.info("\nPERFORMANCE STABILITY ANALYSIS")
        logger.info("-" * 80)
        
        if std_r2_test < 0.01:
            stability = "✅ EXCELLENT - Model performance very consistent"
        elif std_r2_test < 0.02:
            stability = "✅ GOOD - Model performance stable across periods"
        elif std_r2_test < 0.05:
            stability = "⚠️ MODERATE - Some variation in performance"
        else:
            stability = "❌ POOR - Model performance varies significantly"
        
        logger.info(f"  {stability}")
        logger.info(f"  R² std dev: {std_r2_test:.4f}")
        
        # Check for performance degradation
        test_r2_values = [r['r2_test'] for r in self.fold_metrics]
        if test_r2_values[-1] < test_r2_values[0] - 0.05:
            logger.info("  ⚠️ WARNING: Performance degrading over time (later folds have lower R²)")
        else:
            logger.info("  ✅ No significant performance degradation detected")
        
        logger.info("=" * 80)
        
        # Recommendation
        logger.info("\nDEPLOYMENT READINESS")
        logger.info("-" * 80)
        if avg_r2_test > 0.98 and std_r2_test < 0.02:
            logger.info("✅ Model is READY for production deployment")
            logger.info("   - Consistent high accuracy across time periods")
            logger.info("   - Good directional accuracy for trading signals")
            logger.info("   - Recommend proceeding to Phase D & F (training pipeline)")
        elif avg_r2_test > 0.95:
            logger.info("✅ Model is acceptable for production with monitoring")
            logger.info("   - Good performance but monitor for degradation")
        else:
            logger.info("❌ Model needs improvement before production deployment")
        logger.info("=" * 80 + "\n")
    
    def validate(self, n_folds: int = 5) -> Dict:
        """
        Execute full validation pipeline.
        
        Args:
            n_folds: Number of walk-forward folds
        
        Returns:
            Dictionary with validation results
        """
        # Load data
        self.load_full_data()
        
        # Run walk-forward validation
        self.validate_all_folds(n_folds)
        
        # Print summary
        self.print_summary()
        
        return self.fold_metrics


def run_unit_tests():
    """Run unit tests for validator."""
    logger.info("\n" + "=" * 60)
    logger.info("RUNNING UNIT TESTS")
    logger.info("=" * 60)
    
    test_results = {}
    
    try:
        # Test 1: Load full data
        logger.info("\n[TEST 1] Loading full data...")
        validator = TimeSeriesValidatorV2('data/model_data', 'bitcoin')
        validator.load_full_data()
        test_results['test_load_data'] = validator.df_full is not None and len(validator.df_full) > 0
        logger.info(f"  {'✅ PASS' if test_results['test_load_data'] else '❌ FAIL'}")
        
        # Test 2: Create walk-forward folds
        logger.info("\n[TEST 2] Creating walk-forward folds...")
        folds = validator.create_walk_forward_folds(n_folds=5, test_size=365)
        test_results['test_create_folds'] = len(folds) == 5
        logger.info(f"  {'✅ PASS' if test_results['test_create_folds'] else '❌ FAIL'}")
        
        # Test 3: Validate fold structure (no temporal overlap)
        logger.info("\n[TEST 3] Validating fold structure...")
        all_valid = True
        for i, (train_df, test_df) in enumerate(folds, 1):
            train_max = train_df['timestamp'].max()
            test_min = test_df['timestamp'].min()
            if test_min <= train_max:
                all_valid = False
                logger.warning(f"  Fold {i}: Temporal overlap detected!")
        test_results['test_fold_structure'] = all_valid
        logger.info(f"  {'✅ PASS' if all_valid else '❌ FAIL'}")
        
        # Test 4: Train single fold
        logger.info("\n[TEST 4] Training single fold...")
        train_df, test_df = folds[0]
        results = validator.train_and_evaluate_fold(1, train_df, test_df)
        test_results['test_train_fold'] = results['r2_test'] > 0
        logger.info(f"  {'✅ PASS' if test_results['test_train_fold'] else '❌ FAIL'}")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
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
        logger.info("\n" + "=" * 60)
        logger.info("EXECUTING FULL WALK-FORWARD VALIDATION")
        logger.info("=" * 60 + "\n")
        
        validator = TimeSeriesValidatorV2('data/model_data', 'bitcoin')
        fold_metrics = validator.validate(n_folds=5)
        
        logger.info("\n✅ Phase C Complete!")
        logger.info(f"Next: Phase D - Training Pipeline (train_all_models_v2.py)")
    else:
        logger.error("\n❌ Unit tests failed. Please fix issues before proceeding.")
        sys.exit(1)
