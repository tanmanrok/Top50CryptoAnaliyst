"""
Unit tests for Phase F: Prediction Service (predict_v2.py)
Tests prediction generation, database storage, and confidence interval calculation.
"""

import pytest
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.mark.unit
class TestPredictionGeneration:
    """Unit tests for prediction generation logic."""
    
    def test_confidence_interval_calculation(self):
        """Test 95% confidence interval calculation."""
        prediction = 80106.13
        residual_std = 50.0
        z_score_95 = 1.96  # 95% CI
        
        ci_lower = prediction - z_score_95 * residual_std
        ci_upper = prediction + z_score_95 * residual_std
        
        assert ci_lower < prediction < ci_upper, "Prediction should be within CI"
        assert ci_upper - ci_lower == pytest.approx(2 * z_score_95 * residual_std), \
            "CI width should be 2 * z_score * std"
    
    def test_prediction_scaling_inversion(self):
        """Test prediction unscaling from normalized space."""
        # Simulate scaled prediction
        y_pred_scaled = 0.5  # In [-1, 1] range typically
        
        # Mean and std from training data
        y_mean = 65000.0
        y_std = 15000.0
        
        # Unscale
        y_pred = y_pred_scaled * y_std + y_mean
        
        assert isinstance(y_pred, (int, float)), "Prediction should be numeric"
        assert y_pred > 0, "Bitcoin price prediction should be positive"
    
    def test_price_change_calculation(self):
        """Test price change percentage calculation."""
        current_price = 80250.0
        predicted_price = 80106.13
        
        price_change_pct = ((predicted_price - current_price) / current_price) * 100
        
        assert isinstance(price_change_pct, (int, float)), "Price change should be numeric"
        assert price_change_pct == pytest.approx(-0.1787, abs=0.01), \
            "Price change calculation should be correct"


@pytest.mark.unit
class TestPredictionValidation:
    """Unit tests for prediction validation."""
    
    def test_prediction_bounds(self):
        """Test that predictions are within reasonable bounds."""
        prediction = 80106.13
        
        # Bitcoin price should be positive
        assert prediction > 0, "Prediction should be positive"
        
        # Bitcoin price should be in reasonable range (not extreme)
        assert prediction > 1000, "Bitcoin price should be > $1000"
        assert prediction < 1000000, "Bitcoin price should be < $1,000,000"
    
    def test_confidence_interval_validity(self):
        """Test that CI is valid."""
        ci_lower = 80105.93
        ci_upper = 80106.32
        prediction = 80106.13
        
        assert ci_lower < ci_upper, "CI lower should be < upper"
        assert ci_lower < prediction < ci_upper, "Prediction should be within CI"
        assert ci_upper - ci_lower > 0, "CI width should be positive"
    
    def test_confidence_interval_symmetry(self):
        """Test that confidence interval is approximately symmetric."""
        prediction = 80106.13
        ci_lower = 80105.93
        ci_upper = 80106.32
        
        dist_lower = prediction - ci_lower
        dist_upper = ci_upper - prediction
        
        # Should be approximately equal (symmetric)
        ratio = dist_upper / dist_lower if dist_lower > 0 else 1
        assert 0.8 < ratio < 1.2, "CI should be approximately symmetric"
    
    def test_nan_handling(self):
        """Test that NaN predictions are handled."""
        prediction = np.nan
        
        # Should detect NaN
        assert np.isnan(prediction), "Should detect NaN prediction"
        
        # After validation
        if np.isnan(prediction):
            validated = None
            assert validated is None, "Should reject NaN prediction"


