"""Nightly workflow orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable

from src.signal_generator import generate_signals
from src.strategy_etf import run_trend_strategy
from src.utils import io as io_utils
from src.logging import get_logger

LOGGER = get_logger("scheduler.nightly")


def run_nightly_pipeline(settings: Dict, universe: Iterable[str] | None = None) -> None:
    """Minimal nightly job: generate placeholder signals and log them."""
    symbols = list(universe or settings.get("strategy", {}).get("universe", []))
    if not symbols:
        LOGGER.warning("Universe is empty. Nightly pipeline skipped.")
        return

    fast = [idx + 1 for idx in range(len(symbols))]
    slow = [idx + 2 for idx in range(len(symbols))]
    signals = generate_signals(symbols, fast, slow)
    strategy_outputs = run_trend_strategy(symbols, fast, slow)

    log_path = Path(settings.get("data", {}).get("signal_log", "data/signal_log.csv"))
    io_utils.append_signal_log(signals, log_path=log_path)
    LOGGER.info("Nightly pipeline generated %s signals -> %s", len(signals), log_path)
    io_utils.write_json(Path("outputs/nightly_snapshot.json"), strategy_outputs)
