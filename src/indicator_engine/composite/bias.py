"""BIAS指标."""

from __future__ import annotations

import pandas as pd

from ..trend.ma import ma


def bias(series: pd.Series, periods: tuple[int, ...] = (6, 12, 24)) -> pd.DataFrame:
    data = {}
    for idx, p in enumerate(periods, start=1):
        ma_val = ma(series, p)
        bias_val = (series - ma_val) / (ma_val + 1e-9) * 100
        label = f"bias{idx}"
        data[label] = bias_val
        data[f"bias_{p}"] = bias_val
    return pd.DataFrame(data)
