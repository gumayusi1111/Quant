"""Runner for watchlist backtest."""

from __future__ import annotations

from typing import Dict

import pandas as pd

from src.logging import get_logger
from src.signal_generator import strategy_router

from .analytics import summarize_by_regime, summarize_trades
from .context import WatchlistBacktestContext, build_watchlist_backtest_context, load_market_regime, load_symbols
from .signals import build_signal_dataset
from .trades import simulate_trades

LOGGER = get_logger("backtester.watchlist")


def run_watchlist_backtest(settings: Dict) -> None:
    ctx = build_watchlist_backtest_context(settings)
    ctx.signals_path.parent.mkdir(parents=True, exist_ok=True)
    ctx.trades_path.parent.mkdir(parents=True, exist_ok=True)
    ctx.summary_path.parent.mkdir(parents=True, exist_ok=True)

    if not ctx.indicators_dir.exists() or not ctx.daily_dir.exists():
        LOGGER.error("Daily or indicator directory missing; run data pipelines first.")
        return

    symbols = load_symbols(ctx)
    if not symbols:
        LOGGER.warning("No symbols to backtest.")
        return

    strategy_router.configure_strategies(settings)
    regime_map = load_market_regime(ctx.regime_path)
    signals_df, symbol_inputs, buy_map = build_signal_dataset(ctx, symbols, regime_map)
    if signals_df.empty:
        LOGGER.warning("No signals generated for backtest.")
        return

    signals_df.to_csv(ctx.signals_path, index=False, float_format="%.6f")

    trades = simulate_trades(ctx, symbol_inputs, buy_map, regime_map)
    if not trades:
        LOGGER.warning("No trades simulated; check sell rules or filters.")
        return

    trades_df = pd.DataFrame(trades).sort_values(["entry_date", "ts_code"])
    trades_df.to_csv(ctx.trades_path, index=False, float_format="%.6f")

    summary_df = summarize_trades(trades_df)
    summary_df.to_csv(ctx.summary_path, index=False, float_format="%.6f")

    summary_regime = summarize_by_regime(trades_df)
    summary_regime.to_csv(ctx.summary_by_regime_path, index=False, float_format="%.6f")

    LOGGER.info(
        "Watchlist backtest complete. Signals=%s -> %s, Trades=%s -> %s",
        len(signals_df),
        ctx.signals_path,
        len(trades_df),
        ctx.trades_path,
    )
