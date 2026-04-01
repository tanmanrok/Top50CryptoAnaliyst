# Top 50 Cryptocurrency Price Prediction  

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>

## Project Overview

This project develops machine learning models to predict future cryptocurrency prices using comprehensive exploratory data analysis (EDA) and time series forecasting techniques. The analysis focuses on the top 50 cryptocurrencies by market capitalization, examining their historical price trends, volatility patterns, and key technical indicators.

## Objectives

1. **Exploratory Data Analysis**: Thoroughly investigate cryptocurrency price data including distributions, correlations, and statistical properties
2. **Feature Engineering**: Calculate technical indicators (SMA, EMA, RSI, MACD) and time series metrics (returns, volatility, trends)
3. **Feature Selection**: Identify the best cryptocurrency candidates based on risk-adjusted returns (Sharpe Ratio), trend strength, and win rates
4. **Data Preparation**: Clean and preprocess data for downstream modeling
5. **Price Prediction**: Build time series forecasting models to predict future cryptocurrency prices

## Key Analysis Components

### Exploratory Data Analysis (EDA)
- **Univariate Analysis**: Histograms and box plots for individual features
- **Bivariate Analysis**: Correlation matrices and heatmaps to identify relationships
- **Statistical Testing**: 
  - Kolmogorov-Smirnov test (normality)
  - Pearson correlation test (significance)
  - Levene's test (variance homogeneity)
  - Mann-Whitney U test (distribution comparison)

### Technical Indicators
- **SMA (Simple Moving Average)**: 7, 20, and 50-day moving averages
- **EMA (Exponential Moving Average)**: 20-day exponential moving average
- **RSI (Relative Strength Index)**: 14-period momentum oscillator (0-100 scale)
- **MACD**: Moving Average Convergence Divergence for trend identification

### Time Series Analysis
- **Daily/Weekly/Monthly Returns**: Percentage price changes at multiple timeframes
- **Volatility**: 30-day rolling standard deviation
- **Trend Analysis**: Linear regression slopes to identify uptrends vs downtrends
- **Sharpe Ratio**: Risk-adjusted return metric
- **Win Rate**: Percentage of positive return days

## Feature Selection Strategy

The final model candidates are selected using a **combined ranking matrix** that balances:
1. **Sharpe Ratio** (risk-adjusted returns): Higher is better
2. **Trend Strength** (absolute slope): Stronger directional movement is better
3. **Win Rate**: Higher percentage of positive return days is better
4. **Volatility Profile**: Categorized as Low/Medium/High Risk for strategy matching


## Project Organization

```
├── LICENSE            <- Open-source license if one is chosen
├── Makefile           <- Makefile with convenience commands like `make data` or `make train`
├── README.md          <- The top-level README for developers using this project.
├── data
│   ├── external       <- Data from third party sources.
│   ├── interim        <- Intermediate data that has been transformed.
│   ├── processed      <- The final, canonical data sets for modeling.
│   └── raw            <- The original, immutable data dump.
│
├── docs               <- A default mkdocs project; see www.mkdocs.org for details
│
├── models             <- Trained and serialized models, model predictions, or model summaries
│
├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
│   └── helpers           the creator's initials, and a short `-` delimited description, e.g.
│                         `1.0-jqp-initial-data-exploration`.
│                         
│
├── pyproject.toml     <- Project configuration file with package metadata for 
│                         Top50CyrptoAnaliyst and configuration for tools like black
│
├── references         <- Data dictionaries, manuals, and all other explanatory materials.
│
├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
│   └── figures        <- Generated graphics and figures to be used in reporting
│
├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
│                         generated with `pip freeze > requirements.txt`
│
├── setup.cfg          <- Configuration file for flake8
│
└── Top50CyrptoAnaliyst   <- Source code for use in this project.
    │
    ├── __init__.py             <- Makes Top50CyrptoAnaliyst a Python module
    │
    ├── config.py               <- Store useful variables and configuration
    │
    ├── dataset.py              <- Scripts to download or generate data
    │
    ├── features.py             <- Code to create features for modeling
    │
    ├── modeling                
    │   ├── __init__.py 
    │   ├── predict.py          <- Code to run model inference with trained models          
    │   └── train.py            <- Code to train models
    │
    └── plots.py                <- Code to create visualizations
```

## How It Works

1. **Data Loading**: Load OHLCV (Open, High, Low, Close, Volume) data for 50 cryptocurrencies
2. **Feature Calculation**: 
   - Compute technical indicators (SMA, EMA, RSI, MACD)
   - Calculate time series metrics (returns, volatility, trends)
3. **Statistical Analysis**: Apply statistical tests to identify feature relationships and significance
4. **Feature Ranking**: Use combined scoring (Sharpe Ratio, Trend Strength, Win Rate) to rank cryptocurrencies
5. **Data Export**: Save top 15 cryptos with all features to CSV files for modeling

## Helper Modules

- **`helpers.py`**: Data loading, visualization, correlation analysis
- **`indicators.py`**: Technical indicator calculations
- **`time_series_analysis.py`**: Time series metrics (returns, volatility, trends, Sharpe ratio)

## Performance Metrics Used

- **Sharpe Ratio**: Risk-adjusted return metric (return / volatility)
- **Trend Slope**: Direction and strength of price movement via linear regression
- **R-squared**: How well trend line fits the data (0-1 scale)
- **Win Rate**: Percentage of days with positive returns
- **Volatility**: 30-day rolling standard deviation

## Acknowledgments

- Data source: Historical cryptocurrency price data
- Project template: Cookiecutter Data Science
- Built with pandas, scikit-learn, and jupyter

