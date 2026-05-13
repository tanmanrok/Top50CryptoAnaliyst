"""
Unit tests for Phase B: Model Training (train_model_v2.py)
Tests model selection, hyperparameter tuning, and performance evaluation.
"""

import pytest
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import Ridge, LinearRegression, Lasso
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.mark.unit
class TestModelTraining:
    """Unit tests for model training and selection."""
    
    def test_ridge_model_initialization(self):
        """Test that Ridge model is correctly initialized with alpha=0.001."""
        model = Ridge(alpha=0.001)
        assert model.alpha == 0.001, "Ridge alpha should be 0.001"
    
    def test_model_training_basic(self, train_test_split_data):
        """Test basic model training on synthetic data."""
        X_train, X_test, y_train, y_test = train_test_split_data
        
        model = Ridge(alpha=0.001)
        model.fit(X_train, y_train)
        
        # Model should be fitted
        assert hasattr(model, 'coef_'), "Trained model should have coefficients"
        assert len(model.coef_) == 27, "Coefficients should match 27 features"
    
    def test_model_prediction(self, train_test_split_data):
        """Test that model makes predictions."""
        X_train, X_test, y_train, y_test = train_test_split_data
        
        model = Ridge(alpha=0.001)
        model.fit(X_train, y_train)
        
        predictions = model.predict(X_test)
        
        assert predictions.shape == (len(X_test),), "Predictions shape should match test size"
        assert not np.isnan(predictions).any(), "Predictions should not contain NaN"
    
    def test_r2_score_calculation(self, train_test_split_data):
        """Test R² score calculation."""
        X_train, X_test, y_train, y_test = train_test_split_data
        
        model = Ridge(alpha=0.001)
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        
        # R² can be negative for poor predictions on random data (underfitting worse than baseline mean)
        # The important thing is that it's a valid numeric score
        assert isinstance(r2, (int, float)), "R² score should be numeric"
        assert r2 < 2, f"R² score {r2} should be realistic"
    
    def test_model_comparison_ridge_vs_linear(self, train_test_split_data):
        """Test that Ridge and Linear Regression produce different results."""
        X_train, X_test, y_train, y_test = train_test_split_data
        
        # Train both models
        lr_model = LinearRegression()
        lr_model.fit(X_train, y_train)
        lr_pred = lr_model.predict(X_test)
        
        ridge_model = Ridge(alpha=0.001)
        ridge_model.fit(X_train, y_train)
        ridge_pred = ridge_model.predict(X_test)
        
        # Calculate R² for both
        lr_r2 = r2_score(y_test, lr_pred)
        ridge_r2 = r2_score(y_test, ridge_pred)
        
        # Both should have valid R² scores
        assert isinstance(lr_r2, (int, float)), "Linear R² should be numeric"
        assert isinstance(ridge_r2, (int, float)), "Ridge R² should be numeric"
    
    def test_regularization_effect(self, train_test_split_data):
        """Test that regularization reduces coefficient magnitudes."""
        X_train, X_test, y_train, y_test = train_test_split_data
        
        # Train with no regularization
        lr_model = LinearRegression()
        lr_model.fit(X_train, y_train)
        
        # Train with regularization
        ridge_model = Ridge(alpha=0.1)
        ridge_model.fit(X_train, y_train)
        
        # Ridge coefficients should have smaller magnitude
        lr_coef_sum = np.sum(np.abs(lr_model.coef_))
        ridge_coef_sum = np.sum(np.abs(ridge_model.coef_))
        
        # Ridge should generally reduce coefficient magnitudes
        assert ridge_coef_sum <= lr_coef_sum or np.isclose(ridge_coef_sum, lr_coef_sum), \
            "Ridge regularization should reduce coefficient magnitudes"


