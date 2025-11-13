"""Shared helpers for universe filters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Sequence, Tuple

import pandas as pd


@dataclass
class FilterResult:
    ts_code: str
    tier: str
    score: float
    metadata: Dict


def latest_rows(indicators: pd.DataFrame, daily_df: pd.DataFrame) -> Tuple[pd.Series, Optional[pd.Series], pd.Series]:
    """Return (latest_indicator, prev_indicator, latest_daily)."""
    ind_sorted = indicators.sort_values("trade_date").reset_index(drop=True)
    daily_sorted = daily_df.sort_values("trade_date").reset_index(drop=True)
    if ind_sorted.empty or daily_sorted.empty:
        raise ValueError("Empty data frame")
    latest = ind_sorted.iloc[-1]
    prev = ind_sorted.iloc[-2] if len(ind_sorted) > 1 else None
    daily_latest = daily_sorted.iloc[-1]
    return latest, prev, daily_latest


def to_float(value) -> Optional[float]:
    if value is None or pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def atr_ratio(daily_df: pd.DataFrame, period: int = 10) -> Optional[float]:
    if daily_df.empty:
        return None
    df = daily_df.sort_values("trade_date").tail(period + 1).copy()
    for col in ("high", "low", "close"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df.dropna(subset=["high", "low", "close"], inplace=True)
    if len(df) < 2:
        return None
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([(high - low).abs(), (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    atr = tr.rolling(window=period, min_periods=1).mean().iloc[-1]
    last_close = close.iloc[-1]
    if pd.isna(atr) or pd.isna(last_close) or not last_close:
        return None
    return float(atr / last_close)


def range_median(daily_df: pd.DataFrame, window: int = 5) -> Optional[float]:
    df = daily_df.sort_values("trade_date").tail(window)
    for col in ("high", "low", "close"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df.dropna(subset=["high", "low", "close"], inplace=True)
    if df.empty:
        return None
    ranges = (df["high"] - df["low"]) / df["close"].replace(0, pd.NA)
    ranges = ranges.dropna()
    return float(ranges.median()) if not ranges.empty else None


def volume_stats(daily_df: pd.DataFrame, recent: int = 5, base: int = 20) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    if "amount" not in daily_df.columns:
        return (None, None, None)
    series = pd.to_numeric(daily_df.sort_values("trade_date")["amount"], errors="coerce").dropna()
    if series.empty:
        return (None, None, None)
    avg_recent = float(series.tail(recent).mean()) if len(series) >= 1 else None
    avg_base = float(series.tail(base).mean()) if len(series) >= 1 else None
    ratio = (avg_recent / avg_base) if avg_recent is not None and avg_base not in (None, 0) else None
    latest = float(series.iloc[-1])
    return avg_recent, avg_base, ratio


def close_series(daily_df: pd.DataFrame) -> pd.Series:
    if "close_front_adj" in daily_df.columns:
        series = pd.to_numeric(daily_df["close_front_adj"], errors="coerce")
        fallback = pd.to_numeric(daily_df.get("close"), errors="coerce")
        return series.fillna(fallback)
    return pd.to_numeric(daily_df.get("close"), errors="coerce")


def price_vs_ma(price: Optional[float], ma: Optional[float]) -> Optional[float]:
    if price is None or ma in (None, 0) or pd.isna(ma):
        return None
    return (price - ma) / ma


def ma_slope(latest: pd.Series, prev: Optional[pd.Series], key: str) -> Optional[float]:
    if prev is None:
        return None
    curr = latest.get(key)
    prev_val = prev.get(key)
    if curr is None or prev_val is None or pd.isna(curr) or pd.isna(prev_val):
        return None
    return float(curr - prev_val)


def percentage_gap(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a in (None, 0) or b in (None, 0) or pd.isna(a) or pd.isna(b):
        return None
    return abs(a / b - 1)


def bool_all(values: Sequence[bool]) -> bool:
    return all(values)
