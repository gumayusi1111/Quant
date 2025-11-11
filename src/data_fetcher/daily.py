"""Daily bar fetch helpers."""

from __future__ import annotations

from datetime import date, datetime
from typing import Dict, Iterable, List, Sequence

import pandas as pd

from src.data_fetcher.chinadata_client import ChinaDataClient, build_chinadata_client

DEFAULT_FIELDS: Sequence[str] = (
    "ts_code",
    "trade_date",
    "open",
    "high",
    "low",
    "close",
    "vol",
    "amount",
    "pre_close",
    "pct_chg",
)


def fetch_daily_bars(
    symbols: Iterable[str],
    start: date | str | None = None,
    end: date | str | None = None,
    client: ChinaDataClient | None = None,
    fields: Sequence[str] | None = None,
    limit: int = 2000,
) -> Dict[str, pd.DataFrame]:
    """Fetch daily bars from chinadata for a list of symbols."""
    _client = client or build_chinadata_client()
    start_str = _to_datestr(start)
    end_str = _to_datestr(end)
    selected_fields = ",".join(fields or DEFAULT_FIELDS)
    result: Dict[str, pd.DataFrame] = {}
    for symbol in symbols:
        params = {
            "ts_code": symbol,
            "start_date": start_str,
            "end_date": end_str,
            "limit": limit,
            "fields": selected_fields,
        }
        params = {key: value for key, value in params.items() if value}
        try:
            frame = _client.pro.fund_daily(**params)
        except Exception as exc:  # pragma: no cover - API failure
            result[symbol] = _empty_frame(fields or DEFAULT_FIELDS)
            continue
        if frame is None or frame.empty:
            result[symbol] = _empty_frame(fields or DEFAULT_FIELDS)
            continue
        result[symbol] = frame.sort_values("trade_date")
    return result


def _to_datestr(value: date | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        return value.strftime("%Y%m%d")
    return value.strftime("%Y%m%d")


def _empty_frame(columns: Sequence[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=list(columns))
