"""DMI/ADX/ADXR indicator."""

from __future__ import annotations

import pandas as pd

from ..utils import true_range


def dmi(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14, smooth: int = 6) -> pd.DataFrame:
    plus_dm = (high - high.shift(1)).clip(lower=0)
    minus_dm = (low.shift(1) - low).clip(lower=0)
    plus_dm[plus_dm < minus_dm] = 0
    minus_dm[minus_dm <= plus_dm] = 0
    tr = true_range(high, low, close)
    atr = tr.rolling(period, min_periods=1).sum()
    plus_di = 100 * plus_dm.rolling(period, min_periods=1).sum() / (atr + 1e-9)
    minus_di = 100 * minus_dm.rolling(period, min_periods=1).sum() / (atr + 1e-9)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-9)
    adx = dx.rolling(smooth, min_periods=1).mean()
    adxr = (adx + adx.shift(smooth)) / 2
    return pd.DataFrame({"+DI": plus_di, "-DI": minus_di, "ADX": adx, "ADXR": adxr})
