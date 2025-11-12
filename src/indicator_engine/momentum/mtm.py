"""MTM indicator."""

from __future__ import annotations

import pandas as pd

from ..trend.ma import ma


def mtm(series: pd.Series, period: int = 12, ma_period: int = 6) -> pd.DataFrame:
    momentum = series - series.shift(period)
    mtm_ma = ma(momentum, ma_period)
    return pd.DataFrame({"MTM": momentum, "MTMMA": mtm_ma})
