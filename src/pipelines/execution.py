"""Generate minute-level execution plan based on watch pool and 5min bars."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from src.data_fetcher.minute import MINUTE_FIELDS, fetch_minute_bars
from src.logging import get_logger
from src.utils.watch_pool import load_watch_pool

from ..execution.rules import evaluate_entry_signal

LOGGER = get_logger("pipelines.execution")


@dataclass
class ExecutionContext:
    watch_pool_path: Path
    minute_dir: Path
    orders_path: Path
    frequency: str
    limit: int
    fetch_enabled: bool
    session_start: str
    session_end: str


def build_execution_context(settings: Dict) -> ExecutionContext:
    data_cfg = settings.get("data", {})
    exec_cfg = settings.get("execution", {})
    minute_dir = Path(exec_cfg.get("minute_dir") or data_cfg.get("minute_dir", "data/minute"))
    orders_path = Path(exec_cfg.get("orders_path", "data/execution/pending_orders.csv"))
    pool_path = Path(settings.get("watchlist", {}).get("pool", {}).get("path", "data/watchlists/watch_pool.csv"))
    return ExecutionContext(
        watch_pool_path=pool_path,
        minute_dir=minute_dir,
        orders_path=orders_path,
        frequency=exec_cfg.get("frequency", "5min"),
        limit=int(exec_cfg.get("limit", 300)),
        fetch_enabled=bool(exec_cfg.get("fetch_enabled", False)),
        session_start=exec_cfg.get("session_start", "09:25:00"),
        session_end=exec_cfg.get("session_end", "15:05:00"),
    )


def run_execution_pipeline(settings: Dict) -> None:
    ctx = build_execution_context(settings)
    pool_df = load_watch_pool(ctx.watch_pool_path)
    active = pool_df[pool_df["status"] == "active"]
    if active.empty:
        LOGGER.info("Watch pool has no active entries; skipping execution plan.")
        _write_orders(ctx.orders_path, [])
        return

    symbols = active["ts_code"].dropna().astype(str).tolist()
    minute_map = _load_minute_data(ctx, symbols)
    if not minute_map:
        LOGGER.warning("No minute data available; cannot generate orders.")
        _write_orders(ctx.orders_path, [])
        return

    orders: List[Dict] = []
    for _, row in active.iterrows():
        symbol = row["ts_code"]
        minute_df = minute_map.get(symbol)
        if minute_df is None or minute_df.empty:
            continue
        signal = evaluate_entry_signal(symbol, minute_df)
        if not signal:
            continue
        signal.update(
            {
                "tier": row.get("tier"),
                "env": row.get("env"),
                "env_score": row.get("env_score"),
                "last_seen": row.get("last_seen"),
            }
        )
        orders.append(signal)

    _write_orders(ctx.orders_path, orders)
    LOGGER.info("Execution plan generated with %s pending orders -> %s", len(orders), ctx.orders_path)


def _load_minute_data(ctx: ExecutionContext, symbols: List[str]) -> Dict[str, pd.DataFrame]:
    ctx.minute_dir.mkdir(parents=True, exist_ok=True)
    loaded: Dict[str, pd.DataFrame] = {}
    if ctx.fetch_enabled and symbols:
        today = datetime.now().strftime("%Y-%m-%d")
        start = f"{today} {ctx.session_start}"
        end = f"{today} {ctx.session_end}"
        fetched = fetch_minute_bars(symbols, start=start, end=end, frequency=ctx.frequency, limit=ctx.limit)
        for symbol, frame in fetched.items():
            _persist_minutes(ctx.minute_dir, symbol, frame)

    for symbol in symbols:
        path = ctx.minute_dir / f"{symbol}.csv"
        if not path.exists():
            continue
        try:
            df = pd.read_csv(path)
        except Exception:
            continue
        if df.empty:
            continue
        df = df.sort_values("trade_time")
        loaded[symbol] = df
    return loaded


def _persist_minutes(minute_dir: Path, symbol: str, frame: pd.DataFrame) -> None:
    if frame is None or frame.empty:
        return
    minute_dir.mkdir(parents=True, exist_ok=True)
    path = minute_dir / f"{symbol}.csv"
    if path.exists():
        try:
            existing = pd.read_csv(path)
        except Exception:
            existing = pd.DataFrame(columns=MINUTE_FIELDS)
        frame = pd.concat([existing, frame], ignore_index=True)
    frame = frame.drop_duplicates(subset="trade_time", keep="last").sort_values("trade_time")
    frame.to_csv(path, index=False)


def _write_orders(path: Path, rows: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "ts_code",
        "action",
        "price",
        "confidence",
        "reason",
        "trigger_time",
        "tier",
        "env",
        "env_score",
        "last_seen",
    ]
    if rows:
        pd.DataFrame(rows, columns=columns).to_csv(path, index=False, float_format="%.6f")
    else:
        path.write_text(",".join(columns) + "\n", encoding="utf-8")
