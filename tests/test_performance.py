"""
Performance benchmarking tests
Tests computational efficiency and scalability.
"""

import pytest
import sys
import pandas as pd
import numpy as np
import time
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.mark.performance
class TestDataPreparationPerformance:
    """Benchmark data preparation operations."""
    
    def test_target_creation_performance(self):
        """Benchmark target variable creation."""
        df = pd.DataFrame({
            'close': np.random.randn(10000),
            'timestamp': pd.date_range('2020-01-01', periods=10000, freq='D')
        })
        
        start = time.time()
        df['target'] = df['close'].shift(-1)
        elapsed = time.time() - start
        
        # Should complete in < 0.1 seconds for 10k rows
        assert elapsed < 0.1, f"Target creation took {elapsed:.3f}s (should be <0.1s)"
    
    def test_nan_dropping_performance(self):
        """Benchmark NaN row dropping."""
        df = pd.DataFrame(np.random.randn(10000, 30))
        df.iloc[::100, ::5] = np.nan  # Introduce some NaNs
        
        start = time.time()
        df_clean = df.dropna()
        elapsed = time.time() - start
        
        # Should complete in < 0.1 seconds
        assert elapsed < 0.1, f"NaN dropping took {elapsed:.3f}s (should be <0.1s)"
    
    def test_temporal_split_performance(self):
        """Benchmark temporal train-test split."""
        df = pd.DataFrame({
            'timestamp': pd.date_range('2020-01-01', periods=100000, freq='H'),
            'value': np.random.randn(100000)
        })
        
        start = time.time()
        split_idx = int(len(df) * 0.8)
        train = df.iloc[:split_idx]
        test = df.iloc[split_idx:]
        elapsed = time.time() - start
        
        # Should complete in < 0.01 seconds (trivial operation)
        assert elapsed < 0.01, f"Temporal split took {elapsed:.4f}s (should be <0.01s)"


@pytest.mark.performance
class TestScalingPerformance:
    """Benchmark feature scaling operations."""
    
    def test_scaler_fit_performance(self):
        """Benchmark StandardScaler fitting."""
        X = np.random.randn(10000, 27)
        
        scaler = StandardScaler()
        start = time.time()
        scaler.fit(X)
        elapsed = time.time() - start
        
        # Should fit very quickly
        assert elapsed < 0.1, f"Scaler fit took {elapsed:.3f}s (should be <0.1s)"
    
    def test_scaler_transform_performance(self):
        """Benchmark StandardScaler transformation."""
        X_train = np.random.randn(10000, 27)
        X_test = np.random.randn(1000, 27)
        
        scaler = StandardScaler()
        scaler.fit(X_train)
        
        start = time.time()
        X_test_scaled = scaler.transform(X_test)
        elapsed = time.time() - start
        
        # Should transform 1000 samples quickly
        assert elapsed < 0.01, f"Transform took {elapsed:.4f}s (should be <0.01s)"
    
    def test_inverse_transform_performance(self):
        """Benchmark inverse transform."""
        y_train = np.random.randn(10000, 1)
        y_test_scaled = np.random.randn(1000, 1)
        
        scaler = StandardScaler()
        scaler.fit(y_train)
        
        start = time.time()
        y_test = scaler.inverse_transform(y_test_scaled)
        elapsed = time.time() - start
        
        assert elapsed < 0.01, f"Inverse transform took {elapsed:.4f}s (should be <0.01s)"


@pytest.mark.performance
class TestModelTrainingPerformance:
    """Benchmark model training performance."""
    
    def test_ridge_training_performance(self):
        """Benchmark Ridge model training."""
        X = np.random.randn(5000, 27)
        y = np.random.randn(5000)
        
        model = Ridge(alpha=0.001)
        
        start = time.time()
        model.fit(X, y)
        elapsed = time.time() - start
        
        # Should train on 5k samples in < 1 second
        assert elapsed < 1.0, f"Training took {elapsed:.3f}s (should be <1s)"
    
    def test_prediction_performance_small_batch(self):
        """Benchmark prediction on small batch."""
        X_train = np.random.randn(5000, 27)
        y_train = np.random.randn(5000)
        X_test = np.random.randn(100, 27)
        
        model = Ridge(alpha=0.001)
        model.fit(X_train, y_train)
        
        start = time.time()
        predictions = model.predict(X_test)
        elapsed = time.time() - start
        
        # Should predict 100 samples in < 0.01 seconds
        assert elapsed < 0.01, f"Prediction took {elapsed:.4f}s (should be <0.01s)"
    
    def test_prediction_performance_single(self):
        """Benchmark single prediction."""
        X_train = np.random.randn(5000, 27)
        y_train = np.random.randn(5000)
        X_test = np.random.randn(1, 27)
        
        model = Ridge(alpha=0.001)
        model.fit(X_train, y_train)
        
        start = time.time()
        prediction = model.predict(X_test)
        elapsed = time.time() - start
        
        # Single prediction should be very fast
        assert elapsed < 0.005, f"Single prediction took {elapsed:.4f}s (should be <0.005s)"
    
    def test_scoring_performance(self):
        """Benchmark model scoring (R² calculation)."""
        X_train = np.random.randn(5000, 27)
        y_train = np.random.randn(5000)
        X_test = np.random.randn(1000, 27)
        y_test = np.random.randn(1000)
        
        model = Ridge(alpha=0.001)
        model.fit(X_train, y_train)
        
        start = time.time()
        score = model.score(X_test, y_test)
        elapsed = time.time() - start
        
        # Should score quickly
        assert elapsed < 0.1, f"Scoring took {elapsed:.3f}s (should be <0.1s)"


