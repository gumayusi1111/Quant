"""Williams %R indicator."""

from __future__ import annotations

from typing import Iterable

import pandas as pd


def wr(high: pd.Series, low: pd.Series, close: pd.Series, periods: int | Iterable[int] = (10, 6)) -> pd.Series | pd.DataFrame:
    if isinstance(periods, int):
        periods = (periods,)
    data = {}
    for idx, period in enumerate(periods, start=1):
        high_max = high.rolling(period, min_periods=1).max()
        low_min = low.rolling(period, min_periods=1).min()
        wr_series = (high_max - close) / (high_max - low_min + 1e-9) * 100
        label = f"wr{idx}" if idx <= 2 else f"wr{period}"
        data[label] = wr_series
    df = pd.DataFrame(data)
    if len(periods) == 1:
        return df.iloc[:, 0]
    return df
