"""DMA indicator (DDD/AMA)."""

from __future__ import annotations

import pandas as pd

from .ma import ma


def dma(series: pd.Series, short: int = 10, long: int = 50, ama_period: int = 10) -> pd.DataFrame:
    ddd = ma(series, short) - ma(series, long)
    ama = ma(ddd, ama_period)
    return pd.DataFrame({"DDD": ddd, "AMA": ama})
