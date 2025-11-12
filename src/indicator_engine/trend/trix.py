"""TRIX indicator."""

from __future__ import annotations

import pandas as pd

from .ema import ema
from .ma import ma


def trix(series: pd.Series, period: int = 12, signal: int = 20) -> pd.DataFrame:
    ema1 = ema(series, period)
    ema2 = ema(ema1, period)
    ema3 = ema(ema2, period)
    trix_val = ema3.pct_change() * 100
    trma = ma(trix_val, signal)
    return pd.DataFrame({"TRIX": trix_val, "TRMA": trma})
