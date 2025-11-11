"""Intraday monitoring workflow."""

from __future__ import annotations

from datetime import datetime
from typing import Dict

from src.logging import get_logger

LOGGER = get_logger("scheduler.intraday")


def run_intraday_pipeline(settings: Dict) -> None:
    """Placeholder intraday hook."""
    interval = settings.get("scheduler", {}).get("intraday_interval_minutes", 5)
    LOGGER.info(
        "Intraday pipeline placeholder triggered at %s (interval=%smin)",
        datetime.utcnow().isoformat(),
        interval,
    )
