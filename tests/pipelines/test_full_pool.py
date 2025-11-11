from src.pipelines import build_full_pool_context


def test_build_full_pool_context_defaults():
    ctx = build_full_pool_context({})
    assert ctx.history_days == 90
    assert ctx.refresh_interval_days == 60
    assert str(ctx.master_path).endswith("data/master/etf_master.csv")
    assert ctx.chunk_size == 25
