"""Pipeline for detecting market regimes with modular components."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from src.logging import get_logger
from src.market import RegimeParams, detect_regime_states
from src.pipelines.active_pool import build_active_pool_context

LOGGER = get_logger("pipelines.market_regime")


@dataclass
class MarketRegimeContext:
    daily_dir: Path
    active_universe_path: Path
    output_path: Path
    segments_path: Path
    benchmarks: List[str]
    composite_limit: int
    regime_params: RegimeParams


def build_market_regime_context(settings: Dict) -> MarketRegimeContext:
    data_cfg = settings.get("data", {})
    active_ctx = build_active_pool_context(settings)
    guard_cfg = settings.get("market_guard", {})

    params = RegimeParams(
        ma_fast=guard_cfg.get("ma_fast", 60),
        ma_slow=guard_cfg.get("ma_slow", 120),
        trend_threshold=guard_cfg.get("trend_threshold", 0.002),
        macd_fast=guard_cfg.get("macd_fast", 12),
        macd_slow=guard_cfg.get("macd_slow", 26),
        macd_signal=guard_cfg.get("macd_signal", 9),
        rsi_period=guard_cfg.get("rsi_period", 14),
        bull_rsi=guard_cfg.get("bull_rsi", 55),
        bear_rsi=guard_cfg.get("bear_rsi", 45),
        vol_period=guard_cfg.get("vol_period", 14),
        high_vol_threshold=guard_cfg.get("high_vol_threshold", 0.02),
        low_vol_threshold=guard_cfg.get("low_vol_threshold", 0.01),
    )

    benchmarks = guard_cfg.get("benchmarks", [])
    return MarketRegimeContext(
        daily_dir=Path(data_cfg.get("daily_dir", "data/daily")),
        active_universe_path=active_ctx.universe_path,
        output_path=Path(guard_cfg.get("output_path", "data/backtests/market_regime.csv")),
        segments_path=Path(guard_cfg.get("segments_path", "data/backtests/market_regime_segments.csv")),
        benchmarks=benchmarks,
        composite_limit=int(guard_cfg.get("composite_limit", 100)),
        regime_params=params,
    )


def run_market_regime_detection(settings: Dict) -> None:
    ctx = build_market_regime_context(settings)
    ctx.output_path.parent.mkdir(parents=True, exist_ok=True)
    ctx.segments_path.parent.mkdir(parents=True, exist_ok=True)

    price_frames = _load_benchmark_frames(ctx.daily_dir, ctx.benchmarks)
    if not price_frames:
        LOGGER.warning("No benchmark price data found; building composite index from active universe.")
        composite_frame = _build_composite_frame(ctx)
        if composite_frame is None or composite_frame.empty:
            LOGGER.error("Unable to build composite index; aborting regime detection.")
            return
        price_frames = {"composite": composite_frame}

    regime_df = detect_regime_states(price_frames, ctx.regime_params)
    if regime_df.empty:
        LOGGER.error("Failed to classify regimes.")
        return

    regime_df.to_csv(ctx.output_path, index=False)
    _write_segments(regime_df, ctx.segments_path)
    summary = regime_df["regime"].value_counts().to_dict()
    LOGGER.info(
        "Market regime detection complete (%s rows). Distribution: %s",
        len(regime_df),
        summary,
    )


def _load_benchmark_frames(daily_dir: Path, benchmarks: List[str]) -> Dict[str, pd.DataFrame]:
    frames: Dict[str, pd.DataFrame] = {}
    for symbol in benchmarks:
        path = daily_dir / f"{symbol}.csv"
        if not path.exists():
            LOGGER.warning("Benchmark %s missing daily data at %s", symbol, path)
            continue
        df = pd.read_csv(path)
        if df.empty:
            continue
        frames[symbol] = df[["trade_date", "close_front_adj", "close", "high", "low"]].copy()
    return frames


def _build_composite_frame(ctx: MarketRegimeContext) -> Optional[pd.DataFrame]:
    if not ctx.active_universe_path.exists():
        return None
    universe = pd.read_csv(ctx.active_universe_path)
    symbols = universe["ts_code"].dropna().astype(str).tolist()
    symbols = symbols[: ctx.composite_limit]
    if not symbols:
        return None

    totals: Dict[str, float] = {}
    counts: Dict[str, int] = {}
    for symbol in symbols:
        path = ctx.daily_dir / f"{symbol}.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path, usecols=["trade_date", "close_front_adj", "close"])
        df["close"] = df["close_front_adj"].fillna(df["close"])
        df.dropna(subset=["close"], inplace=True)
        if df.empty:
            continue
        base = df["close"].iloc[0]
        if not base:
            continue
        df["normalized"] = df["close"] / base
        for _, row in df.iterrows():
            date = _normalize_date(row["trade_date"])
            val = float(row["normalized"])
            totals[date] = totals.get(date, 0.0) + val
            counts[date] = counts.get(date, 0) + 1

    if not totals:
        return None

    rows = []
    for date, total in totals.items():
        count = counts.get(date, 0)
        if count == 0:
            continue
        rows.append({"trade_date": date, "close": total / count})

    composite = pd.DataFrame(rows).sort_values("trade_date")
    return composite


def _write_segments(regime_df: pd.DataFrame, segments_path: Path) -> None:
    segments: List[Dict[str, str]] = []
    current = None
    start = None

    for _, row in regime_df.iterrows():
        date = row["date"]
        regime = row["regime"]
        if current is None:
            current = regime
            start = date
            prev = date
            continue
        if regime != current:
            segments.append(
                {"regime": current, "start": start, "end": prev, "days": _diff_days(start, prev)}
            )
            current = regime
            start = date
        prev = date

    if current is not None:
        segments.append(
            {"regime": current, "start": start, "end": prev, "days": _diff_days(start, prev)}
        )

    pd.DataFrame(segments).to_csv(segments_path, index=False)


def _diff_days(start: str, end: str) -> int:
    s = pd.to_datetime(_normalize_date(start), format="%Y%m%d")
    e = pd.to_datetime(_normalize_date(end), format="%Y%m%d")
    return int((e - s).days) + 1


def _normalize_date(value) -> str:
    text = str(value).split(".")[0]
    return text.zfill(8)
