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

# 1. Load data
crypto_data = load_data_csv_files('../data/interim/')
print(f"Loaded {len(crypto_data)} cryptocurrencies")

# 2. Data exploration
plot_crypto_prices(crypto_data, plot_type='normalized')
plot_histograms(crypto_data)
plot_boxplots(crypto_data)

# 3. Correlation analysis
corr_matrix = get_correlation_matrix(crypto_data)
plot_correlation_heatmap(crypto_data)

# 4. Statistical testing
results = perform_statistical_tests(crypto_data)
print(results.head(20))

# 5. Technical indicator analysis (on selected cryptos)
selected = list(crypto_data.keys())[:5]
crypto_data = calculate_sma_ema(crypto_data, selected_cryptos=selected)
crypto_data = calculate_rsi_for_cryptos(crypto_data, selected_cryptos=selected)
crypto_data = calculate_macd_for_cryptos(crypto_data, selected_cryptos=selected)

# 6. Visualize indicators
plot_sma_ema(crypto_data, selected_cryptos=selected)
plot_rsi(crypto_data, selected_cryptos=selected)
plot_macd(crypto_data, selected_cryptos=selected)
```
- `plot_sma_ema(crypto_data, selected_cryptos=None, sma_periods=[7, 20, 50], ema_periods=[7, 20])`
  - Visualizes price with multiple moving averages
  - Shows trend identification and smoothing effects

#### RSI Calculation
- `calculate_rsi(prices, period=14)`
  - Calculates Relative Strength Index (momentum indicator)
  - Returns array of RSI values (0-100 range)
  - >70: Overbought | <30: Oversold

- `calculate_rsi_for_cryptos(crypto_data, selected_cryptos=None, period=14)`
  - Wrapper to calculate RSI for multiple cryptocurrencies
  - Adds RSI column to each DataFrame

#### RSI Plotting
- `plot_rsi(crypto_data, selected_cryptos=None, period=14)`
  - Displays price with RSI indicator below
  - Shows overbought (red) and oversold (green) zones
  - Signal zones help identify trading opportunities

#### MACD Calculation
- `calculate_macd(prices, fast=12, slow=26, signal=9)`
  - Calculates Moving Average Convergence Divergence
  - MACD Line = EMA(12) - EMA(26)
  - Signal Line = EMA(9) of MACD
  - Histogram = MACD - Signal (momentum)
  - Returns (macd_line, signal_line, histogram)

- `calculate_macd_for_cryptos(crypto_data, selected_cryptos=None, fast=12, slow=26, signal=9)`
  - Wrapper to calculate MACD for multiple cryptocurrencies
  - Adds MACD, MACD_Signal, MACD_Histogram columns

#### MACD Plotting
- `plot_macd(crypto_data, selected_cryptos=None)`
  - Displays price with MACD indicator below
  - Shows MACD line, signal line, and histogram
  - Histogram bars indicate momentum direction

### Usage Example

```python
import sys
sys.path.append('./helpers')
from indicators import (calculate_sma_ema, plot_sma_ema, calculate_rsi_for_cryptos, plot_rsi,
                        calculate_macd_for_cryptos, plot_macd)

# Calculate and plot moving averages
crypto_data = calculate_sma_ema(crypto_data, selected_cryptos=['bitcoin_cleaned', 'ethereum_cleaned'])
plot_sma_ema(crypto_data, selected_cryptos=['bitcoin_cleaned', 'ethereum_cleaned'])

# Calculate and plot RSI
crypto_data = calculate_rsi_for_cryptos(crypto_data, selected_cryptos=['bitcoin_cleaned', 'ethereum_cleaned'])
plot_rsi(crypto_data, selected_cryptos=['bitcoin_cleaned', 'ethereum_cleaned'])

# Calculate and plot MACD
crypto_data = calculate_macd_for_cryptos(crypto_data, selected_cryptos=['bitcoin_cleaned', 'ethereum_cleaned'])
plot_macd(crypto_data, selected_cryptos=['bitcoin_cleaned', 'ethereum_cleaned'])
```

### Indicator Interpretation

| Indicator | Bullish Signal | Bearish Signal | Notes |
|-----------|---|---|---|
| **SMA** | Price above MA | Price below MA | Longer MA = stronger trend |
| **EMA** | Fast EMA > Slow EMA | Fast EMA < Slow EMA | Faster response than SMA |
| **RSI** | <30 (Oversold) | >70 (Overbought) | Oscillator: identifies extremes |
| **MACD** | Positive histogram | Negative histogram | Momentum indicator |
| **MACD Signal** | MACD > Signal | MACD < Signal | Crossovers indicate reversals |

---

```python
import sys
sys.path.append('./helpers')
from helpers import (load_data_csv_files, plot_crypto_prices, plot_histograms, 
                     plot_boxplots, get_correlation_matrix, plot_correlation_heatmap, 
                     perform_statistical_tests)

# 1. Load data
crypto_data = load_data_csv_files('../data/interim/')

# 2. Visualize price trends
plot_crypto_prices(crypto_data, plot_type='normalized')

# 3. Analyze distributions
plot_histograms(crypto_data)
plot_boxplots(crypto_data)

# 4. Check correlations
corr_matrix = get_correlation_matrix(crypto_data)
plot_correlation_heatmap(crypto_data)

# 5. Run statistical tests
results = perform_statistical_tests(crypto_data)
print(results[results['Test Type'] == 'K-S Test'].head())
```
