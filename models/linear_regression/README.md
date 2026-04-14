# Linear Regression Model - Production Models

## Overview
This directory contains trained Linear Regression models for predicting cryptocurrency close prices across 15 cryptocurrencies. The models use technical indicators and temporal features to generate trading signals.

## Model Details
- **Model Type:** Linear Regression (scikit-learn)
- **Training Date:** April 14, 2026
- **Version:** 1.0
- **Status:** Production Ready
- **Purpose:** Predict next-day cryptocurrency close prices for trading signals

## Cryptocurrencies Covered
- avalanche
- axie_infinity
- binance_coin
- bitcoin
- chainlink
- ethereum
- fantom
- injective
- litecoin
- maker
- render
- solana
- the_graph
- toncoin
- tron

## File Structure
- `{crypto_name}_model.pkl`: Trained Linear Regression model (pickle format)
- `{crypto_name}_metadata.json`: Model metadata including hyperparameters, features, and performance metrics
- `linear_regression_performance_summary.csv`: Performance metrics across all cryptocurrencies
- `README.md`: This documentation file

## Performance Metrics Summary

### Metric Definitions
- **R² Score:** Model fit quality on test set (0-1 scale, higher is better)
  - 1.0 = Perfect predictions
  - 0.5 = Model explains 50% of variance
  - 0 = Model no better than mean

- **MAPE (%):** Mean Absolute Percentage Error (lower is better)
  - Measures average prediction error as percentage of actual values

- **MAE ($):** Mean Absolute Error in dollars (lower is better)
  - Average dollar amount of prediction error

- **RMSE ($):** Root Mean Squared Error (lower is better)
  - Penalizes larger errors more heavily than MAE

- **Dir. Accuracy (%):** Directional Accuracy (higher is better)
  - Percentage of correct price movement direction predictions
  - Critical for trading signal generation

- **Correlation:** Pearson correlation between actual and predicted (higher is better)
  - Measures strength of linear relationship

### Performance Highlights
See `linear_regression_performance_summary.csv` for detailed metrics on all 15 cryptocurrencies.

## Features Used (28 total)

### Technical Indicators
- **SMA (Simple Moving Averages):** 7-day, 20-day, 50-day
- **EMA (Exponential Moving Average):** 20-day
- **RSI (Relative Strength Index):** 14-period momentum oscillator
- **MACD (Moving Average Convergence Divergence):** Trend indicator

### Temporal Features
- **Trend_Up:** Binary indicator of uptrend
- **Day_of_Week:** Categorical (0-6, where 0=Monday, 6=Sunday)
- **Month:** Categorical (1-12)

### Price Features
- **Open, High, Low:** Daily OHLC prices (scaled)
- **Volume:** Trading volume (scaled)
- **Daily_Return, Weekly_Return, Monthly_Return:** Price change metrics (scaled)
- **Volatility_30:** 30-day rolling volatility (scaled)

### Full Feature List
1. SMA_7
2. SMA_20
3. SMA_50
4. EMA_20
5. RSI_14
6. MACD_Line
7. MACD_Signal
8. MACD_Histogram
9. Trend_Up
10. Day_of_Week
11. Month
12. Open
13. High
14. Low
15. Volume
16. Daily_Return
17. Weekly_Return
18. Monthly_Return
19. Volatility_30
20. (Additional derived features from technical calculations)

## Model Hyperparameters
```
fit_intercept: True
positive: False
normalize: False
```

## Data Preparation

### Train/Test Split
- **Training Set:** 80% of historical data
- **Test Set:** 20% of historical data (used for evaluation)

### Scaling
- **Method:** StandardScaler normalization
- **Applied to:** All features and target variable
- **Reason:** Improves model convergence and coefficient interpretability

### Cross-Validation
- **Method:** TimeSeriesSplit (5 splits)
- **Reason:** Preserves temporal order of data (prevents data leakage)

## Usage Example

### Loading and Making Predictions
```python
import pickle
import json
import pandas as pd

# Load model
with open('models/linear_regression/bitcoin_model.pkl', 'rb') as f:
    model = pickle.load(f)

# Load metadata
with open('models/linear_regression/bitcoin_metadata.json', 'r') as f:
    metadata = json.load(f)

print(f"Model R² Score: {metadata['performance_metrics']['r2_score']}")
print(f"Model MAPE: {metadata['performance_metrics']['mape']:.2f}%")
print(f"Features: {metadata['features_used']}")

# Make predictions on new data (X_new must have scaled features)
predictions = model.predict(X_new)
```

### Batch Prediction Across All Models
```python
import pickle
import glob

models = {}
predictions = {}

# Load all models
for model_file in glob.glob('models/linear_regression/*_model.pkl'):
    crypto_name = model_file.split('/')[-1].replace('_model.pkl', '')
    with open(model_file, 'rb') as f:
        models[crypto_name] = pickle.load(f)

# Make predictions
for crypto, model in models.items():
    predictions[crypto] = model.predict(X_new)
```

## Important Notes

1. **Feature Order Matters:** Features must be in exact order specified in metadata JSON files
2. **Data Scaling:** Input features must be scaled using StandardScaler (mean=0, std=1)
3. **Feature Engineering:** All technical indicators must be pre-calculated before prediction
4. **Time Series:** Model designed for next-period predictions (t+1), not multi-step forecasting
5. **Market Conditions:** Model trained on historical data; performance varies with market regimes
6. **Interpretation:** Positive coefficients indicate positive relationship with close price

