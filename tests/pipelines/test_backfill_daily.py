from __future__ import annotations

import pandas as pd

from src.pipelines.backfill_daily import run_incremental_daily


def test_run_incremental_daily_normalizes_trade_dates(tmp_path, monkeypatch):
    """Mixed trade_date dtypes should not crash incremental updates."""
    master_path = tmp_path / "master.csv"
    daily_dir = tmp_path / "daily"
    daily_dir.mkdir()
    pd.DataFrame({"ts_code": ["AAA.ETF"]}).to_csv(master_path, index=False)
    # Existing file mixes string/int representations.
    pd.DataFrame(
        {
            "trade_date": ["20250101", 20250102],
            "close": [1.0, 2.0],
        }
    ).to_csv(daily_dir / "AAA.ETF.csv", index=False)

    new_frame = pd.DataFrame(
        {
            "trade_date": [20250103, "20250104"],
            "close": [3.0, 4.0],
        }
    )

    def fake_fetch(symbols, start, end):
        return {symbols[0]: new_frame}

    monkeypatch.setattr("src.pipelines.backfill_daily.fetch_daily_bars", fake_fetch)
    monkeypatch.setattr(
        "src.pipelines.indicator_batch.run_indicator_batch",
        lambda settings, symbols=None: None,
    )

    settings = {
        "full_pool": {"master_path": str(master_path)},
        "data": {"daily_dir": str(daily_dir)},
        "history_backfill": {"start_date": "20200101", "end_date": "20251231"},
    }

    run_incremental_daily(settings)

    result = pd.read_csv(daily_dir / "AAA.ETF.csv", dtype={"trade_date": str})
    # trade_date should be uniform strings sorted ascending.
    assert result["trade_date"].tolist() == ["20250101", "20250102", "20250103", "20250104"]
