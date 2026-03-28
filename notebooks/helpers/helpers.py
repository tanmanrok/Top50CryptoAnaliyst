#Imports
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

#Making load_data_csv_files function
def load_data_csv_files(directory):
    data_dict = {}
    for filename in os.listdir(directory):
        if filename.endswith('.csv'):
            file_path = os.path.join(directory, filename)
            df = pd.read_csv(file_path)
            # Remove .csv extension for cleaner variable names
            var_name = filename.replace('.csv', '')
            data_dict[var_name] = df
            print(f"Loaded: {filename}")
    return data_dict

# Plotting function for cryptocurrency price data
def plot_crypto_prices(crypto_data, plot_type='subplots', crypto_name=None):
    """
    Plot cryptocurrency price data in various formats.
    
    Parameters:
    -----------
    crypto_data : dict
        Dictionary of DataFrames containing cryptocurrency data
    plot_type : str, default='subplots'
        Type of plot to create:
        - 'subplots': All cryptos in grid layout
        - 'individual': Individual plots for each crypto (opens sequentially)
        - 'normalized': All cryptos on one plot with normalized prices
        - 'ohlc': OHLC plot for a single cryptocurrency (requires crypto_name)
    crypto_name : str, optional
        Name of the cryptocurrency to plot (used with 'ohlc' plot_type)
    
    Returns:
    --------
    None (displays plots)
    """
    
    if plot_type == 'subplots':
        # Create subplots for all cryptocurrencies
        n_cryptos = len(crypto_data)
        n_cols = 5
        n_rows = (n_cryptos + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(20, 4*n_rows))
        axes = axes.flatten()
        
        for idx, (name, df) in enumerate(crypto_data.items()):
            axes[idx].plot(df['Date'], df['Close'], linewidth=1)
            axes[idx].set_title(f"{name.upper()}")
            axes[idx].tick_params(axis='x', rotation=45)
        
        # Hide empty subplots
        for idx in range(len(crypto_data), len(axes)):
            axes[idx].set_visible(False)
        
        plt.tight_layout()
        plt.show()
    
    elif plot_type == 'individual':
        # Create individual line plots for each cryptocurrency
        for name, df in crypto_data.items():
            plt.figure(figsize=(12, 4))
            plt.plot(df['Date'], df['Close'])
            plt.title(f"{name.upper()} - Closing Price Over Time")
            plt.xlabel("Date")
            plt.ylabel("Price ($)")
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.show()
    
    elif plot_type == 'normalized':
        # Plot normalized prices to compare trends
        plt.figure(figsize=(14, 6))
        
        for name, df in crypto_data.items():
            normalized_price = df['Close'] / df['Close'].iloc[0]
            plt.plot(df['Date'], normalized_price, label=name, alpha=0.7)
        
        plt.title("Normalized Crypto Prices Over Time")
        plt.xlabel("Date")
        plt.ylabel("Normalized Price (Start = 1.0)")
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
    
    elif plot_type == 'ohlc':
        if crypto_name is None:
            raise ValueError("crypto_name must be provided for 'ohlc' plot_type")
        
        if crypto_name not in crypto_data:
            raise ValueError(f"{crypto_name} not found in crypto_data")
        
        df = crypto_data[crypto_name]
        
        plt.figure(figsize=(14, 6))
        plt.plot(df['Date'], df['Open'], label='Open', alpha=0.7)
        plt.plot(df['Date'], df['High'], label='High', alpha=0.7)
        plt.plot(df['Date'], df['Low'], label='Low', alpha=0.7)
        plt.plot(df['Date'], df['Close'], label='Close', alpha=0.7, linewidth=2)
        
        plt.title(f"{crypto_name.upper()} - OHLC Prices")
        plt.xlabel("Date")
        plt.ylabel("Price ($)")
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
    
    else:
        raise ValueError(f"Invalid plot_type: {plot_type}. Choose from 'subplots', 'individual', 'normalized', or 'ohlc'")

