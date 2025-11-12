"""BBI indicator."""

from __future__ import annotations

import pandas as pd

from .ma import ma


def bbi(series: pd.Series, periods: tuple[int, ...] = (3, 6, 12, 24)) -> pd.Series:
    mas = [ma(series, p) for p in periods]
    stacked = pd.concat(mas, axis=1)
    return stacked.mean(axis=1)
