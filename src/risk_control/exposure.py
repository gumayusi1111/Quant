"""Position sizing helpers."""

from __future__ import annotations

from typing import Dict, List


def allocate_capital(signals: List[Dict], capital: float) -> List[Dict]:
    """Allocate capital equally to positive signals."""
    active = [sig for sig in signals if sig.get("action") == 1]
    if not active:
        return []
    allocation = capital / len(active)
    return [
        {**sig, "capital": allocation, "shares": allocation / sig.get("price", 1.0)}
        for sig in active
    ]
