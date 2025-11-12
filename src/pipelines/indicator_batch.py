"""Batch compute technical indicators for cached daily data."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pandas as pd

from src.indicator_engine.calculator import compute_indicators
from src.logging import get_logger

LOGGER = get_logger("pipelines.indicators")


@dataclass
class IndicatorContext:
    daily_dir: Path
    indicators_dir: Path


def build_indicator_context(settings: Dict) -> IndicatorContext:
    data_cfg = settings.get("data", {})
    return IndicatorContext(
        daily_dir=Path(data_cfg.get("daily_dir", "data/daily")),
        indicators_dir=Path(data_cfg.get("indicators_dir", "data/indicators")),
    )


def run_indicator_batch(settings: Dict, symbols: Optional[Iterable[str]] = None) -> None:
    ctx = build_indicator_context(settings)
    ctx.indicators_dir.mkdir(parents=True, exist_ok=True)
    if not ctx.daily_dir.exists():
        LOGGER.error("Daily directory %s missing. Run full-pool refresh first.", ctx.daily_dir)
        return

    symbol_filter = _resolve_symbol_filter(settings, symbols)
    if symbol_filter:
        files = []
        missing = []
        for symbol in symbol_filter:
            path = ctx.daily_dir / f"{symbol}.csv"
            if path.exists():
                files.append(path)
            else:
                missing.append(symbol)
        if missing:
            LOGGER.warning("Skipping %s symbols missing daily cache: %s", len(missing), ", ".join(sorted(missing)[:10]))
    else:
        files = sorted(ctx.daily_dir.glob("*.csv"))

    if not files:
        LOGGER.warning("No daily files found for indicator batch.")
        return

    total = len(files)
    LOGGER.info("Starting indicator batch for %s symbols.", total)

    processed = 0
    for idx, file_path in enumerate(files, start=1):
        symbol = file_path.stem
        df = pd.read_csv(file_path)
        indicators = compute_indicators(df)
        if indicators.empty:
            LOGGER.warning("No data for %s; skipping.", symbol)
            continue
        out_path = ctx.indicators_dir / f"{symbol}.csv"
        indicators.to_csv(out_path, index=False, float_format="%.6f")
        processed += 1
        if idx % 50 == 0:
            LOGGER.info("Processed %s/%s files.", idx, total)

    LOGGER.info("Indicator batch complete. Generated %s files.", processed)


def _resolve_symbol_filter(settings: Dict, symbols: Optional[Iterable[str]]) -> Optional[set[str]]:
    if symbols:
        return set(symbols)
    active_cfg = settings.get("active_pool", {})
    universe_path = Path(active_cfg.get("universe_path", "data/universe/active_universe.csv"))
    if not universe_path.exists():
        LOGGER.warning("Active universe file %s not found; using all daily files.", universe_path)
        return None
    try:
        df = pd.read_csv(universe_path)
    except Exception as exc:  # pragma: no cover
        LOGGER.warning("Failed to read %s: %s; using all symbols.", universe_path, exc)
        return None
    if "ts_code" not in df.columns:
        LOGGER.warning("Active universe file %s lacks ts_code column; using all symbols.", universe_path)
        return None
    symbols = set(df["ts_code"].astype(str))
    LOGGER.info("Loaded %s active symbols from %s.", len(symbols), universe_path)
    return symbols
