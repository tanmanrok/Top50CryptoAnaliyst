# Technical Indicators Helper Module
import pandas as pd
import numpy as np


def add_technical_indicators(df):
    """
    Add all technical indicators to a dataframe.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with columns: Date, Close, High, Low, Open, Volume
    
    Returns:
    --------
    pd.DataFrame
        DataFrame with added technical indicators:
        - SMA_7, SMA_20, SMA_50 (Simple Moving Averages)
        - EMA_7, EMA_20, EMA_50 (Exponential Moving Averages)
        - RSI_14 (Relative Strength Index)
        - MACD, MACD_Signal, MACD_Histogram (Moving Average Convergence Divergence)
        - Daily_Return, Weekly_Return, Monthly_Return (Price returns)
        - Volatility_30 (30-day rolling standard deviation)
    """
    df = df.sort_values('Date').reset_index(drop=True)
    
    # Simple Moving Averages (SMA)
    df['SMA_7'] = df['Close'].rolling(window=7, min_periods=1).mean()
    df['SMA_20'] = df['Close'].rolling(window=20, min_periods=1).mean()
    df['SMA_50'] = df['Close'].rolling(window=50, min_periods=1).mean()
    
    # Exponential Moving Averages (EMA)
    df['EMA_7'] = df['Close'].ewm(span=7, adjust=False).mean()
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    
    # Relative Strength Index (RSI)
    def calculate_rsi(prices, period=14):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period, min_periods=1).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    df['RSI_14'] = calculate_rsi(df['Close'], period=14)
    
    # MACD (Moving Average Convergence Divergence)
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
    
    # Returns
    df['Daily_Return'] = df['Close'].pct_change() * 100
    df['Weekly_Return'] = df['Close'].pct_change(periods=7) * 100
    df['Monthly_Return'] = df['Close'].pct_change(periods=30) * 100
    
    # Volatility (30-day rolling standard deviation)
    df['Volatility_30'] = df['Close'].rolling(window=30, min_periods=1).std()
    
    return df


def validate_indicators(df, crypto_name):
    """
    Validate indicator calculations for data quality.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with calculated indicators
    crypto_name : str
        Name of the cryptocurrency (for reporting)
    
    Returns:
    --------
    list
        List of issues found during validation
    """
    issues = []
    
    # Check for unexpected NaN values (initial rows may have NaN which is OK)
    indicator_cols = [col for col in df.columns if col not in ['Date', 'Close', 'High', 'Low', 'Open', 'Volume']]
    
    for col in indicator_cols:
        nan_count = df[col].isna().sum()
        if nan_count > len(df) * 0.5:  # Flag if more than 50% NaN
            issues.append(f"{col}: {nan_count} NaN values ({nan_count/len(df)*100:.1f}%)")
    
    # Check data types
    for col in indicator_cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            issues.append(f"{col}: Not numeric type ({df[col].dtype})")
    
    # Check for infinite values
    for col in indicator_cols:
        if np.isinf(df[col]).any():
            issues.append(f"{col}: Contains infinite values")
    
    return issues
