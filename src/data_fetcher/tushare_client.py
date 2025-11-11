"""Wrappers for market data clients.

The project uses:

- Official Tushare package (token starts with 822...) strictly for historical minute data.
- chinadata package (token starts with b3...) for daily K-line and other endpoints.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.utils.config import load_tokens

try:
    import tushare as ts  # type: ignore
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "tushare package is required. Install via `pip install tushare` inside .venv."
    ) from exc


@dataclass
class TushareClient:
    """Wrapper around the official Tushare SDK (minute bars only)."""

    token: str
    _pro: Any

    @property
    def pro(self):
        return self._pro


def build_tushare_client(tokens_path: str | Path | None = None) -> TushareClient:
    """Construct a client bound to the official Tushare package (historical minute data)."""
    tokens = load_tokens(tokens_path)
    entry = tokens.get("tushare", {})
    token = entry.get("token")
    if not token:
        raise RuntimeError(
            "Missing official Tushare token. Update config/tokens.json (tushare.token)."
        )
    ts.set_token(token)
    pro = ts.pro_api()
    return TushareClient(token=token, _pro=pro)