@pytest.mark.performance
class TestMemoryEfficiency:
    """Benchmark memory usage patterns."""
    
    def test_large_array_memory(self):
        """Test memory usage for large arrays."""
        # Create 100k x 27 array
        X = np.random.randn(100000, 27)
        
        # Should be able to hold in memory
        assert X.nbytes > 0, "Array should exist in memory"
        assert X.nbytes < 1e8, "Array should be < 100MB"  # Approximately 100MB
    
    def test_scaler_memory_footprint(self):
        """Test scaler memory usage."""
        X = np.random.randn(10000, 27)
        scaler = StandardScaler()
        scaler.fit(X)
        
        # Scaler should be small
        # It stores mean and scale vectors (2 * 27 elements)
        assert hasattr(scaler, 'mean_'), "Scaler should store mean"
        assert hasattr(scaler, 'scale_'), "Scaler should store scale"
        assert len(scaler.mean_) == 27, "Mean should be 27-element vector"


@pytest.mark.performance
@pytest.mark.slow
class TestLargeScalePerformance:
    """Test performance on larger datasets."""
    
    def test_full_pipeline_performance_large_dataset(self):
        """Test complete pipeline on large dataset."""
        # Create large dataset
        n_samples = 50000
        n_features = 27
        
        X = np.random.randn(n_samples, n_features)
        y = np.random.randn(n_samples)
        
        split_idx = int(n_samples * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Time full pipeline
        start = time.time()
        
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
        
        # Predict
        predictions = model.predict(X_test_scaled)
        
        # Unscale
        predictions_unscaled = scaler_y.inverse_transform(predictions.reshape(-1, 1))
        
        elapsed = time.time() - start
        
        # Full pipeline should complete in reasonable time
        assert elapsed < 10.0, f"Full pipeline took {elapsed:.2f}s (should be <10s)"
        assert len(predictions) == len(X_test), "Should produce correct predictions"


@pytest.mark.performance
class TestScalabilityTrends:
    """Test scalability characteristics."""
    
    def test_prediction_throughput(self):
        """Measure prediction throughput (predictions per second)."""
        X_train = np.random.randn(5000, 27)
        y_train = np.random.randn(5000)
        X_test = np.random.randn(10000, 27)
        
        model = Ridge(alpha=0.001)
        model.fit(X_train, y_train)
        
        start = time.time()
        predictions = model.predict(X_test)
        elapsed = time.time() - start
        
        throughput = len(X_test) / elapsed
        
        # Should predict at least 100k predictions per second
        assert throughput > 100000, f"Throughput {throughput:.0f} preds/s (should be >100k)"
    
    def test_feature_scaling_throughput(self):
        """Measure feature scaling throughput."""
        X = np.random.randn(100000, 27)
        scaler = StandardScaler()
        scaler.fit(X[:10000])
        
        start = time.time()
        X_scaled = scaler.transform(X)
        elapsed = time.time() - start
        
        throughput = len(X) / elapsed
        
        # Should scale at least 1M samples per second
        assert throughput > 1000000, f"Throughput {throughput:.0f} samples/s (should be >1M)"


@pytest.mark.performance
class TestCachingAndOptimization:
    """Test caching and optimization opportunities."""
    
    def test_repeated_predictions_efficiency(self):
        """Test efficiency of repeated predictions."""
        X_train = np.random.randn(5000, 27)
        y_train = np.random.randn(5000)
        X_test = np.random.randn(100, 27)
        
        model = Ridge(alpha=0.001)
        model.fit(X_train, y_train)
        
        # First prediction
        start1 = time.time()
        pred1 = model.predict(X_test)
        elapsed1 = time.time() - start1
        
        # Second prediction (should be similar speed)
        start2 = time.time()
        pred2 = model.predict(X_test)
        elapsed2 = time.time() - start2
        
        # Both should be similar
        ratio = elapsed2 / elapsed1 if elapsed1 > 0 else 1
        assert 0.5 < ratio < 2, "Repeated predictions should have similar timing"
    
    def test_batch_vs_single_prediction_ratio(self):
        """Compare batch vs single prediction performance."""
        X_train = np.random.randn(5000, 27)
        y_train = np.random.randn(5000)
        X_test = np.random.randn(1000, 27)
        
        model = Ridge(alpha=0.001)
        model.fit(X_train, y_train)
        
        # Batch prediction
        start = time.time()
        batch_preds = model.predict(X_test)
        batch_time = time.time() - start
        
        # Single predictions (1000 times)
        start = time.time()
        for i in range(1000):
            single_pred = model.predict(X_test[i:i+1])
        single_time = time.time() - start
        
        # Batch should be significantly faster
        speedup = single_time / batch_time
        assert speedup > 5, f"Batch should be >{5}x faster than 1000 singles (got {speedup:.1f}x)"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'performance'])
