"""Volume-based indicators."""

from __future__ import annotations

from typing import Iterable, List


def volume_ratio(volumes: Iterable[float], window: int = 5) -> List[float]:
    """Compute a naive volume ratio placeholder."""
    window = max(1, window)
    vol_list = [float(v) for v in volumes]
    ratios: List[float] = []
    for idx, volume in enumerate(vol_list):
        start = max(0, idx - window + 1)
        lookback = vol_list[start : idx + 1]
        baseline = sum(lookback) / len(lookback)
        ratios.append(volume / baseline if baseline else 0.0)
    return ratios
