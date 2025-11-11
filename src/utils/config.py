"""Config helpers for settings & tokens."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from src.logging import get_logger

LOGGER = get_logger("utils.config")


def load_settings(path: str | Path | None = None) -> Dict:
    settings_path = Path(path or "config/settings.json")
    if not settings_path.exists():
        LOGGER.warning("Settings file %s missing, returning empty dict.", settings_path)
        return {}
    return json.loads(settings_path.read_text(encoding="utf-8"))


def load_tokens(path: str | Path | None = None) -> Dict[str, Dict[str, Any]]:
    tokens_path = Path(path or "config/tokens.json")
    if tokens_path.exists():
        return _normalize_tokens(json.loads(tokens_path.read_text(encoding="utf-8")))

    template_path = Path("config/tokens.template.json")
    if template_path.exists():
        LOGGER.warning("Tokens file missing; falling back to template.")
        return _normalize_tokens(json.loads(template_path.read_text(encoding="utf-8")))

    LOGGER.warning("No tokens file located. Returning empty dict.")
    return {}


def _normalize_tokens(raw: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    normalized: Dict[str, Dict[str, Any]] = {}
    for key, value in raw.items():
        if isinstance(value, dict):
            normalized[key] = value
        else:
            normalized[key] = {"token": value}
    return normalized
