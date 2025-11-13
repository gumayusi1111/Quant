"""Signal dataset generation for watchlist backtest."""

from __future__ import annotations

from typing import Dict, List, Tuple

import pandas as pd

from src.signal_generator.strategy_router import generate_historical_signals

from .context import WatchlistBacktestContext
from .utils import normalize_date


def build_signal_dataset(
    ctx: WatchlistBacktestContext,
    symbols: List[str],
    regime_map: Dict[str, str],
) -> Tuple[pd.DataFrame, Dict[str, Tuple[pd.DataFrame, pd.DataFrame]], Dict[str, pd.DataFrame]]:
    """Generate historical buy signals and attach forward returns."""
    signal_rows: List[Dict] = []
    symbol_inputs: Dict[str, Tuple[pd.DataFrame, pd.DataFrame]] = {}
    buy_map: Dict[str, pd.DataFrame] = {}

    for symbol in symbols:
        ind_file = ctx.indicators_dir / f"{symbol}.csv"
        daily_file = ctx.daily_dir / f"{symbol}.csv"
        if not ind_file.exists() or not daily_file.exists():
            continue
        ind_df = pd.read_csv(ind_file)
        daily_df = pd.read_csv(daily_file)
        historical = generate_historical_signals(symbol, ind_df, daily_df, regime_map=regime_map)
        if historical.empty:
            continue
        enriched = _attach_forward_returns(historical, daily_df, ctx.horizons)
        signal_rows.extend(enriched)
        symbol_inputs[symbol] = (ind_df, daily_df)
        buy_map[symbol] = historical

    if not signal_rows:
        return pd.DataFrame(), {}, {}

    signals_df = pd.DataFrame(signal_rows)
    signals_df.sort_values(["trade_date", "ts_code"], inplace=True)
    return signals_df, symbol_inputs, buy_map


def _attach_forward_returns(signals: pd.DataFrame, daily_df: pd.DataFrame, horizons: List[int]) -> List[Dict]:
    if signals.empty:
        return []

    daily_sorted = daily_df.sort_values("trade_date").reset_index(drop=True)
    daily_sorted["close_adj"] = daily_sorted.get("close_front_adj", daily_sorted.get("close"))
    date_to_index = {normalize_date(row["trade_date"]): idx for idx, row in daily_sorted.iterrows()}

    enriched: List[Dict] = []
    for _, row in signals.iterrows():
        date = normalize_date(row["trade_date"])
        idx = date_to_index.get(date)
        if idx is None:
            continue
        entry_price = daily_sorted.at[idx, "close_adj"]
        record = row.to_dict()
        record["entry_price"] = entry_price
        for horizon in horizons:
            target_idx = idx + horizon
            col = f"ret_{horizon}"
            if target_idx >= len(daily_sorted):
                record[col] = None
                continue
            future_price = daily_sorted.at[target_idx, "close_adj"]
            if entry_price and future_price:
                record[col] = round(float(future_price) / float(entry_price) - 1, 6)
            else:
                record[col] = None
        enriched.append(record)
    return enriched
