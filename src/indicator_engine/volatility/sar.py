"""SAR indicator."""

from __future__ import annotations

import pandas as pd


def sar(high: pd.Series, low: pd.Series, step: float = 0.02, max_step: float = 0.2) -> pd.Series:
    sar = pd.Series(index=high.index, dtype=float)
    ep = high.iloc[0]
    af = step
    trend_up = True
    sar.iloc[0] = low.iloc[0]
    for i in range(1, len(high)):
        prev_sar = sar.iloc[i - 1]
        if trend_up:
            sar.iloc[i] = prev_sar + af * (ep - prev_sar)
            sar.iloc[i] = min(sar.iloc[i], low.iloc[i - 1], low.iloc[i])
            if high.iloc[i] > ep:
                ep = high.iloc[i]
                af = min(af + step, max_step)
            if low.iloc[i] < sar.iloc[i]:
                trend_up = False
                sar.iloc[i] = ep
                ep = low.iloc[i]
                af = step
        else:
            sar.iloc[i] = prev_sar + af * (ep - prev_sar)
            sar.iloc[i] = max(sar.iloc[i], high.iloc[i - 1], high.iloc[i])
            if low.iloc[i] < ep:
                ep = low.iloc[i]
                af = min(af + step, max_step)
            if high.iloc[i] > sar.iloc[i]:
                trend_up = True
                sar.iloc[i] = ep
                ep = high.iloc[i]
                af = step
    return sar
