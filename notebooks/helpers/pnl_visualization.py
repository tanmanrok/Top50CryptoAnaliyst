"""
P&L Visualization Helper Functions
Provides utilities for visualizing trading model profit & loss performance
"""

import numpy as np
import matplotlib.pyplot as plt


def plot_pnl_comparison(model_daily_pnl, model_cumulative_pnl, bh_baseline, profit_diff, 
                        crypto_name, model_name="Linear Regression", figsize=(14, 10)):
    """
    Create a comprehensive P&L visualization comparing model performance vs Buy & Hold baseline
    
    Parameters:
    -----------
    model_daily_pnl : np.ndarray
        Daily profit/loss array for the model trading strategy
    model_cumulative_pnl : np.ndarray
        Cumulative profit/loss array for the model
    bh_baseline : float
        Total profit from Buy & Hold baseline strategy
    profit_diff : float
        Difference between model profit and baseline profit
    crypto_name : str
        Name of cryptocurrency being analyzed
    model_name : str, optional
        Name of the model for chart labels. Default: "Linear Regression"
    figsize : tuple, optional
        Figure size (width, height) in inches. Default: (14, 10)
    
    Returns:
    --------
    fig : matplotlib.figure.Figure
        The figure object containing both plots
    axes : np.ndarray
        Array of axes objects
    
    Example:
    --------
    fig, axes = plot_pnl_comparison(model_daily_pnl, model_cumulative_pnl, 
                                     66524.87, 13534.68, 'bitcoin')
    plt.show()
    """
    
    # Create visualization
    fig, axes = plt.subplots(2, 1, figsize=figsize)
    
    # Plot 1: Cumulative P&L Comparison
    ax1 = axes[0]
    ax1.plot(model_cumulative_pnl, label=f'{model_name} Model', linewidth=2, 
             marker='o', markersize=3, alpha=0.7)
    ax1.axhline(y=bh_baseline, color='orange', linewidth=2, linestyle='--', 
                label='Buy & Hold Baseline')
    ax1.fill_between(range(len(model_cumulative_pnl)), model_cumulative_pnl, bh_baseline, 
                      where=(model_cumulative_pnl >= bh_baseline), alpha=0.2, color='green', 
                      label='Model Advantage')
    ax1.fill_between(range(len(model_cumulative_pnl)), model_cumulative_pnl, bh_baseline, 
                      where=(model_cumulative_pnl < bh_baseline), alpha=0.2, color='red', 
                      label='Model Disadvantage')
    ax1.set_title(f'Cumulative P&L: {model_name} vs Buy & Hold - {crypto_name.upper()}', 
                  fontsize=14, fontweight='bold')
    ax1.set_xlabel('Trading Days (Test Period)', fontsize=11)
    ax1.set_ylabel('Cumulative Profit ($)', fontsize=11)
    ax1.legend(loc='best', fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    
    # Plot 2: Daily P&L
    ax2 = axes[1]
    colors = ['green' if x > 0 else 'red' for x in model_daily_pnl]
    ax2.bar(range(len(model_daily_pnl)), model_daily_pnl, color=colors, alpha=0.6, 
            label='Daily Trade P&L')
    ax2.axhline(y=0, color='black', linewidth=0.8, linestyle='-')
    ax2.set_title(f'Daily P&L: Model Trading Strategy - {crypto_name.upper()}', 
                  fontsize=14, fontweight='bold')
    ax2.set_xlabel('Trading Days (Test Period)', fontsize=11)
    ax2.set_ylabel('Daily Profit/Loss ($)', fontsize=11)
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.legend(loc='best', fontsize=10)
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    
    plt.tight_layout()
    
    return fig, axes


def print_pnl_summary(model_daily_pnl, model_cumulative_pnl, bh_baseline, profit_diff, crypto_name, model_name="Linear Regression"):
    """
    Print a detailed P&L analysis summary comparing model vs Buy & Hold
    
    Parameters:
    -----------
    model_daily_pnl : np.ndarray
        Daily profit/loss array for the model trading strategy
    model_cumulative_pnl : np.ndarray
        Cumulative profit/loss array for the model
    bh_baseline : float
        Total profit from Buy & Hold baseline strategy
    profit_diff : float
        Difference between model profit and baseline profit
    crypto_name : str
        Name of cryptocurrency being analyzed
    model_name : str, optional
        Name of the model for summary labels. Default: "Linear Regression"
        Name of cryptocurrency being analyzed
    
    Example:
    --------
    print_pnl_summary(model_daily_pnl, model_cumulative_pnl, 66524.87, 13534.68, 'bitcoin')
    """
    
    print(f"\nP&L Analysis Summary - {crypto_name.upper()}:")
    print("="*80)
    print(f"Model - Profitable Days:   {(model_daily_pnl > 0).sum()} out of {len(model_daily_pnl)} "
          f"({(model_daily_pnl > 0).sum()/len(model_daily_pnl)*100:.1f}%)")
    print(f"Model - Avg Daily P&L:     ${model_daily_pnl.mean():,.2f}")
    print(f"Model - Max Daily Profit:  ${model_daily_pnl.max():,.2f}")
    print(f"Model - Max Daily Loss:    ${model_daily_pnl.min():,.2f}")
    print(f"Model - Cumulative P&L:    ${model_cumulative_pnl[-1]:,.2f}")
    print(f"\nBuy & Hold - Final P&L:    ${bh_baseline:,.2f}")
    print(f"\nOutperformance:            ${profit_diff:,.2f} ({(profit_diff/bh_baseline)*100:.2f}%)")


def analyze_and_plot_pnl(model_daily_pnl, open_prices, close_actual, y_pred_unscaled,
                         bh_baseline, crypto_name, show_plot=True):
    """
    Complete P&L analysis: calculate metrics, plot comparison, and print summary
    Convenience function that wraps the individual visualization functions
    
    Parameters:
    -----------
    model_daily_pnl : np.ndarray
        Daily profit/loss array for the model trading strategy
    open_prices : np.ndarray
        Array of opening prices for the test period
    close_actual : np.ndarray
        Array of actual closing prices for the test period
    y_pred_unscaled : np.ndarray
        Unscaled model predictions (predicted closing prices)
    bh_baseline : float
        Total profit from Buy & Hold baseline strategy
    crypto_name : str
        Name of cryptocurrency being analyzed
    show_plot : bool, optional
        Whether to display the plot. Default: True
    
    Returns:
    --------
    model_cumulative_pnl : np.ndarray
        Cumulative profit/loss array for reference
    profit_diff : float
        Outperformance relative to Buy & Hold (model_profit - bh_baseline)
    
    Example:
    --------
    cumulative_pnl, outperformance = analyze_and_plot_pnl(
        model_daily_pnl, open_prices, close_actual, y_pred_unscaled,
        66524.87, 'bitcoin'
    )
    """
    
    # Calculate cumulative P&L
    model_cumulative_pnl = np.cumsum(model_daily_pnl)
    
    # Calculate outperformance
    profit_diff = model_cumulative_pnl[-1] - bh_baseline
    
    # Create visualization
    fig, axes = plot_pnl_comparison(model_daily_pnl, model_cumulative_pnl, 
                                    bh_baseline, profit_diff, crypto_name)
    
    if show_plot:
        plt.show()
    
    # Print summary
    print_pnl_summary(model_daily_pnl, model_cumulative_pnl, bh_baseline, profit_diff, crypto_name)
    
    return model_cumulative_pnl, profit_diff
