"""Wrapper around the chinadata API (TuShare-compatible syntax)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.utils.config import load_tokens

try:
    import chinadata.ca_data as cd  # type: ignore
except ImportError as exc:  # pragma: no cover - import error highlighted at runtime
    raise RuntimeError(
        "chinadata package is required. Install via `pip install chinadata` inside .venv."
    ) from exc


@dataclass
class ChinaDataClient:
    token: str
    _pro: Any

    @property
    def pro(self):
        return self._pro


def build_chinadata_client(tokens_path: str | None = None) -> ChinaDataClient:
    tokens = load_tokens(tokens_path)
    entry = tokens.get("chinadata", {})
    token = entry.get("token")
    if not token:
        raise RuntimeError("Missing chinadata token. Update config/tokens.json.")
    cd.set_token(token)
    pro = cd.pro_api()
    return ChinaDataClient(token=token, _pro=pro)
