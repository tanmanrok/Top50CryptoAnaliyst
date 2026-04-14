# Helpers Module Documentation

## Overview
This module provides comprehensive utility functions for loading, visualizing, and analyzing cryptocurrency data used in the Top 50 Crypto Analysis project. It includes data loading, visualization, and statistical testing capabilities.

## Dependencies
- `os` - For file system operations
- `pandas` - For data manipulation and CSV reading
- `numpy` - For numerical operations
- `matplotlib.pyplot` - For plotting
- `seaborn` - For enhanced statistical visualizations
- `scipy.stats` - For statistical tests

---

## Functions

### 1. `load_data_csv_files(directory)`

Loads all CSV files from a specified directory into a dictionary of pandas DataFrames.

**Parameters:**
- `directory` (str): Path to the directory containing CSV files

**Returns:**
- `data_dict` (dict): Dictionary where keys are CSV filenames (without extension) and values are pandas DataFrames

**Functionality:**
- Iterates through all files in the specified directory
- Identifies and loads only `.csv` files
- Removes `.csv` extension from filenames for cleaner variable names
- Prints a status message for each loaded file
- Returns a dictionary containing all loaded datasets

**Usage Example:**
```python
import sys
sys.path.append('./helpers')
from helpers import load_data_csv_files

# Load data from the interim directory
crypto_data = load_data_csv_files('../data/interim/')

# Access individual datasets
aave_df = crypto_data['aave_cleaned']
algorand_df = crypto_data['algorand_cleaned']

# See how many datasets were loaded
print(f"Total cryptocurrencies loaded: {len(crypto_data)}")
```

**Notes:**
- Useful for batch loading multiple cryptocurrency datasets
- Assumes all `.csv` files in the directory are valid datasets
- File processing order depends on the operating system's file listing order

---

### 2. `plot_crypto_prices(crypto_data, plot_type='subplots', crypto_name=None)`

Plot cryptocurrency price data in various formats.

**Parameters:**
- `crypto_data` (dict): Dictionary of DataFrames containing cryptocurrency data
- `plot_type` (str, default='subplots'): Type of plot:
  - `'subplots'`: All cryptos in grid layout
  - `'individual'`: Individual plots for each crypto (opens sequentially)
  - `'normalized'`: All cryptos on one plot with normalized prices
  - `'ohlc'`: OHLC (Open, High, Low, Close) plot for a single cryptocurrency
- `crypto_name` (str, optional): Name of cryptocurrency to plot (required for `'ohlc'` plot_type)

**Returns:**
- None (displays plots)

**Usage Examples:**
```python
# Plot all cryptos in grid layout
plot_crypto_prices(crypto_data, plot_type='subplots')

# Plot normalized prices to compare trends
plot_crypto_prices(crypto_data, plot_type='normalized')

# Plot OHLC for specific crypto
plot_crypto_prices(crypto_data, plot_type='ohlc', crypto_name='bitcoin_cleaned')
```

---

### 3. `plot_histograms(crypto_data, features=['Open', 'High', 'Low', 'Close', 'Volume'], crypto_names=None)`

Create histograms for specified features and cryptocurrencies with distribution analysis.

**Parameters:**
- `crypto_data` (dict): Dictionary of DataFrames containing cryptocurrency data
- `features` (list, default=['Open', 'High', 'Low', 'Close', 'Volume']): Features to create histograms for
- `crypto_names` (str, list, or None, default=None): Cryptocurrencies to include:
  - `None`: Use all cryptocurrencies (grid layout)
  - `str`: Single cryptocurrency name
  - `list`: List of cryptocurrency names

**Returns:**
- None (displays plots)

**Features:**
- Includes kernel density estimation (KDE) curves
- Displays mean and median lines on each histogram
- Useful for analyzing feature distributions

