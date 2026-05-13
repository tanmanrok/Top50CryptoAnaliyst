"""
Phase 2.5 - Phase B: Model Training for Model v2
Test 4 models (Linear, Ridge, Lasso, RandomForest) with GridSearchCV
to find best performer for Bitcoin next-day price prediction.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import logging
import pickle
import warnings
from typing import Dict, Tuple, List
from datetime import datetime

# Add parent Code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelTrainerV2:
    """
    Train and evaluate 4 models for Bitcoin next-day price prediction.
    
    Models tested:
    1. Linear Regression - baseline linear model
    2. Ridge Regression - L2 regularization (prevents overfitting)
    3. Lasso Regression - L1 regularization (feature selection)
    4. RandomForest - ensemble non-linear model
    
    Uses GridSearchCV for hyperparameter tuning on each model.
    """
    
    def __init__(self, data_dir: str = 'data/model_data', cryptocurrency: str = 'bitcoin'):
        """
        Initialize model trainer.
        
        Args:
            data_dir: Directory containing train/test CSV files
            cryptocurrency: Name for file naming (e.g., 'bitcoin')
        """
        self.data_dir = Path(data_dir)
        self.cryptocurrency = cryptocurrency.lower()
        self.engine = None
        
        # Data containers
        self.X_train = None
        self.y_train = None
        self.X_test = None
        self.y_test = None
        
        # Scalers
        self.scaler_X = StandardScaler()
        self.scaler_y = StandardScaler()
        
        # Models
        self.models = {}
        self.best_model = None
        self.best_model_name = None
        self.results = {}
        
        logger.info(f"ModelTrainerV2 initialized for {self.cryptocurrency}")
    
    def load_data(self) -> None:
        """Load train/test data from CSV files created in Phase A."""
        logger.info("Loading training and test data...")
        
        train_file = self.data_dir / f'{self.cryptocurrency}_train_v2.csv'
        test_file = self.data_dir / f'{self.cryptocurrency}_test_v2.csv'
        
        if not train_file.exists() or not test_file.exists():
            raise FileNotFoundError(f"Missing data files in {self.data_dir}")
        
        # Load data
        df_train = pd.read_csv(train_file)
        df_test = pd.read_csv(test_file)
        
        logger.info(f"✓ Loaded {len(df_train)} training samples")
        logger.info(f"✓ Loaded {len(df_test)} test samples")
        
        # Extract features and targets
        # Exclude: timestamp, close, target, trend_up
        exclude_cols = {'timestamp', 'close', 'target', 'trend_up'}
        feature_cols = [col for col in df_train.columns if col not in exclude_cols]
        
        # Training data
        self.X_train = df_train[feature_cols].copy()
        self.y_train = df_train['target'].copy()
        
        # Test data
        self.X_test = df_test[feature_cols].copy()
        self.y_test = df_test['target'].copy()
        
        logger.info(f"✓ Feature set: {len(feature_cols)} indicators")
        logger.info(f"  Columns: {', '.join(feature_cols[:5])}...")
    
    def scale_data(self) -> None:
        """
        Scale features and targets using StandardScaler.
        
        StandardScaler: zero mean, unit variance
        Important: Fit on training data only, then transform test data
        """
        logger.info("Scaling data...")
        
        # Scale features
        self.X_train = self.scaler_X.fit_transform(self.X_train)
        self.X_test = self.scaler_X.transform(self.X_test)
        
        # Scale targets (important for regression)
        self.y_train = self.scaler_y.fit_transform(self.y_train.values.reshape(-1, 1)).ravel()
        self.y_test = self.scaler_y.transform(self.y_test.values.reshape(-1, 1)).ravel()
        
        logger.info("✓ Data scaled (StandardScaler)")
        logger.info(f"  X_train mean: {self.X_train.mean():.4f}, std: {self.X_train.std():.4f}")
        logger.info(f"  y_train mean: {self.y_train.mean():.4f}, std: {self.y_train.std():.4f}")
    
    def train_linear_regression(self) -> Dict:
        """Train Linear Regression model."""
        logger.info("\n[MODEL 1] Linear Regression")
        logger.info("  No hyperparameters to tune - fitting directly...")
        
        model = LinearRegression()
        model.fit(self.X_train, self.y_train)
        
        y_pred_train = model.predict(self.X_train)
        y_pred_test = model.predict(self.X_test)
        
        results = self._evaluate_model(y_pred_train, y_pred_test, 'Linear Regression')
        self.models['Linear'] = model
        
        return results
    
    def train_ridge_regression(self) -> Dict:
        """Train Ridge Regression with GridSearchCV for alpha tuning."""
        logger.info("\n[MODEL 2] Ridge Regression")
        logger.info("  Tuning alpha parameter...")
        
        param_grid = {
            'alpha': [0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 1000.0]
        }
        
        ridge = Ridge()
        grid_search = GridSearchCV(
            ridge,
            param_grid,
            cv=5,
            scoring='r2',
            n_jobs=-1,
            verbose=0
        )
        grid_search.fit(self.X_train, self.y_train)
        
        logger.info(f"  Best alpha: {grid_search.best_params_['alpha']}")
        logger.info(f"  CV R² score: {grid_search.best_score_:.4f}")
        
        model = grid_search.best_estimator_
        y_pred_train = model.predict(self.X_train)
        y_pred_test = model.predict(self.X_test)
        
        results = self._evaluate_model(y_pred_train, y_pred_test, 'Ridge')
        self.models['Ridge'] = model
        
        return results
    
    def train_lasso_regression(self) -> Dict:
        """Train Lasso Regression with GridSearchCV for alpha tuning."""
        logger.info("\n[MODEL 3] Lasso Regression")
        logger.info("  Tuning alpha parameter...")
        
        param_grid = {
            'alpha': [0.0001, 0.001, 0.01, 0.1, 1.0, 10.0]
        }
        
        lasso = Lasso(max_iter=10000)
        grid_search = GridSearchCV(
            lasso,
            param_grid,
            cv=5,
            scoring='r2',
            n_jobs=-1,
            verbose=0
        )
        grid_search.fit(self.X_train, self.y_train)
        
        logger.info(f"  Best alpha: {grid_search.best_params_['alpha']}")
        logger.info(f"  CV R² score: {grid_search.best_score_:.4f}")
        
        model = grid_search.best_estimator_
        y_pred_train = model.predict(self.X_train)
        y_pred_test = model.predict(self.X_test)
        
        results = self._evaluate_model(y_pred_train, y_pred_test, 'Lasso')
        self.models['Lasso'] = model
        
        return results
    
    def train_random_forest(self) -> Dict:
        """Train RandomForest with GridSearchCV for hyperparameter tuning."""
        logger.info("\n[MODEL 4] Random Forest")
        logger.info("  Tuning hyperparameters...")
        
        param_grid = {
            'n_estimators': [50, 100, 200],
            'max_depth': [10, 15, 20],
            'min_samples_split': [5, 10],
            'min_samples_leaf': [2, 4]
        }
        
        rf = RandomForestRegressor(random_state=42, n_jobs=-1)
        grid_search = GridSearchCV(
            rf,
            param_grid,
            cv=5,
            scoring='r2',
            n_jobs=-1,
            verbose=0
        )
        grid_search.fit(self.X_train, self.y_train)
        
        logger.info(f"  Best params: n_est={grid_search.best_params_['n_estimators']}, "
                   f"depth={grid_search.best_params_['max_depth']}")
        logger.info(f"  CV R² score: {grid_search.best_score_:.4f}")
        
        model = grid_search.best_estimator_
        y_pred_train = model.predict(self.X_train)
        y_pred_test = model.predict(self.X_test)
        
        results = self._evaluate_model(y_pred_train, y_pred_test, 'RandomForest')
        self.models['RandomForest'] = model
        
        return results
    
    def _evaluate_model(self, y_pred_train: np.ndarray, y_pred_test: np.ndarray, 
                       model_name: str) -> Dict:
        """
        Evaluate model on train and test sets.
        
        Args:
            y_pred_train: Predictions on training set (scaled)
            y_pred_test: Predictions on test set (scaled)
            model_name: Name of model for logging
        
        Returns:
            Dictionary with all metrics
        """
        # Calculate metrics on scaled data
        r2_train = r2_score(self.y_train, y_pred_train)
        r2_test = r2_score(self.y_test, y_pred_test)
        
        mse_train = mean_squared_error(self.y_train, y_pred_train)
        mse_test = mean_squared_error(self.y_test, y_pred_test)
        
        mae_train = mean_absolute_error(self.y_train, y_pred_train)
        mae_test = mean_absolute_error(self.y_test, y_pred_test)
        
        # Also calculate RMSE and MAPE
        rmse_train = np.sqrt(mse_train)
        rmse_test = np.sqrt(mse_test)
        
        # MAPE on unscaled predictions
        y_pred_test_unscaled = self.scaler_y.inverse_transform(y_pred_test.reshape(-1, 1)).ravel()
        y_test_unscaled = self.scaler_y.inverse_transform(self.y_test.reshape(-1, 1)).ravel()
        mape_test = np.mean(np.abs((y_test_unscaled - y_pred_test_unscaled) / y_test_unscaled)) * 100
        
        results = {
            'model_name': model_name,
            'r2_train': r2_train,
            'r2_test': r2_test,
            'rmse_train': rmse_train,
            'rmse_test': rmse_test,
            'mae_train': mae_train,
            'mae_test': mae_test,
            'mape_test': mape_test,
            'y_pred_test_unscaled': y_pred_test_unscaled,
            'y_test_unscaled': y_test_unscaled
        }
        
        logger.info(f"  Train R²: {r2_train:.4f} | Test R²: {r2_test:.4f}")
        logger.info(f"  Train RMSE: {rmse_train:.4f} | Test RMSE: {rmse_test:.4f}")
        logger.info(f"  Test MAE: {mae_test:.4f}")
        logger.info(f"  Test MAPE: {mape_test:.2f}%")
        
        return results
    
    def train_all_models(self) -> None:
        """Train all 4 models and store results."""
        logger.info("=" * 60)
        logger.info("TRAINING 4 MODELS")
        logger.info("=" * 60)
        
        self.results['Linear'] = self.train_linear_regression()
        self.results['Ridge'] = self.train_ridge_regression()
        self.results['Lasso'] = self.train_lasso_regression()
        self.results['RandomForest'] = self.train_random_forest()
    
    def select_best_model(self) -> Tuple[str, Dict]:
        """
        Select best model based on test R² score.
        
        Returns:
            Tuple of (model_name, results_dict)
        """
        logger.info("\n" + "=" * 60)
        logger.info("MODEL COMPARISON")
        logger.info("=" * 60)
        
        # Create comparison table
        comparison = []
        for model_name, results in self.results.items():
            comparison.append({
                'Model': model_name,
                'Train R²': f"{results['r2_train']:.4f}",
                'Test R²': f"{results['r2_test']:.4f}",
                'RMSE': f"{results['rmse_test']:.4f}",
                'MAE': f"{results['mae_test']:.4f}",
                'MAPE': f"{results['mape_test']:.2f}%"
            })
        
        comparison_df = pd.DataFrame(comparison)
        logger.info("\n" + comparison_df.to_string(index=False))
        
        # Select best by test R²
        best_model_name = max(self.results, key=lambda x: self.results[x]['r2_test'])
        best_results = self.results[best_model_name]
        
        self.best_model_name = best_model_name
        self.best_model = self.models[best_model_name]
        
        logger.info("\n" + "=" * 60)
        logger.info(f"✅ BEST MODEL: {best_model_name}")
        logger.info(f"   Test R²: {best_results['r2_test']:.4f}")
        logger.info(f"   Test MAPE: {best_results['mape_test']:.2f}%")
        logger.info("=" * 60)
        
        return best_model_name, best_results
    
    def save_best_model(self, output_dir: str = 'models') -> Path:
        """
        Save best model and metadata to disk.
        
        Args:
            output_dir: Directory to save model
        
        Returns:
            Path to saved model
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        model_file = output_path / f'v2_{self.best_model_name}_{self.cryptocurrency}.pkl'
        
        # Save model
        with open(model_file, 'wb') as f:
            pickle.dump(self.best_model, f)
        
        # Save scalers
        scaler_X_file = output_path / f'v2_scaler_X_{self.cryptocurrency}.pkl'
        scaler_y_file = output_path / f'v2_scaler_y_{self.cryptocurrency}.pkl'
        
        with open(scaler_X_file, 'wb') as f:
            pickle.dump(self.scaler_X, f)
        
        with open(scaler_y_file, 'wb') as f:
            pickle.dump(self.scaler_y, f)
        
        # Save metadata
        metadata = {
            'model_type': self.best_model_name,
            'cryptocurrency': self.cryptocurrency,
            'created_at': datetime.now().isoformat(),
            'performance': {
                'test_r2': float(self.results[self.best_model_name]['r2_test']),
                'test_rmse': float(self.results[self.best_model_name]['rmse_test']),
                'test_mape': float(self.results[self.best_model_name]['mape_test'])
            }
        }
        
        metadata_file = output_path / f'v2_{self.best_model_name}_{self.cryptocurrency}_metadata.txt'
        with open(metadata_file, 'w') as f:
            for key, value in metadata.items():
                f.write(f"{key}: {value}\n")
        
        logger.info(f"\n✓ Model saved: {model_file}")
        logger.info(f"✓ Scalers saved: {scaler_X_file}, {scaler_y_file}")
        logger.info(f"✓ Metadata saved: {metadata_file}")
        
        return model_file
    
    def train(self) -> Tuple[str, Dict, Path]:
        """
        Execute full training pipeline.
        
        Returns:
            Tuple of (best_model_name, best_results, model_file_path)
        """
        # Load data
        self.load_data()
        
        # Scale data
        self.scale_data()
        
        # Train all models
        self.train_all_models()
        
        # Select best model
        best_model_name, best_results = self.select_best_model()
        
        # Save best model
        model_file = self.save_best_model()
        
        return best_model_name, best_results, model_file


