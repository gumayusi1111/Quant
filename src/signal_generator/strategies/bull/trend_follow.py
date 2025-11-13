"""Trend-following strategy tuned for bull markets."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, List, Optional, Sequence, Tuple

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
class TrendFollowConfig:
    """Config knobs for the bull-market trend strategy."""

    min_turnover: float = 1_000_000
    volume_ratio_min: float = 1.3
    volume_recent_window: int = 5
    volume_base_window: int = 20
    breakout_lookback: int = 10
    breakout_buffer: float = 0.003
    rsi_max: float = 70.0
    allow_retest: bool = True
    ma_trend_fast: str = "ma10"
    ma_trend_slow: str = "ma20"


DEFAULT_CONFIG = TrendFollowConfig()
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
    config: TrendFollowConfig = ACTIVE_CONFIG,
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
    config: TrendFollowConfig = ACTIVE_CONFIG,
) -> Optional[Dict]:
    if idx < 1 or idx >= len(indicators):
        return None

    latest = indicators.iloc[idx]
    prev = indicators.iloc[idx - 1]
    trade_date = latest["trade_date"]

    daily_df = daily_df.sort_values("trade_date").reset_index(drop=True)
    daily_row = find_daily_row(daily_df, trade_date)
    if daily_row is None:
        return None

    close = _resolve_price(latest, daily_row)
    low = _resolve_low(latest, daily_row)
    pct = pd.to_numeric(daily_row.get("pct_chg", 0), errors="coerce")
    turnover = pd.to_numeric(daily_row.get("amount", 0), errors="coerce")

    history = daily_df[daily_df["trade_date"] <= trade_date]
    risk_metrics = compute_risk_metrics(history)

    volume_ratio = _compute_volume_ratio(history, config.volume_recent_window, config.volume_base_window)
    trend_ok = _check_trend(latest, prev, close, config.ma_trend_fast, config.ma_trend_slow)
    macd_ok = _check_macd(latest)
    liquidity_ok = (risk_metrics.get("avg_turnover_5") or 0) >= config.min_turnover
    volume_ok = volume_ratio is not None and volume_ratio >= config.volume_ratio_min
    rsi_val = latest.get("rsi6")
    rsi_ok = pd.notna(rsi_val) and rsi_val < config.rsi_max

    boll_mid = latest.get("boll_mid")
    boll_ok = pd.notna(close) and pd.notna(boll_mid) and close >= boll_mid

    price_vs_ma20 = None
    ma_slow = latest.get(config.ma_trend_slow)
    if pd.notna(ma_slow) and ma_slow and close is not None:
        price_vs_ma20 = (close - ma_slow) / ma_slow

    breakout_ok, retest_ok = _structure_checks(
        latest,
        history,
        close,
        low,
        lookback=config.breakout_lookback,
        buffer=config.breakout_buffer,
        allow_retest=config.allow_retest,
    )
    structure_ok = breakout_ok or retest_ok

    if not all((trend_ok, macd_ok, liquidity_ok, volume_ok, rsi_ok, boll_ok, structure_ok)):
        return None

    score_items = [
        trend_ok,
        macd_ok,
        liquidity_ok,
        volume_ok,
        rsi_ok,
        boll_ok,
        breakout_ok,
        retest_ok,
    ]
    score = sum(1 for item in score_items if item)

    tier = assign_tier(
        score=score,
        avg_turnover_5=risk_metrics.get("avg_turnover_5"),
        atr_ratio=risk_metrics.get("atr_ratio"),
        range_median_5=risk_metrics.get("range_median_5"),
        price_vs_ma20=price_vs_ma20,
    )

    structure = "breakout" if breakout_ok else ("retest" if retest_ok else "trend")

    return {
        "ts_code": symbol,
        "trade_date": trade_date,
        "close": round_value(close),
        "pct_chg": round_value(pct),
        "score": score,
        "volume_ratio": round_value(volume_ratio),
        "structure": structure,
        "ma10": round_value(latest.get("ma10")),
        "ma20": round_value(latest.get("ma20")),
        "macd_dif": round_value(latest.get("macd_dif")),
        "macd_dea": round_value(latest.get("macd_dea")),
        "rsi6": round_value(rsi_val),
        "boll_mid": round_value(boll_mid),
        "turnover": round_value(turnover),
        "avg_turnover_5": round_value(risk_metrics.get("avg_turnover_5")),
        "atr_ratio": round_value(risk_metrics.get("atr_ratio")),
        "price_vs_ma20": round_value(price_vs_ma20),
        "tier": tier,
    }


def _check_trend(
    latest: pd.Series,
    prev: pd.Series,
    close: Optional[float],
    fast_key: str,
    slow_key: str,
) -> bool:
    if not has_values(latest, (fast_key, slow_key)) or close is None:
        return False
    fast = latest[fast_key]
    slow = latest[slow_key]
    prev_slow = prev.get(slow_key)
    if pd.isna(fast) or pd.isna(slow) or pd.isna(prev_slow):
        return False
    return fast > slow and slow > prev_slow and close >= fast


def _check_macd(latest: pd.Series) -> bool:
    dif = latest.get("macd_dif")
    dea = latest.get("macd_dea")
    if pd.isna(dif):
        return False
    if pd.isna(dea):
        return dif > 0
    return dif > dea or dif > 0


def _structure_checks(
    latest: pd.Series,
    history: pd.DataFrame,
    close: Optional[float],
    low: Optional[float],
    lookback: int,
    buffer: float,
    allow_retest: bool,
) -> Tuple[bool, bool]:
    breakout_ok = False
    retest_ok = False
    trimmed = history.iloc[:-1]
    if not trimmed.empty:
        closes = extract_close_series(trimmed).dropna()
        if close is not None and not closes.empty:
            high = closes.tail(max(lookback, 5)).max()
            breakout_ok = bool(pd.notna(high) and close >= high * (1 + buffer))
    if allow_retest and close is not None and low is not None:
        ma10 = latest.get("ma10")
        if pd.notna(ma10):
            retest_ok = (low <= ma10) and (close >= ma10)
    return breakout_ok, retest_ok


def _compute_volume_ratio(history: pd.DataFrame, recent_window: int, base_window: int) -> Optional[float]:
    if history.empty or "amount" not in history.columns:
        return None
    series = pd.to_numeric(history["amount"], errors="coerce").dropna()
    if series.empty:
        return None
    recent = series.tail(recent_window).mean()
    base = series.tail(base_window).mean()
    if base is None or base == 0:
        return None
    return float(recent / base) if recent is not None else None


def _resolve_price(indicator_row: pd.Series, daily_row: pd.Series) -> Optional[float]:
    price = daily_row.get("close_front_adj")
    if price is None or pd.isna(price):
        price = daily_row.get("close")
    if price is None or pd.isna(price):
        price = indicator_row.get("close")
    return float(price) if price is not None and not pd.isna(price) else None


def _resolve_low(indicator_row: pd.Series, daily_row: pd.Series) -> Optional[float]:
    low = daily_row.get("low_front_adj")
    if low is None or pd.isna(low):
        low = daily_row.get("low")
    if low is None or pd.isna(low):
        low = indicator_row.get("low")
    return float(low) if low is not None and not pd.isna(low) else None


def set_config(config: Dict) -> None:
    """Update active config from runtime settings."""
    global ACTIVE_CONFIG
    current = ACTIVE_CONFIG
    updates = {field: config.get(field, getattr(current, field)) for field in current.__dataclass_fields__}
    ACTIVE_CONFIG = replace(current, **updates)