# Histograms function for crypto features
def plot_histograms(crypto_data, features=['Open', 'High', 'Low', 'Close', 'Volume'], crypto_names=None):
    """
    Create histograms for specified features and cryptocurrencies.
    Can show individual distributions for each crypto, a single crypto, or selected cryptos.
    
    Parameters:
    -----------
    crypto_data : dict
        Dictionary of DataFrames containing cryptocurrency data
    features : list, default=['Open', 'High', 'Low', 'Close', 'Volume']
        List of column names to create histograms for
    crypto_names : str, list, or None, default=None
        Cryptocurrencies to include:
        - None: Use all cryptocurrencies (grid layout)
        - str: Single cryptocurrency name (e.g., 'bitcoin')
        - list: List of cryptocurrency names (e.g., ['bitcoin', 'ethereum'])
    
    Returns:
    --------
    None (displays plots)
    """
    n_features = len(features)
    
    if isinstance(crypto_names, str):
        # Single cryptocurrency mode
        if crypto_names not in crypto_data:
            raise ValueError(f"{crypto_names} not found in crypto_data")
        
        df = crypto_data[crypto_names]
        fig, axes = plt.subplots(1, n_features, figsize=(5*n_features, 4))
        
        if n_features == 1:
            axes = [axes]
        
        for idx, feature in enumerate(features):
            if feature in df.columns:
                data = df[feature].dropna()
                sns.histplot(data=data, bins=30, kde=True, ax=axes[idx], color='steelblue')
                axes[idx].set_title(f"{crypto_names.upper()} - {feature}")
                axes[idx].set_xlabel(feature)
                axes[idx].set_ylabel("Frequency")
                
                # Add statistics to the plot
                mean_val = data.mean()
                median_val = data.median()
                axes[idx].axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.2f}')
                axes[idx].axvline(median_val, color='green', linestyle='--', linewidth=2, label=f'Median: {median_val:.2f}')
                axes[idx].legend(fontsize=9)
        
        plt.suptitle(f"Histograms for {crypto_names.upper()}", fontsize=14)
        plt.tight_layout()
        plt.show()
    
    elif isinstance(crypto_names, list):
        # Multiple selected cryptocurrencies mode
        for name in crypto_names:
            if name not in crypto_data:
                raise ValueError(f"{name} not found in crypto_data")
        
        for feature in features:
            n_cols = 5
            n_rows = (len(crypto_names) + n_cols - 1) // n_cols
            
            fig, axes = plt.subplots(n_rows, n_cols, figsize=(20, 4*n_rows))
            axes = axes.flatten()
            
            for idx, crypto_name in enumerate(crypto_names):
                df = crypto_data[crypto_name]
                if feature in df.columns:
                    data = df[feature].dropna()
                    sns.histplot(data=data, bins=30, kde=True, ax=axes[idx], color='steelblue')
                    axes[idx].set_title(f"{crypto_name.upper()} - {feature}")
                    axes[idx].set_xlabel(feature)
                    axes[idx].set_ylabel("Frequency")
                    
                    # Add statistics to the plot
                    mean_val = data.mean()
                    median_val = data.median()
                    axes[idx].axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.2f}')
                    axes[idx].axvline(median_val, color='green', linestyle='--', linewidth=2, label=f'Median: {median_val:.2f}')
                    axes[idx].legend(fontsize=8)
            
            # Hide empty subplots
            for idx in range(len(crypto_names), len(axes)):
                axes[idx].set_visible(False)
            
            plt.suptitle(f"Distribution of {feature} - {len(crypto_names)} Selected Cryptocurrencies", fontsize=16, y=1.00)
            plt.tight_layout()
            plt.show()
    
    else:
        # All cryptocurrencies mode (default)
        n_cryptos = len(crypto_data)
        
        for feature in features:
            # Create subplots for each feature (one subplot per crypto)
            n_cols = 5
            n_rows = (n_cryptos + n_cols - 1) // n_cols
            
            fig, axes = plt.subplots(n_rows, n_cols, figsize=(20, 4*n_rows))
            axes = axes.flatten()
            
            for idx, (name, df) in enumerate(crypto_data.items()):
                if feature in df.columns:
                    data = df[feature].dropna()
                    sns.histplot(data=data, bins=30, kde=True, ax=axes[idx], color='steelblue')
                    axes[idx].set_title(f"{name.upper()} - {feature}")
                    axes[idx].set_xlabel(feature)
                    axes[idx].set_ylabel("Frequency")
                    
                    # Add statistics to the plot
                    mean_val = data.mean()
                    median_val = data.median()
                    axes[idx].axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.2f}')
                    axes[idx].axvline(median_val, color='green', linestyle='--', linewidth=2, label=f'Median: {median_val:.2f}')
                    axes[idx].legend(fontsize=8)
            
            # Hide empty subplots
            for idx in range(len(crypto_data), len(axes)):
                axes[idx].set_visible(False)
            
            plt.suptitle(f"Distribution of {feature} Across All Cryptocurrencies", fontsize=16, y=1.00)
            plt.tight_layout()
            plt.show()

