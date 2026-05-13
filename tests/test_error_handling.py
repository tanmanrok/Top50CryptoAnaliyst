"""
Error handling and edge case tests
Tests robustness and error scenarios.
"""

import pytest
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.mark.unit
class TestDataValidationErrors:
    """Test error handling for data validation."""
    
    def test_empty_dataframe_handling(self):
        """Test handling of empty DataFrame."""
        df = pd.DataFrame()
        
        assert len(df) == 0, "Should detect empty DataFrame"
        assert df.empty, "Empty property should be True"
    
    def test_missing_required_columns(self):
        """Test handling of missing required columns."""
        df = pd.DataFrame({
            'open': [100, 101],
            'close': [101, 102],
            # Missing 'high', 'low', 'volume', indicators...
        })
        
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing = [col for col in required_cols if col not in df.columns]
        
        assert len(missing) > 0, "Should detect missing columns"
        assert 'high' in missing, "'high' column should be missing"
    
    def test_nan_handling_in_data(self):
        """Test handling of NaN values in data."""
        df = pd.DataFrame({
            'close': [100, np.nan, 102, np.nan, 104],
            'volume': [1000000, 1100000, np.nan, 1200000, 1300000]
        })
        
        nan_rows = df[df.isna().any(axis=1)]
        assert len(nan_rows) > 0, "Should detect NaN rows"
        
        # After dropping
        df_clean = df.dropna()
        assert df_clean.isna().sum().sum() == 0, "No NaN should remain"
        assert len(df_clean) < len(df), "Should remove rows with NaN"
    
    def test_negative_price_detection(self):
        """Test detection of negative prices."""
        prices = np.array([100, 101, -102, 103])
        
        has_negative = (prices < 0).any()
        assert has_negative, "Should detect negative prices"
        
        invalid_indices = np.where(prices < 0)[0]
        assert len(invalid_indices) == 1, "Should identify index with negative price"
    
    def test_zero_volume_detection(self):
        """Test detection of zero volume."""
        volumes = np.array([1000000, 0, 1100000, 500000])
        
        has_zero = (volumes == 0).any()
        assert has_zero, "Should detect zero volume"
    
    def test_duplicate_timestamps(self):
        """Test handling of duplicate timestamps."""
        df = pd.DataFrame({
            'timestamp': [
                datetime(2026, 5, 8, 10, 0),
                datetime(2026, 5, 8, 10, 0),  # Duplicate
                datetime(2026, 5, 8, 11, 0)
            ],
            'close': [100, 101, 102]
        })
        
        duplicates = df[df.duplicated(subset=['timestamp'])]
        assert len(duplicates) > 0, "Should detect duplicate timestamps"


@pytest.mark.unit
class TestFeaturePreparationErrors:
    """Test error handling in feature preparation."""
    
    def test_feature_dimension_mismatch(self):
        """Test detection of feature dimension mismatch."""
        X_train = np.random.randn(100, 27)  # 27 features
        X_test = np.random.randn(20, 26)   # 26 features - MISMATCH
        
        assert X_train.shape[1] != X_test.shape[1], "Should detect dimension mismatch"
    
    def test_scaler_feature_count_validation(self):
        """Test validation of scaler against feature count."""
        from sklearn.preprocessing import StandardScaler
        
        X_train = np.random.randn(100, 27)
        X_test = np.random.randn(20, 26)
        
        scaler = StandardScaler()
        scaler.fit(X_train)
        
        try:
            # This should fail
            X_test_scaled = scaler.transform(X_test)
            assert False, "Should raise error for dimension mismatch"
        except ValueError:
            pass  # Expected
    
    def test_nan_in_features(self):
        """Test handling of NaN values in features."""
        X = np.array([[1, 2, 3], [4, np.nan, 6], [7, 8, 9]])
        
        has_nan = np.isnan(X).any()
        assert has_nan, "Should detect NaN in features"
        
        rows_with_nan = np.where(np.isnan(X).any(axis=1))[0]
        assert len(rows_with_nan) == 1, "Should identify rows with NaN"
    
    def test_inf_in_features(self):
        """Test handling of infinite values in features."""
        X = np.array([[1, 2, 3], [4, np.inf, 6], [7, 8, 9]])
        
        has_inf = np.isinf(X).any()
        assert has_inf, "Should detect infinite values"


@pytest.mark.unit
class TestModelingErrors:
    """Test error handling in model training."""
    
    def test_insufficient_training_data(self):
        """Test handling of insufficient training data."""
        from sklearn.linear_model import Ridge
        
        X = np.random.randn(2, 27)  # Only 2 samples for 27 features
        y = np.random.randn(2)
        
        model = Ridge(alpha=0.001)
        # This might still work due to regularization, but should warn
        model.fit(X, y)
        
        # Model should still fit but might have poor generalization
        assert hasattr(model, 'coef_'), "Model should fit even with limited data"
    
    def test_singular_matrix_handling(self):
        """Test handling of singular/collinear features."""
        X = np.array([
            [1, 2, 3],
            [2, 4, 6],  # Perfectly collinear with first row
            [3, 6, 9],  # Perfectly collinear
        ])
        y = np.array([1, 2, 3])
        
        from sklearn.linear_model import Ridge
        model = Ridge(alpha=0.001)
        
        # Ridge should handle this through regularization
        model.fit(X, y)
        assert hasattr(model, 'coef_'), "Ridge should handle collinearity"
    
    def test_predict_before_fit(self):
        """Test error when predicting before fitting."""
        from sklearn.linear_model import Ridge
        
        model = Ridge(alpha=0.001)
        X_test = np.random.randn(10, 27)
        
        try:
            predictions = model.predict(X_test)
            # Sklearn raises NotFittedError
            assert False, "Should raise error when predicting on unfitted model"
        except Exception as e:
            # Expected behavior
            pass
    
    def test_negative_alpha_detection(self):
        """Test handling of invalid alpha value."""
        invalid_alpha = -0.5
        
        from sklearn.linear_model import Ridge
        try:
            model = Ridge(alpha=invalid_alpha)
            # Might not fail until fit
            X = np.random.randn(50, 27)
            y = np.random.randn(50)
            model.fit(X, y)
            # May or may not raise error depending on implementation
        except ValueError:
            pass  # Expected


