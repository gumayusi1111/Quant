"""Backfill long-horizon daily data for all ETFs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

import pandas as pd

from src.data_fetcher.daily import fetch_daily_bars
from src.logging import get_logger

LOGGER = get_logger("pipelines.backfill_daily")


@dataclass
class BackfillDailyContext:
    master_path: Path
    daily_dir: Path
    start_date: str
    end_date: str
    batch_size: int


def build_backfill_context(settings: Dict) -> BackfillDailyContext:
    data_cfg = settings.get("data", {})
    full_cfg = settings.get("full_pool", {})
    hist_cfg = settings.get("history_backfill", {})
    end_date = hist_cfg.get("end_date") or datetime.now().strftime("%Y%m%d")
    return BackfillDailyContext(
        master_path=Path(full_cfg.get("master_path", "data/master/etf_master.csv")),
        daily_dir=Path(data_cfg.get("daily_dir", "data/daily")),
        start_date=hist_cfg.get("start_date", "20200101"),
        end_date=end_date,
        batch_size=int(hist_cfg.get("batch_size", 20)),
    )


def run_backfill_daily(settings: Dict) -> None:
    ctx = build_backfill_context(settings)
    if not ctx.master_path.exists():
        LOGGER.error("Master file %s missing; run --full-pool first.", ctx.master_path)
        return
    ctx.daily_dir.mkdir(parents=True, exist_ok=True)

    master_df = pd.read_csv(ctx.master_path)
    if "ts_code" not in master_df.columns:
        LOGGER.error("Master file %s has no ts_code column.", ctx.master_path)
        return
    symbols = master_df["ts_code"].dropna().astype(str).tolist()
    if not symbols:
        LOGGER.warning("No symbols found in master file; aborting backfill.")
        return

    LOGGER.info(
        "Starting daily backfill from %s to %s for %s symbols (batch=%s).",
        ctx.start_date,
        ctx.end_date,
        len(symbols),
        ctx.batch_size,
    )

    processed = 0
    for batch_idx, chunk in enumerate(_chunked(symbols, ctx.batch_size), start=1):
        frames = fetch_daily_bars(chunk, start=ctx.start_date, end=ctx.end_date)
        for symbol, frame in frames.items():
            if frame is None or frame.empty:
                LOGGER.warning("No daily data fetched for %s; skipping.", symbol)
                continue
            out_path = ctx.daily_dir / f"{symbol}.csv"
            frame.to_csv(out_path, index=False, float_format="%.6f")
            processed += 1
        LOGGER.info(
            "Processed batch %s/%s (symbols=%s, cumulative=%s).",
            batch_idx,
            _calc_total_batches(len(symbols), ctx.batch_size),
            len(chunk),
            processed,
        )

    LOGGER.info("Daily backfill complete. Updated %s symbols.", processed)


def _chunked(items: Sequence[str], size: int) -> Iterable[List[str]]:
    size = max(1, size)
    for idx in range(0, len(items), size):
        yield list(items[idx : idx + size])


def _calc_total_batches(total: int, size: int) -> int:
    size = max(1, size)
    return (total + size - 1) // size