**Usage Examples:**
```python
# Plot histograms for all cryptos
plot_histograms(crypto_data)

# Plot histograms for single crypto
plot_histograms(crypto_data, crypto_names='bitcoin_cleaned')

# Plot specific features
plot_histograms(crypto_data, features=['Close', 'Volume'], crypto_names=['bitcoin_cleaned', 'ethereum_cleaned'])
```

---

### 4. `plot_boxplots(crypto_data, features=['Open', 'High', 'Low', 'Close', 'Volume'], crypto_names=None)`

Create box plots for specified features and cryptocurrencies to identify outliers and compare distributions.

**Parameters:**
- `crypto_data` (dict): Dictionary of DataFrames containing cryptocurrency data
- `features` (list, default=['Open', 'High', 'Low', 'Close', 'Volume']): Features to create box plots for
- `crypto_names` (str, list, or None, default=None): Cryptocurrencies to include

**Returns:**
- None (displays plots)

**Features:**
- Displays quartiles (Q1, Q2/median, Q3)
- Shows min and max values
- Highlights outliers
- Includes IQR (Interquartile Range) calculations

**Usage Examples:**
```python
# Plot box plots for all cryptos
plot_boxplots(crypto_data)

# Plot box plots for specific crypto
plot_boxplots(crypto_data, crypto_names='bitcoin_cleaned')
```

---

### 5. `get_correlation_matrix(crypto_data, features=['Open', 'High', 'Low', 'Close', 'Volume'], crypto_names=None)`

Calculate the Pearson correlation matrix for specified features and cryptocurrencies.

**Parameters:**
- `crypto_data` (dict): Dictionary of DataFrames containing cryptocurrency data
- `features` (list, default=['Open', 'High', 'Low', 'Close', 'Volume']): Features to calculate correlations for
- `crypto_names` (str, list, or None, default=None): Cryptocurrencies to include

**Returns:**
- `pd.DataFrame`: Correlation matrix with Pearson correlation coefficients

**Features:**
- Combines data from selected cryptocurrencies
- Calculates Pearson correlation coefficients
- Prints correlation matrix to console

**Usage Examples:**
```python
# Get correlation matrix for all cryptos
corr_matrix = get_correlation_matrix(crypto_data)

# Get correlation matrix for specific crypto
corr_matrix = get_correlation_matrix(crypto_data, crypto_names='bitcoin_cleaned')
```

---

### 6. `plot_correlation_heatmap(crypto_data, features=['Open', 'High', 'Low', 'Close', 'Volume'], crypto_names=None)`

Create a correlation heatmap for specified features using an intuitive color scale.

**Parameters:**
- `crypto_data` (dict): Dictionary of DataFrames containing cryptocurrency data
- `features` (list, default=['Open', 'High', 'Low', 'Close', 'Volume']): Features to visualize
- `crypto_names` (str, list, or None, default=None): Cryptocurrencies to include

**Returns:**
- None (displays plot)

**Features:**
- Uses 'coolwarm' color palette (blue = negative, red = positive correlation)
- Displays correlation coefficients on each cell
- Center of scale at 0 for easy interpretation

**Usage Examples:**
```python
# Plot correlation heatmap for all cryptos
plot_correlation_heatmap(crypto_data)

# Plot for combined data across multiple cryptos
plot_correlation_heatmap(crypto_data, crypto_names=['bitcoin_cleaned', 'ethereum_cleaned'])
```

---

### 7. `perform_statistical_tests(crypto_data, features=['Open', 'High', 'Low', 'Close', 'Volume'], crypto_names=None)`

Perform comprehensive statistical tests on cryptocurrency data.

**Tests Included:**

#### K-S Test (Kolmogorov-Smirnov)
- Tests if a sample follows a normal distribution
- Statistic range: 0-1 (smaller values indicate more normal distribution)
- p-value > 0.05 indicates normally distributed data

#### Pearson Correlation Test
- Tests if correlations between feature pairs are statistically significant
- Returns correlation coefficient (-1 to 1) and p-value
- Interprets significance and strength (weak/moderate/strong)