## Limitations

- **Linear Assumptions:** Model assumes linear relationship between features and price
- **Non-linear Patterns:** Cannot capture complex non-linear market dynamics
- **Market Regimes:** Performance varies significantly across different market conditions
- **Tail Events:** May underperform during extreme market movements
- **Feature Quality:** Highly dependent on quality of technical indicator calculations
- **Lookback Window:** Limited by historical data availability for indicator calculation

## Production Deployment Considerations

1. **Backtesting:** Run comprehensive backtesting before deploying to live trading
2. **Monitoring:** Track prediction accuracy and model drift over time
3. **Retraining:** Retrain models monthly or quarterly with new market data
4. **Risk Management:** Always implement position sizing and stop-loss orders
5. **Ensemble:** Consider combining with other models for improved robustness
6. **Transaction Costs:** Account for commissions and fees in backtesting/production
7. **Slippage:** Factor in realistic execution prices in strategy simulations

## Retraining Instructions

1. **Prepare data:** Collect new training data with same 28 features
2. **Preprocess:** Apply same scaling and feature engineering as original training
3. **Train:** Train new Linear Regression models using GridSearchCV with TimeSeriesSplit
4. **Evaluate:** Compare new vs old model performance on test set
5. **Validate:** Run backtesting on new models
6. **Update:** Replace old model files with new ones
7. **Document:** Update metadata with new training date and metrics

## File Formats

### Model Files (.pkl)
- **Format:** Python pickle (binary serialization)
- **Load with:** `pickle.load(open('file.pkl', 'rb'))`
- **sklearn version:** Compatible with scikit-learn >= 0.20
- **Size:** ~1-5 KB per model

### Metadata Files (.json)
- **Format:** JSON (human-readable text)
- **Contains:** 
  - Hyperparameters
  - Features list and count
  - Performance metrics
  - Training/test sample counts
  - Training timestamp
- **Load with:** `json.load(open('file.json', 'r'))`

### CSV Files (.csv)
- **Format:** Comma-separated values
- **Content:** Performance metrics across all 15 cryptocurrencies
- **Readable:** Any spreadsheet application or pandas
- **Load with:** `pd.read_csv('file.csv')`

## Performance Tracking

**Summary Statistics Across All Models:**
- See `linear_regression_performance_summary.csv` for complete metrics
- Models ranked by R² Score (best model = highest R²)
- Directional Accuracy averages indicate overall signal quality
- MAPE averages show typical prediction error magnitudes

## Troubleshooting Guide

### Problem: "Dimension mismatch" or "ValueError: X has n features but this model was trained with m features"
**Solution:** Ensure input features match exactly with trained model (28 features in correct order). Verify feature names against metadata.

### Problem: Predictions seem completely wrong or off by orders of magnitude
**Solution:** Verify that features are scaled using StandardScaler with training data statistics. Raw unscaled features will produce incorrect predictions.

### Problem: Model performance degrading noticeably over time
**Solution:** Market conditions have changed; retrain model with recent data. Linear models can be sensitive to shifts in market regime.

### Problem: Different predictions across runs
**Solution:** Check that scaling parameters (mean, std) are consistent. Ensure no randomness in preprocessing steps.

### Problem: Cannot load model files
**Solution:** Verify pickle file is not corrupted. Check scikit-learn version compatibility. Ensure file path is correct.

## Version History

### v1.0 (April 14, 2026)
- Initial production release
- Linear Regression on 15 cryptocurrencies
- 28 technical features
- GridSearchCV hyperparameter tuning
- TimeSeriesSplit (5-fold) cross-validation
- Comprehensive performance metrics

## Architecture Details

### Model Algorithm
- **Base Algorithm:** Ordinary Least Squares (OLS) Linear Regression
- **Loss Function:** Mean Squared Error (MSE)
- **Optimization:** Analytical solution (closed-form)
- **Computational Complexity:** O(n * m²) where n = samples, m = features

### Feature Engineering Pipeline
1. **Raw Data:** Load OHLCV data
2. **Technical Indicators:** Calculate SMA, EMA, RSI, MACD
3. **Temporal Features:** Extract day-of-week, month
4. **Scaling:** Apply StandardScaler to all features
5. **Input:** Feed to Linear Regression model

### Prediction Pipeline
1. **Raw Input:** New price data
2. **Feature Calculation:** Compute 28 features
3. **Scaling:** Apply same StandardScaler (training statistics)
4. **Prediction:** Pass through trained model
5. **Output:** Predicted close price (must be inverse-scaled)

## Best Practices for Use

1. **Always scale input data** using training set statistics
2. **Validate feature order** before making predictions
3. **Monitor model performance** in production
4. **Retrain regularly** as market conditions evolve
5. **Use with complementary strategies** for robustness
6. **Implement risk management** regardless of model confidence
7. **Document all changes** when updating models

## References

- scikit-learn Linear Regression: https://scikit-learn.org/stable/modules/linear_model.html
- Time Series Cross-Validation: https://scikit-learn.org/stable/modules/cross_validation.html#time-series-split
- Technical Analysis Indicators: https://en.wikipedia.org/wiki/Technical_analysis
- Cryptocurrency Trading Best Practices

## Contact & Support

For questions about model interpretation, retraining, or deployment, refer to:
- Training notebook: `notebooks/Model.ipynb`
- EDA notebook: `notebooks/EDA.ipynb`
- Feature engineering: `notebooks/Preprocessing.ipynb`
