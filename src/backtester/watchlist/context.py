"""Context and helpers for watchlist backtest."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd


@dataclass
class WatchlistBacktestContext:
    indicators_dir: Path
    daily_dir: Path
    universe_path: Optional[Path]
    signals_path: Path
    trades_path: Path
    summary_path: Path
    summary_by_regime_path: Path
    horizons: List[int]
    max_hold_days: int
    regime_path: Optional[Path]
    position_config: Dict


def build_watchlist_backtest_context(settings: Dict) -> WatchlistBacktestContext:
    data_cfg = settings.get("data", {})
    backtest_cfg = settings.get("watchlist_backtest", {})
    guard_cfg = settings.get("market_guard", {})

    universe_path = backtest_cfg.get("universe_path")
    summary_path = Path(backtest_cfg.get("summary_path", "data/backtests/watchlist_summary.csv"))
    summary_by_regime_path = summary_path.parent / "watchlist_summary_by_regime.csv"
    regime_path = guard_cfg.get("output_path")

    return WatchlistBacktestContext(
        indicators_dir=Path(data_cfg.get("indicators_dir", "data/indicators")),
        daily_dir=Path(data_cfg.get("daily_dir", "data/daily")),
        universe_path=Path(universe_path) if universe_path else None,
        signals_path=Path(backtest_cfg.get("signals_path", "data/backtests/watchlist_signals.csv")),
        trades_path=Path(backtest_cfg.get("trades_path", "data/backtests/watchlist_trades.csv")),
        summary_path=summary_path,
        summary_by_regime_path=summary_by_regime_path,
        horizons=backtest_cfg.get("horizons", [1, 3, 5]),
        max_hold_days=int(backtest_cfg.get("max_hold_days", 5)),
        regime_path=Path(regime_path) if regime_path else None,
        position_config=settings.get("positions", {}),
    )


def load_symbols(ctx: WatchlistBacktestContext) -> List[str]:
    if ctx.universe_path and ctx.universe_path.exists():
        df = pd.read_csv(ctx.universe_path)
        if "ts_code" in df.columns:
            return df["ts_code"].dropna().astype(str).tolist()
    return [file.stem for file in ctx.indicators_dir.glob("*.csv") if file.stem]


def load_market_regime(path: Optional[Path]) -> Dict[str, str]:
    if path and path.exists():
        df = pd.read_csv(path)
        return dict(zip(df["date"].astype(str), df["regime"]))
    return {}