#### Levene's Test
- Tests for equality of variances across multiple cryptocurrencies
- p-value > 0.05 indicates equal variances
- Important for ANOVA and other parametric tests

#### Mann-Whitney U Test
- Non-parametric test comparing distributions between two samples
- Tests if first cryptocurrency differs significantly from others
- p-value < 0.05 indicates significantly different distributions

**Parameters:**
- `crypto_data` (dict): Dictionary of DataFrames containing cryptocurrency data
- `features` (list, default=['Open', 'High', 'Low', 'Close', 'Volume']): Features to analyze
- `crypto_names` (str, list, or None, default=None): Cryptocurrencies to include

**Returns:**
- `pd.DataFrame`: Results DataFrame with columns:
  - `Test Type`: Type of statistical test performed
  - `Feature`: Feature being tested
  - `Cryptocurrency/Pair`: Cryptocurrency or pair tested
  - `Statistic`: Test statistic value
  - `P-Value`: Statistical significance p-value
  - `Interpretation`: Human-readable interpretation

**Usage Examples:**
```python
# Run all statistical tests on all cryptos
results_df = perform_statistical_tests(crypto_data)

# View results
results_df.head(10)

# Filter for specific test type
ks_test_results = results_df[results_df['Test Type'] == 'K-S Test']

# Filter for specific feature
correlation_results = results_df[results_df['Test Type'] == 'Pearson Correlation']
```

**Output Example:**
| Test Type | Feature | Cryptocurrency/Pair | Statistic | P-Value | Interpretation |
|-----------|---------|---------------------|-----------|---------|----------------|
| K-S Test | Close | BITCOIN | 0.0847 | 0.0032 | NOT NORMAL |
| Pearson Correlation | Open vs Close | All Combined | 0.9542 | 0.0000 | Strong - SIGNIFICANT |
| Levene's Test | Volume | 49 cryptos | 15.3421 | 0.0001 | UNEQUAL VARIANCE |
| Mann-Whitney U | Close | BITCOIN vs ETHEREUM | 12345.5 | 0.0234 | DIFFERENT |

---

## Technical Indicators Module (`indicators.py`)

Advanced technical analysis functions for calculating and visualizing trading indicators.

### Functions Available

#### SMA & EMA Calculation
- `calculate_sma_ema(crypto_data, selected_cryptos=None, sma_periods=[7, 20, 50], ema_periods=[7, 20, 50])`
  - Calculates Simple Moving Average (SMA) and Exponential Moving Average (EMA)
  - SMA: Equal weighting over N periods
  - EMA: Exponential weighting (more weight to recent prices)
  - Returns updated crypto_data dict

#### SMA & EMA Plotting
- `plot_sma_ema(crypto_data, selected_cryptos=None, sma_periods=[7, 20, 50], ema_periods=[7, 20])`
  - Visualizes price with multiple moving averages
  - Shows trend identification and smoothing effects
  - Compares SMA (dashed lines) vs EMA (dash-dot lines)

#### RSI Calculation
- `calculate_rsi(prices, period=14)`
  - Calculates Relative Strength Index (momentum indicator)
  - Returns array of RSI values (0-100 range)
  - >70: Overbought | <30: Oversold
  - Formula: RSI = 100 - (100/(1 + RS)) where RS = Avg Gain / Avg Loss

- `calculate_rsi_for_cryptos(crypto_data, selected_cryptos=None, period=14)`
  - Wrapper to calculate RSI for multiple cryptocurrencies
  - Adds RSI column to each DataFrame
  - Returns updated crypto_data dict

#### RSI Plotting
- `plot_rsi(crypto_data, selected_cryptos=None, period=14)`
  - Plots price and RSI indicator together
  - Overlays overbought (>70) and oversold (<30) zones
  - Shows filled zones for quick visual identification

