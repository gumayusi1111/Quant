"""Utility helpers for watchlist backtest."""

from __future__ import annotations

from typing import Any, Optional

import pandas as pd


def normalize_date(value: Any) -> str:
    """Convert trade_date values (float/int/str) into YYYYMMDD strings."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    try:
        return str(int(float(value)))
    except (ValueError, TypeError):
        return str(value)
