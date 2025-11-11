"""Volatility oscillators such as Bollinger Bands and RSI."""

from __future__ import annotations

from math import sqrt
from typing import Iterable, List, Tuple


def bollinger_bands(prices: Iterable[float], window: int = 20, num_std: float = 2.0) -> Tuple[List[float], List[float], List[float]]:
    """Return (lower, mid, upper) bands."""
    prices_list = [float(p) for p in prices]
    if not prices_list:
        return ([], [], [])
    mids: List[float] = []
    upper: List[float] = []
    lower: List[float] = []
    for idx, price in enumerate(prices_list):
        start = max(0, idx - window + 1)
        slice_ = prices_list[start : idx + 1]
        mean = sum(slice_) / len(slice_)
        variance = sum((x - mean) ** 2 for x in slice_) / len(slice_)
        std = sqrt(variance)
        mids.append(mean)
        upper.append(mean + num_std * std)
        lower.append(mean - num_std * std)
    return (lower, mids, upper)


def rsi(prices: Iterable[float], window: int = 14) -> List[float]:
    """Compute a naive RSI placeholder."""
    prices_list = [float(p) for p in prices]
    if len(prices_list) < 2:
        return [50.0 for _ in prices_list]
    gains: List[float] = []
    losses: List[float] = []
    for idx in range(1, len(prices_list)):
        delta = prices_list[idx] - prices_list[idx - 1]
        gains.append(max(delta, 0.0))
        losses.append(abs(min(delta, 0.0)))
    rsi_values: List[float] = [50.0]  # seed
    for idx in range(1, len(prices_list)):
        start = max(0, idx - window)
        avg_gain = sum(gains[start:idx]) / window if window else 0.0
        avg_loss = sum(losses[start:idx]) / window if window else 0.0
        if avg_loss == 0:
            rsi_values.append(100.0)
            continue
        rs = avg_gain / avg_loss
        rsi_values.append(100 - (100 / (1 + rs)))
    return rsi_values