# Box plots function for crypto features
def plot_boxplots(crypto_data, features=['Open', 'High', 'Low', 'Close', 'Volume'], crypto_names=None):
    """
    Create box plots for specified features and cryptocurrencies.
    Can show individual box plots for each crypto, a single crypto, or selected cryptos.
    Useful for identifying outliers and comparing distributions.
    
    Parameters:
    -----------
    crypto_data : dict
        Dictionary of DataFrames containing cryptocurrency data
    features : list, default=['Open', 'High', 'Low', 'Close', 'Volume']
        List of column names to create box plots for
    crypto_names : str, list, or None, default=None
        Cryptocurrencies to include:
        - None: Use all cryptocurrencies (grid layout)
        - str: Single cryptocurrency name (e.g., 'bitcoin')
        - list: List of cryptocurrency names (e.g., ['bitcoin', 'ethereum'])
    
    Returns:
    --------
    None (displays plots)
    """
    n_features = len(features)
    
    if isinstance(crypto_names, str):
        # Single cryptocurrency mode
        if crypto_names not in crypto_data:
            raise ValueError(f"{crypto_names} not found in crypto_data")
        
        df = crypto_data[crypto_names]
        fig, axes = plt.subplots(1, n_features, figsize=(5*n_features, 4))
        
        if n_features == 1:
            axes = [axes]
        
        for idx, feature in enumerate(features):
            if feature in df.columns:
                data = df[feature].dropna()
                
                # Create box plot
                bp = axes[idx].boxplot(data, vert=True, patch_artist=True)
                
                # Customize box plot colors
                for patch in bp['boxes']:
                    patch.set_facecolor('lightblue')
                    patch.set_alpha(0.7)
                
                axes[idx].set_title(f"{feature}")
                axes[idx].set_ylabel(feature)
                
                # Add statistics text
                q1 = data.quantile(0.25)
                median = data.quantile(0.50)
                q3 = data.quantile(0.75)
                iqr = q3 - q1
                min_val = data.min()
                max_val = data.max()
                
                stats_text = f"Min: {min_val:.2f}\nQ1: {q1:.2f}\nMed: {median:.2f}\nQ3: {q3:.2f}\nMax: {max_val:.2f}"
                axes[idx].text(1.15, median, stats_text, fontsize=9, verticalalignment='center',
                              bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
        
        plt.suptitle(f"Box Plots for {crypto_names.upper()}", fontsize=14)
        plt.tight_layout()
        plt.show()
    
    elif isinstance(crypto_names, list):
        # Multiple selected cryptocurrencies mode
        for name in crypto_names:
            if name not in crypto_data:
                raise ValueError(f"{name} not found in crypto_data")
        
        for feature in features:
            n_cols = 5
            n_rows = (len(crypto_names) + n_cols - 1) // n_cols
            
            fig, axes = plt.subplots(n_rows, n_cols, figsize=(20, 4*n_rows))
            axes = axes.flatten()
            
            for idx, crypto_name in enumerate(crypto_names):
                df = crypto_data[crypto_name]
                if feature in df.columns:
                    data = df[feature].dropna()
                    
                    # Create box plot
                    bp = axes[idx].boxplot(data, vert=True, patch_artist=True)
                    
                    # Customize box plot colors
                    for patch in bp['boxes']:
                        patch.set_facecolor('lightblue')
                        patch.set_alpha(0.7)
                    
                    axes[idx].set_title(f"{crypto_name.upper()}")
                    axes[idx].set_ylabel(feature)
                    
                    # Add statistics text
                    q1 = data.quantile(0.25)
                    median = data.quantile(0.50)
                    q3 = data.quantile(0.75)
                    iqr = q3 - q1
                    min_val = data.min()
                    max_val = data.max()
                    
                    stats_text = f"Min: {min_val:.2f}\nQ1: {q1:.2f}\nMed: {median:.2f}\nQ3: {q3:.2f}\nMax: {max_val:.2f}"
                    axes[idx].text(1.15, median, stats_text, fontsize=7, verticalalignment='center',
                                  bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
            
            # Hide empty subplots
            for idx in range(len(crypto_names), len(axes)):
                axes[idx].set_visible(False)
            
            plt.suptitle(f"Box Plot of {feature} - {len(crypto_names)} Selected Cryptocurrencies", fontsize=16, y=1.00)
            plt.tight_layout()
            plt.show()
    
    else:
        # All cryptocurrencies mode (default)
        n_cryptos = len(crypto_data)
        
        for feature in features:
            # Create subplots for each feature (one subplot per crypto)
            n_cols = 5
            n_rows = (n_cryptos + n_cols - 1) // n_cols
            
            fig, axes = plt.subplots(n_rows, n_cols, figsize=(20, 4*n_rows))
            axes = axes.flatten()
            
            for idx, (name, df) in enumerate(crypto_data.items()):
                if feature in df.columns:
                    data = df[feature].dropna()
                    
                    # Create box plot
                    bp = axes[idx].boxplot(data, vert=True, patch_artist=True)
                    
                    # Customize box plot colors
                    for patch in bp['boxes']:
                        patch.set_facecolor('lightblue')
                        patch.set_alpha(0.7)
                    
                    axes[idx].set_title(f"{name.upper()}")
                    axes[idx].set_ylabel(feature)
                    
                    # Add statistics text
                    q1 = data.quantile(0.25)
                    median = data.quantile(0.50)
                    q3 = data.quantile(0.75)
                    iqr = q3 - q1
                    min_val = data.min()
                    max_val = data.max()
                    
                    stats_text = f"Min: {min_val:.2f}\nQ1: {q1:.2f}\nMed: {median:.2f}\nQ3: {q3:.2f}\nMax: {max_val:.2f}"
                    axes[idx].text(1.15, median, stats_text, fontsize=7, verticalalignment='center',
                                  bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
            
            # Hide empty subplots
            for idx in range(len(crypto_data), len(axes)):
                axes[idx].set_visible(False)
            
            plt.suptitle(f"Box Plot of {feature} - Outlier Detection Across All Cryptocurrencies", fontsize=16, y=1.00)
            plt.tight_layout()
            plt.show()

# Correlation matrix function for crypto features
def get_correlation_matrix(crypto_data, features=['Open', 'High', 'Low', 'Close', 'Volume'], crypto_names=None):
    """
    Calculate the correlation matrix for specified features and cryptocurrencies.
    
    Parameters:
    -----------
    crypto_data : dict
        Dictionary of DataFrames containing cryptocurrency data
    features : list, default=['Open', 'High', 'Low', 'Close', 'Volume']
        List of column names to calculate correlations for
    crypto_names : str, list, or None, default=None
        Cryptocurrencies to include:
        - None: Use all cryptocurrencies
        - str: Single cryptocurrency name (e.g., 'bitcoin')
        - list: List of cryptocurrency names (e.g., ['bitcoin', 'ethereum'])
    
    Returns:
    --------
    pd.DataFrame
        Correlation matrix showing Pearson correlation coefficients between features
    """
    # Determine which cryptos to use
    if crypto_names is None:
        cryptos_to_use = list(crypto_data.keys())
    elif isinstance(crypto_names, str):
        if crypto_names not in crypto_data:
            raise ValueError(f"{crypto_names} not found in crypto_data")
        cryptos_to_use = [crypto_names]
    elif isinstance(crypto_names, list):
        for name in crypto_names:
            if name not in crypto_data:
                raise ValueError(f"{name} not found in crypto_data")
        cryptos_to_use = crypto_names
    else:
        raise ValueError("crypto_names must be None, a string, or a list of strings")
    
    # Combine data from selected cryptos
    combined_data = []
    
    for name in cryptos_to_use:
        df = crypto_data[name]
        # Select only the features that exist in the dataframe
        available_features = [f for f in features if f in df.columns]
        combined_data.append(df[available_features])
    
    # Concatenate all data
    all_data = pd.concat(combined_data, ignore_index=True)
    
    # Calculate correlation matrix
    correlation_matrix = all_data.corr(method='pearson')
    
    print("Correlation Matrix:")
    print(correlation_matrix)
    print("\n")
    
    return correlation_matrix

# Correlation heatmap function
def plot_correlation_heatmap(crypto_data, features=['Open', 'High', 'Low', 'Close', 'Volume'], crypto_names=None):
    """
    Create a correlation heatmap for specified features and cryptocurrencies.
    
    Parameters:
    -----------
    crypto_data : dict
        Dictionary of DataFrames containing cryptocurrency data
    features : list, default=['Open', 'High', 'Low', 'Close', 'Volume']
        List of column names to create correlation heatmap for
    crypto_names : str, list, or None, default=None
        Cryptocurrencies to include:
        - None: Use all cryptocurrencies
        - str: Single cryptocurrency name (e.g., 'bitcoin')
        - list: List of cryptocurrency names (e.g., ['bitcoin', 'ethereum'])
    
    Returns:
    --------
    None (displays plot)
    """
    # Determine which cryptos to use
    if crypto_names is None:
        cryptos_to_use = list(crypto_data.keys())
        title_suffix = "All Cryptocurrencies"
    elif isinstance(crypto_names, str):
        if crypto_names not in crypto_data:
            raise ValueError(f"{crypto_names} not found in crypto_data")
        cryptos_to_use = [crypto_names]
        title_suffix = crypto_names.upper()
    elif isinstance(crypto_names, list):
        for name in crypto_names:
            if name not in crypto_data:
                raise ValueError(f"{name} not found in crypto_data")
        cryptos_to_use = crypto_names
        title_suffix = f"{len(crypto_names)} Selected Cryptocurrencies"
    else:
        raise ValueError("crypto_names must be None, a string, or a list of strings")
    
    # Combine data from selected cryptos
    combined_data = []
    
    for name in cryptos_to_use:
        df = crypto_data[name]
        # Select only the features that exist in the dataframe
        available_features = [f for f in features if f in df.columns]
        combined_data.append(df[available_features])
    
    # Concatenate all data
    all_data = pd.concat(combined_data, ignore_index=True)
    
    # Calculate correlation matrix
    correlation_matrix = all_data.corr(method='pearson')
    
    # Create heatmap
    plt.figure(figsize=(10, 8))
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0, 
                fmt='.2f', square=True, linewidths=1, cbar_kws={'label': 'Correlation Coefficient'})
    plt.title(f"Correlation Heatmap - {title_suffix}")
    plt.tight_layout()
    plt.show()

# Statistical tests function
def perform_statistical_tests(crypto_data, features=['Open', 'High', 'Low', 'Close', 'Volume'], crypto_names=None):
    """
    Perform statistical tests on cryptocurrency data:
    - K-S Test (Kolmogorov-Smirnov): Tests for normality
    - Pearson Correlation Test: Tests if correlations are statistically significant
    - Levene's Test: Tests for equal variances across cryptocurrencies
    - Mann-Whitney U Test: Non-parametric test for comparing distributions
    
    Parameters:
    -----------
    crypto_data : dict
        Dictionary of DataFrames containing cryptocurrency data
    features : list, default=['Open', 'High', 'Low', 'Close', 'Volume']
        List of features to analyze
    crypto_names : str, list, or None, default=None
        Cryptocurrencies to include:
        - None: Use all cryptocurrencies
        - str: Single cryptocurrency name
        - list: List of cryptocurrency names
    
    Returns:
    --------
    pd.DataFrame
        DataFrame containing results of all statistical tests with columns:
        Test Type, Feature, Cryptocurrency/Pair, Statistic, P-Value, Interpretation
    """
    # Determine which cryptos to use
    if crypto_names is None:
        cryptos_to_use = list(crypto_data.keys())
    elif isinstance(crypto_names, str):
        if crypto_names not in crypto_data:
            raise ValueError(f"{crypto_names} not found in crypto_data")
        cryptos_to_use = [crypto_names]
    elif isinstance(crypto_names, list):
        for name in crypto_names:
            if name not in crypto_data:
                raise ValueError(f"{name} not found in crypto_data")
        cryptos_to_use = crypto_names
    else:
        raise ValueError("crypto_names must be None, a string, or a list of strings")
    
    # Store all results in a list to convert to DataFrame
    results_list = []
    
    # ===== K-S TEST (Kolmogorov-Smirnov Test for Normality) =====
    for feature in features:
        for crypto_name in cryptos_to_use:
            df = crypto_data[crypto_name]
            if feature in df.columns:
                data = df[feature].dropna()
                # Standardize data for K-S test
                data_standardized = (data - data.mean()) / data.std()
                ks_stat, ks_pval = stats.kstest(data_standardized, 'norm')
                
                status = "NORMAL" if ks_pval > 0.05 else "NOT NORMAL"
                
                results_list.append({
                    'Test Type': 'K-S Test',
                    'Feature': feature,
                    'Cryptocurrency/Pair': crypto_name.upper(),
                    'Statistic': ks_stat,
                    'P-Value': ks_pval,
                    'Interpretation': status
                })
    
    # ===== PEARSON CORRELATION TEST =====
    
    combined_data = []
    for name in cryptos_to_use:
        df = crypto_data[name]
        available_features = [f for f in features if f in df.columns]
        combined_data.append(df[available_features])
    
    all_data = pd.concat(combined_data, ignore_index=True)
    
    # Test correlations between all feature pairs
    feature_list = [f for f in features if f in all_data.columns]
    
    for i, feat1 in enumerate(feature_list):
        for feat2 in feature_list[i+1:]:
            corr_coef, p_val = stats.pearsonr(all_data[feat1].dropna(), all_data[feat2].dropna())
            
            significant = "SIGNIFICANT" if p_val < 0.05 else "NOT SIGNIFICANT"
            strength = "Strong" if abs(corr_coef) > 0.7 else "Moderate" if abs(corr_coef) > 0.4 else "Weak"
            
            results_list.append({
                'Test Type': 'Pearson Correlation',
                'Feature': f"{feat1} vs {feat2}",
                'Cryptocurrency/Pair': 'All Combined',
                'Statistic': corr_coef,
                'P-Value': p_val,
                'Interpretation': f"{strength} - {significant}"
            })
    
    # ===== LEVENE'S TEST (Test for Equal Variances) =====
    
    for feature in features:
        # Collect data for each cryptocurrency
        groups = []
        valid_cryptos = [crypto_name for crypto_name in cryptos_to_use 
                         if feature in crypto_data[crypto_name].columns]
        
        for crypto_name in valid_cryptos:
            df = crypto_data[crypto_name]
            if feature in df.columns:
                data = df[feature].dropna()
                if len(data) > 0:
                    groups.append(data)
        
        if len(groups) > 1:  # Levene's test requires at least 2 groups
            levene_stat, levene_pval = stats.levene(*groups)
            
            status = "EQUAL VARIANCE" if levene_pval > 0.05 else "UNEQUAL VARIANCE"
            
            results_list.append({
                'Test Type': "Levene's Test",
                'Feature': feature,
                'Cryptocurrency/Pair': f"{len(valid_cryptos)} cryptos",
                'Statistic': levene_stat,
                'P-Value': levene_pval,
                'Interpretation': status
            })
    
    # ===== MANN-WHITNEY U TEST (Non-parametric comparison) =====
    
    # Compare first cryptocurrency against all others
    if len(cryptos_to_use) >= 2:
        reference_crypto = cryptos_to_use[0]
        
        for feature in features:
            ref_df = crypto_data[reference_crypto]
            
            if feature in ref_df.columns:
                ref_data = ref_df[feature].dropna()
                
                for compare_crypto in cryptos_to_use[1:]:
                    comp_df = crypto_data[compare_crypto]
                    
                    if feature in comp_df.columns:
                        comp_data = comp_df[feature].dropna()
                        
                        if len(ref_data) > 0 and len(comp_data) > 0:
                            mw_stat, mw_pval = stats.mannwhitneyu(ref_data, comp_data, alternative='two-sided')
                            
                            significant = "DIFFERENT" if mw_pval < 0.05 else "SIMILAR"
                            comparison_pair = f"{reference_crypto.upper()} vs {compare_crypto.upper()}"
                            
                            results_list.append({
                                'Test Type': 'Mann-Whitney U',
                                'Feature': feature,
                                'Cryptocurrency/Pair': comparison_pair,
                                'Statistic': mw_stat,
                                'P-Value': mw_pval,
                                'Interpretation': significant
                            })
    else:
        print("Mann-Whitney U test requires at least 2 cryptocurrencies. Skipping...")
    
    
    # Convert results list to DataFrame
    results_df = pd.DataFrame(results_list)
    
    return results_df