#### MACD Calculation
- `calculate_macd(prices, fast=12, slow=26, signal=9)`
  - Calculates MACD (Moving Average Convergence Divergence)
  - Returns tuple: (macd_line, signal_line, histogram)
  - MACD Line = EMA(12) - EMA(26)
  - Signal Line = EMA(9) of MACD Line
  - Histogram = MACD Line - Signal Line

- `calculate_macd_for_cryptos(crypto_data, selected_cryptos=None, fast=12, slow=26, signal=9)`
  - Wrapper to calculate MACD for multiple cryptocurrencies
  - Adds MACD, MACD_Signal, and MACD_Histogram columns
  - Returns updated crypto_data dict

#### MACD Plotting
- `plot_macd(crypto_data, selected_cryptos=None)`
  - Plots price and MACD indicator together
  - Shows MACD line, signal line, and histogram bars
  - Histogram color intensity indicates momentum strength

### Usage Examples

#### Calculate and Plot All Technical Indicators
```python
import sys
sys.path.append('./helpers')
from indicators import (calculate_sma_ema, plot_sma_ema, 
                       calculate_rsi_for_cryptos, plot_rsi,
                       calculate_macd_for_cryptos, plot_macd)

# Select cryptocurrencies to analyze
selected = ['bitcoin_cleaned', 'ethereum_cleaned', 'cardano_cleaned']

# Calculate SMA and EMA
crypto_data = calculate_sma_ema(crypto_data, selected_cryptos=selected)
plot_sma_ema(crypto_data, selected_cryptos=selected)

# Calculate and plot RSI
crypto_data = calculate_rsi_for_cryptos(crypto_data, selected_cryptos=selected, period=14)
plot_rsi(crypto_data, selected_cryptos=selected)

# Calculate and plot MACD
crypto_data = calculate_macd_for_cryptos(crypto_data, selected_cryptos=selected)
plot_macd(crypto_data, selected_cryptos=selected)
```

#### Quick Analysis Workflow
```python
# 1. Load and prepare data
crypto_data = load_data_csv_files('../data/interim/')

# 2. Apply technical indicators
crypto_data = calculate_sma_ema(crypto_data, selected_cryptos=['bitcoin_cleaned'])
crypto_data = calculate_rsi_for_cryptos(crypto_data, selected_cryptos=['bitcoin_cleaned'])
crypto_data = calculate_macd_for_cryptos(crypto_data, selected_cryptos=['bitcoin_cleaned'])

# 3. Visualize all indicators
plot_sma_ema(crypto_data, selected_cryptos=['bitcoin_cleaned'])
plot_rsi(crypto_data, selected_cryptos=['bitcoin_cleaned'])
plot_macd(crypto_data, selected_cryptos=['bitcoin_cleaned'])

# 4. Access calculated values
bitcoin_df = crypto_data['bitcoin_cleaned']
print(bitcoin_df[['Date', 'Close', 'SMA_20', 'EMA_20', 'RSI_14', 'MACD']].tail(10))
```

### Indicator Interpretation Guide

**SMA vs EMA:**
- SMA reacts slowly to price changes (more stable but lags)
- EMA responds faster to recent price movements
- Golden Cross: Fast MA > Slow MA (bullish signal)
- Death Cross: Fast MA < Slow MA (bearish signal)

**RSI (Relative Strength Index):**
- 0-30: Oversold zone (potential buy opportunity)
- 30-70: Normal trading range
- 70-100: Overbought zone (potential sell opportunity)
- Divergences: Price makes new high/low but RSI doesn't (reversal signal)

**MACD (Moving Average Convergence Divergence):**
- Positive histogram: Bullish momentum (MACD > Signal)
- Negative histogram: Bearish momentum (MACD < Signal)
- Zero line crossover: Trend change signal
- Peak/trough: Momentum strengthening/weakening

---

## Time Split Module (`time_split.py`)

Time-based train/test split utilities for properly handling time series data.

### Functions Available

#### `split_train_test_time(df, test_size=0.2, date_col="Date")`
Splits a DataFrame chronologically so the newest rows are the test set.

