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
PRICE_COLUMNS: Sequence[str] = ("open", "high", "low", "close", "pre_close")


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
        frame = frame.sort_values("trade_date")
        frame = _attach_adjustments(symbol, frame, _client, start_str, end_str)
        result[symbol] = frame
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
    cols = list(columns) + ["adj_factor"]
    for col in PRICE_COLUMNS:
        cols.append(f"{col}_front_adj")
        cols.append(f"{col}_back_adj")
    return pd.DataFrame(columns=cols)


def _attach_adjustments(
    symbol: str,
    frame: pd.DataFrame,
    client: ChinaDataClient,
    start_date: str | None,
    end_date: str | None,
) -> pd.DataFrame:
    adj = _fetch_adj_factors(symbol, client, start_date, end_date)
    if not adj.empty:
        frame = frame.merge(adj, on="trade_date", how="left")
    else:
        frame["adj_factor"] = 1.0
    frame["adj_factor"] = (
        frame["adj_factor"]
        .fillna(method="ffill")
        .fillna(method="bfill")
        .fillna(1.0)
        .astype(float)
    )
    latest_factor = frame["adj_factor"].iloc[-1] or 1.0
    first_factor = frame["adj_factor"].iloc[0] or 1.0
    for col in PRICE_COLUMNS:
        if col in frame.columns:
            frame[f"{col}_front_adj"] = frame[col] * frame["adj_factor"] / latest_factor
            frame[f"{col}_back_adj"] = frame[col] * frame["adj_factor"] / first_factor
    return frame


def _fetch_adj_factors(
    symbol: str,
    client: ChinaDataClient,
    start_date: str | None,
    end_date: str | None,
) -> pd.DataFrame:
    params = {
        "ts_code": symbol,
        "start_date": start_date,
        "end_date": end_date,
        "limit": 2000,
    }
    params = {k: v for k, v in params.items() if v}
    try:
        df = client.pro.fund_adj(**params)
    except Exception:  # pragma: no cover
        return pd.DataFrame(columns=["trade_date", "adj_factor"])
    if df is None or df.empty:
        return pd.DataFrame(columns=["trade_date", "adj_factor"])
    return df[["trade_date", "adj_factor"]]
