"""CLI entry for ETF Quant scaffolding."""

from __future__ import annotations

import argparse

from src.pipelines import run_full_pool_refresh, run_active_pool_refresh
from src.pipelines.indicator_batch import run_indicator_batch
from src.scheduler import run_intraday_pipeline, run_nightly_pipeline
from src.utils.config import load_settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ETF Quant System")
    parser.add_argument("--full-pool", action="store_true", help="Run the 60-90 day full-pool refresh.")
    parser.add_argument("--active-pool", action="store_true", help="Refresh active ETF universe.")
    parser.add_argument("--nightly", action="store_true", help="Run nightly pipeline.")
    parser.add_argument("--intraday", action="store_true", help="Run intraday pipeline.")
    parser.add_argument("--indicators", action="store_true", help="Recompute indicators for cached daily data.")
    parser.add_argument("--watchlist", action="store_true", help="Generate watchlist from indicators.")
    parser.add_argument(
        "--backfill-daily",
        action="store_true",
        help="Backfill historical daily data (e.g., from 2020 onward).",
    )
    parser.add_argument(
        "--backtest-watchlist",
        action="store_true",
        help="Run historical backtest for the watchlist signal.",
    )
    parser.add_argument(
        "--market-regime",
        action="store_true",
        help="Compute market bull/bear regimes using benchmark ETFs.",
    )
    parser.add_argument(
        "--execution",
        action="store_true",
        help="Generate minute-level execution plan for active watchlist entries.",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto pipeline: refresh data/active pool/indicators/watchlist as needed.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = load_settings()

    if args.full_pool:
        run_full_pool_refresh(settings)
    if args.active_pool:
        run_active_pool_refresh(settings)
    if args.indicators:
        run_indicator_batch(settings)
    if args.watchlist:
        from src.pipelines import run_watchlist_pipeline

        run_watchlist_pipeline(settings)
    if args.backfill_daily:
        from src.pipelines import run_backfill_daily

        run_backfill_daily(settings)
    if args.backtest_watchlist:
        from src.backtester import run_watchlist_backtest

        run_watchlist_backtest(settings)
    if args.market_regime:
        from src.pipelines import run_market_regime_detection

        run_market_regime_detection(settings)
    if args.execution:
        from src.pipelines import run_execution_pipeline

        run_execution_pipeline(settings)
    if args.auto:
        from src.pipelines import run_auto_pipeline

        run_auto_pipeline(settings)
    if args.nightly:
        run_nightly_pipeline(settings)
    if args.intraday:
        run_intraday_pipeline(settings)
    if not any(
        (
            args.full_pool,
            args.active_pool,
            args.indicators,
            args.watchlist,
            args.backtest_watchlist,
            args.backfill_daily,
            args.market_regime,
            args.execution,
            args.auto,
            args.nightly,
            args.intraday,
        )
    ):
        print(
            "Specify --full-pool/--active-pool/--indicators/--watchlist/"
            "--backtest-watchlist/--backfill-daily/--market-regime/--auto/--nightly/--intraday to run a pipeline."
        )


if __name__ == "__main__":
    main()
