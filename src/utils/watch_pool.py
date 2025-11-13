"""Helpers for reading/writing the persistent watch pool."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

POOL_COLUMNS = [
    "ts_code",
    "first_seen",
    "last_seen",
    "tier",
    "last_score",
    "env",
    "env_score",
    "status",
    "days_inactive",
]


def load_watch_pool(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=POOL_COLUMNS)
    try:
        df = pd.read_csv(path)
    except Exception:
        return pd.DataFrame(columns=POOL_COLUMNS)
    for column in POOL_COLUMNS:
        if column not in df.columns:
            df[column] = None
    return df[POOL_COLUMNS]


def save_watch_pool(path: Path, rows: List[Dict]) -> None:
    if rows:
        pd.DataFrame(rows, columns=POOL_COLUMNS).to_csv(path, index=False)
    else:
        path.write_text(",".join(POOL_COLUMNS) + "\n", encoding="utf-8")


def sanitize_date(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    try:
        return str(int(value))
    except (ValueError, TypeError):
        try:
            return datetime.fromisoformat(str(value)).strftime("%Y%m%d")
        except ValueError:
            return ""


def infer_today(rows: List[Dict]) -> str:
    for row in rows:
        date = sanitize_date(row.get("date"))
        if date:
            return date
    return datetime.now().strftime("%Y%m%d")


def days_between(current: str, previous: Optional[str]) -> Optional[int]:
    if not previous:
        return None
    current_norm = sanitize_date(current)
    previous_norm = sanitize_date(previous)
    if not current_norm or not previous_norm:
        return None
    try:
        current_dt = datetime.strptime(current_norm, "%Y%m%d")
        previous_dt = datetime.strptime(previous_norm, "%Y%m%d")
    except ValueError:
        return None
    return (current_dt - previous_dt).days
