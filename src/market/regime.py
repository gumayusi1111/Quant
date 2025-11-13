"""Market regime detection based on trend + volatility features."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

from src.indicator_engine import macd as macd_fn
from src.indicator_engine import rsi as rsi_fn


@dataclass
class RegimeParams:
    ma_fast: int = 60
    ma_slow: int = 120
    trend_threshold: float = 0.002
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    rsi_period: int = 14
    bull_rsi: float = 55.0
    bear_rsi: float = 45.0
    vol_period: int = 14
    high_vol_threshold: float = 0.02
    low_vol_threshold: float = 0.01


def detect_regime_states(
    price_frames: Dict[str, pd.DataFrame],
    params: RegimeParams,
) -> pd.DataFrame:
    """Return combined regime states from benchmark price frames."""
    states: List[pd.DataFrame] = []
    for symbol, frame in price_frames.items():
        features = _prepare_features(frame.copy(), params)
        classification = _classify(features, params)
        classification = classification.rename(columns={"regime": symbol})
        classification.set_index("trade_date", inplace=True)
        states.append(classification)

    if not states:
        return pd.DataFrame()

    merged = pd.concat(states, axis=1, join="inner").dropna()
    merged["bull_count"] = (merged == "bull").sum(axis=1)
    merged["bear_count"] = (merged == "bear").sum(axis=1)
    total = len(states)

    def _vote(row) -> str:
        if row["bull_count"] == total:
            return "bull"
        if row["bear_count"] == total:
            return "bear"
        if row["bull_count"] > row["bear_count"]:
            return "bull"
        if row["bear_count"] > row["bull_count"]:
            return "bear"
        return "sideways"

    merged["regime"] = merged.apply(_vote, axis=1)
    merged = merged[["regime"]]
    merged.index.name = "date"
    merged.reset_index(inplace=True)
    return merged


def _prepare_features(df: pd.DataFrame, params: RegimeParams) -> pd.DataFrame:
    df = df.sort_values("trade_date").copy()
    df["trade_date"] = df["trade_date"].apply(_normalize_date)

    available_cols = {"close_front_adj", "close", "high", "low"}
    for column in available_cols:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    close_col = "close_front_adj" if "close_front_adj" in df.columns else "close"
    if close_col not in df.columns:
        raise ValueError("Price frame missing close column.")
    df["close"] = pd.to_numeric(df[close_col], errors="coerce")

    df["ma_fast"] = df["close"].rolling(window=params.ma_fast, min_periods=params.ma_fast).mean()
    df["ma_slow"] = df["close"].rolling(window=params.ma_slow, min_periods=params.ma_slow).mean()

    macd_df = macd_fn(df["close"], fast=params.macd_fast, slow=params.macd_slow, signal=params.macd_signal)
    df["macd_hist"] = macd_df["macd"]

    rsi_df = rsi_fn(df["close"], periods=(params.rsi_period,))
    df["rsi"] = rsi_df[f"rsi{params.rsi_period}"]

    returns = df["close"].pct_change()
    df["volatility"] = returns.rolling(window=params.vol_period).std()

    df.dropna(subset=["ma_fast", "ma_slow", "macd_hist", "rsi", "volatility"], inplace=True)
    return df


def _classify(df: pd.DataFrame, params: RegimeParams) -> pd.DataFrame:
    threshold = params.trend_threshold
    df["trend_up"] = df["ma_fast"] > df["ma_slow"] * (1 + threshold)
    df["trend_down"] = df["ma_fast"] < df["ma_slow"] * (1 - threshold)

    df["momentum_up"] = df["macd_hist"] > 0
    df["momentum_down"] = df["macd_hist"] < 0

    df["vol_state"] = np.where(
        df["volatility"] >= params.high_vol_threshold,
        "high",
        np.where(df["volatility"] <= params.low_vol_threshold, "low", "mid"),
    )

    conditions = []
    for _, row in df.iterrows():
        if row["trend_up"] and row["momentum_up"] and row["rsi"] >= params.bull_rsi:
            conditions.append("bull")
        elif row["trend_down"] and row["momentum_down"] and row["rsi"] <= params.bear_rsi:
            conditions.append("bear")
        else:
            conditions.append("sideways")
    df["regime"] = conditions
    return df[["trade_date", "regime"]]


def _normalize_date(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).split(".")[0]
    return text.zfill(8)