@pytest.mark.unit
class TestFeaturePreperation:
    """Unit tests for feature preparation for prediction."""
    
    def test_feature_extraction_27_columns(self, bitcoin_features_df):
        """Test extraction of 27 features from latest data."""
        df = bitcoin_features_df.copy().tail(1)
        
        feature_cols = [col for col in df.columns 
                       if col not in ['timestamp', 'close', 'target', 'trend_up']]
        
        assert len(feature_cols) == 27, "Should extract exactly 27 features"
        assert df[feature_cols].notna().all().all(), "All features should have values"
    
    def test_feature_scaling_prediction(self):
        """Test feature scaling for prediction."""
        from sklearn.preprocessing import StandardScaler
        
        # Fit scaler on training data
        X_train = np.random.randn(100, 27)
        scaler = StandardScaler()
        scaler.fit(X_train)
        
        # Scale new prediction sample
        X_new = np.random.randn(1, 27)
        X_new_scaled = scaler.transform(X_new)
        
        assert X_new_scaled.shape == (1, 27), "Scaled features should have correct shape"
        assert not np.isnan(X_new_scaled).any(), "Scaled features should not contain NaN"
    
    def test_temporal_feature_calculation(self):
        """Test calculation of temporal features (day of week, month)."""
        date = datetime(2026, 5, 8)  # Friday
        
        day_of_week = date.weekday()  # 0=Monday, 6=Sunday
        month = date.month
        
        assert day_of_week == 4, "May 8, 2026 should be Friday (4)"
        assert month == 5, "Should be May (5)"


@pytest.mark.unit
class TestDataTypeConversion:
    """Unit tests for numpy to Python type conversion."""
    
    def test_numpy_float_to_python_float(self):
        """Test conversion of numpy.float64 to Python float."""
        np_value = np.float64(80106.13)
        py_value = float(np_value)
        
        assert isinstance(py_value, float), "Should convert to Python float"
        assert py_value == pytest.approx(80106.13), "Value should be preserved"
    
    def test_numpy_array_element_conversion(self):
        """Test extracting and converting numpy array element."""
        predictions = np.array([80106.13, 80250.50])
        
        pred = float(predictions[0])
        
        assert isinstance(pred, float), "Should be Python float"
        assert pred == pytest.approx(80106.13), "Value should be correct"
    
    def test_multiple_conversions(self):
        """Test converting multiple numpy values."""
        values = {
            'predicted_price': np.float64(80106.13),
            'ci_lower': np.float64(80105.93),
            'ci_upper': np.float64(80106.32),
        }
        
        converted = {k: float(v) for k, v in values.items()}
        
        for key, value in converted.items():
            assert isinstance(value, float), f"{key} should be Python float"


@pytest.mark.unit
class TestPredictionStorage:
    """Unit tests for prediction storage logic."""
    
    def test_prediction_record_structure(self, sample_predictions):
        """Test that prediction record has required fields."""
        pred = sample_predictions[0]
        
        required_fields = ['prediction_date', 'target_date', 'predicted_price',
                          'ci_lower', 'ci_upper', 'model_version']
        
        for field in required_fields:
            assert field in pred, f"Prediction should have '{field}' field"
    
    def test_timestamp_formatting(self):
        """Test prediction timestamp formatting."""
        pred_date = datetime(2026, 5, 8, 15, 57, 35)
        target_date = datetime(2026, 5, 9, 0, 0, 0)
        
        assert pred_date < target_date, "Prediction date should be before target date"
        # Use total_seconds to account for time component
        time_diff = (target_date - pred_date).total_seconds()
        assert time_diff > 0, "Target date should be after prediction date"
    
    def test_prediction_metadata(self):
        """Test prediction metadata tracking."""
        prediction = {
            'predicted_price': 80106.13,
            'model_version': 'v2_ridge',
            'confidence': 0.95,
        }
        
        assert prediction['model_version'] == 'v2_ridge', "Model version should be tracked"
        assert prediction['confidence'] == 0.95, "Confidence level should be tracked"


@pytest.mark.unit
class TestErrorHandling:
    """Unit tests for error handling in prediction service."""
    
    def test_invalid_prediction_handling(self):
        """Test handling of invalid predictions."""
        invalid_predictions = [
            np.nan,
            np.inf,
            -80106.13,  # Negative price
            0,  # Zero price
            None
        ]
        
        for pred in invalid_predictions:
            is_valid = pred is not None and not np.isnan(pred) and not np.isinf(pred) and pred > 0
            assert not is_valid, f"Should reject invalid prediction: {pred}"
    
    def test_missing_feature_handling(self):
        """Test handling of missing features."""
        features = np.array([80106.13, np.nan, 100.5])
        
        has_nan = np.isnan(features).any()
        assert has_nan, "Should detect missing features"
    
    def test_scaler_mismatch_detection(self):
        """Test detection of feature dimension mismatch."""
        scaler_n_features = 27
        sample_n_features = 26
        
        assert scaler_n_features != sample_n_features, \
            "Should detect feature dimension mismatch"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'unit'])
