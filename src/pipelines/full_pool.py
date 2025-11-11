"""Full-pool refresh pipeline (ETFs master + 90-day history)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List

import pandas as pd

from src.data_fetcher import build_chinadata_client, fetch_daily_bars
from src.logging import get_logger

LOGGER = get_logger("pipelines.full_pool")


@dataclass
class FullPoolContext:
    history_days: int
    refresh_interval_days: int
    master_path: Path
    universe_path: Path
    daily_dir: Path
    chunk_size: int


def build_full_pool_context(settings: Dict) -> FullPoolContext:
    """Derive filesystem paths and parameters from settings.json."""
    data_cfg = settings.get("data", {})
    full_cfg = settings.get("full_pool", {})
    active_cfg = settings.get("active_pool", {})

    return FullPoolContext(
        history_days=full_cfg.get("history_days", 90),
        refresh_interval_days=full_cfg.get("refresh_interval_days", 60),
        master_path=Path(full_cfg.get("master_path", "data/master/etf_master.csv")),
        universe_path=Path(active_cfg.get("universe_path", "data/universe/active_universe.csv")),
        daily_dir=Path(data_cfg.get("daily_dir", "data/daily")),
        chunk_size=max(1, full_cfg.get("chunk_size", 25)),
    )


def run_full_pool_refresh(settings: Dict) -> None:
    """Entry for the 'every 60–90 days' full-pool refresh."""
    ctx = build_full_pool_context(settings)
    ctx.master_path.parent.mkdir(parents=True, exist_ok=True)
    ctx.universe_path.parent.mkdir(parents=True, exist_ok=True)
    ctx.daily_dir.mkdir(parents=True, exist_ok=True)

    if not _needs_refresh(ctx.master_path, ctx.refresh_interval_days):
        LOGGER.info(
            "Full-pool refresh skipped: %s was updated within %s days.",
            ctx.master_path,
            ctx.refresh_interval_days,
        )
        return

    cutoff = datetime.utcnow().date() - timedelta(days=ctx.history_days)
    start_time = datetime.utcnow()
    LOGGER.info("Starting full-pool refresh. Target history >= %s days.", ctx.history_days)
    client = build_chinadata_client()
    master_df = _fetch_etf_master(client)
    if master_df.empty:
        LOGGER.warning("ETf master fetch returned empty frame; aborting refresh.")
        return
    master_df.to_csv(ctx.master_path, index=False)
    LOGGER.info("Wrote master metadata to %s (rows=%s)", ctx.master_path, len(master_df))

    symbols = master_df["ts_code"].dropna().tolist()
    _cache_daily_history(
        symbols=symbols,
        ctx=ctx,
        client=client,
        start_date=cutoff.strftime("%Y%m%d"),
        end_date=datetime.utcnow().strftime("%Y%m%d"),
    )
    duration = datetime.utcnow() - start_time
    LOGGER.info(
        "Full-pool refresh complete. Master rows=%s, daily files=%s, duration=%s.",
        len(symbols),
        len(symbols),
        duration,
    )


def _needs_refresh(master_path: Path, refresh_interval_days: int) -> bool:
    if not master_path.exists():
        return True
    modified = datetime.fromtimestamp(master_path.stat().st_mtime)
    age_days = (datetime.now() - modified).days
    return age_days >= max(1, refresh_interval_days)


def _fetch_etf_master(client) -> pd.DataFrame:
    try:
        if hasattr(client.pro, "etf_basic"):
            df = client.pro.etf_basic(list_status="L")
        else:
            df = client.pro.fund_basic(list_status="L")
    except Exception as exc:  # pragma: no cover - remote failure
        LOGGER.error("Fetching ETF master failed: %s", exc)
        return pd.DataFrame()
    if df is None:
        return pd.DataFrame()
    filtered = df.copy()
    if "market" in filtered.columns:
        filtered = filtered[filtered["market"].str.upper().isin({"E", "EM"})]
    filtered = filtered[filtered["ts_code"].str.endswith((".SH", ".SZ"), na=False)]
    filtered = filtered.reset_index(drop=True)
    columns = [
        "ts_code",
        "csname",
        "index_code",
        "index_name",
        "mgr_name",
        "list_date",
        "list_status",
        "exchange",
    ]
    subset = filtered[columns] if all(col in filtered.columns for col in columns) else filtered
    LOGGER.info("ETF master filtered down to %s entries.", len(subset))
    return subset


def _cache_daily_history(
    symbols: List[str],
    ctx: FullPoolContext,
    client,
    start_date: str,
    end_date: str,
) -> None:
    total = len(symbols)
    LOGGER.info("Fetching %s symbols of daily history (start=%s end=%s).", total, start_date, end_date)
    total_chunks = (total + ctx.chunk_size - 1) // ctx.chunk_size
    for index, chunk in enumerate(_chunk(symbols, ctx.chunk_size), start=1):
        frames = fetch_daily_bars(
            symbols=chunk,
            start=start_date,
            end=end_date,
            client=client,
        )
        for symbol, frame in frames.items():
            _write_daily_file(ctx.daily_dir, symbol, frame)
        if index % 10 == 0 or index == total_chunks:
            LOGGER.info("Processed chunk %s/%s (symbols=%s)", index, total_chunks, len(chunk))


def _write_daily_file(daily_dir: Path, symbol: str, frame: pd.DataFrame) -> None:
    path = daily_dir / f"{symbol}.csv"
    if frame.empty:
        path.write_text("ts_code,trade_date,open,high,low,close,vol,amount\n", encoding="utf-8")
        return
    frame.to_csv(path, index=False)


def _chunk(items: Iterable[str], size: int) -> Iterable[List[str]]:
    chunk: List[str] = []
    for item in items:
        chunk.append(item)
        if len(chunk) >= size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk
