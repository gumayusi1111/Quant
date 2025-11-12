"""ASI 指标."""

from __future__ import annotations

import numpy as np
import pandas as pd


def asi(open_: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series, ma_period: int = 10) -> pd.DataFrame:
    prev_close = close.shift(1)
    prev_open = open_.shift(1)
    k = pd.Series(np.maximum.reduce([(high - prev_close).abs(), (low - prev_close).abs()]), index=close.index)
    r = pd.Series(np.where(
        (high - prev_close).abs() > (low - prev_close).abs(),
        (high - prev_close).abs() - 0.5 * (low - prev_close).abs() + 0.25 * (close - prev_close).abs(),
        (low - prev_close).abs() - 0.5 * (high - prev_close).abs() + 0.25 * (close - prev_close).abs(),
    ), index=close.index)
    r += 1e-9
    si = 50 * ((close - prev_close) + 0.5 * (close - open_) + 0.25 * (prev_close - prev_open)) / r * k
    asi_series = si.cumsum()
    asit = asi_series.rolling(ma_period, min_periods=1).mean()
    return pd.DataFrame({"ASI": asi_series, "ASIT": asit})