**Parameters:**
- `df` (pd.DataFrame): Input DataFrame to split
- `test_size` (float, default=0.2): Fraction of data to use as test set (0-1)
- `date_col` (str, default="Date"): Column name containing dates

**Returns:**
- `train_df` (pd.DataFrame): Training set containing oldest rows
- `test_df` (pd.DataFrame): Test set containing newest rows

**Features:**
- Automatically sorts by date if date column exists
- Ensures proper temporal ordering for time series
- Validates split index is valid

**Example:**
```python
from time_split import split_train_test_time
import pandas as pd

# Load data
df = pd.read_csv('bitcoin_data.csv')

# Split 80% train, 20% test
train, test = split_train_test_time(df, test_size=0.2, date_col='Date')
print(f"Train size: {len(train)}, Test size: {len(test)}")
```

#### `split_dataset_dict_time(dataset_dict, test_size=0.2, date_col="Date")`
Applies time-based split to every DataFrame in a dictionary.

**Parameters:**
- `dataset_dict` (dict): Dictionary where values are DataFrames to split
- `test_size` (float, default=0.2): Fraction of data to use as test set
- `date_col` (str, default="Date"): Column name containing dates

**Returns:**
- `split_data` (dict): Dictionary with structure `{name: {'train': df_train, 'test': df_test}, ...}`

**Example:**
```python
from time_split import split_dataset_dict_time

# Assume crypto_data is a dict of DataFrames
split_data = split_dataset_dict_time(crypto_data, test_size=0.2)

# Access split data
bitcoin_train = split_data['bitcoin_cleaned']['train']
bitcoin_test = split_data['bitcoin_cleaned']['test']
```

---

## Time Series Analysis Module (`time_series_analysis.py`)

Functions for calculating returns, volatility, trends, and other time series metrics.

### Functions Available

#### `calculate_returns(crypto_data)`
Calculate daily, weekly, and monthly returns for each cryptocurrency.

**Parameters:**
- `crypto_data` (dict): Dictionary of DataFrames containing cryptocurrency data

**Returns:**
- `dict`: Updated crypto_data dictionary with columns added:
  - `Daily_Return`: Percentage change from previous day
  - `Weekly_Return`: Percentage change over 7 days
  - `Monthly_Return`: Percentage change over 30 days

**Example:**
```python
from time_series_analysis import calculate_returns

crypto_data = calculate_returns(crypto_data)

# Access returns
returns = crypto_data['bitcoin_cleaned'][['Date', 'Close', 'Daily_Return', 'Weekly_Return']]
print(returns.head())
```

#### `calculate_volatility(crypto_data, window=30)`
Calculate rolling volatility (standard deviation of returns).

**Parameters:**
- `crypto_data` (dict): Dictionary of DataFrames containing cryptocurrency data
- `window` (int, default=30): Rolling window size in days

**Returns:**
- `dict`: Updated crypto_data dictionary with column `Volatility_{window}` added

**Example:**
```python
from time_series_analysis import calculate_volatility

# Calculate 30-day rolling volatility
crypto_data = calculate_volatility(crypto_data, window=30)

# Calculate 60-day volatility
crypto_data = calculate_volatility(crypto_data, window=60)
```

#### `get_volatility_summary(crypto_data, window=30)`
Generate summary statistics for volatility across all cryptocurrencies.

**Parameters:**
- `crypto_data` (dict): Dictionary of DataFrames containing cryptocurrency data
- `window` (int, default=30): Rolling window size in days

**Returns:**
- `pd.DataFrame`: Summary statistics sorted by mean volatility, with columns:
  - `Mean_Volatility`: Average volatility across entire period
  - `Max_Volatility`: Peak volatility observed
  - `Min_Volatility`: Lowest volatility observed
  - `Current_Volatility`: Most recent volatility value

**Example:**
```python
from time_series_analysis import get_volatility_summary

volatility_summary = get_volatility_summary(crypto_data, window=30)
print(volatility_summary)
# Shows: Bitcoin, Ethereum, Cardano ranked by volatility
```

