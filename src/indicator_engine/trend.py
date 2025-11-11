"""Trend style indicators (moving averages, MACD, etc.)."""

from __future__ import annotations

from collections import deque
from typing import Iterable, List


def moving_average(prices: Iterable[float], window: int = 20) -> List[float]:
    """Simple moving average implementation for bootstrapping."""
    window = max(1, window)
    q: deque[float] = deque(maxlen=window)
    averages: List[float] = []
    for price in prices:
        q.append(float(price))
        averages.append(sum(q) / len(q))
    return averages
