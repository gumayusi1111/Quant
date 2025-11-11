"""Active pool refresh: derive tradable universe based on liquidity filters."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

import pandas as pd

from src.logging import get_logger

LOGGER = get_logger("pipelines.active_pool")


@dataclass
class ActivePoolContext:
    universe_path: Path
    daily_dir: Path
    master_path: Path
    filters: Dict[str, float]
    refresh_interval_days: int


def build_active_pool_context(settings: Dict) -> ActivePoolContext:
    data_cfg = settings.get("data", {})
    active_cfg = settings.get("active_pool", {})
    full_cfg = settings.get("full_pool", {})
    return ActivePoolContext(
        universe_path=Path(active_cfg.get("universe_path", "data/universe/active_universe.csv")),
        daily_dir=Path(data_cfg.get("daily_dir", "data/daily")),
        master_path=Path(full_cfg.get("master_path", "data/master/etf_master.csv")),
        filters=active_cfg.get("filters", {}),
        refresh_interval_days=active_cfg.get("refresh_interval_days", 7),
    )


def run_active_pool_refresh(settings: Dict) -> None:
    ctx = build_active_pool_context(settings)
    ctx.universe_path.parent.mkdir(parents=True, exist_ok=True)
    if not ctx.master_path.exists():
        LOGGER.error("Master file %s missing. Run full-pool refresh first.", ctx.master_path)
        return

    if not _needs_refresh(ctx.universe_path, ctx.refresh_interval_days):
        LOGGER.info("Active pool refresh skipped: %s updated recently.", ctx.universe_path)
        return

    master_df = pd.read_csv(ctx.master_path)
    metrics = _compute_metrics(master_df, ctx.daily_dir)
    filtered = _apply_filters(metrics, ctx.filters)

    filtered.sort_values("mean_amount_60", ascending=False, inplace=True)
    filtered.to_csv(ctx.universe_path, index=False)
    LOGGER.info(
        "Active pool refresh complete. Selected %s symbols out of %s.",
        len(filtered),
        len(metrics),
    )


def _needs_refresh(path: Path, refresh_interval_days: int) -> bool:
    if not path.exists():
        return True
    modified = datetime.fromtimestamp(path.stat().st_mtime)
    return (datetime.now() - modified).days >= max(1, refresh_interval_days)


def _compute_metrics(master_df: pd.DataFrame, daily_dir: Path) -> pd.DataFrame:
    rows: List[Dict] = []
    for _, row in master_df.iterrows():
        ts_code = row["ts_code"]
        daily_path = daily_dir / f"{ts_code}.csv"
        if not daily_path.exists():
            continue
        df = pd.read_csv(daily_path).tail(60)
        if df.empty:
            continue
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
        df["vol"] = pd.to_numeric(df["vol"], errors="coerce")
        df["open"] = pd.to_numeric(df["open"], errors="coerce")
        df["high"] = pd.to_numeric(df["high"], errors="coerce")
        df["low"] = pd.to_numeric(df["low"], errors="coerce")
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df = df.dropna(subset=["amount", "vol", "close"])
        if df.empty:
            continue
        amount = df["amount"].clip(lower=0)
        mean_amount = amount.mean()
        median_amount = amount.median()
        floor_amount = amount.quantile(0.1)
        trade_days_ratio = (df["vol"] > 0).mean()
        median_range = ((df["high"] - df["low"]) / df["close"]).median()
        recent_close = df["close"].iloc[-1]
        listed_days = _calc_listed_days(row.get("list_date"))
        rows.append(
            {
                "ts_code": ts_code,
                "name": row.get("name", ""),
                "mean_amount_60": mean_amount,
                "median_amount_60": median_amount,
                "floor_amount_60": floor_amount,
                "trade_days_ratio_60": trade_days_ratio,
                "median_range_60": median_range,
                "recent_close": recent_close,
                "listed_days": listed_days,
            }
        )
    metrics = pd.DataFrame(rows)
    LOGGER.info("Computed metrics for %s symbols.", len(metrics))
    return metrics


def _calc_listed_days(list_date: str | float | None) -> int:
    if not list_date or pd.isna(list_date):
        return 0
    try:
        date_obj = datetime.strptime(str(int(list_date)), "%Y%m%d")
    except ValueError:
        return 0
    return (datetime.utcnow() - date_obj).days


def _apply_filters(metrics: pd.DataFrame, filters: Dict[str, float]) -> pd.DataFrame:
    if metrics.empty:
        return metrics
    filtered = metrics.copy()
    min_listed = filters.get("listed_days_min", 90)
    min_trade_ratio = filters.get("trade_days_ratio_60", 0.8)
    min_price = filters.get("min_price", 0.5)
    max_range = filters.get("max_range", 0.06)
    min_mean_amount = filters.get("mean_amount_60", 50_000_000)
    min_median_amount = filters.get("median_amount_60", 30_000_000)
    min_floor_amount = filters.get("floor_amount_60", 20_000_000)

    filtered = filtered[
        (filtered["listed_days"] >= min_listed)
        & (filtered["trade_days_ratio_60"] >= min_trade_ratio)
        & (filtered["recent_close"] >= min_price)
        & (filtered["median_range_60"] <= max_range)
        & (filtered["mean_amount_60"] >= min_mean_amount)
        & (filtered["median_amount_60"] >= min_median_amount)
        & (filtered["floor_amount_60"] >= min_floor_amount)
    ]

    if filtered.empty:
        LOGGER.warning(
            "Hard filters removed all symbols; consider relaxing thresholds in settings."
        )
        return filtered

    # Percentile-based refinement
    if not filtered.empty:
        p_mean = filtered["mean_amount_60"].quantile(0.6)
        p_median = filtered["median_amount_60"].quantile(0.55)
        p_floor = filtered["floor_amount_60"].quantile(0.45)
        p_days = filtered["trade_days_ratio_60"].quantile(0.6)
        filtered = filtered[
            (filtered["mean_amount_60"] >= min(p_mean, filtered["mean_amount_60"].max()))
            & (filtered["median_amount_60"] >= min(p_median, filtered["median_amount_60"].max()))
            & (filtered["floor_amount_60"] >= min(p_floor, filtered["floor_amount_60"].max()))
            & (filtered["trade_days_ratio_60"] >= min(p_days, filtered["trade_days_ratio_60"].max()))
        ]

    LOGGER.info("Percentile refinement retained %s symbols.", len(filtered))
    return filtered
