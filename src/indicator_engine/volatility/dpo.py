"""DPO indicator."""

from __future__ import annotations

import pandas as pd

from ..trend.ma import ma


def dpo(series: pd.Series, m1: int = 20, m2: int = 10, m3: int = 6) -> pd.DataFrame:
    base = ma(series, m1)
    dpo_val = series - base.shift(m2)
    madpo = ma(dpo_val, m3)
    return pd.DataFrame({"DPO": dpo_val, "MADPO": madpo})
