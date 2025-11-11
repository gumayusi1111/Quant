"""Data acquisition layer for ETF Quant system."""

from .chinadata_client import build_chinadata_client
from .daily import fetch_daily_bars
from .minute import fetch_minute_bars
from .tushare_client import build_tushare_client

__all__ = [
    "build_chinadata_client",
    "build_tushare_client",
    "fetch_daily_bars",
    "fetch_minute_bars",
]
