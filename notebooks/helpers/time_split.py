"""Time-based train/test split helpers."""

from __future__ import annotations

from typing import Dict, Tuple

import pandas as pd


def split_train_test_time(
    df: pd.DataFrame,
    test_size: float = 0.2,
    date_col: str = "Date",
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Split a DataFrame so the newest rows are the test set.

    If ``date_col`` exists, data is sorted ascending by that column before splitting.
    The last ``test_size`` fraction is returned as test data.
    """
    if not 0 < test_size < 1:
        raise ValueError("test_size must be between 0 and 1")
    if df.empty:
        raise ValueError("df is empty")

    data = df.copy()
    if date_col in data.columns:
        data = data.sort_values(by=date_col).reset_index(drop=True)

    split_idx = int(len(data) * (1 - test_size))
    if split_idx <= 0 or split_idx >= len(data):
        raise ValueError("Split index is invalid for this dataset size")

    train_df = data.iloc[:split_idx].copy()
    test_df = data.iloc[split_idx:].copy()
    return train_df, test_df


def split_dataset_dict_time(
    dataset_dict: Dict[str, pd.DataFrame],
    test_size: float = 0.2,
    date_col: str = "Date",
) -> Dict[str, Dict[str, pd.DataFrame]]:
    """Apply time-based split to every DataFrame in a dictionary."""
    split_data: Dict[str, Dict[str, pd.DataFrame]] = {}
    for name, df in dataset_dict.items():
        train_df, test_df = split_train_test_time(df, test_size=test_size, date_col=date_col)
        split_data[name] = {"train": train_df, "test": test_df}
    return split_data
