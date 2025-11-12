"""ARBR indicators."""

from __future__ import annotations

import pandas as pd


def arbr(high: pd.Series, low: pd.Series, open_: pd.Series, close: pd.Series, period: int = 26) -> pd.DataFrame:
    ar = (high - open_).rolling(period, min_periods=1).sum() / ((open_ - low).rolling(period, min_periods=1).sum() + 1e-9) * 100
    br = (high - close.shift(1)).rolling(period, min_periods=1).sum() / ((close.shift(1) - low).rolling(period, min_periods=1).sum() + 1e-9) * 100
    return pd.DataFrame({"AR": ar, "BR": br})
