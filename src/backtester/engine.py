"""Toy backtest engine placeholder."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass
class BacktestResult:
    equity_curve: List[float]
    trades: List[dict]


def run_backtest(
    prices: Iterable[float],
    signals: Iterable[int],
    initial_capital: float = 100_000.0,
) -> BacktestResult:
    """Very rough equity curve generator."""
    equity = initial_capital
    equity_curve: List[float] = []
    trades: List[dict] = []
    for price, signal in zip(prices, signals):
        if signal == 1:
            trades.append({"action": "buy", "price": price})
            equity *= 1.001
        elif signal == -1:
            trades.append({"action": "sell", "price": price})
            equity *= 0.999
        equity_curve.append(equity)
    return BacktestResult(equity_curve=equity_curve, trades=trades)
