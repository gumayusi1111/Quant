"""Backfill long-horizon daily data for all ETFs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
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


def run_incremental_daily(settings: Dict) -> None:
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
        LOGGER.warning("No symbols found in master file; aborting incremental update.")
        return

    LOGGER.info("Starting incremental daily update up to %s for %s symbols.", ctx.end_date, len(symbols))
    updated = 0
    for symbol in symbols:
        out_path = ctx.daily_dir / f"{symbol}.csv"
        last_trade = _get_last_trade_date(out_path)
        start_int = _coerce_int_date(_next_date(last_trade) if last_trade else ctx.start_date)
        end_int = _coerce_int_date(ctx.end_date)
        if start_int is None or end_int is None:
            LOGGER.warning("Invalid date for %s; skipping.", symbol)
            continue
        if start_int > end_int:
            continue
        start_date = f"{start_int:08d}"
        end_date = f"{end_int:08d}"
        try:
            frames = fetch_daily_bars([symbol], start=start_date, end=end_date)
            frame = frames.get(symbol)
            if frame is None or frame.empty:
                continue
            frame = _normalize_trade_dates(frame)
            if frame.empty:
                continue
            if out_path.exists():
                try:
                    existing = pd.read_csv(out_path)
                except Exception:
                    existing = pd.DataFrame()
                existing = _normalize_trade_dates(existing)
                combined = pd.concat([existing, frame], ignore_index=True)
            else:
                combined = frame
            combined = _normalize_trade_dates(combined)
            combined = combined.drop_duplicates(subset="trade_date").sort_values("trade_date")
            combined.to_csv(out_path, index=False, float_format="%.6f")
            updated += 1
        except Exception:  # pragma: no cover - logged for diagnostics
            LOGGER.exception("Incremental update failed for %s", symbol)
    LOGGER.info("Incremental daily update complete. Updated %s symbols.", updated)
    if updated:
        LOGGER.info("Recomputing indicators for updated universe.")
        from src.pipelines.indicator_batch import run_indicator_batch  # local import to avoid cycle

        run_indicator_batch(settings)


def _chunked(items: Sequence[str], size: int) -> Iterable[List[str]]:
    size = max(1, size)
    for idx in range(0, len(items), size):
        yield list(items[idx : idx + size])


def _calc_total_batches(total: int, size: int) -> int:
    size = max(1, size)
    return (total + size - 1) // size


def _get_last_trade_date(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path, usecols=["trade_date"])
    except Exception:
        return None
    if df.empty:
        return None
    return str(df["trade_date"].iloc[-1])


def _next_date(value: str | None) -> str:
    if not value:
        return "19000101"
    try:
        dt = datetime.strptime(value, "%Y%m%d") + timedelta(days=1)
    except (ValueError, TypeError):
        return str(value)
    return dt.strftime("%Y%m%d")


def _coerce_int_date(value: str | int | None) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.isdigit():
        return int(text)
    if text.endswith(".0") and text[:-2].isdigit():
        return int(text[:-2])
    try:
        return int(float(text))
    except ValueError:
        return None


def _normalize_trade_dates(frame: pd.DataFrame) -> pd.DataFrame:
    """Ensure trade_date is zero-padded string so sorting/dedup never mixes dtypes."""
    if "trade_date" not in frame.columns or frame.empty:
        return frame
    normalized = frame["trade_date"].apply(_format_trade_date)
    result = frame.copy()
    result["trade_date"] = normalized
    return result.dropna(subset=["trade_date"])


def _format_trade_date(value) -> str | None:
    coerced = _coerce_int_date(value)
    if coerced is None:
        return None
    return f"{coerced:08d}"
