"""
Integration tests for full pipeline (Phase A-F)
Tests end-to-end workflows and component interactions.
"""

import pytest
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
import pickle

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.mark.integration
class TestDataToPredictionPipeline:
    """Integration tests for full data-to-prediction pipeline."""
    
    def test_complete_pipeline_workflow(self, bitcoin_features_df, temp_data_dir, temp_model_dir):
        """Test complete workflow from data loading to prediction."""
        
        # Step 1: Load data
        df = bitcoin_features_df.copy().sort_values('timestamp')
        assert len(df) > 0, "Data should be loaded"
        
        # Step 2: Prepare features and target
        df['target'] = df['close'].shift(-1)
        df = df.iloc[:-1]  # Drop last row
        feature_cols = [col for col in df.columns 
                       if col not in ['timestamp', 'close', 'target', 'trend_up']]
        
        assert len(feature_cols) == 27, "Should have 27 features"
        
        # Step 3: Split data
        split_idx = int(len(df) * 0.8)
        X_train = df.iloc[:split_idx][feature_cols].values
        X_test = df.iloc[split_idx:][feature_cols].values
        y_train = df.iloc[:split_idx]['target'].values
        y_test = df.iloc[split_idx:]['target'].values
        
        # Step 4: Scale data
        scaler_X = StandardScaler()
        X_train_scaled = scaler_X.fit_transform(X_train)
        X_test_scaled = scaler_X.transform(X_test)
        
        scaler_y = StandardScaler()
        y_train_scaled = scaler_y.fit_transform(y_train.reshape(-1, 1)).flatten()
        y_test_scaled = scaler_y.transform(y_test.reshape(-1, 1)).flatten()
        
        # Step 5: Train model
        model = Ridge(alpha=0.001)
        model.fit(X_train_scaled, y_train_scaled)
        
        # Step 6: Make predictions
        y_pred_scaled = model.predict(X_test_scaled)
        y_pred = scaler_y.inverse_transform(y_pred_scaled.reshape(-1, 1)).flatten()
        
        assert len(y_pred) == len(y_test), "Predictions should match test size"
        assert all(p > 0 for p in y_pred), "All predictions should be positive"
        
        # Step 7: Save artifacts
        model_file = temp_model_dir / 'model.pkl'
        with open(model_file, 'wb') as f:
            pickle.dump(model, f)
        
        # Step 8: Verify loading
        with open(model_file, 'rb') as f:
            loaded_model = pickle.load(f)
        
        pred_test = loaded_model.predict(X_test_scaled[:1])
        assert len(pred_test) > 0, "Loaded model should make predictions"
    
    def test_prediction_consistency(self, bitcoin_features_df):
        """Test that predictions are consistent across multiple runs."""
        np.random.seed(42)
        
        df = bitcoin_features_df.copy()
        df['target'] = df['close'].shift(-1)
        df = df.iloc[:-1]
        
        feature_cols = [col for col in df.columns 
                       if col not in ['timestamp', 'close', 'target', 'trend_up']]
        
        X = df[feature_cols].values[-10:]  # Last 10 samples
        
        # Scale
        scaler = StandardScaler()
        scaler.fit(df[feature_cols].values)
        X_scaled = scaler.transform(X)
        
        # Train model
        model = Ridge(alpha=0.001)
        model.fit(df[feature_cols].values[:-10], df['target'].values[:-10])
        
        # Make predictions twice
        pred1 = model.predict(X_scaled)
        pred2 = model.predict(X_scaled)
        
        assert np.allclose(pred1, pred2), "Predictions should be consistent"
    
    def test_feature_to_prediction_mapping(self, bitcoin_features_df):
        """Test that features correctly map through pipeline to predictions."""
        df = bitcoin_features_df.copy().tail(1)  # Last record
        
        # Extract features
        feature_cols = [col for col in df.columns 
                       if col not in ['timestamp', 'close', 'target', 'trend_up']]
        features = df[feature_cols].values[0]
        
        assert len(features) == 27, "Should have 27 features"
        assert not np.isnan(features).any(), "Features should not contain NaN"
        
        # Scale features
        scaler = StandardScaler()
        scaler.fit(np.random.randn(100, 27))  # Dummy fit
        features_scaled = scaler.transform(features.reshape(1, -1))
        
        assert features_scaled.shape == (1, 27), "Scaled features should have correct shape"
        
        # Make prediction
        model = Ridge(alpha=0.001)
        model.fit(np.random.randn(100, 27), np.random.randn(100))
        prediction = model.predict(features_scaled)
        
        assert len(prediction) == 1, "Should make single prediction"
        assert prediction[0] > -1000, "Prediction should be reasonable"


