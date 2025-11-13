"""Bull-market universe filter focusing on trend-following candidates."""

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
    price_vs_ma,
    range_median,
    to_float,
    volume_stats,
)


@dataclass(frozen=True)
class BullFilterConfig:
    atr_min: float = 0.02
    atr_max: float = 0.10
    atr_a_max: float = 0.08
    atr_b_max: float = 0.12
    range_a_max: float = 0.08
    range_b_max: float = 0.12
    price_vs_ma20_a_low: float = -0.04
    price_vs_ma20_a_high: float = 0.08
    price_vs_ma20_b_low: float = -0.06
    price_vs_ma20_b_high: float = 0.12
    min_turnover_a: float = 400_000
    min_turnover_b: float = 200_000
    volume_ratio_min: float = 0.8
    ma_slope_key: str = "ma20"
    score_breakout_window: int = 20


ACTIVE_CONFIG = BullFilterConfig()


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
    slope_ma20 = ma_slope(latest, prev, cfg.ma_slope_key)

    if not _hard_filters(latest, ma20, ma60, close, slope_ma20, daily_df, cfg):
        return None

    score = _trend_score(latest, prev, daily_df, cfg)
    avg_turnover_5, _, volume_ratio = volume_stats(daily_df)
    atr_rt = atr_ratio(daily_df, period=10)
    range_med = range_median(daily_df, window=5)
    price_dev = price_vs_ma(close, ma20)

    tier = _assign_tier(score, avg_turnover_5, atr_rt, range_med, price_dev, cfg)
    if tier == "C":
        return None

    metadata = {
        "env_score": round(score, 3),
        "avg_turnover_5": avg_turnover_5,
        "atr_ratio": atr_rt,
        "range_median_5": range_med,
        "price_vs_ma20": price_dev,
        "volume_ratio_5_20": volume_ratio,
        "env": "bull",
    }
    return FilterResult(symbol, tier, score, metadata)


def _hard_filters(
    latest: pd.Series,
    ma20: Optional[float],
    ma60: Optional[float],
    close: Optional[float],
    slope_ma20: Optional[float],
    daily_df: pd.DataFrame,
    cfg: BullFilterConfig,
) -> bool:
    if ma20 is None or ma60 is None or close is None:
        return False
    if ma20 <= ma60:
        return False
    if slope_ma20 is None or slope_ma20 <= 0:
        return False
    if close < ma20:
        return False
    atr_rt = atr_ratio(daily_df, period=10)
    if atr_rt is None or not (cfg.atr_min <= atr_rt <= cfg.atr_max):
        return False
    avg5, _, ratio = volume_stats(daily_df)
    if avg5 is None:
        return False
    if ratio is not None and ratio < cfg.volume_ratio_min and avg5 < cfg.min_turnover_a:
        return False
    return True


def _trend_score(latest: pd.Series, prev: Optional[pd.Series], daily_df: pd.DataFrame, cfg: BullFilterConfig) -> float:
    score = 0.0
    ma5 = to_float(latest.get("ma5"))
    ma10 = to_float(latest.get("ma10"))
    ma20 = to_float(latest.get("ma20"))
    ma60 = to_float(latest.get("ma60"))
    if None not in (ma5, ma10, ma20):
        if ma5 > ma10 > ma20 and ma20 and (ma60 is None or ma20 > ma60):
            score += 2
        elif ma5 > ma10 > ma20:
            score += 1
    macd_dif = to_float(latest.get("macd_dif"))
    macd_dea = to_float(latest.get("macd_dea"))
    if macd_dif is not None:
        if macd_dif > 0 and (macd_dea is None or macd_dif > macd_dea):
            score += 2
        elif macd_dea is not None and macd_dif > macd_dea:
            score += 1
    closes = close_series(daily_df).dropna()
    if len(closes) >= cfg.score_breakout_window:
        window = closes.tail(cfg.score_breakout_window)
        recent_high = window.max()
        latest_price = closes.iloc[-1]
        if recent_high and latest_price:
            if latest_price > recent_high:
                score += 2
            else:
                gap = (recent_high - latest_price) / recent_high
                if 0 <= gap <= 0.03:
                    score += 1
    amounts = pd.to_numeric(daily_df.sort_values("trade_date")["amount"], errors="coerce").dropna()
    if len(amounts) >= 20:
        recent = amounts.iloc[-1]
        avg20 = amounts.tail(20).mean()
        if avg20 and recent >= avg20 * 1.3:
            score += 1
    obv = to_float(latest.get("obv"))
    if prev is not None:
        prev_obv = to_float(prev.get("obv"))
        if obv is not None and prev_obv is not None and obv >= prev_obv:
            score += 1
    rsi6 = to_float(latest.get("rsi6"))
    if rsi6 is not None and 50 <= rsi6 <= 70:
        score += 1
    return score


def _assign_tier(
    score: float,
    avg_turnover_5: Optional[float],
    atr_rt: Optional[float],
    range_med: Optional[float],
    price_dev: Optional[float],
    cfg: BullFilterConfig,
) -> str:
    if (
        score >= 5
        and (avg_turnover_5 or 0) >= cfg.min_turnover_a
        and (atr_rt or 0) <= cfg.atr_a_max
        and (range_med or 0) <= cfg.range_a_max
        and _within(price_dev, cfg.price_vs_ma20_a_low, cfg.price_vs_ma20_a_high)
    ):
        return "A"
    if (
        score >= 3
        and (avg_turnover_5 or 0) >= cfg.min_turnover_b
        and (atr_rt or 0) <= cfg.atr_b_max
        and (range_med or 0) <= cfg.range_b_max
        and _within(price_dev, cfg.price_vs_ma20_b_low, cfg.price_vs_ma20_b_high)
    ):
        return "B"
    return "C"


def _within(value: Optional[float], low: float, high: float) -> bool:
    if value is None:
        return False
    return low <= value <= high
