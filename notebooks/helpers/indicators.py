"""
Technical Indicators Module
Functions for calculating and plotting technical indicators (SMA, EMA, RSI, MACD)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def calculate_sma_ema(crypto_data, selected_cryptos=None, sma_periods=[7, 20, 50], ema_periods=[7, 20, 50]):
    """
    Calculate Simple Moving Average (SMA) and Exponential Moving Average (EMA).
    
    Parameters:
    -----------
    crypto_data : dict
        Dictionary of DataFrames containing cryptocurrency data
    selected_cryptos : list, optional
        List of crypto names to calculate for. If None, uses all cryptos.
    sma_periods : list, default=[7, 20, 50]
        Periods for SMA calculation
    ema_periods : list, default=[7, 20, 50]
        Periods for EMA calculation
    
    Returns:
    --------
    dict
        Updated crypto_data dictionary with SMA and EMA columns added
    """
    if selected_cryptos is None:
        selected_cryptos = list(crypto_data.keys())
    
    for crypto_name in selected_cryptos:
        df = crypto_data[crypto_name].copy()
        
        # Calculate SMA
        for period in sma_periods:
            df[f"SMA_{period}"] = df["Close"].rolling(window=period).mean()
        
        # Calculate EMA
        for period in ema_periods:
            df[f"EMA_{period}"] = df["Close"].ewm(span=period, adjust=False).mean()
        
        crypto_data[crypto_name] = df
    
    print(f"SMA and EMA calculated for {len(selected_cryptos)} cryptocurrencies")
    return crypto_data


def plot_sma_ema(crypto_data, selected_cryptos=None, sma_periods=[7, 20, 50], ema_periods=[7, 20]):
    """
    Plot SMA and EMA trends for selected cryptocurrencies.
    
    Parameters:
    -----------
    crypto_data : dict
        Dictionary of DataFrames containing cryptocurrency data
    selected_cryptos : list, optional
        List of crypto names to plot. If None, uses all cryptos.
    sma_periods : list, default=[7, 20, 50]
        Periods to plot for SMA
    ema_periods : list, default=[7, 20]
        Periods to plot for EMA
    
    Returns:
    --------
    None (displays plots)
    """
    if selected_cryptos is None:
        selected_cryptos = list(crypto_data.keys())
    
    for crypto_name in selected_cryptos:
        df = crypto_data[crypto_name]
        
        plt.figure(figsize=(14, 7))
        
        # Plot price
        plt.plot(df["Date"], df["Close"], label="Close Price", linewidth=2, alpha=0.7, color="black")
        
        # Plot SMA
        for period in sma_periods:
            if f"SMA_{period}" in df.columns:
                plt.plot(df["Date"], df[f"SMA_{period}"], label=f"SMA-{period}", alpha=0.7, linestyle="--")
        
        # Plot EMA
        for period in ema_periods:
            if f"EMA_{period}" in df.columns:
                plt.plot(df["Date"], df[f"EMA_{period}"], label=f"EMA-{period}", alpha=0.7, linestyle="-.")
        
        plt.title(f"{crypto_name.upper()} - Simple Moving Average (SMA) vs Exponential Moving Average (EMA)")
        plt.xlabel("Date")
        plt.ylabel("Price ($)")
        plt.legend(loc="best", fontsize=8)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()


def calculate_rsi(prices, period=14):
    """
    Calculate Relative Strength Index (RSI).
    
    RSI = 100 - (100 / (1 + RS))
    RS = Average Gain / Average Loss
    
    Range: 0-100
    - >70: Overbought (potential sell signal)
    - <30: Oversold (potential buy signal)
    
    Parameters:
    -----------
    prices : array-like
        Price data (typically closing prices)
    period : int, default=14
        Period for RSI calculation
    
    Returns:
    --------
    np.ndarray
        RSI values
    """
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 0
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - 100. / (1. + rs)
    
    for i in range(period, len(prices)):
        delta = deltas[i-1]
        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta
        
        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period
        
        rs = up / down if down != 0 else 0
        rsi[i] = 100. - 100. / (1. + rs)
    
    return rsi


def calculate_rsi_for_cryptos(crypto_data, selected_cryptos=None, period=14):
    """
    Calculate RSI for selected cryptocurrencies.
    
    Parameters:
    -----------
    crypto_data : dict
        Dictionary of DataFrames containing cryptocurrency data
    selected_cryptos : list, optional
        List of crypto names. If None, uses all cryptos.
    period : int, default=14
        RSI period
    
    Returns:
    --------
    dict
        Updated crypto_data dictionary with RSI column added
    """
    if selected_cryptos is None:
        selected_cryptos = list(crypto_data.keys())
    
    for crypto_name in selected_cryptos:
        df = crypto_data[crypto_name]
        df[f"RSI_{period}"] = calculate_rsi(df["Close"].values, period=period)
        crypto_data[crypto_name] = df
    
    print(f"RSI-{period} calculated for {len(selected_cryptos)} cryptocurrencies")
    return crypto_data


def plot_rsi(crypto_data, selected_cryptos=None, period=14):
    """
    Plot RSI indicator with overbought/oversold zones.
    
    Parameters:
    -----------
    crypto_data : dict
        Dictionary of DataFrames containing cryptocurrency data
    selected_cryptos : list, optional
        List of crypto names to plot. If None, uses first 3 cryptos.
    period : int, default=14
        RSI period (used for column name)
    
    Returns:
    --------
    None (displays plots)
    """
    if selected_cryptos is None:
        selected_cryptos = list(crypto_data.keys())[:3]
    
    for crypto_name in selected_cryptos:
        df = crypto_data[crypto_name]
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), gridspec_kw={"height_ratios": [2, 1]})
        
        # Price
        ax1.plot(df["Date"], df["Close"], linewidth=2, color="steelblue")
        ax1.set_title(f"{crypto_name.upper()} - Price")
        ax1.set_ylabel("Price ($)")
        ax1.grid(True, alpha=0.3)
        
        # RSI
        rsi_col = f"RSI_{period}"
        if rsi_col in df.columns:
            ax2.plot(df["Date"], df[rsi_col], linewidth=2, color="orange", label=f"RSI-{period}")
            ax2.axhline(70, color="red", linestyle="--", alpha=0.7, label="Overbought (70)")
            ax2.axhline(30, color="green", linestyle="--", alpha=0.7, label="Oversold (30)")
            ax2.fill_between(df["Date"], 70, 100, alpha=0.1, color="red")
            ax2.fill_between(df["Date"], 0, 30, alpha=0.1, color="green")
            ax2.set_title("RSI (Relative Strength Index)")
            ax2.set_ylabel("RSI")
            ax2.set_xlabel("Date")
            ax2.legend(loc="best")
            ax2.set_ylim([0, 100])
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()


def calculate_macd(prices, fast=12, slow=26, signal=9):
    """
    Calculate MACD (Moving Average Convergence Divergence).
    
    MACD Line = EMA(12) - EMA(26)
    Signal Line = EMA(9) of MACD Line
    Histogram = MACD Line - Signal Line
    
    Parameters:
    -----------
    prices : array-like
        Price data (typically closing prices)
    fast : int, default=12
        Fast EMA period
    slow : int, default=26
        Slow EMA period
    signal : int, default=9
        Signal line EMA period
    
    Returns:
    --------
    tuple
        (macd_line, signal_line, histogram) as pandas Series
    """
    ema_fast = pd.Series(prices).ewm(span=fast, adjust=False).mean()
    ema_slow = pd.Series(prices).ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def calculate_macd_for_cryptos(crypto_data, selected_cryptos=None, fast=12, slow=26, signal=9):
    """
    Calculate MACD for selected cryptocurrencies.
    
    Parameters:
    -----------
    crypto_data : dict
        Dictionary of DataFrames containing cryptocurrency data
    selected_cryptos : list, optional
        List of crypto names. If None, uses all cryptos.
    fast : int, default=12
        Fast EMA period
    slow : int, default=26
        Slow EMA period
    signal : int, default=9
        Signal line EMA period
    
    Returns:
    --------
    dict
        Updated crypto_data dictionary with MACD columns added
    """
    if selected_cryptos is None:
        selected_cryptos = list(crypto_data.keys())
    
    for crypto_name in selected_cryptos:
        df = crypto_data[crypto_name]
        macd, signal_line, histogram = calculate_macd(df["Close"].values, fast=fast, slow=slow, signal=signal)
        df["MACD"] = macd.values
        df["MACD_Signal"] = signal_line.values
        df["MACD_Histogram"] = histogram.values
        crypto_data[crypto_name] = df
    
    print(f"MACD calculated for {len(selected_cryptos)} cryptocurrencies")
    return crypto_data


def plot_macd(crypto_data, selected_cryptos=None):
    """
    Plot MACD indicator with signal line and histogram.
    
    Parameters:
    -----------
    crypto_data : dict
        Dictionary of DataFrames containing cryptocurrency data
    selected_cryptos : list, optional
        List of crypto names to plot. If None, uses all cryptos.
    
    Returns:
    --------
    None (displays plots)
    """
    if selected_cryptos is None:
        selected_cryptos = list(crypto_data.keys())
    
    for crypto_name in selected_cryptos:
        df = crypto_data[crypto_name]
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), gridspec_kw={"height_ratios": [2, 1]})
        
        # Price
        ax1.plot(df["Date"], df["Close"], linewidth=2, color="steelblue")
        ax1.set_title(f"{crypto_name.upper()} - Price")
        ax1.set_ylabel("Price ($)")
        ax1.grid(True, alpha=0.3)
        
        # MACD
        if "MACD" in df.columns:
            ax2.plot(df["Date"], df["MACD"], linewidth=2, label="MACD", color="blue")
            ax2.plot(df["Date"], df["MACD_Signal"], linewidth=2, label="Signal", color="red")
            ax2.bar(df["Date"], df["MACD_Histogram"], label="Histogram", alpha=0.3, color="gray")
            ax2.axhline(0, color="black", linestyle="-", alpha=0.3)
            ax2.set_title("MACD (Moving Average Convergence Divergence)")
            ax2.set_ylabel("MACD Value")
            ax2.set_xlabel("Date")
            ax2.legend(loc="best")
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
