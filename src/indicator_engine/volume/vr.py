"""Volume ratio indicator."""

from __future__ import annotations

import pandas as pd


def vr(close: pd.Series, volume: pd.Series, period: int = 26) -> pd.Series:
    up_vol = volume.where(close > close.shift(1), 0)
    down_vol = volume.where(close < close.shift(1), 0)
    tie_vol = volume.where(close == close.shift(1), 0)
    vr = (up_vol.rolling(period, min_periods=1).sum() + tie_vol.rolling(period, min_periods=1).sum() / 2) / (
        down_vol.rolling(period, min_periods=1).sum() + tie_vol.rolling(period, min_periods=1).sum() / 2 + 1e-9
    ) * 100
    return vr
