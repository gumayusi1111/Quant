"""ETF trend following placeholder."""

from __future__ import annotations

from typing import Iterable, List

from src.signal_generator import generate_signals


def run_trend_strategy(symbols: Iterable[str], fast: List[float], slow: List[float]) -> List[dict]:
    """Return placeholder orders based on generated signals."""
    signals = generate_signals(symbols, fast, slow)
    return [
        {"symbol": sig.symbol, "action": sig.action, "confidence": sig.confidence}
        for sig in signals
    ]
