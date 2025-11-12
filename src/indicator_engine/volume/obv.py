"""OBV indicator."""

from __future__ import annotations

import pandas as pd


def obv(close: pd.Series, volume: pd.Series, ma_period: int = 30) -> pd.DataFrame:
    direction = np.sign(close.diff()).fillna(0)
    obv_series = (volume * direction).cumsum()
    maobv = obv_series.rolling(ma_period, min_periods=1).mean()
    return pd.DataFrame({"OBV": obv_series, "MAOBV": maobv})