#### `calculate_trend_analysis(crypto_data)`
Calculate trend using linear regression for each cryptocurrency.

**Parameters:**
- `crypto_data` (dict): Dictionary of DataFrames containing cryptocurrency data

**Returns:**
- `dict`: Updated crypto_data dictionary with trend-related columns added

---

## Model Helpers Module (`model_helpers.py`)

Functions for preparing model predictions and calculating trading performance metrics.

### Functions Available

#### `unscale_predictions(y_pred_scaled, close_price_mean, close_price_std)`
Convert scaled model predictions back to actual price values.

**IMPORTANT:** The mean and std MUST be from the original (unscaled) training data, NOT from scaled data.

**Parameters:**
- `y_pred_scaled` (array-like): Scaled predictions from the model (values with mean~0, std~1)
- `close_price_mean` (float): Mean of Close prices from original training data
- `close_price_std` (float): Standard deviation of Close prices from original training data

**Returns:**
- `np.ndarray`: Unscaled predictions in actual dollar amounts

**Formula:**
```
unscaled_value = (scaled_value * std) + mean
```

**Example:**
```python
from model_helpers import unscale_predictions
import numpy as np

# Get original statistics from unscaled training data
close_mean = unscaled_train_df['Close'].mean()
close_std = unscaled_train_df['Close'].std()

# Unscale model predictions
y_pred_unscaled = unscale_predictions(y_pred_scaled, close_mean, close_std)
print(f"Prediction range: ${y_pred_unscaled.min():.2f} - ${y_pred_unscaled.max():.2f}")
```

#### `calculate_trading_profit(y_pred_unscaled, open_prices, close_actual=None)`
Calculate trading profit from unscaled model predictions.

**Strategy:** Buy at market open price each day, sell at model's predicted close price.

**Parameters:**
- `y_pred_unscaled` (array-like): Unscaled model predictions (actual predicted close prices in $)
- `open_prices` (array-like): Actual opening prices for each day (entry price)
- `close_actual` (array-like, optional): Actual closing prices (for reference only)

**Returns:**
- `dict`: Dictionary containing:
  - `daily_profits`: Array of daily profits (predicted_close - open_price)
  - `total_profit`: Sum of all daily profits ($)
  - `total_return_%`: Total return as percentage of first day's open price
  - `num_trading_days`: Number of days traded
  - `mape_error`: Mean Absolute Percentage Error
  - Additional metrics for performance evaluation

**Example:**
```python
from model_helpers import calculate_trading_profit

pred_prices = [100.5, 102.3, 99.8, 103.2]
open_prices = [99.0, 101.5, 98.5, 102.0]

results = calculate_trading_profit(pred_prices, open_prices)
print(f"Total Profit: ${results['total_profit']:.2f}")
print(f"Total Return: {results['total_return_%']:.2f}%")
print(f"Prediction Error: {results['mape_error']:.2f}%")
```

---

## P&L Visualization Module (`pnl_visualization.py`)

Functions for visualizing trading model profit and loss performance.

### Functions Available

#### `plot_pnl_comparison(model_daily_pnl, model_cumulative_pnl, bh_baseline, profit_diff, crypto_name, model_name="Linear Regression", figsize=(14, 10))`
Create a comprehensive P&L visualization comparing model performance vs Buy & Hold baseline.

**Parameters:**
- `model_daily_pnl` (np.ndarray): Daily profit/loss array for the model trading strategy
- `model_cumulative_pnl` (np.ndarray): Cumulative profit/loss array
- `bh_baseline` (float): Total profit from Buy & Hold baseline strategy
- `profit_diff` (float): Difference between model profit and baseline profit
- `crypto_name` (str): Name of cryptocurrency being analyzed
- `model_name` (str, default="Linear Regression"): Model name for chart labels
- `figsize` (tuple, default=(14, 10)): Figure size (width, height) in inches

