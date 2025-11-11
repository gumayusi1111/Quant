"""ETF rotation placeholder."""

from __future__ import annotations

from typing import Iterable, List


def run_rotation_strategy(symbols: Iterable[str], scores: List[float]) -> List[str]:
    """Pick the top N symbols by score (default 1)."""
    tuples = list(zip(symbols, scores))
    tuples.sort(key=lambda item: item[1], reverse=True)
    return [symbol for symbol, _ in tuples[:1]]
