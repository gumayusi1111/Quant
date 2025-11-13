"""Sideways-market universe filter focusing on range-trade candidates."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, Optional

import pandas as pd

from .base import (
    FilterResult,
    atr_ratio,
    close_series,
    latest_rows,
    ma_slope,
    percentage_gap,
    price_vs_ma,
    range_median,
    to_float,
    volume_stats,
)


@dataclass(frozen=True)
class SidewaysFilterConfig:
    ma_gap_max: float = 0.02
    ma_slope_limit: float = 0.01
    boll_bandwidth_max: float = 0.12
    atr_max: float = 0.05
    atr_a_max: float = 0.04
    atr_b_max: float = 0.06
    range_a_max: float = 0.04
    range_b_max: float = 0.06
    price_ma20_a: float = 0.03
    price_ma20_b: float = 0.05
    min_turnover: float = 200_000


ACTIVE_CONFIG = SidewaysFilterConfig()


def configure(cfg: Dict) -> None:
    global ACTIVE_CONFIG
    current = ACTIVE_CONFIG
    updates = {field: cfg.get(field, getattr(current, field)) for field in current.__dataclass_fields__}
    ACTIVE_CONFIG = replace(current, **updates)


def evaluate(symbol: str, indicators: pd.DataFrame, daily_df: pd.DataFrame) -> Optional[FilterResult]:
    if indicators.empty or daily_df.empty:
        return None
    try:
        latest, prev, daily_latest = latest_rows(indicators, daily_df)
    except ValueError:
        return None

    cfg = ACTIVE_CONFIG
    ma20 = to_float(latest.get("ma20"))
    ma60 = to_float(latest.get("ma60"))
    close = to_float(daily_latest.get("close_front_adj") or daily_latest.get("close"))
    ma_gap = percentage_gap(ma20, ma60)
    slope_ma20 = ma_slope(latest, prev, "ma20")

    if not _hard_filters(latest, daily_df, ma_gap, slope_ma20, cfg):
        return None

    score = _sideways_score(latest, daily_df, close)
    avg_turnover_5, _, _ = volume_stats(daily_df)
    atr_rt = atr_ratio(daily_df, period=10)
    range_med = range_median(daily_df, window=5)
    price_dev = price_vs_ma(close, ma20)

    tier = _assign_tier(score, atr_rt, range_med, price_dev, cfg)
    if tier == "C":
        return None

    metadata = {
        "env_score": round(score, 3),
        "avg_turnover_5": avg_turnover_5,
        "atr_ratio": atr_rt,
        "range_median_5": range_med,
        "price_vs_ma20": price_dev,
        "env": "sideways",
    }
    return FilterResult(symbol, tier, score, metadata)


def _hard_filters(
    latest: pd.Series,
    daily_df: pd.DataFrame,
    ma_gap: Optional[float],
    slope_ma20: Optional[float],
    cfg: SidewaysFilterConfig,
) -> bool:
    if ma_gap is None or ma_gap > cfg.ma_gap_max:
        return False
    if slope_ma20 is None or abs(slope_ma20) > cfg.ma_slope_limit:
        return False
    upper = to_float(latest.get("boll_upper"))
    lower = to_float(latest.get("boll_lower"))
    mid = to_float(latest.get("boll_mid"))
    if None in (upper, lower, mid) or mid == 0:
        return False
    bandwidth = (upper - lower) / mid
    if bandwidth > cfg.boll_bandwidth_max:
        return False
    atr_rt = atr_ratio(daily_df, period=10)
    if atr_rt is None or atr_rt > cfg.atr_max:
        return False
    range_med = range_median(daily_df, window=5)
    if range_med is None or range_med > cfg.range_b_max:
        return False
    avg_turnover_5, _, _ = volume_stats(daily_df)
    if avg_turnover_5 is None or avg_turnover_5 < cfg.min_turnover:
        return False
    return True


def _sideways_score(latest: pd.Series, daily_df: pd.DataFrame, close: Optional[float]) -> float:
    score = 0.0
    upper = to_float(latest.get("boll_upper"))
    lower = to_float(latest.get("boll_lower"))
    mid = to_float(latest.get("boll_mid"))
    if None not in (upper, lower, mid) and close is not None:
        bandwidth = upper - lower
        if bandwidth > 0:
            if close <= lower + 0.5 * bandwidth:
                score += 2
            elif close <= mid:
                score += 1
    rsi6 = to_float(latest.get("rsi6"))
    if rsi6 is not None and 30 <= rsi6 <= 40:
        score += 1
    wr1 = to_float(latest.get("wr1"))
    if wr1 is not None and wr1 < 20:
        score += 1
    rebounds = _count_rebounds(daily_df, close)
    if rebounds >= 2:
        score += 2
    elif rebounds == 1:
        score += 1
    avg_turnover_5, _, _ = volume_stats(daily_df)
    if avg_turnover_5 is not None and avg_turnover_5 >= 200_000:
        score += 1
    return score


def _count_rebounds(daily_df: pd.DataFrame, current_price: Optional[float]) -> int:
    if current_price is None:
        return 0
    closes = close_series(daily_df).dropna().tail(30)
    if len(closes) < 5:
        return 0
    closes = closes.reset_index(drop=True)
    rebounds = 0
    for idx in range(len(closes) - 3):
        price_i = closes.iloc[idx]
        if price_i == 0:
            continue
        if abs(price_i - current_price) / current_price <= 0.01:
            future = closes.iloc[idx + 3]
            if future / price_i - 1 >= 0.03:
                rebounds += 1
    return rebounds


def _assign_tier(
    score: float,
    atr_rt: Optional[float],
    range_med: Optional[float],
    price_dev: Optional[float],
    cfg: SidewaysFilterConfig,
) -> str:
    if (
        score >= 5
        and (atr_rt or 0) <= cfg.atr_a_max
        and (range_med or 0) <= cfg.range_a_max
        and price_dev is not None
        and abs(price_dev) <= cfg.price_ma20_a
    ):
        return "A"
    if (
        score >= 3
        and (atr_rt or 0) <= cfg.atr_b_max
        and (range_med or 0) <= cfg.range_b_max
        and price_dev is not None
        and abs(price_dev) <= cfg.price_ma20_b
    ):
        return "B"
    return "C"