**Returns:**
- `fig` (matplotlib.figure.Figure): The figure object containing both plots
- `axes` (np.ndarray): Array of axes objects

**Visualizations:**
- **Top panel:** Cumulative P&L comparison with model vs Buy & Hold traces
- **Bottom panel:** Daily P&L bar chart with profit/loss color coding

**Example:**
```python
from pnl_visualization import plot_pnl_comparison
import matplotlib.pyplot as plt

fig, axes = plot_pnl_comparison(
    model_daily_pnl, 
    model_cumulative_pnl,
    bh_baseline=50000,
    profit_diff=13534.68,
    crypto_name='bitcoin',
    model_name='Linear Regression'
)
plt.show()
```

#### `print_pnl_summary(model_daily_pnl, model_cumulative_pnl, bh_baseline, profit_diff, crypto_name, model_name="Linear Regression")`
Print a detailed P&L analysis summary comparing model vs Buy & Hold.

**Parameters:**
- `model_daily_pnl` (np.ndarray): Daily profit/loss array for the model trading strategy
- `model_cumulative_pnl` (np.ndarray): Cumulative profit/loss array
- `bh_baseline` (float): Total profit from Buy & Hold baseline strategy
- `profit_diff` (float): Difference between model profit and baseline profit
- `crypto_name` (str): Name of cryptocurrency being analyzed
- `model_name` (str, default="Linear Regression"): Model name for labels

**Returns:**
- `None` (Prints summary to console)

**Output includes:**
- Total profit and return percentage
- Comparison to Buy & Hold baseline
- Number of profitable vs losing days
- Average daily P&L
- Outperformance metrics

**Example:**
```python
from pnl_visualization import print_pnl_summary

print_pnl_summary(
    model_daily_pnl,
    model_cumulative_pnl,
    bh_baseline=50000,
    profit_diff=13534.68,
    crypto_name='bitcoin',
    model_name='Linear Regression'
)

# Output:
# ================================================================================
# P&L Analysis Summary: Linear Regression - BITCOIN
# ================================================================================
# Total Profit:                 $13,534.68
# Total Return:                 27.07%
# Buy & Hold Baseline:          $50,000.00
# Model Outperformance:         $13,534.68 (✓ BEAT)
# Profitable Days:              45/60 (75%)
# Losing Days:                  15/60 (25%)
# Average Daily P&L:            $225.58
```

#### `analyze_and_plot_pnl(model_daily_pnl, model_cumulative_pnl, bh_baseline, profit_diff, crypto_name, model_name="Linear Regression")`
Combined function that both visualizes and prints P&L analysis summary.

**Parameters:** Same as above two functions

**Returns:**
- `fig` (matplotlib.figure.Figure): The figure object
- `axes` (np.ndarray): Array of axes objects

**Example:**
```python
from pnl_visualization import analyze_and_plot_pnl

fig, axes = analyze_and_plot_pnl(
    model_daily_pnl,
    model_cumulative_pnl,
    bh_baseline=50000,
    profit_diff=13534.68,
    crypto_name='bitcoin'
)
plt.show()
```

---

## Complete Workflow Example

