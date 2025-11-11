"""Score signals before turning them into orders."""

from __future__ import annotations

from typing import Iterable, List


def score_signals(signals: Iterable[int]) -> List[float]:
    """Assign a naive confidence score."""
    return [float(signal) for signal in signals]
