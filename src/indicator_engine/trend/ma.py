"""Simple moving averages."""

from __future__ import annotations

import pandas as pd


def ma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window, min_periods=1).mean()
