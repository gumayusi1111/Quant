"""Range-trading strategy for sideways markets."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, List, Optional

import pandas as pd

from ..common import (
    assign_tier,
    compute_risk_metrics,
    extract_close_series,
    find_daily_row,
    has_values,
    round_value,
)

HAS_IMPLEMENTATION = True


@dataclass(frozen=True)
class RangeTradeConfig:
    flat_threshold: float = 0.01
    max_distance_ma20: float = 0.015
    min_turnover: float = 200_000


DEFAULT_CONFIG = RangeTradeConfig()
ACTIVE_CONFIG = DEFAULT_CONFIG


def generate_latest_signal(symbol: str, indicators: pd.DataFrame, daily_df: pd.DataFrame) -> Optional[Dict]:
    if indicators.empty:
        return None
    indicators = indicators.sort_values("trade_date").reset_index(drop=True)
    return _evaluate_at_index(symbol, indicators, daily_df, len(indicators) - 1)


def generate_historical_signals(
    symbol: str,
    indicators: pd.DataFrame,
    daily_df: pd.DataFrame,
    config: RangeTradeConfig = ACTIVE_CONFIG,
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
    config: RangeTradeConfig = ACTIVE_CONFIG,
) -> Optional[Dict]:
    latest = indicators.iloc[idx]
    prev = indicators.iloc[idx - 1]

    if not has_values(latest, ("ma5", "ma10", "ma20")):
        return None

    ma20 = latest["ma20"]
    if ma20 == 0 or pd.isna(ma20):
        return None

    flat_trend = (
        abs(latest["ma5"] - ma20) / ma20 <= config.flat_threshold
        and abs(latest["ma10"] - ma20) / ma20 <= config.flat_threshold * 1.5
    )
    if not flat_trend:
        return None

    daily_df = daily_df.sort_values("trade_date").reset_index(drop=True)
    date = latest["trade_date"]
    daily_row = find_daily_row(daily_df, date)
    if daily_row is None:
        return None

    close = pd.to_numeric(daily_row.get("close_front_adj", daily_row.get("close")), errors="coerce")
    pct = pd.to_numeric(daily_row.get("pct_chg", 0), errors="coerce")
    turnover = pd.to_numeric(daily_row.get("amount", 0), errors="coerce")

    history = daily_df[daily_df["trade_date"] <= date]
    risk_metrics = compute_risk_metrics(history)
    if (risk_metrics.get("avg_turnover_5") or 0) < config.min_turnover:
        return None

    boll_ok = has_values(latest, ("boll_mid", "boll_lower", "boll_upper")) and pd.notna(close)
    if boll_ok:
        boll_ok = (close <= latest["boll_mid"]) and (close >= latest["boll_lower"])

    kdj_ok = has_values(latest, ("kdj_k", "kdj_d")) and latest["kdj_k"] <= 45
    rsi_val = latest.get("rsi6")
    rsi_ok = pd.notna(rsi_val) and 35 <= rsi_val <= 55
    wr_ok = has_values(latest, ("wr1", "wr2")) and 55 <= latest["wr1"] <= 90

    price_vs_ma20 = None
    if pd.notna(close):
        price_vs_ma20 = (float(close) - float(ma20)) / float(ma20)
        if abs(price_vs_ma20) > config.max_distance_ma20:
            return None

    # ensure price oscillating within recent range
    recent_prices = extract_close_series(history.tail(30)).dropna()
    range_ok = False
    if pd.notna(close) and recent_prices.size >= 10:
        recent_high = recent_prices.max()
        recent_low = recent_prices.min()
        range_ok = recent_low * 1.02 <= close <= recent_high * 0.99
    if not range_ok:
        return None

    rsi_prev = prev.get("rsi6")
    reversal_hint = pd.notna(rsi_val) and pd.notna(rsi_prev) and rsi_prev <= 40 and rsi_val > rsi_prev

    conditions = [flat_trend, boll_ok, kdj_ok, rsi_ok, wr_ok, reversal_hint]
    score = sum(1 for cond in conditions if cond)
    if score < 3:
        return None

    tier = assign_tier(
        score=score,
        avg_turnover_5=risk_metrics.get("avg_turnover_5"),
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
        "kdj_k": round_value(latest.get("kdj_k")),
        "kdj_d": round_value(latest.get("kdj_d")),
        "rsi6": round_value(rsi_val),
        "wr1": round_value(latest.get("wr1")),
        "wr2": round_value(latest.get("wr2")),
        "turnover": round_value(turnover),
        "avg_turnover_5": round_value(risk_metrics.get("avg_turnover_5")),
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