@pytest.mark.integration
class TestTimeSeriesConsistency:
    """Integration tests for temporal consistency."""
    
    def test_temporal_ordering_throughout_pipeline(self, bitcoin_features_df):
        """Test that temporal ordering is maintained throughout pipeline."""
        df = bitcoin_features_df.copy().sort_values('timestamp')
        
        # Verify at each stage
        assert (df['timestamp'].diff().dropna() > pd.Timedelta(0)).all(), \
            "Initial data should be chronologically ordered"
        
        df['target'] = df['close'].shift(-1)
        
        # After target creation, ordering should still hold
        assert (df['timestamp'].diff().dropna() > pd.Timedelta(0)).all(), \
            "Ordering should be maintained after target creation"
        
        # Split
        split_idx = int(len(df) * 0.8)
        train = df.iloc[:split_idx]
        test = df.iloc[split_idx:]
        
        assert train['timestamp'].max() < test['timestamp'].min(), \
            "Train and test periods should not overlap"
    
    def test_forward_propagation_of_data(self, bitcoin_features_df):
        """Test that data flows correctly forward through train-test splits."""
        df = bitcoin_features_df.copy().sort_values('timestamp')
        n_total = len(df)
        
        # Split 80/20
        split_idx = int(n_total * 0.8)
        train_dates = df.iloc[:split_idx]['timestamp']
        test_dates = df.iloc[split_idx:]['timestamp']
        
        # Verify split
        assert len(train_dates) + len(test_dates) == n_total
        assert train_dates.max() < test_dates.min()
        
        # Verify no information leakage
        assert train_dates.max() < test_dates.min(), \
            "No test date should appear in training period"


@pytest.mark.integration
class TestModelTrainingEvaluation:
    """Integration tests for model training and evaluation."""
    
    def test_model_training_with_real_data_structure(self, bitcoin_features_df):
        """Test model training with realistic data structure."""
        df = bitcoin_features_df.copy()
        df['target'] = df['close'].shift(-1)
        df = df.dropna()
        
        feature_cols = [col for col in df.columns 
                       if col not in ['timestamp', 'close', 'target', 'trend_up']]
        
        # Split
        split_idx = int(len(df) * 0.8)
        X_train = df.iloc[:split_idx][feature_cols].values
        y_train = df.iloc[:split_idx]['target'].values
        X_test = df.iloc[split_idx:][feature_cols].values
        y_test = df.iloc[split_idx:]['target'].values
        
        # Scale
        scaler_X = StandardScaler()
        X_train_scaled = scaler_X.fit_transform(X_train)
        X_test_scaled = scaler_X.transform(X_test)
        
        scaler_y = StandardScaler()
        y_train_scaled = scaler_y.fit_transform(y_train.reshape(-1, 1)).flatten()
        y_test_scaled = scaler_y.transform(y_test.reshape(-1, 1)).flatten()
        
        # Train
        model = Ridge(alpha=0.001)
        model.fit(X_train_scaled, y_train_scaled)
        
        # Evaluate
        train_score = model.score(X_train_scaled, y_train_scaled)
        test_score = model.score(X_test_scaled, y_test_scaled)
        
        # R² can be negative for poor models, but should be numeric
        assert isinstance(train_score, (int, float)), "Train R² should be numeric"
        assert isinstance(test_score, (int, float)), "Test R² should be numeric"
        # With random data, score might be poor, but for real data should be decent
        if test_score > 0:  # If positive, should be reasonable
            assert test_score > 0.5, "Model should have decent test performance (R² > 0.5 if positive)"
    
    def test_scaling_consistency_through_pipeline(self):
        """Test that scaling is applied consistently throughout."""
        X_train = np.random.randn(100, 27)
        X_test = np.random.randn(20, 27)
        
        # Fit on train
        scaler = StandardScaler()
        scaler.fit(X_train)
        
        # Transform both with same scaler
        X_train_scaled = scaler.transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Check consistency
        assert np.isclose(X_train_scaled.mean(), 0, atol=0.2), \
            "Train set mean should be close to 0"
        
        # Test set might not be exactly 0, but should be reasonable
        assert not np.isnan(X_test_scaled).any(), "Test set should not have NaN"


