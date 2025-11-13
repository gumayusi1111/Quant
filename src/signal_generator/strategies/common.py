"""Common helpers shared by strategy modules."""

from __future__ import annotations

from typing import Dict, Optional, Sequence

import pandas as pd


def find_daily_row(daily_df: pd.DataFrame, trade_date) -> Optional[pd.Series]:
    if daily_df.empty:
        return None
    row = daily_df[daily_df["trade_date"] == trade_date]
    if row.empty:
        return None
    return row.iloc[-1]


def has_values(row: pd.Series, columns: Sequence[str]) -> bool:
    for column in columns:
        if column not in row.index or pd.isna(row[column]):
            return False
    return True


def compute_risk_metrics(daily_df: pd.DataFrame) -> Dict[str, float]:
    metrics: Dict[str, float] = {}
    if daily_df.empty:
        return metrics

    df = daily_df.copy()
    for column in ("amount", "high", "low", "close", "vol"):
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    df.dropna(subset=["amount", "high", "low", "close"], inplace=True)
    if df.empty:
        return metrics

    recent = df.tail(20)
    metrics["avg_turnover_5"] = recent["amount"].tail(5).mean()
    ranges = ((recent["high"] - recent["low"]) / recent["close"]).tail(5)
    metrics["range_median_5"] = float(ranges.median()) if not ranges.empty else None

    atr = _compute_atr(recent)
    if atr is not None:
        last_close = recent["close"].iloc[-1]
        metrics["atr"] = atr
        if last_close:
            metrics["atr_ratio"] = atr / last_close
    return metrics


def _compute_atr(df: pd.DataFrame, period: int = 14) -> Optional[float]:
    if len(df) < 2:
        return None
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    close = df["close"].astype(float)
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            (high - low).abs(),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr = tr.rolling(window=period, min_periods=1).mean().iloc[-1]
    return float(atr)


def assign_tier(
    score: int,
    avg_turnover_5: Optional[float],
    atr_ratio: Optional[float],
    range_median_5: Optional[float],
    price_vs_ma20: Optional[float],
) -> str:
    def _check_range(value: Optional[float], upper: float) -> bool:
        return value is not None and value <= upper

    def _check_abs(value: Optional[float], upper: float) -> bool:
        return value is not None and abs(value) <= upper

    if (
        score >= 5
        and (avg_turnover_5 or 0) >= 400_000
        and _check_range(atr_ratio, 0.04)
        and _check_range(range_median_5, 0.04)
        and _check_abs(price_vs_ma20, 0.02)
    ):
        return "A"

    if (
        score >= 4
        and (avg_turnover_5 or 0) >= 200_000
        and _check_range(atr_ratio, 0.06)
        and _check_range(range_median_5, 0.06)
        and _check_abs(price_vs_ma20, 0.04)
    ):
        return "B"

    return "C"


def round_value(value, digits: int = 6):
    return None if pd.isna(value) else round(float(value), digits)


def extract_close_series(df: pd.DataFrame) -> pd.Series:
    if "close_front_adj" in df.columns:
        series = pd.to_numeric(df["close_front_adj"], errors="coerce")
        fallback = pd.to_numeric(df.get("close"), errors="coerce")
        return series.fillna(fallback)
    return pd.to_numeric(df.get("close"), errors="coerce")
