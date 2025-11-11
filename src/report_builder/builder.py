"""HTML/CSV report builder placeholder."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable


def build_daily_report(output_dir: str | Path, trades: Iterable[dict]) -> Path:
    """Write a very small CSV summary."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "daily_report.csv"
    lines = ["symbol,action,price"]
    for trade in trades:
        lines.append(f"{trade.get('symbol','NA')},{trade.get('action')},{trade.get('price',0)}")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path
