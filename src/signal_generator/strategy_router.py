"""Strategy router that selects signals based on market regime."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from src.logging import get_logger

from .strategies.bear import oversold_rebound
from .strategies.bull import trend_follow
from .strategies.sideways import range_trade

LOGGER = get_logger("signal_router")
REGIME_FILE = Path("data/backtests/market_regime.csv")
_CONFIGURED = False
_STRATEGY_MAP = {
    "bull": trend_follow,
    "sideways": range_trade,
    "bear": oversold_rebound,
}


def configure_strategies(settings: Dict) -> None:
    global _CONFIGURED
    strat_cfg = settings.get("strategies", {}) if settings else {}
    if "bull" in strat_cfg:
        trend_follow.set_config(strat_cfg["bull"])
    if "sideways" in strat_cfg:
        range_trade.set_config(strat_cfg["sideways"])
    if "bear" in strat_cfg:
        oversold_rebound.set_config(strat_cfg["bear"])
    _CONFIGURED = True


def _load_latest_regime() -> str:
    if not REGIME_FILE.exists():
        return "bull"
    try:
        df = pd.read_csv(REGIME_FILE)
    except Exception:  # pragma: no cover
        return "bull"
    if df.empty:
        return "bull"
    return str(df.iloc[-1]["regime"]).lower()


def select_strategy(regime: Optional[str] = None):
    regime = (regime or _load_latest_regime()).lower()
    strategy = _STRATEGY_MAP.get(regime, trend_follow)
    if not getattr(strategy, "HAS_IMPLEMENTATION", True):
        LOGGER.debug("Strategy for regime '%s' not implemented; falling back to bull strategy.", regime)
        return trend_follow
    return strategy


def get_current_regime() -> str:
    return _load_latest_regime()


def generate_latest_signal(symbol: str, indicators: pd.DataFrame, daily_df: pd.DataFrame, regime: Optional[str] = None):
    strategy = select_strategy(regime)
    return strategy.generate_latest_signal(symbol, indicators, daily_df)


def generate_historical_signals(
    symbol: str,
    indicators: pd.DataFrame,
    daily_df: pd.DataFrame,
    regime: Optional[str] = None,
    regime_map: Optional[Dict[str, str]] = None,
):
    if regime_map:
        frames = []
        for regime_name, strategy in _STRATEGY_MAP.items():
            hist = strategy.generate_historical_signals(symbol, indicators, daily_df)
            if hist.empty:
                continue
            frame = hist.copy()
            frame["_candidate_regime"] = regime_name.lower()
            frames.append(frame)
        if not frames:
            return pd.DataFrame()
        combined = pd.concat(frames, ignore_index=True)
        combined["_normalized_date"] = combined["trade_date"].apply(_normalize_date)
        combined["_regime_actual"] = combined["_normalized_date"].map(
            lambda d: (regime_map.get(d) or "").lower()
        )
        filtered = combined[combined["_regime_actual"] == combined["_candidate_regime"]].copy()
        if filtered.empty:
            return pd.DataFrame()
        filtered["regime"] = filtered["_regime_actual"]
        filtered.drop(columns=["_candidate_regime", "_normalized_date", "_regime_actual"], inplace=True)
        return filtered

    strategy = select_strategy(regime)
    hist = strategy.generate_historical_signals(symbol, indicators, daily_df)
    if hist.empty:
        return hist
    if regime:
        hist = hist.copy()
        hist["regime"] = regime.lower()
    return hist


def _normalize_date(value) -> str:
    if value is None or pd.isna(value):
        return ""
    try:
        return str(int(value))
    except (ValueError, TypeError):
        return str(value)
