"""Oversold rebound strategy for bear markets."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, List, Optional

import pandas as pd

from ..common import assign_tier, compute_risk_metrics, find_daily_row, has_values, round_value

HAS_IMPLEMENTATION = True


@dataclass(frozen=True)
class OversoldConfig:
    min_rebound_pct: float = 1.0
    volume_multiplier: float = 1.2


DEFAULT_CONFIG = OversoldConfig()
ACTIVE_CONFIG = DEFAULT_CONFIG


def generate_latest_signal(symbol: str, indicators: pd.DataFrame, daily_df: pd.DataFrame) -> Optional[Dict]:
    if len(indicators) < 2:
        return None
    indicators = indicators.sort_values("trade_date").reset_index(drop=True)
    return _evaluate_at_index(symbol, indicators, daily_df, len(indicators) - 1)


def generate_historical_signals(
    symbol: str,
    indicators: pd.DataFrame,
    daily_df: pd.DataFrame,
    config: OversoldConfig = ACTIVE_CONFIG,
) -> pd.DataFrame:
    if len(indicators) < 2:
        return pd.DataFrame()
    ind_sorted = indicators.sort_values("trade_date").reset_index(drop=True)
    signals: List[Dict] = []
    for idx in range(1, len(ind_sorted)):
        row = _evaluate_at_index(symbol, ind_sorted, daily_df, idx, config)
        if row:
            signals.append(row)
    return pd.DataFrame(signals)


def _evaluate_at_index(
    symbol: str,
    indicators: pd.DataFrame,
    daily_df: pd.DataFrame,
    idx: int,
    config: OversoldConfig = ACTIVE_CONFIG,
) -> Optional[Dict]:
    latest = indicators.iloc[idx]
    prev = indicators.iloc[idx - 1]

    trend_down = has_values(latest, ("ma5", "ma10", "ma20")) and latest["ma5"] < latest["ma10"] < latest["ma20"]
    if not trend_down:
        return None

    rsi_val = latest.get("rsi6")
    oversold = pd.notna(rsi_val) and rsi_val <= 35
    wr_ok = has_values(latest, ("wr1", "wr2")) and (latest["wr1"] >= 85 or latest["wr2"] >= 85)
    if not (oversold or wr_ok):
        return None

    daily_df = daily_df.sort_values("trade_date").reset_index(drop=True)
    date = latest["trade_date"]
    daily_row = find_daily_row(daily_df, date)
    if daily_row is None:
        return None

    close = daily_row.get("close_front_adj", daily_row.get("close"))
    pct = pd.to_numeric(daily_row.get("pct_chg", 0), errors="coerce")
    if pd.isna(pct) or pct < config.min_rebound_pct:
        return None

    history = daily_df[daily_df["trade_date"] <= date]
    risk_metrics = compute_risk_metrics(history)
    avg_turnover = risk_metrics.get("avg_turnover_5") or 0
    turnover = pd.to_numeric(daily_row.get("amount", 0), errors="coerce")
    volume_spike = turnover and avg_turnover and turnover >= avg_turnover * config.volume_multiplier
    if not volume_spike:
        return None

    price_vs_ma20 = None
    if has_values(latest, ("ma20",)) and pd.notna(close):
        ma20 = latest.get("ma20")
        if ma20:
            price_vs_ma20 = (float(close) - float(ma20)) / float(ma20)

    kdj_k = latest.get("kdj_k")
    kdj_prev = prev.get("kdj_k")
    kdj_turn = pd.notna(kdj_k) and pd.notna(kdj_prev) and kdj_prev <= 25 and kdj_k > kdj_prev

    conditions = [trend_down, oversold, wr_ok, volume_spike, kdj_turn]
    score = sum(1 for cond in conditions if cond)

    tier = assign_tier(
        score=score,
        avg_turnover_5=avg_turnover,
        atr_ratio=risk_metrics.get("atr_ratio"),
        range_median_5=risk_metrics.get("range_median_5"),
        price_vs_ma20=price_vs_ma20,
    )

    return {
        "ts_code": symbol,
        "trade_date": date,
        "close": round_value(close),
        "pct_chg": round_value(pct),
        "score": score,
        "ma5": round_value(latest.get("ma5")),
        "ma10": round_value(latest.get("ma10")),
        "ma20": round_value(latest.get("ma20")),
        "kdj_k": round_value(kdj_k),
        "rsi6": round_value(rsi_val),
        "wr1": round_value(latest.get("wr1")),
        "wr2": round_value(latest.get("wr2")),
        "turnover": round_value(turnover),
        "avg_turnover_5": round_value(avg_turnover),
        "atr_ratio": round_value(risk_metrics.get("atr_ratio")),
        "price_vs_ma20": round_value(price_vs_ma20),
        "tier": tier,
    }


def set_config(config: Dict) -> None:
    global ACTIVE_CONFIG
    current = ACTIVE_CONFIG
    field_names = current.__dataclass_fields__.keys()
    updates = {k: config[k] for k in field_names if k in config}
    ACTIVE_CONFIG = replace(current, **updates)
