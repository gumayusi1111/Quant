"""Primitive signal rules."""

from __future__ import annotations

from typing import Sequence


def crossover_rule(fast_series: Sequence[float], slow_series: Sequence[float]) -> list[int]:
    """Return +1 / -1 / 0 based on fast crossing slow."""
    length = min(len(fast_series), len(slow_series))
    signals: list[int] = []
    prev_diff = 0.0
    for idx in range(length):
        diff = fast_series[idx] - slow_series[idx]
        if diff > 0 and prev_diff <= 0:
            signals.append(1)
        elif diff < 0 and prev_diff >= 0:
            signals.append(-1)
        else:
            signals.append(0)
        prev_diff = diff
    return signals
