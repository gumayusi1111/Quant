"""Chart helpers (placeholder)."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence


def render_equity_curve(equity_curve: Sequence[float], output_path: str | Path) -> Path:
    """Dump equity values to a TSV file for now."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["index\tequity"]
    for idx, value in enumerate(equity_curve):
        lines.append(f"{idx}\t{value}")
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path
