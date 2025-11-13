"""Analytics helpers for watchlist backtest."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


def summarize_trades(trades_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    tiers = sorted(trades_df["tier"].dropna().unique().tolist())
    tiers.append("ALL")
    for tier in tiers:
        subset = trades_df if tier == "ALL" else trades_df[trades_df["tier"] == tier]
        if subset.empty:
            continue
        returns = subset["return"].astype(float)
        sharpe, max_dd = _calc_metrics(returns)
        rows.append(
            {
                "tier": tier,
                "trades": len(subset),
                "win_rate": (returns > 0).mean(),
                "avg_return": returns.mean(),
                "median_return": returns.median(),
                "avg_hold_days": subset["hold_days"].mean(),
                "sharpe": sharpe,
                "max_drawdown": max_dd,
            }
        )
    return pd.DataFrame(rows)


def summarize_by_regime(trades_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (tier, regime), group in trades_df.groupby(["tier", "entry_regime"]):
        if regime is None or (isinstance(regime, float) and pd.isna(regime)) or group.empty:
            continue
        returns = group["return"].astype(float)
        sharpe, max_dd = _calc_metrics(returns)
        rows.append(
            {
                "tier": tier,
                "regime": regime,
                "trades": len(group),
                "win_rate": (returns > 0).mean(),
                "avg_return": returns.mean(),
                "median_return": returns.median(),
                "sharpe": sharpe,
                "max_drawdown": max_dd,
            }
        )
    return pd.DataFrame(rows).sort_values(["tier", "regime"])


def _calc_metrics(returns: pd.Series) -> tuple[float, float]:
    if returns.empty:
        return 0.0, 0.0
    std = returns.std(ddof=0)
    sharpe = 0.0
    if std and not math.isclose(std, 0.0):
        sharpe = returns.mean() / std * math.sqrt(len(returns))

    equity = (1 + returns).cumprod()
    peak = equity.cummax()
    drawdown = (peak - equity) / peak
    max_dd = drawdown.max() if not drawdown.empty else 0.0
    if math.isnan(max_dd):
        max_dd = 0.0
    return sharpe, max_dd
