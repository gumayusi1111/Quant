"""Multi-line exponential moving averages."""

from __future__ import annotations

from typing import Sequence

import pandas as pd

from .ema import ema


def expma(series: pd.Series, spans: int | Sequence[int] = (5, 10, 20, 60)) -> pd.Series | pd.DataFrame:
    if isinstance(spans, int):
        return ema(series, spans)
    data = {}
    for idx, span in enumerate(spans, start=1):
        data[f"ma{idx}"] = ema(series, span)
    return pd.DataFrame(data)
