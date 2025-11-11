"""Centralized logging configuration (console + file)."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict
import json

_configured = False


def configure_logging(settings: Dict | None = None) -> None:
    """Configure logging once for the entire application."""
    global _configured
    if _configured:
        return
    app_settings = settings or _load_settings_direct()
    log_cfg = app_settings.get("logs", {})
    log_dir = Path(log_cfg.get("directory", "data/logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    level_str = log_cfg.get("level", "INFO").upper()
    level = getattr(logging, level_str, logging.INFO)
    logfile = log_dir / log_cfg.get("filename", "quant.log")

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root_logger.addHandler(console)

    file_handler = RotatingFileHandler(logfile, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    if not _configured:
        configure_logging()
    return logging.getLogger(name)


def _load_settings_direct() -> Dict:
    settings_path = Path("config/settings.json")
    if not settings_path.exists():
        return {}
    return json.loads(settings_path.read_text(encoding="utf-8"))
