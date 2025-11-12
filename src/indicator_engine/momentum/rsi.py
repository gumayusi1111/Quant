"""RSI indicator."""

from __future__ import annotations

from typing import Iterable

import pandas as pd


def rsi(series: pd.Series, periods: int | Iterable[int] = (6, 12, 24)) -> pd.Series | pd.DataFrame:
    if isinstance(periods, int):
        return _rsi_single(series, periods)
    data = {}
    for period in periods:
        data[f"rsi{period}"] = _rsi_single(series, period)
    return pd.DataFrame(data)


def _rsi_single(series: pd.Series, period: int) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = -delta.clip(upper=0).ewm(alpha=1 / period, adjust=False).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))