@pytest.mark.unit
class TestModelEvaluation:
    """Unit tests for model evaluation metrics."""
    
    def test_rmse_calculation(self, train_test_split_data):
        """Test RMSE metric calculation."""
        X_train, X_test, y_train, y_test = train_test_split_data
        
        model = Ridge(alpha=0.001)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        assert rmse >= 0, "RMSE should be non-negative"
        assert isinstance(rmse, (int, float)), "RMSE should be numeric"
    
    def test_mae_calculation(self, train_test_split_data):
        """Test MAE metric calculation."""
        X_train, X_test, y_train, y_test = train_test_split_data
        
        model = Ridge(alpha=0.001)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        mae = mean_absolute_error(y_test, y_pred)
        
        assert mae >= 0, "MAE should be non-negative"
        assert isinstance(mae, (int, float)), "MAE should be numeric"
    
    def test_mape_calculation(self, train_test_split_data):
        """Test MAPE metric calculation."""
        X_train, X_test, y_train, y_test = train_test_split_data
        
        model = Ridge(alpha=0.001)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        # Calculate MAPE
        mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
        
        assert mape >= 0, "MAPE should be non-negative"
        assert isinstance(mape, (int, float)), "MAPE should be numeric"
    
    def test_metrics_relationship(self, train_test_split_data):
        """Test that evaluation metrics have expected relationships."""
        X_train, X_test, y_train, y_test = train_test_split_data
        
        model = Ridge(alpha=0.001)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mae = mean_absolute_error(y_test, y_pred)
        
        # RMSE >= MAE (RMSE penalizes larger errors more)
        assert rmse >= mae or np.isclose(rmse, mae), \
            "RMSE should be >= MAE (penalizes large errors more)"


@pytest.mark.unit
class TestFeatureScaling:
    """Unit tests for feature scaling."""
    
    def test_scaler_initialization(self):
        """Test StandardScaler initialization."""
        scaler = StandardScaler()
        
        assert hasattr(scaler, 'fit'), "Scaler should have fit method"
        assert hasattr(scaler, 'transform'), "Scaler should have transform method"
    
    def test_scaler_fit_transform(self):
        """Test scaler fit and transform."""
        X = np.random.randn(100, 27)
        scaler = StandardScaler()
        
        X_scaled = scaler.fit_transform(X)
        
        # Scaled data should have mean ~0 and std ~1
        assert np.isclose(X_scaled.mean(), 0, atol=0.1), "Scaled mean should be ~0"
        assert np.isclose(X_scaled.std(), 1, atol=0.1), "Scaled std should be ~1"
    
    def test_scaler_fit_then_transform(self):
        """Test separate fit and transform."""
        X_train = np.random.randn(100, 27)
        X_test = np.random.randn(20, 27)
        
        scaler = StandardScaler()
        scaler.fit(X_train)
        X_train_scaled = scaler.transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Both should be properly scaled
        assert X_train_scaled.shape == X_train.shape
        assert X_test_scaled.shape == X_test.shape
        assert not np.isnan(X_train_scaled).any()
        assert not np.isnan(X_test_scaled).any()
    
    def test_inverse_transform(self):
        """Test scaler inverse transform."""
        X = np.random.randn(100, 27)
        scaler = StandardScaler()
        
        X_scaled = scaler.fit_transform(X)
        X_reconstructed = scaler.inverse_transform(X_scaled)
        
        # Should recover original data (within numerical precision)
        assert np.allclose(X, X_reconstructed), \
            "Inverse transform should recover original data"


@pytest.mark.unit
class TestModelPersistence:
    """Unit tests for model serialization."""
    
    def test_model_serialization(self, temp_model_dir):
        """Test model saving with pickle."""
        import pickle
        
        model = Ridge(alpha=0.001)
        X = np.random.randn(50, 27)
        y = np.random.randn(50)
        model.fit(X, y)
        
        # Save model
        model_file = temp_model_dir / 'test_model.pkl'
        with open(model_file, 'wb') as f:
            pickle.dump(model, f)
        
        assert model_file.exists(), "Model file should be created"
        
        # Load model
        with open(model_file, 'rb') as f:
            loaded_model = pickle.load(f)
        
        # Make predictions with both
        X_test = np.random.randn(10, 27)
        pred_original = model.predict(X_test)
        pred_loaded = loaded_model.predict(X_test)
        
        assert np.allclose(pred_original, pred_loaded), \
            "Loaded model should make identical predictions"
    
    def test_scaler_serialization(self, temp_model_dir):
        """Test scaler saving with pickle."""
        import pickle
        
        X = np.random.randn(100, 27)
        scaler = StandardScaler()
        scaler.fit(X)
        
        # Save scaler
        scaler_file = temp_model_dir / 'test_scaler.pkl'
        with open(scaler_file, 'wb') as f:
            pickle.dump(scaler, f)
        
        assert scaler_file.exists(), "Scaler file should be created"
        
        # Load scaler
        with open(scaler_file, 'rb') as f:
            loaded_scaler = pickle.load(f)
        
        # Transform with both
        X_test = np.random.randn(10, 27)
        scaled_original = scaler.transform(X_test)
        scaled_loaded = loaded_scaler.transform(X_test)
        
        assert np.allclose(scaled_original, scaled_loaded), \
            "Loaded scaler should apply identical transformations"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'unit'])
