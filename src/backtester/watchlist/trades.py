"""Trade simulation using sell rules."""

from __future__ import annotations

import json
from typing import Dict, List, Optional, Tuple

import pandas as pd

from src.signal_generator.sell_rules import SellSignalResult, evaluate_sell_signal, prepare_daily_features
from src.strategy_etf.position_manager import recommend_weight

from .context import WatchlistBacktestContext
from .utils import normalize_date


def simulate_trades(
    ctx: WatchlistBacktestContext,
    symbol_inputs: Dict[str, Tuple[pd.DataFrame, pd.DataFrame]],
    buy_map: Dict[str, pd.DataFrame],
    regime_map: Dict[str, str],
) -> List[Dict]:
    trades: List[Dict] = []
    for symbol, (ind_df, daily_df) in symbol_inputs.items():
        buy_df = buy_map.get(symbol)
        if buy_df is None or buy_df.empty:
            continue

        ind_sorted = ind_df.sort_values("trade_date").reset_index(drop=True)
        ind_sorted["trade_date"] = ind_sorted["trade_date"].apply(normalize_date)
        idx_map = {row["trade_date"]: idx for idx, row in ind_sorted.iterrows()}

        daily_feat = prepare_daily_features(daily_df)
        daily_map = {row["trade_date"]: row for _, row in daily_feat.iterrows()}

        buy_df = buy_df.sort_values("trade_date").reset_index(drop=True)
        buy_df["trade_date"] = buy_df["trade_date"].apply(normalize_date)

        last_exit_idx = -1
        for _, buy_row in buy_df.iterrows():
            entry_date = buy_row["trade_date"]
            buy_idx = idx_map.get(entry_date)
            if buy_idx is None or buy_idx <= last_exit_idx:
                continue

            daily_entry = daily_map.get(entry_date)
            if daily_entry is None:
                continue
            entry_price = _price_from_daily(daily_entry)
            if entry_price is None:
                continue

            entry_regime = regime_map.get(entry_date, "bull")

            exit_idx, exit_result = _find_exit(
                ind_sorted,
                buy_idx,
                daily_map,
                ctx.max_hold_days,
                regime_map,
                entry_regime,
            )
            exit_date = ind_sorted.iloc[exit_idx]["trade_date"]
            daily_exit = daily_map.get(exit_date)
            if daily_exit is None:
                continue
            exit_price = _price_from_daily(daily_exit)
            if exit_price is None:
                continue

            hold_days = exit_idx - buy_idx
            trade_return = (exit_price / entry_price) - 1
            last_exit_idx = exit_idx

            core_hits = {k: bool(v) for k, v in exit_result.core_hits.items()}
            aux_hits = {k: bool(v) for k, v in exit_result.aux_hits.items()}
            weight = recommend_weight(ctx.position_config, entry_regime, buy_row.get("tier", "C"))
            trades.append(
                {
                    "ts_code": symbol,
                    "tier": buy_row.get("tier"),
                    "entry_date": entry_date,
                    "exit_date": exit_date,
                    "entry_price": round(entry_price, 6),
                    "exit_price": round(exit_price, 6),
                    "return": round(trade_return, 6),
                    "hold_days": hold_days,
                    "exit_reason": exit_result.reason,
                    "sell_score": round(exit_result.score, 4),
                    "exit_action": exit_result.action,
                    "core_hits": json.dumps(core_hits),
                    "aux_hits": json.dumps(aux_hits),
                    "entry_regime": entry_regime,
                    "position_weight": round(weight, 4),
                }
            )
    return trades


def _find_exit(
    indicators: pd.DataFrame,
    start_idx: int,
    daily_map: Dict[str, pd.Series],
    max_hold: int,
    regime_map: Dict[str, str],
    default_regime: str,
) -> Tuple[int, SellSignalResult]:
    for offset in range(1, max_hold + 1):
        idx = start_idx + offset
        if idx >= len(indicators):
            break
        trade_date = indicators.iloc[idx]["trade_date"]
        daily_row = daily_map.get(trade_date)
        if daily_row is None:
            continue
        prev_row = indicators.iloc[idx - 1]
        prev_daily = daily_map.get(prev_row["trade_date"])
        regime = regime_map.get(trade_date, default_regime)
        result = evaluate_sell_signal(indicators, idx, daily_row, prev_row, prev_daily, regime)
        if result.triggered:
            return idx, result
    exit_idx = min(start_idx + max_hold, len(indicators) - 1)
    placeholder = SellSignalResult(False, "time", {}, {}, 0.0, "time")
    return exit_idx, placeholder


def _price_from_daily(daily_row: pd.Series) -> Optional[float]:
    price = daily_row.get("close_front_adj")
    if price is None or pd.isna(price):
        price = daily_row.get("close")
    return float(price) if price is not None and not pd.isna(price) else None
