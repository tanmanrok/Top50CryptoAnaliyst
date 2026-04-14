"""
Model Helper Functions for Cryptocurrency Price Prediction
Handles unscaling predictions and calculating trading profits
"""

import numpy as np
import pandas as pd


def unscale_predictions(y_pred_scaled, close_price_mean, close_price_std):
    """
    Convert scaled model predictions back to actual price values.
    
    IMPORTANT: close_price_mean and close_price_std MUST be from original (unscaled) training data,
    NOT from the scaled training data.
    
    Parameters:
    -----------
    y_pred_scaled : array-like
        Scaled predictions from the model (e.g., values with mean~0, std~1)
    close_price_mean : float
        Mean of Close prices from ORIGINAL (unscaled) training data
    close_price_std : float
        Standard deviation of Close prices from ORIGINAL (unscaled) training data
    
    Returns:
    --------
    y_pred_unscaled : np.array
        Unscaled predictions in actual dollar amounts
    
    Formula:
    --------
    unscaled_value = (scaled_value * std) + mean
    
    Example:
    --------
    >>> # Get original statistics from unscaled data
    >>> unscaled_train_df = unscaled_test_dict['bitcoin_graph'].iloc[:split_idx]
    >>> orig_mean = unscaled_train_df['Close'].mean()
    >>> orig_std = unscaled_train_df['Close'].std()
    >>> # Then unscale
    >>> y_unscaled = unscale_predictions(y_pred_scaled, orig_mean, orig_std)
    """
    # Convert to numpy array
    y_pred_scaled = np.array(y_pred_scaled)
    
    # Unscale predictions using ORIGINAL statistics
    y_pred_unscaled = (y_pred_scaled * close_price_std) + close_price_mean
    
    return y_pred_unscaled


def calculate_trading_profit(y_pred_unscaled, open_prices, close_actual=None):
    """
    Calculate trading profit from unscaled model predictions.
    
    Strategy: Buy at market open price, sell at model's predicted close price each day.
    
    Parameters:
    -----------
    y_pred_unscaled : array-like
        Unscaled model predictions (actual predicted close prices in $)
    open_prices : array-like
        Actual opening prices for each day (entry price)
    close_actual : array-like, optional
        Actual closing prices (for reference/analysis only, not used in profit calculation)
    
    Returns:
    --------
    results : dict
        Dictionary containing:
        - 'daily_profits': array of daily profits (predicted_close - open_price)
        - 'total_profit': sum of all daily profits ($)
        - 'total_return_%': total return as percentage of first day's open price
        - 'num_trading_days': number of days traded
    
    Example:
    --------
    >>> pred = [100, 102, 99]  # Model predictions
    >>> opens = [99, 101, 98]   # Actual open prices
    >>> result = calculate_trading_profit(pred, opens)
    >>> print(f"Total Profit: ${result['total_profit']:.2f}")
    """
    # Convert to numpy arrays for calculation
    y_pred_unscaled = np.array(y_pred_unscaled)
    open_prices = np.array(open_prices)
    
    # Calculate daily profits: predicted_close - open_price
    daily_profits = y_pred_unscaled - open_prices
    total_profit = daily_profits.sum()
    
    # Calculate return percentage
    first_open = open_prices[0]
    total_return_pct = (total_profit / first_open * 100) if first_open != 0 else 0
    
    results = {
        'daily_profits': daily_profits,
        'total_profit': total_profit,
        'total_return_%': total_return_pct,
        'num_trading_days': len(open_prices),
        'avg_daily_profit': total_profit / len(open_prices)
    }
    
    # Add actual close data for reference if provided
    if close_actual is not None:
        close_actual = np.array(close_actual)
        results['close_actual'] = close_actual
        results['prediction_error'] = y_pred_unscaled - close_actual
        results['mape_error'] = np.mean(np.abs((close_actual - y_pred_unscaled) / close_actual)) * 100
    
    return results


def extract_unscaled_test_data(graph_data):
    """
    Extract unscaled test data (80/20 time split) from graph data.
    
    Parameters:
    -----------
    graph_data : dict
        Dictionary of unscaled DataFrames from graph folder
    
    Returns:
    --------
    unscaled_test_dict : dict
        Dictionary with unscaled test DataFrames for each cryptocurrency
        (last 20% of data by time)
    """
    unscaled_test_dict = {}
    
    for crypto_name, df in graph_data.items():
        # Sort by date
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date').reset_index(drop=True)
        
        # Get 80/20 split indices and extract test portion
        split_idx = int(len(df) * 0.8)
        test_df = df.iloc[split_idx:].reset_index(drop=True)
        
        unscaled_test_dict[crypto_name] = test_df
    
    return unscaled_test_dict


def calculate_buy_hold_baseline(unscaled_test_dict):
    """
    Calculate Buy & Hold baseline profit for each cryptocurrency.
    
    Strategy: Buy on first day (open), hold, sell on last day (close).
    
    Parameters:
    -----------
    unscaled_test_dict : dict
        Dictionary of unscaled test DataFrames
    
    Returns:
    --------
    buy_hold_baseline : dict
        Dictionary with Buy & Hold metrics for each cryptocurrency:
        - 'Entry': first day opening price
        - 'Exit': last day closing price
        - 'Profit': $ profit
        - 'Return_%': % return
    """
    buy_hold_baseline = {}
    
    for crypto_name, test_df in unscaled_test_dict.items():
        open_price = test_df['Open'].iloc[0]
        close_price = test_df['Close'].iloc[-1]
        profit = close_price - open_price
        return_pct = (profit / open_price * 100) if open_price != 0 else 0
        
        buy_hold_baseline[crypto_name] = {
            'Entry': open_price,
            'Exit': close_price,
            'Profit': profit,
            'Return_%': return_pct
        }
    
    return buy_hold_baseline