```python
import sys
sys.path.append('./helpers')
from helpers import (load_data_csv_files, plot_crypto_prices, plot_histograms, 
                     plot_boxplots, get_correlation_matrix, plot_correlation_heatmap, 
                     perform_statistical_tests)
from indicators import (calculate_sma_ema, plot_sma_ema,
                       calculate_rsi_for_cryptos, plot_rsi,
                       calculate_macd_for_cryptos, plot_macd)
from time_split import split_dataset_dict_time
from time_series_analysis import calculate_returns, calculate_volatility, get_volatility_summary
from model_helpers import unscale_predictions, calculate_trading_profit
from pnl_visualization import plot_pnl_comparison, print_pnl_summary

# 1. Load data
crypto_data = load_data_csv_files('../data/interim/')
print(f"Loaded {len(crypto_data)} cryptocurrencies")

# 2. Time-based train/test split
split_data = split_dataset_dict_time(crypto_data, test_size=0.2)

# 3. Time series analysis
crypto_data = calculate_returns(crypto_data)
crypto_data = calculate_volatility(crypto_data, window=30)
volatility_summary = get_volatility_summary(crypto_data)
print(volatility_summary)

# 4. Data exploration
plot_crypto_prices(crypto_data, plot_type='normalized')
plot_histograms(crypto_data)
plot_boxplots(crypto_data)

# 5. Correlation analysis
corr_matrix = get_correlation_matrix(crypto_data)
plot_correlation_heatmap(crypto_data)

# 6. Statistical testing
results = perform_statistical_tests(crypto_data)
print(results.head(20))

# 7. Technical indicator analysis (on selected cryptos)
selected = list(crypto_data.keys())[:5]
crypto_data = calculate_sma_ema(crypto_data, selected_cryptos=selected)
crypto_data = calculate_rsi_for_cryptos(crypto_data, selected_cryptos=selected)
crypto_data = calculate_macd_for_cryptos(crypto_data, selected_cryptos=selected)

# 8. Visualize indicators
plot_sma_ema(crypto_data, selected_cryptos=selected)
plot_rsi(crypto_data, selected_cryptos=selected)
plot_macd(crypto_data, selected_cryptos=selected)

# 9. Model workflow example
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import numpy as np

# Get Bitcoin training data
bitcoin_train = split_data['bitcoin_cleaned']['train']
bitcoin_test = split_data['bitcoin_cleaned']['test']

# Prepare features and target
feature_cols = [col for col in bitcoin_train.columns if col not in ['Date', 'Close']]
X_train = bitcoin_train[feature_cols].values
y_train = bitcoin_train['Close'].values
X_test = bitcoin_test[feature_cols].values
y_test = bitcoin_test['Close'].values

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train model
model = LinearRegression()
model.fit(X_train_scaled, y_train)

# Make predictions
y_pred_scaled = model.predict(X_test_scaled)

# Unscale predictions
close_mean = bitcoin_train['Close'].mean()
close_std = bitcoin_train['Close'].std()
y_pred_unscaled = unscale_predictions(y_pred_scaled, close_mean, close_std)

# Calculate trading profit
open_prices = bitcoin_test['Open'].values
results = calculate_trading_profit(y_pred_unscaled, open_prices)

print(f"Model Profit: ${results['total_profit']:.2f}")
print(f"Model Return: {results['total_return_%']:.2f}%")

# 10. Visualize P&L performance
model_daily_pnl = y_pred_unscaled - open_prices
model_cumulative_pnl = np.cumsum(model_daily_pnl)
bh_baseline = bitcoin_test['Close'].iloc[-1] - bitcoin_test['Open'].iloc[0]
profit_diff = model_cumulative_pnl[-1] - bh_baseline

fig, axes = plot_pnl_comparison(
    model_daily_pnl, 
    model_cumulative_pnl, 
    bh_baseline, 
    profit_diff, 
    'bitcoin'
)
plt.show()

# Print summary
print_pnl_summary(model_daily_pnl, model_cumulative_pnl, 
                  bh_baseline, profit_diff, 'bitcoin')
```

---

## Summary

This helpers module provides a comprehensive toolkit for cryptocurrency analysis, including:

- **Data Loading & Exploration** - Quick import and visualization of multiple datasets
- **Statistical Analysis** - Correlation, distributions, and hypothesis testing
- **Technical Indicators** - SMA, EMA, RSI, MACD calculations and visualizations
- **Time Series Analysis** - Returns, volatility, and trend calculations
- **Time-Based Splitting** - Proper temporal train/test splits
- **Model Development** - Prediction unscaling and trading profit calculations
- **P&L Visualization** - Comprehensive performance comparison and reporting

All modules are designed to work together seamlessly for end-to-end cryptocurrency price prediction and analysis workflows.
