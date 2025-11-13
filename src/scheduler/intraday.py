"""Intraday monitoring workflow."""

from __future__ import annotations

from datetime import datetime
from typing import Dict

from src.logging import get_logger
from src.pipelines import run_execution_pipeline

LOGGER = get_logger("scheduler.intraday")


def run_intraday_pipeline(settings: Dict) -> None:
    """Trigger intraday execution planning."""
    interval = settings.get("scheduler", {}).get("intraday_interval_minutes", 5)
    LOGGER.info(
        "Intraday pipeline triggered at %s (interval=%smin)",
        datetime.utcnow().isoformat(),
        interval,
    )
    run_execution_pipeline(settings)
