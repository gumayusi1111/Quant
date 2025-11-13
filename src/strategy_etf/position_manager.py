"""Position sizing utilities based on regime and tier."""

from __future__ import annotations

from typing import Dict

DEFAULT_REGIME_WEIGHTS = {"bull": 1.0, "sideways": 0.5, "bear": 0.2}
DEFAULT_TIER_MULTIPLIERS = {"A": 1.0, "B": 0.7, "C": 0.4}


def recommend_weight(config: Dict, regime: str, tier: str) -> float:
    """Return recommended position weight (0-1) given regime and tier."""
    regime_weights = config.get("regime_weights", DEFAULT_REGIME_WEIGHTS)
    tier_multipliers = config.get("tier_multipliers", DEFAULT_TIER_MULTIPLIERS)

    regime_weight = regime_weights.get(regime, regime_weights.get("default", DEFAULT_REGIME_WEIGHTS["bull"]))
    tier_weight = tier_multipliers.get(tier, tier_multipliers.get("default", DEFAULT_TIER_MULTIPLIERS["C"]))

    weight = regime_weight * tier_weight
    return max(0.0, min(1.0, float(weight)))
