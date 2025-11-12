"""MACD indicator."""

from __future__ import annotations

import pandas as pd

from ..trend.ema import ema


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    fast_ema = ema(series, fast)
    slow_ema = ema(series, slow)
    dif = fast_ema - slow_ema
    dea = ema(dif, signal)
    hist = (dif - dea) * 2
    return pd.DataFrame({"dif": dif, "dea": dea, "macd": hist})
