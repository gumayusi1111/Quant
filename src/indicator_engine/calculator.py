"""Batch indicator calculator."""

from __future__ import annotations

from typing import Iterable, List

import pandas as pd

from . import (
    asi,
    bias,
    bbi,
    boll,
    dma,
    dmi,
    dpo,
    expma,
    kdj,
    macd,
    ma,
    mtm,
    obv,
    rsi,
    sar,
    trix,
    vr,
    wr,
)
from .volume.arbr import arbr


MA_WINDOWS = (5, 10, 20, 30, 60)


def compute_indicators(daily_df: pd.DataFrame) -> pd.DataFrame:
    """Compute all default indicators for a symbol."""
    if daily_df.empty:
        return pd.DataFrame()

    df = daily_df.sort_values("trade_date").copy()
    df = df.reset_index(drop=True)

    idx = pd.Index(df["trade_date"], name="trade_date")
    price = _resolve_series(df, "close_front_adj", "close", idx)
    high = _resolve_series(df, "high_front_adj", "high", idx)
    low = _resolve_series(df, "low_front_adj", "low", idx)
    open_ = _resolve_series(df, "open_front_adj", "open", idx)
    volume = df.get("vol")
    if volume is None:
        volume = df.get("volume")
    if volume is not None:
        volume = pd.Series(pd.to_numeric(volume, errors="coerce").values, index=idx)

    result = pd.DataFrame(index=idx)

    # Moving averages
    for window in MA_WINDOWS:
        result[f"ma{window}"] = ma(price, window)

    expma_df = expma(price)
    for column in expma_df.columns:
        result[column] = expma_df[column]

    macd_df = macd(price)
    for column in macd_df.columns:
        result[f"macd_{column}"] = macd_df[column]

    kdj_df = kdj(high, low, price)
    for column in kdj_df.columns:
        result[f"kdj_{column.lower()}"] = kdj_df[column]

    rsi_df = rsi(price, periods=(6, 12, 24))
    for column in rsi_df.columns:
        result[column] = rsi_df[column]

    boll_df = boll(price)
    for column in boll_df.columns:
        result[column] = boll_df[column]

    wr_df = wr(high, low, price, periods=(10, 6))
    for column in wr_df.columns:
        result[column] = wr_df[column]

    dmi_df = dmi(high, low, price)
    for col in dmi_df.columns:
        name = col.replace("+", "plus").replace("-", "minus")
        result[f"dmi_{name.lower()}"] = dmi_df[col]

    bias_df = bias(price)
    for column in bias_df.columns:
        result[column] = bias_df[column]

    asi_df = asi(open_, high, low, price)
    for column in asi_df.columns:
        result[column.lower()] = asi_df[column]

    if volume is not None:
        result["vr"] = vr(price, volume)
        arbr_df = arbr(high, low, open_, price)
        for column in arbr_df.columns:
            result[column.lower()] = arbr_df[column]
        obv_df = obv(price, volume)
        for column in obv_df.columns:
            result[column.lower()] = obv_df[column]

    dpo_df = dpo(price)
    for column in dpo_df.columns:
        result[column.lower()] = dpo_df[column]

    trix_df = trix(price)
    for column in trix_df.columns:
        result[column.lower()] = trix_df[column]

    dma_df = dma(price)
    for column in dma_df.columns:
        result[column.lower()] = dma_df[column]

    result["bbi"] = bbi(price)

    mtm_df = mtm(price)
    for column in mtm_df.columns:
        result[column.lower()] = mtm_df[column]

    result["sar"] = sar(high, low)

    result.reset_index(inplace=True)
    result = _round_numeric(result, decimals=6)
    return result


def _resolve_series(df: pd.DataFrame, primary: str, fallback: str, idx: pd.Index) -> pd.Series:
    if primary in df.columns:
        series = df[primary]
    else:
        series = df[fallback]
    return pd.Series(pd.to_numeric(series, errors="coerce").values, index=idx)


def _round_numeric(df: pd.DataFrame, decimals: int = 6) -> pd.DataFrame:
    for column in df.columns:
        if pd.api.types.is_numeric_dtype(df[column]):
            df[column] = df[column].round(decimals)
    return df


def format_numeric(value, decimals: int = 6) -> str:
    if pd.isna(value):
        return ""
    return f"{float(value):.{decimals}f}"
