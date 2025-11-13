"""Auto pipeline: check timestamps and run required refreshes."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from src.logging import get_logger

from .active_pool import run_active_pool_refresh
from .backfill_daily import run_backfill_daily
from .full_pool import run_full_pool_refresh
from .indicator_batch import run_indicator_batch
from .watchlist import run_watchlist_pipeline
from .market_regime import run_market_regime_detection

LOGGER = get_logger("pipelines.auto")


def run_auto_pipeline(settings: Dict) -> None:
    """Main entry to orchestrate refreshes based on timestamps."""
    daily_dir = Path(settings.get("data", {}).get("daily_dir", "data/daily"))
    indicators_dir = Path(settings.get("data", {}).get("indicators_dir", "data/indicators"))
    master_path = Path(settings.get("full_pool", {}).get("master_path", "data/master/etf_master.csv"))
    universe_path = Path(settings.get("active_pool", {}).get("universe_path", "data/universe/active_universe.csv"))

    LOGGER.info("Starting auto pipeline...")

    if _needs_refresh(master_path, settings.get("full_pool", {}).get("refresh_interval_days", 60)):
        LOGGER.info("Full-pool data stale; running full-pool refresh.")
        run_full_pool_refresh(settings)
    else:
        LOGGER.info("Full-pool data fresh; skipping.")

    if _needs_daily_refresh(daily_dir):
        LOGGER.info("Daily cache stale; running backfill/daily refresh.")
        run_backfill_daily(settings)
    else:
        LOGGER.info("Daily cache up to date; skipping backfill.")

    if _needs_refresh(universe_path, settings.get("active_pool", {}).get("refresh_interval_days", 7)):
        LOGGER.info("Active universe stale; running active-pool refresh.")
        run_active_pool_refresh(settings)
    else:
        LOGGER.info("Active universe fresh; skipping.")

    if _needs_indicator_refresh(indicators_dir, daily_dir):
        LOGGER.info("Indicator cache stale; recomputing indicators.")
        run_indicator_batch(settings)
    else:
        LOGGER.info("Indicator cache fresh; skipping.")

    LOGGER.info("Generating watchlist for latest data.")
    run_watchlist_pipeline(settings)
    LOGGER.info("Updating market regime snapshot.")
    try:
        run_market_regime_detection(settings)
    except Exception as exc:  # pragma: no cover
        LOGGER.warning("Market regime detection failed: %s", exc)
    LOGGER.info("Auto pipeline complete.")


def _needs_refresh(path: Path, interval_days: int) -> bool:
    if not path.exists():
        return True
    modified = datetime.fromtimestamp(path.stat().st_mtime)
    return (datetime.now() - modified).days >= max(1, interval_days)


def _needs_daily_refresh(daily_dir: Path) -> bool:
    sample = _pick_sample_file(daily_dir)
    if not sample:
        return True
    latest = _latest_trade_date(sample)
    if latest is None:
        return True
    today = datetime.now().date()
    return (today - latest).days >= 1


def _needs_indicator_refresh(indicators_dir: Path, daily_dir: Path) -> bool:
    sample = _pick_sample_file(indicators_dir, suffix=".csv")
    if not sample:
        return True
    latest_indicator = _latest_trade_date(sample)
    if latest_indicator is None:
        return True
    daily_sample = _pick_sample_file(daily_dir)
    if not daily_sample:
        return True
    latest_daily = _latest_trade_date(daily_sample)
    if latest_daily is None:
        return True
    return latest_indicator < latest_daily


def _pick_sample_file(directory: Path, suffix: str = ".csv") -> Optional[Path]:
    if not directory.exists():
        return None
    for path in directory.iterdir():
        if path.is_file() and path.suffix == suffix and path.stat().st_size > 0:
            return path
    return None


def _latest_trade_date(path: Path) -> Optional[datetime.date]:
    try:
        df = pd.read_csv(path, usecols=["trade_date"])
    except Exception:
        return None
    if df.empty:
        return None
    raw = str(df.iloc[-1]["trade_date"]).split(".")[0]
    raw = raw.zfill(8)
    try:
        return datetime.strptime(raw, "%Y%m%d").date()
    except ValueError:
        return None
