"""File IO helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from src.signal_generator.generator import Signal


def append_signal_log(signals: Iterable[Signal], log_path: str | Path) -> None:
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not log_path.exists()
    with log_path.open("a", encoding="utf-8") as handle:
        if write_header:
            handle.write("symbol,action,confidence\n")
        for signal in signals:
            handle.write(f"{signal.symbol},{signal.action},{signal.confidence}\n")


def write_json(path: str | Path, payload) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
