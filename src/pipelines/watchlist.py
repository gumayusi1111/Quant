"""Generate watchlist candidates based on indicator signals."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from src.logging import get_logger
from src.signal_generator import strategy_router
from src.signal_generator.universe_filters import configure as configure_filters
from src.signal_generator.universe_filters import evaluate as evaluate_filter
from src.strategy_etf.position_manager import recommend_weight
from src.utils.watch_pool import POOL_COLUMNS, days_between, infer_today, load_watch_pool, save_watch_pool

LOGGER = get_logger("pipelines.watchlist")


@dataclass
class WatchlistContext:
    indicators_dir: Path
    daily_dir: Path
    universe_path: Path
    output_path: Path
    position_config: Dict
    top_n: Optional[int]
    pool_path: Path
    pool_expiry_days: int


def build_watchlist_context(settings: Dict) -> WatchlistContext:
    data_cfg = settings.get("data", {})
    watch_cfg = settings.get("watchlist", {})
    pool_cfg = watch_cfg.get("pool", {})
    return WatchlistContext(
        indicators_dir=Path(data_cfg.get("indicators_dir", "data/indicators")),
        daily_dir=Path(data_cfg.get("daily_dir", "data/daily")),
        universe_path=Path(settings.get("active_pool", {}).get("universe_path", "data/universe/active_universe.csv")),
        output_path=Path(watch_cfg.get("path", "data/watchlists/watchlist_today.csv")),
        position_config=settings.get("positions", {}),
        top_n=watch_cfg.get("top_n"),
        pool_path=Path(pool_cfg.get("path", "data/watchlists/watch_pool.csv")),
        pool_expiry_days=int(pool_cfg.get("expiry_days", 10)),
    )


def run_watchlist_pipeline(settings: Dict) -> None:
    ctx = build_watchlist_context(settings)
    if not ctx.indicators_dir.exists():
        LOGGER.error("Indicators directory %s missing. Run --indicators first.", ctx.indicators_dir)
        return
    if not ctx.universe_path.exists():
        LOGGER.error("Active universe file %s missing. Run --active-pool first.", ctx.universe_path)
        return

    symbols = _load_active_symbols(ctx.universe_path)
    if not symbols:
        LOGGER.warning("No active symbols found; watchlist not generated.")
        return

    strategy_router.configure_strategies(settings)
    configure_filters(settings.get("watchlist", {}).get("filters", {}))
    current_regime = strategy_router.get_current_regime()
    candidates: List[Dict] = []
    for symbol in symbols:
        ind_file = ctx.indicators_dir / f"{symbol}.csv"
        if not ind_file.exists():
            LOGGER.warning("Indicator file %s missing; skipping.", ind_file)
            continue
        daily_file = ctx.daily_dir / f"{symbol}.csv"
        if not daily_file.exists():
            LOGGER.warning("Daily file %s missing; skipping.", daily_file)
            continue

        ind_df = pd.read_csv(ind_file)
        daily_df = pd.read_csv(daily_file)

        filter_result = evaluate_filter(current_regime, symbol, ind_df, daily_df)
        if not filter_result:
            continue

        row = strategy_router.generate_latest_signal(symbol, ind_df, daily_df, regime=current_regime)
        if not row:
            continue

        trade_date = row.pop("trade_date", None)
        row["date"] = _format_trade_date(trade_date)
        row["tier"] = filter_result.tier
        row["env_score"] = filter_result.score
        for key, value in (filter_result.metadata or {}).items():
            if value is not None:
                row[key] = value
        row["env_regime"] = current_regime
        row["position_weight"] = recommend_weight(ctx.position_config, current_regime, filter_result.tier)
        candidates.append(row)

    ctx.output_path.parent.mkdir(parents=True, exist_ok=True)
    ctx.pool_path.parent.mkdir(parents=True, exist_ok=True)
    if candidates:
        df = pd.DataFrame(candidates)
        df["tier_priority"] = df["tier"].map({"A": 0, "B": 1, "C": 2}).fillna(3)
        sort_cols = ["tier_priority", "env_score", "score", "turnover"]
        df.sort_values(by=sort_cols, ascending=[True, False, False, False], inplace=True)
        if ctx.top_n:
            df = df.head(int(ctx.top_n))
        df.drop(columns=["tier_priority"], inplace=True)
        df.to_csv(ctx.output_path, index=False, float_format="%.6f")
        LOGGER.info("Watchlist generated with %s symbols -> %s", len(df), ctx.output_path)
    else:
        LOGGER.info("No symbols matched watchlist criteria. Clearing output file.")
        ctx.output_path.write_text("ts_code,date,close,pct_chg,score\n", encoding="utf-8")

    _update_watch_pool(ctx, candidates)


def _load_active_symbols(path: Path) -> List[str]:
    df = pd.read_csv(path)
    if "ts_code" not in df.columns:
        LOGGER.warning("Active universe file %s lacks ts_code column.", path)
        return []
    return df["ts_code"].dropna().astype(str).tolist()


def _format_trade_date(value):
    if value is None or pd.isna(value):
        return None
    try:
        return str(int(value))
    except (ValueError, TypeError):
        return str(value)


POOL_COLUMNS = [
    "ts_code",
    "first_seen",
    "last_seen",
    "tier",
    "last_score",
    "env",
    "env_score",
    "status",
    "days_inactive",
]


def _update_watch_pool(ctx: WatchlistContext, candidates: List[Dict]) -> None:
    pool_df = load_watch_pool(ctx.pool_path)
    today = infer_today(candidates)

    pool_map = {row["ts_code"]: row.copy() for _, row in pool_df.iterrows()}
    updated_entries: List[Dict] = []
    seen_codes = set()

    for row in candidates:
        code = row.get("ts_code")
        if not code:
            continue
        seen_codes.add(code)
        entry = pool_map.get(code, {})
        first_seen = entry.get("first_seen") or row.get("date") or today
        entry.update(
            {
                "ts_code": code,
                "first_seen": first_seen,
                "last_seen": row.get("date") or today,
                "tier": row.get("tier", entry.get("tier")),
                "last_score": row.get("score"),
                "env": row.get("env_regime"),
                "env_score": row.get("env_score"),
                "status": "active",
                "days_inactive": 0,
            }
        )
        pool_map[code] = entry

    for code, entry in pool_map.items():
        if code in seen_codes:
            updated_entries.append(entry)
            continue
        last_seen = entry.get("last_seen")
        days_inactive = days_between(today, last_seen)
        if days_inactive is None:
            days_inactive = ctx.pool_expiry_days + 1
        if days_inactive > ctx.pool_expiry_days:
            continue
        entry["status"] = "stale"
        entry["days_inactive"] = days_inactive
        updated_entries.append(entry)

    save_watch_pool(ctx.pool_path, updated_entries)
