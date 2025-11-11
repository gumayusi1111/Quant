"""Minute-level bar fetch helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterable

import pandas as pd

from src.data_fetcher.tushare_client import TushareClient, build_tushare_client

DEFAULT_MINUTE_LIMIT = 500
MINUTE_FIELDS = [
    "ts_code",
    "trade_time",
    "open",
    "high",
    "low",
    "close",
    "vol",
    "amount",
    "pre_close",
    "pct_chg",
]


def fetch_minute_bars(
    symbols: Iterable[str],
    start: datetime | str | None = None,
    end: datetime | str | None = None,
    client: TushareClient | None = None,
    frequency: str = "5min",
    limit: int = DEFAULT_MINUTE_LIMIT,
) -> Dict[str, pd.DataFrame]:
    """Fetch minute bars via official Tushare package."""
    _client = client or build_tushare_client()
    start_str = _to_timestamp(start)
    end_str = _to_timestamp(end)
    result: Dict[str, pd.DataFrame] = {}
    for symbol in symbols:
        params = {
            "ts_code": symbol,
            "freq": frequency,
            "start_date": start_str,
            "end_date": end_str,
            "limit": limit,
            "fields": ",".join(MINUTE_FIELDS),
        }
        params = {key: value for key, value in params.items() if value}
        try:
            frame = _client.pro.stk_mins(**params)
        except Exception:  # pragma: no cover - actual API failure
            result[symbol] = pd.DataFrame(columns=MINUTE_FIELDS)
            continue
        if frame is None or frame.empty:
            result[symbol] = pd.DataFrame(columns=MINUTE_FIELDS)
            continue
        result[symbol] = frame.sort_values("trade_time")
    return result


def _to_timestamp(value: datetime | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return value.strftime("%Y-%m-%d %H:%M:%S")
