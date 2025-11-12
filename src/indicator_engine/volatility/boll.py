"""Bollinger Bands."""

from __future__ import annotations

import pandas as pd


def boll(series: pd.Series, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    mid = series.rolling(window, min_periods=1).mean()
    std = series.rolling(window, min_periods=1).std(ddof=0)
    upper = mid + num_std * std
    lower = mid - num_std * std
    return pd.DataFrame({"boll_upper": upper, "boll_mid": mid, "boll_lower": lower})
