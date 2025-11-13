"""Bear-market universe filter focusing on oversold rebound candidates."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, Optional

import pandas as pd

from .base import (
    FilterResult,
    atr_ratio,
    close_series,
    latest_rows,
    price_vs_ma,
    to_float,
    volume_stats,
)


@dataclass(frozen=True)
class BearFilterConfig:
    drawdown_min: float = 0.2
    min_turnover_a: float = 200_000
    min_turnover_b: float = 100_000


ACTIVE_CONFIG = BearFilterConfig()


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
    closes = close_series(daily_df).dropna()
    if len(closes) < 60:
        return None
    high_60 = closes.tail(60).max()
    if not _hard_filters(ma20, ma60, close, high_60, cfg):
        return None

    score = _bear_score(latest, prev, daily_df, close)
    avg_turnover_5, _, _ = volume_stats(daily_df)
    price_dev = price_vs_ma(close, ma20)
    atr_rt = atr_ratio(daily_df, period=10)

    tier = _assign_tier(score, avg_turnover_5, cfg)
    if tier == "C":
        return None

    metadata = {
        "env_score": round(score, 3),
        "avg_turnover_5": avg_turnover_5,
        "price_vs_ma20": price_dev,
        "atr_ratio": atr_rt,
        "env": "bear",
    }
    return FilterResult(symbol, tier, score, metadata)


def _hard_filters(ma20: Optional[float], ma60: Optional[float], close: Optional[float], high_60: Optional[float], cfg: BearFilterConfig) -> bool:
    if None in (ma20, ma60, close, high_60):
        return False
    if not (ma20 < ma60 and close < ma20 and close < ma60):
        return False
    drawdown = 1 - close / high_60 if high_60 else None
    if drawdown is None or drawdown < cfg.drawdown_min:
        return False
    return True


def _bear_score(latest: pd.Series, prev: Optional[pd.Series], daily_df: pd.DataFrame, close: Optional[float]) -> float:
    score = 0.0
    rsi6 = to_float(latest.get("rsi6"))
    if rsi6 is not None and rsi6 < 20:
        score += 2
    wr1 = to_float(latest.get("wr1"))
    wr2 = to_float(latest.get("wr2"))
    if (wr1 is not None and wr1 > 90) or (wr2 is not None and wr2 > 90):
        score += 1
    open_price = to_float(daily_df.iloc[-1].get("open"))
    high = to_float(daily_df.iloc[-1].get("high"))
    low = to_float(daily_df.iloc[-1].get("low"))
    if None not in (open_price, close, high, low):
        body = abs(close - open_price)
        range_len = high - low
        if range_len > 0:
            upper_shadow = high - max(open_price, close)
            lower_shadow = min(open_price, close) - low
            if lower_shadow / range_len >= 0.4 and upper_shadow / range_len <= 0.3:
                score += 1
            if (close - low) / close >= 0.03:
                score += 1
    prev_daily = daily_df.iloc[-2] if len(daily_df) >= 2 else None
    if prev_daily is not None:
        prev_pct = to_float(prev_daily.get("pct_chg"))
        prev_vol = to_float(prev_daily.get("vol"))
        curr_vol = to_float(daily_df.iloc[-1].get("vol"))
        if prev_pct is not None and prev_pct <= -2 and None not in (prev_vol, curr_vol) and curr_vol < prev_vol * 0.8:
            score += 1
    macd_dif = to_float(latest.get("macd_dif"))
    macd_dea = to_float(latest.get("macd_dea"))
    prev_dif = to_float(prev.get("macd_dif")) if prev is not None else None
    if None not in (macd_dif, prev_dif) and macd_dif > prev_dif and macd_dif < 0:
        score += 1
    if None not in (macd_dif, macd_dea) and macd_dea is not None and macd_dif < 0 and abs(macd_dif - macd_dea) <= 0.002:
        score += 1
    return score


def _assign_tier(score: float, avg_turnover_5: Optional[float], cfg: BearFilterConfig) -> str:
    if score >= 5 and (avg_turnover_5 or 0) >= cfg.min_turnover_a:
        return "A"
    if score >= 3 and (avg_turnover_5 or 0) >= cfg.min_turnover_b:
        return "B"
    return "C"
