"""Simple minute-level execution rules."""

from __future__ import annotations

from typing import Dict, Optional

import pandas as pd


def evaluate_entry_signal(symbol: str, minute_df: pd.DataFrame) -> Optional[Dict]:
    if minute_df is None or minute_df.empty:
        return None
    df = minute_df.copy()
    if "close" not in df.columns or "trade_time" not in df.columns:
        return None
    df = df.sort_values("trade_time").reset_index(drop=True)
    window = min(5, len(df))
    df["rolling_max"] = df["close"].rolling(window=window, min_periods=1).max()
    df["rolling_min"] = df["close"].rolling(window=window, min_periods=1).min()
    last = df.iloc[-1]
    price = float(last["close"])
    trigger_time = str(last["trade_time"])
    high_ref = float(last["rolling_max"])
    low_ref = float(last["rolling_min"])

    if price >= high_ref:
        confidence = min(1.0, (price - low_ref) / price) if price else 0.3
        return {
            "ts_code": symbol,
            "action": "buy",
            "price": price,
            "confidence": round(confidence, 4),
            "reason": "5min_breakout",
            "trigger_time": trigger_time,
        }
    if price <= low_ref:
        confidence = min(1.0, (high_ref - price) / high_ref) if high_ref else 0.3
        return {
            "ts_code": symbol,
            "action": "sell_alert",
            "price": price,
            "confidence": round(confidence, 4),
            "reason": "5min_breakdown",
            "trigger_time": trigger_time,
        }
    return None
