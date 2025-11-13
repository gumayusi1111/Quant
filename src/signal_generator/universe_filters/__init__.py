"""Environment-specific universe filters for watchlist selection."""

from __future__ import annotations

from typing import Dict, Optional

from . import bear, bull, sideways
from .base import FilterResult

_CONFIGURED = False


def configure(filters_cfg: Dict) -> None:
    """Configure individual filters from settings."""
    global _CONFIGURED
    bull.configure(filters_cfg.get("bull", {}))
    sideways.configure(filters_cfg.get("sideways", {}))
    bear.configure(filters_cfg.get("bear", {}))
    _CONFIGURED = True


def evaluate(regime: str, symbol: str, indicators, daily_df) -> Optional[FilterResult]:
    """Run the appropriate filter based on current regime."""
    if not _CONFIGURED:
        configure({})
    regime = (regime or "bull").lower()
    if regime == "bull":
        return bull.evaluate(symbol, indicators, daily_df)
    if regime == "sideways":
        return sideways.evaluate(symbol, indicators, daily_df)
    if regime == "bear":
        return bear.evaluate(symbol, indicators, daily_df)
    return bull.evaluate(symbol, indicators, daily_df)


__all__ = ["configure", "evaluate", "FilterResult"]
