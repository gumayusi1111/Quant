"""Stop-loss / take-profit placeholder."""

from __future__ import annotations

from typing import Dict


def stop_loss_check(position: Dict[str, float], price: float, threshold: float = 0.05) -> bool:
    """Return True if loss exceeds threshold (placeholder)."""
    entry = position.get("entry_price", price)
    if entry == 0:
        return False
    drop = (entry - price) / entry
    return drop >= threshold