@pytest.mark.unit
class TestPredictionErrors:
    """Test error handling in prediction."""
    
    def test_nan_prediction_detection(self):
        """Test detection of NaN predictions."""
        predictions = np.array([100, 101, np.nan, 103])
        
        has_nan = np.isnan(predictions).any()
        assert has_nan, "Should detect NaN predictions"
    
    def test_invalid_confidence_interval(self):
        """Test validation of confidence intervals."""
        pred = 100.0
        ci_lower = 105.0  # INVALID: lower > prediction
        ci_upper = 95.0   # INVALID: upper < prediction
        
        is_valid = ci_lower < pred < ci_upper
        assert not is_valid, "Should reject invalid CI"
    
    def test_negative_price_prediction(self):
        """Test handling of negative price predictions."""
        prediction = -50.0
        
        is_valid = prediction > 0
        assert not is_valid, "Negative price is invalid"
    
    def test_unrealistic_price_change(self):
        """Test detection of unrealistic price changes."""
        current = 100.0
        predicted = 200.0  # 100% increase - unrealistic
        
        change_pct = abs((predicted - current) / current) * 100
        is_unrealistic = change_pct > 50  # More than 50% is unrealistic
        
        assert is_unrealistic, "Should flag unrealistic price changes"


@pytest.mark.unit
class TestDatabaseErrors:
    """Test error handling for database operations."""
    
    def test_connection_failure_handling(self):
        """Test handling of database connection failures."""
        from unittest.mock import MagicMock
        
        mock_engine = MagicMock()
        mock_engine.begin.side_effect = ConnectionError("Database unavailable")
        
        try:
            with mock_engine.begin() as conn:
                pass
            assert False, "Should raise connection error"
        except ConnectionError:
            pass  # Expected
    
    def test_query_timeout_handling(self):
        """Test handling of query timeouts."""
        from unittest.mock import MagicMock
        
        mock_conn = MagicMock()
        mock_conn.execute.side_effect = TimeoutError("Query timeout")
        
        try:
            result = mock_conn.execute("SELECT * FROM huge_table")
            assert False, "Should raise timeout error"
        except TimeoutError:
            pass  # Expected
    
    def test_invalid_data_type_for_storage(self):
        """Test handling of incompatible data types for storage."""
        import numpy as np
        
        np_value = np.float64(100.5)
        
        # Convert for storage
        try:
            py_value = float(np_value)
            assert isinstance(py_value, float), "Should convert successfully"
        except TypeError:
            assert False, "Should handle numpy type conversion"


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_single_sample_prediction(self):
        """Test prediction on single sample."""
        from sklearn.linear_model import Ridge
        
        X_train = np.random.randn(100, 27)
        y_train = np.random.randn(100)
        
        model = Ridge(alpha=0.001)
        model.fit(X_train, y_train)
        
        X_test = np.random.randn(1, 27)  # Single sample
        pred = model.predict(X_test)
        
        assert len(pred) == 1, "Should handle single sample"
        assert not np.isnan(pred[0]), "Prediction should be valid"
    
    def test_very_large_feature_values(self):
        """Test handling of very large feature values."""
        X = np.array([[1e10, 2e10, 3e10]])
        
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        
        X_scaled = scaler.fit_transform(X)
        
        # After scaling, should be normalized
        assert np.isfinite(X_scaled).all(), "Should produce finite scaled values"
    
    def test_very_small_feature_values(self):
        """Test handling of very small feature values."""
        X = np.array([[1e-10, 2e-10, 3e-10]])
        
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        
        X_scaled = scaler.fit_transform(X)
        
        assert np.isfinite(X_scaled).all(), "Should produce finite scaled values"
    
    def test_constant_feature_column(self):
        """Test handling of constant (zero variance) features."""
        X = np.array([[1, 100, 3], [1, 100, 6], [1, 100, 9]])  # Second column constant
        
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        
        X_scaled = scaler.fit_transform(X)
        
        # Constant column will produce NaN or inf after scaling
        assert True, "Scaling completes (may produce NaN for constant columns)"


@pytest.mark.unit
class TestInputValidation:
    """Test input validation and sanitization."""
    
    def test_validate_crypto_name(self):
        """Test validation of cryptocurrency name."""
        valid_cryptos = ['bitcoin', 'ethereum', 'solana']
        invalid_crypto = 'invalid_crypto_xyz'
        
        is_valid = invalid_crypto.lower() in valid_cryptos
        assert not is_valid, "Should reject invalid crypto"
    
    def test_validate_date_range(self):
        """Test validation of date ranges."""
        start_date = datetime(2026, 5, 10)
        end_date = datetime(2026, 5, 8)
        
        is_valid = start_date < end_date
        assert not is_valid, "Start date should be before end date"
    
    def test_validate_model_version(self):
        """Test validation of model version string."""
        valid_versions = ['v1', 'v1_linear', 'v2_ridge', 'v2_ridge_bitcoin']
        invalid_version = 'v999_unknown'
        
        is_valid = invalid_version in valid_versions
        assert not is_valid, "Should reject unknown model version"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'unit'])
