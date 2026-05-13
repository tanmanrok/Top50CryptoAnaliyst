"""
Pytest configuration and shared fixtures for all tests.
"""

import pytest
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import tempfile
import shutil

# Add parent Code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / 'fixtures'


@pytest.fixture
def bitcoin_features_df():
    """
    Generate synthetic Bitcoin features DataFrame for testing.
    Mimics the structure from the database computed_features table.
    """
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': np.random.uniform(60000, 70000, 100),
        'high': np.random.uniform(61000, 71000, 100),
        'low': np.random.uniform(59000, 69000, 100),
        'close': np.random.uniform(60000, 70000, 100),
        'volume': np.random.uniform(1e9, 5e9, 100),
        'sma_5': np.random.uniform(60000, 70000, 100),
        'sma_10': np.random.uniform(60000, 70000, 100),
        'sma_20': np.random.uniform(60000, 70000, 100),
        'sma_50': np.random.uniform(60000, 70000, 100),
        'ema_12': np.random.uniform(60000, 70000, 100),
        'ema_26': np.random.uniform(60000, 70000, 100),
        'macd': np.random.uniform(-100, 100, 100),
        'macd_signal': np.random.uniform(-100, 100, 100),
        'macd_diff': np.random.uniform(-50, 50, 100),
        'rsi_14': np.random.uniform(30, 70, 100),
        'bb_upper_20': np.random.uniform(61000, 71000, 100),
        'bb_middle_20': np.random.uniform(60000, 70000, 100),
        'bb_lower_20': np.random.uniform(59000, 69000, 100),
        'roc_12': np.random.uniform(-5, 5, 100),
        'momentum_10': np.random.uniform(-1000, 1000, 100),
        'atr_14': np.random.uniform(100, 500, 100),
        'daily_return': np.random.uniform(-0.05, 0.05, 100),
        'weekly_return': np.random.uniform(-0.1, 0.1, 100),
        'monthly_return': np.random.uniform(-0.2, 0.2, 100),
        'volatility_7': np.random.uniform(0.01, 0.05, 100),
        'volatility_30': np.random.uniform(0.02, 0.06, 100),
        'day_of_week': np.random.randint(0, 7, 100),
        'month': np.random.randint(1, 13, 100),
    })
    
    return df


@pytest.fixture
def train_test_split_data():
    """
    Generate train/test split datasets for testing model training.
    Returns: (X_train, X_test, y_train, y_test)
    """
    np.random.seed(42)
    n_train, n_test, n_features = 80, 20, 27
    
    X_train = np.random.randn(n_train, n_features)
    X_test = np.random.randn(n_test, n_features)
    y_train = np.random.randn(n_train)
    y_test = np.random.randn(n_test)
    
    return X_train, X_test, y_train, y_test


@pytest.fixture
def mock_database_engine():
    """
    Create a mock SQLAlchemy engine for testing database operations.
    """
    mock_engine = MagicMock()
    return mock_engine


@pytest.fixture
def temp_model_dir():
    """
    Create temporary directory for test model artifacts.
    Cleaned up after test completes.
    """
    temp_dir = tempfile.mkdtemp(prefix='test_models_')
    yield Path(temp_dir)
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_data_dir():
    """
    Create temporary directory for test data files.
    Cleaned up after test completes.
    """
    temp_dir = tempfile.mkdtemp(prefix='test_data_')
    yield Path(temp_dir)
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_predictions():
    """
    Generate sample prediction records for testing prediction service.
    """
    return [
        {
            'prediction_date': datetime(2026, 5, 8),
            'target_date': datetime(2026, 5, 9),
            'predicted_price': 80106.13,
            'ci_lower': 80105.93,
            'ci_upper': 80106.32,
            'model_version': 'v2_ridge',
        },
        {
            'prediction_date': datetime(2026, 5, 9),
            'target_date': datetime(2026, 5, 10),
            'predicted_price': 80250.50,
            'ci_lower': 80250.10,
            'ci_upper': 80250.90,
            'model_version': 'v2_ridge',
        }
    ]


@pytest.fixture
def mock_prediction_service():
    """
    Create a mock PredictionServiceV2 for testing without database.
    """
    mock_service = MagicMock()
    mock_service.prediction = {
        'predicted_price': 80106.13,
        'predicted_timestamp': datetime(2026, 5, 9),
        'ci_lower': 80105.93,
        'ci_upper': 80106.32,
    }
    return mock_service


@pytest.fixture
def mock_model_artifacts(temp_model_dir):
    """
    Create mock model artifacts (scalers, model) for testing.
    """
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import Ridge
    import pickle
    
    np.random.seed(42)
    
    # Create mock scalers
    scaler_X = StandardScaler()
    scaler_X.fit(np.random.randn(100, 27))
    
    scaler_y = StandardScaler()
    scaler_y.fit(np.random.randn(100, 1))
    
    # Create mock model
    model = Ridge(alpha=0.001)
    X_mock = np.random.randn(100, 27)
    y_mock = np.random.randn(100)
    model.fit(X_mock, y_mock)
    
    # Save artifacts
    with open(temp_model_dir / 'model.pkl', 'wb') as f:
        pickle.dump(model, f)
    
    with open(temp_model_dir / 'scaler_X.pkl', 'wb') as f:
        pickle.dump(scaler_X, f)
    
    with open(temp_model_dir / 'scaler_y.pkl', 'wb') as f:
        pickle.dump(scaler_y, f)
    
    return {
        'model': model,
        'scaler_X': scaler_X,
        'scaler_y': scaler_y,
        'directory': temp_model_dir
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: unit tests for individual components"
    )
    config.addinivalue_line(
        "markers", "integration: integration tests for full pipeline"
    )
    config.addinivalue_line(
        "markers", "performance: performance benchmarking tests"
    )
    config.addinivalue_line(
        "markers", "database: tests requiring database connectivity"
    )
    config.addinivalue_line(
        "markers", "slow: tests that take significant time"
    )
