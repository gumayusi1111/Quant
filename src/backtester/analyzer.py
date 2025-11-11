"""Backtest performance summary helpers."""

from __future__ import annotations

from typing import Sequence

from src.backtester.engine import BacktestResult


def summarize_performance(result: BacktestResult) -> dict:
    """Return simple metrics for now."""
    equity = result.equity_curve
    if not equity:
        return {"cagr": 0.0, "max_drawdown": 0.0}
    start = equity[0]
    end = equity[-1]
    cagr = (end / start - 1) if start else 0.0
    max_drawdown = _max_drawdown(equity)
    return {"cagr": cagr, "max_drawdown": max_drawdown, "trades": len(result.trades)}


def _max_drawdown(equity: Sequence[float]) -> float:
    peak = equity[0]
    max_dd = 0.0
    for value in equity:
        peak = max(peak, value)
        drawdown = (peak - value) / peak if peak else 0.0
        max_dd = max(max_dd, drawdown)
    return max_dd