def run_unit_tests():
    """Run unit tests to verify model training."""
    logger.info("\n" + "=" * 60)
    logger.info("RUNNING UNIT TESTS")
    logger.info("=" * 60)
    
    test_results = {}
    
    try:
        # Test 1: Load data
        logger.info("\n[TEST 1] Loading data...")
        trainer = ModelTrainerV2('data/model_data', 'bitcoin')
        trainer.load_data()
        test_results['test_load_data'] = trainer.X_train.shape[0] > 0 and trainer.X_test.shape[0] > 0
        logger.info(f"  ✅ PASS" if test_results['test_load_data'] else f"  ❌ FAIL")
        
        # Test 2: Scale data
        logger.info("\n[TEST 2] Scaling data...")
        trainer.scale_data()
        test_results['test_scale_data'] = (
            abs(trainer.X_train.mean()) < 0.01 and
            abs(trainer.y_train.mean()) < 0.01
        )
        logger.info(f"  ✅ PASS" if test_results['test_scale_data'] else f"  ❌ FAIL")
        
        # Test 3: Train models
        logger.info("\n[TEST 3] Training models...")
        trainer.train_all_models()
        test_results['test_train_models'] = len(trainer.models) == 4
        logger.info(f"  ✅ PASS" if test_results['test_train_models'] else f"  ❌ FAIL")
        
        # Test 4: Model selection
        logger.info("\n[TEST 4] Model selection...")
        best_model, best_results = trainer.select_best_model()
        test_results['test_model_selection'] = best_model is not None and best_results['r2_test'] > 0
        logger.info(f"  ✅ PASS" if test_results['test_model_selection'] else f"  ❌ FAIL")
        
        # Test 5: Save model
        logger.info("\n[TEST 5] Saving model...")
        model_file = trainer.save_best_model()
        test_results['test_save_model'] = model_file is not None
        logger.info(f"  ✅ PASS" if test_results['test_save_model'] else f"  ❌ FAIL")
        
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
        logger.info("EXECUTING FULL MODEL TRAINING")
        logger.info("=" * 60 + "\n")
        
        trainer = ModelTrainerV2('data/model_data', 'bitcoin')
        best_model_name, best_results, model_file = trainer.train()
        
        logger.info("\n✅ Phase B Complete!")
        logger.info(f"Next: Phase C - Time-Series Validation (validate_timeseries_v2.py)")
    else:
        logger.error("\n❌ Unit tests failed. Please fix issues before proceeding.")
        sys.exit(1)