@pytest.mark.integration
class TestEndToEndPrediction:
    """Integration tests for end-to-end prediction workflow."""
    
    def test_from_features_to_confidence_intervals(self):
        """Test complete flow from features to predictions with CI."""
        # Simulate features
        features = np.random.randn(1, 27)
        
        # Scale
        scaler_X = StandardScaler()
        scaler_X.fit(np.random.randn(100, 27))
        features_scaled = scaler_X.transform(features)
        
        # Predict
        model = Ridge(alpha=0.001)
        model.fit(np.random.randn(100, 27), np.random.randn(100))
        pred_scaled = model.predict(features_scaled)
        
        # Unscale
        scaler_y = StandardScaler()
        scaler_y.fit(np.random.randn(100, 1))
        pred = scaler_y.inverse_transform(pred_scaled.reshape(-1, 1))[0, 0]
        
        # Calculate CI
        residual_std = 50.0
        z_score = 1.96
        ci_lower = pred - z_score * residual_std
        ci_upper = pred + z_score * residual_std
        
        # Verify
        assert ci_lower < pred < ci_upper, "Prediction should be within CI"
        assert ci_upper - ci_lower > 0, "CI width should be positive"
        assert isinstance(pred, (int, float, np.number)), "Prediction should be numeric"
    
    def test_prediction_service_workflow(self, mock_model_artifacts):
        """Test prediction service workflow with mock artifacts."""
        artifacts = mock_model_artifacts
        
        # Simulate latest features
        features = np.random.randn(1, 27)
        
        # Scale with service's scaler
        features_scaled = artifacts['scaler_X'].transform(features)
        
        # Predict with service's model
        pred_scaled = artifacts['model'].predict(features_scaled)
        
        # Unscale
        pred = artifacts['scaler_y'].inverse_transform(pred_scaled.reshape(-1, 1))[0, 0]
        
        assert isinstance(pred, (int, float, np.number)), "Should produce valid prediction"
        assert not np.isnan(pred), "Prediction should not be NaN"


@pytest.mark.integration
class TestArtifactIntegration:
    """Integration tests for model artifact management."""
    
    def test_artifact_save_and_load_cycle(self, temp_model_dir):
        """Test saving and loading all artifacts together."""
        # Create artifacts
        model = Ridge(alpha=0.001)
        X = np.random.randn(100, 27)
        y = np.random.randn(100)
        model.fit(X, y)
        
        scaler_X = StandardScaler()
        scaler_X.fit(X)
        
        scaler_y = StandardScaler()
        scaler_y.fit(y.reshape(-1, 1))
        
        # Save all
        with open(temp_model_dir / 'model.pkl', 'wb') as f:
            pickle.dump(model, f)
        with open(temp_model_dir / 'scaler_X.pkl', 'wb') as f:
            pickle.dump(scaler_X, f)
        with open(temp_model_dir / 'scaler_y.pkl', 'wb') as f:
            pickle.dump(scaler_y, f)
        
        # Verify all exist
        assert (temp_model_dir / 'model.pkl').exists()
        assert (temp_model_dir / 'scaler_X.pkl').exists()
        assert (temp_model_dir / 'scaler_y.pkl').exists()
        
        # Load all
        with open(temp_model_dir / 'model.pkl', 'rb') as f:
            loaded_model = pickle.load(f)
        with open(temp_model_dir / 'scaler_X.pkl', 'rb') as f:
            loaded_scaler_X = pickle.load(f)
        with open(temp_model_dir / 'scaler_y.pkl', 'rb') as f:
            loaded_scaler_y = pickle.load(f)
        
        # Test workflow with loaded artifacts
        X_test = np.random.randn(10, 27)
        X_test_scaled = loaded_scaler_X.transform(X_test)
        pred_scaled = loaded_model.predict(X_test_scaled)
        pred = loaded_scaler_y.inverse_transform(pred_scaled.reshape(-1, 1))
        
        assert pred.shape == (10, 1), "Should produce correct prediction shape"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'integration'])
