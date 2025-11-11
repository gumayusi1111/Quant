"""CLI entry for ETF Quant scaffolding."""

from __future__ import annotations

import argparse

from src.pipelines import run_full_pool_refresh, run_active_pool_refresh
from src.scheduler import run_intraday_pipeline, run_nightly_pipeline
from src.utils.config import load_settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ETF Quant System")
    parser.add_argument("--full-pool", action="store_true", help="Run the 60-90 day full-pool refresh.")
    parser.add_argument("--active-pool", action="store_true", help="Refresh active ETF universe.")
    parser.add_argument("--nightly", action="store_true", help="Run nightly pipeline.")
    parser.add_argument("--intraday", action="store_true", help="Run intraday pipeline.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = load_settings()

    if args.full_pool:
        run_full_pool_refresh(settings)
    if args.active_pool:
        run_active_pool_refresh(settings)
    if args.nightly:
        run_nightly_pipeline(settings)
    if args.intraday:
        run_intraday_pipeline(settings)
    if not any((args.full_pool, args.nightly, args.intraday)):
        print("Specify --full-pool/--nightly/--intraday to run a pipeline.")


if __name__ == "__main__":
    main()
