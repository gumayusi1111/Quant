"""Time utilities."""

from __future__ import annotations

from datetime import datetime, timezone


def now_utc_str() -> str:
    return datetime.now(tz=timezone.utc).isoformat()
