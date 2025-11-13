"""Sell signal evaluation for ETF watchlist trades."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import pandas as pd


@dataclass
class SellSignalResult:
    triggered: bool
    action: str
    core_hits: Dict[str, bool]
    aux_hits: Dict[str, bool]
    score: float
    reason: str


def prepare_daily_features(daily_df: pd.DataFrame) -> pd.DataFrame:
    """Compute rolling stats (vol MA5, ATR, ATR MA5) used for sell checks."""
    if daily_df.empty:
        return daily_df
    df = daily_df.sort_values("trade_date").copy()
    numeric_cols = ["vol", "amount", "high", "low", "close", "pre_close", "pct_chg"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["trade_date"] = df["trade_date"].astype(str)
    df["vol_ma5"] = df["vol"].rolling(window=5, min_periods=5).mean()

    high = pd.to_numeric(df["high"], errors="coerce")
    low = pd.to_numeric(df["low"], errors="coerce")
    close = pd.to_numeric(df["close"], errors="coerce")
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            (high - low).abs(),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    df["atr"] = tr.rolling(window=14, min_periods=1).mean()
    df["atr_ma5"] = df["atr"].rolling(window=5, min_periods=5).mean()
    return df


def evaluate_sell_signal(
    indicators: pd.DataFrame,
    idx: int,
    daily_row: pd.Series,
    prev_indicator_row: Optional[pd.Series],
    prev_daily_row: Optional[pd.Series] = None,
    regime: str = "bull",
) -> SellSignalResult:
    """Evaluate sell score for indicators[idx] with regime awareness."""
    regime_key = (regime or "bull").lower()
    if regime_key == "bull":
        return _evaluate_bull_sell(indicators, idx, daily_row, prev_indicator_row, prev_daily_row)
    if regime_key == "sideways":
        return _evaluate_sideways_sell(indicators, idx, daily_row, prev_indicator_row, prev_daily_row)
    if regime_key == "bear":
        return _evaluate_bear_sell(indicators, idx, daily_row, prev_indicator_row, prev_daily_row)
    return _evaluate_generic_sell(indicators, idx, daily_row, prev_indicator_row)


def _evaluate_bull_sell(
    indicators: pd.DataFrame,
    idx: int,
    daily_row: pd.Series,
    prev_indicator_row: Optional[pd.Series],
    prev_daily_row: Optional[pd.Series],
) -> SellSignalResult:
    row = indicators.iloc[idx]
    price = _resolve_price(row, daily_row)
    prev_price = _resolve_price(prev_indicator_row, prev_daily_row) if prev_indicator_row is not None else None
    pct_chg = _to_float(daily_row.get("pct_chg"))
    vol = _to_float(daily_row.get("vol"))
    vol_ma5 = _to_float(daily_row.get("vol_ma5"))

    core_hits: Dict[str, bool] = {}
    aux_hits: Dict[str, bool] = {}

    ma20 = row.get("ma20")
    prev_ma20 = prev_indicator_row.get("ma20") if prev_indicator_row is not None else None
    ma20_break = _notna(price, prev_price, ma20, prev_ma20) and price < ma20 and prev_price < prev_ma20
    core_hits["ma20_break"] = bool(ma20_break)

    macd_dead = False
    if prev_indicator_row is not None:
        curr_dif = row.get("macd_dif")
        curr_dea = row.get("macd_dea")
        prev_dif = prev_indicator_row.get("macd_dif")
        prev_dea = prev_indicator_row.get("macd_dea")
        macd_dead = (
            _notna(curr_dif, curr_dea, prev_dif, prev_dea)
            and prev_dif >= prev_dea
            and curr_dif < curr_dea
            and curr_dif < 0
        )
    core_hits["macd_dead_below_zero"] = macd_dead

    volume_dump = (
        pct_chg is not None and pct_chg <= -2.0 and _notna(vol, vol_ma5) and vol_ma5 > 0 and vol >= vol_ma5 * 1.5
    )
    core_hits["volume_dump"] = bool(volume_dump)

    rsi_curr = row.get("rsi6")
    rsi_prev = prev_indicator_row.get("rsi6") if prev_indicator_row is not None else None
    aux_hits["rsi_down"] = _notna(rsi_curr, rsi_prev) and rsi_curr < rsi_prev

    kdj_k = row.get("kdj_k")
    aux_hits["kdj_hot"] = _notna(kdj_k) and kdj_k >= 90

    obv = row.get("obv")
    maobv = row.get("maobv")
    aux_hits["obv_exit"] = _notna(obv, maobv) and obv < maobv

    boll_mid = row.get("boll_mid")
    aux_hits["boll_mid_break"] = _notna(price, boll_mid) and price < boll_mid

    atr = daily_row.get("atr")
    atr_ma5 = daily_row.get("atr_ma5")
    atr_spike = (
        _notna(atr, atr_ma5)
        and atr_ma5 > 0
        and atr > atr_ma5 * 1.2
        and pct_chg is not None
        and pct_chg >= 0
    )
    aux_hits["atr_spike_up"] = bool(atr_spike)

    core_score = sum(core_hits.values())
    aux_score = 0.5 * sum(aux_hits.values())
    total_score = core_score + aux_score

    if core_score >= 1:
        action = "exit"
    elif total_score >= 3:
        action = "exit"
    elif total_score >= 2:
        action = "reduce"
    else:
        action = "hold"

    triggered = action != "hold"
    reason = _determine_reason(action, core_hits, aux_hits)

    return SellSignalResult(
        triggered=triggered,
        action=action,
        core_hits=core_hits,
        aux_hits=aux_hits,
        score=total_score,
        reason=reason,
    )


def _evaluate_sideways_sell(
    indicators: pd.DataFrame,
    idx: int,
    daily_row: pd.Series,
    prev_indicator_row: Optional[pd.Series],
    prev_daily_row: Optional[pd.Series],
) -> SellSignalResult:
    row = indicators.iloc[idx]
    price = _resolve_price(row, daily_row)
    prev_price = _resolve_price(prev_indicator_row, prev_daily_row)
    pct_chg = _to_float(daily_row.get("pct_chg"))
    vol = _to_float(daily_row.get("vol"))
    vol_ma5 = _to_float(daily_row.get("vol_ma5"))

    core_hits: Dict[str, bool] = {}
    aux_hits: Dict[str, bool] = {}

    upper = row.get("boll_upper")
    lower = row.get("boll_lower")
    mid = row.get("boll_mid")

    upper_touch = _notna(price, upper) and price >= upper * 0.995
    breakdown = _notna(price, lower) and price <= lower * 0.985
    drop_spike = pct_chg is not None and pct_chg <= -1.5 and _notna(vol, vol_ma5) and vol_ma5 > 0 and vol >= vol_ma5 * 1.2

    core_hits["upper_touch"] = bool(upper_touch)
    core_hits["range_break"] = bool(breakdown)
    core_hits["drop_spike"] = bool(drop_spike)

    rsi_curr = row.get("rsi6")
    rsi_prev = prev_indicator_row.get("rsi6") if prev_indicator_row is not None else None
    aux_hits["rsi_high"] = _notna(rsi_curr) and rsi_curr >= 65

    kdj_k = row.get("kdj_k")
    kdj_prev = prev_indicator_row.get("kdj_k") if prev_indicator_row is not None else None
    aux_hits["kdj_rollover"] = _notna(kdj_k, kdj_prev) and kdj_prev <= kdj_k and kdj_k >= 80

    aux_hits["mid_break"] = _notna(price, mid) and price < mid

    obv = row.get("obv")
    maobv = row.get("maobv")
    aux_hits["obv_exit"] = _notna(obv, maobv) and obv < maobv

    wr1 = row.get("wr1")
    wr2 = row.get("wr2")
    aux_hits["wr_overbought"] = (_notna(wr1) and wr1 <= 10) or (_notna(wr2) and wr2 <= 10)

    core_score = sum(core_hits.values())
    aux_score = 0.5 * sum(aux_hits.values())
    total_score = core_score + aux_score

    if core_score >= 1 or total_score >= 2.5:
        action = "exit"
    elif total_score >= 1.5:
        action = "reduce"
    else:
        action = "hold"

    reason = _determine_reason(action, core_hits, aux_hits)
    return SellSignalResult(
        triggered=action != "hold",
        action=action,
        core_hits=core_hits,
        aux_hits=aux_hits,
        score=total_score,
        reason=reason,
    )


def _evaluate_bear_sell(
    indicators: pd.DataFrame,
    idx: int,
    daily_row: pd.Series,
    prev_indicator_row: Optional[pd.Series],
    prev_daily_row: Optional[pd.Series],
) -> SellSignalResult:
    row = indicators.iloc[idx]
    price = _resolve_price(row, daily_row)
    prev_price = _resolve_price(prev_indicator_row, prev_daily_row)
    pct_chg = _to_float(daily_row.get("pct_chg"))

    ma10 = row.get("ma10")
    ma5 = row.get("ma5")

    core_hits: Dict[str, bool] = {}
    aux_hits: Dict[str, bool] = {}

    target_hit = _notna(price, ma10) and price >= ma10
    failure_drop = pct_chg is not None and pct_chg <= -1.5
    lower_low = _notna(price, prev_price) and price < prev_price * 0.985

    core_hits["target_hit"] = bool(target_hit)
    core_hits["failure_drop"] = bool(failure_drop)
    core_hits["lower_low"] = bool(lower_low)

    rsi_curr = row.get("rsi6")
    rsi_prev = prev_indicator_row.get("rsi6") if prev_indicator_row is not None else None
    aux_hits["rsi_fade"] = _notna(rsi_curr, rsi_prev) and rsi_prev <= rsi_curr and rsi_curr >= 55

    kdj_k = row.get("kdj_k")
    kdj_prev = prev_indicator_row.get("kdj_k") if prev_indicator_row is not None else None
    aux_hits["kdj_rollover"] = _notna(kdj_k, kdj_prev) and kdj_prev <= kdj_k and kdj_k >= 70

    aux_hits["below_ma5"] = _notna(price, ma5) and price < ma5

    obv = row.get("obv")
    maobv = row.get("maobv")
    aux_hits["obv_exit"] = _notna(obv, maobv) and obv < maobv

    core_score = sum(core_hits.values())
    aux_score = 0.5 * sum(aux_hits.values())
    total_score = core_score + aux_score

    if core_score >= 1 or total_score >= 2:
        action = "exit"
    elif total_score >= 1.5:
        action = "reduce"
    else:
        action = "hold"

    reason = _determine_reason(action, core_hits, aux_hits)
    return SellSignalResult(
        triggered=action != "hold",
        action=action,
        core_hits=core_hits,
        aux_hits=aux_hits,
        score=total_score,
        reason=reason,
    )


def _evaluate_generic_sell(
    indicators: pd.DataFrame,
    idx: int,
    daily_row: pd.Series,
    prev_indicator_row: Optional[pd.Series],
) -> SellSignalResult:
    row = indicators.iloc[idx]
    price = _resolve_price(row, daily_row)
    pct_chg = daily_row.get("pct_chg")

    core_hits: Dict[str, bool] = {}
    aux_hits: Dict[str, bool] = {}

    ma5 = row.get("ma5")
    ma10 = row.get("ma10")
    ma20 = row.get("ma20")
    trend_break = _notna(ma5, ma10, ma20) and ((ma5 < ma10) or (ma10 < ma20))
    core_hits["trend_break"] = bool(trend_break)

    macd_dead = False
    if prev_indicator_row is not None:
        curr_dif = row.get("macd_dif")
        curr_dea = row.get("macd_dea")
        prev_dif = prev_indicator_row.get("macd_dif")
        prev_dea = prev_indicator_row.get("macd_dea")
        macd_dead = _notna(curr_dif, curr_dea, prev_dif, prev_dea) and prev_dif >= prev_dea and curr_dif < curr_dea
    core_hits["macd_dead"] = macd_dead

    kdj_k = row.get("kdj_k")
    kdj_d = row.get("kdj_d")
    overheat = _notna(kdj_k, kdj_d) and kdj_k > 90 and kdj_k < kdj_d
    core_hits["kdj_overheat"] = overheat

    boll_mid = row.get("boll_mid")
    mid_break = _notna(price, boll_mid) and price < boll_mid
    core_hits["boll_mid_break"] = mid_break

    vol = daily_row.get("vol")
    vol_ma5 = daily_row.get("vol_ma5")
    vol_dump = False
    if pct_chg is not None and vol is not None and vol_ma5:
        vol_dump = pct_chg <= -1.0 and vol > vol_ma5 * 1.3
    core_hits["volume_dump"] = vol_dump

    rsi_curr = row.get("rsi6")
    rsi_prev = prev_indicator_row.get("rsi6") if prev_indicator_row is not None else None
    rsi_aux = _notna(rsi_curr, rsi_prev) and rsi_prev >= 70 and rsi_curr < rsi_prev
    aux_hits["rsi_reversal"] = rsi_aux

    wr1 = row.get("wr1")
    wr2 = row.get("wr2")
    wr_aux = (_notna(wr1) and wr1 > 90) or (_notna(wr2) and wr2 > 90)
    aux_hits["wr_weak"] = wr_aux

    obv = row.get("obv")
    maobv = row.get("maobv")
    obv_aux = _notna(obv, maobv) and obv < maobv
    aux_hits["obv_exit"] = obv_aux

    below_ma20 = _notna(price, ma20) and price < ma20
    aux_hits["ma20_break"] = below_ma20

    atr = daily_row.get("atr")
    atr_ma5 = daily_row.get("atr_ma5")
    atr_aux = _notna(atr, atr_ma5) and atr_ma5 > 0 and atr > atr_ma5 * 1.2
    aux_hits["atr_spike"] = atr_aux

    core_score = sum(v for v in core_hits.values())
    aux_score = 0.5 * sum(v for v in aux_hits.values())
    total_score = core_score + aux_score

    if core_score >= 1 or total_score >= 2:
        action = "exit"
    elif total_score >= 1:
        action = "reduce"
    else:
        action = "hold"

    triggered = action != "hold"
    reason = _determine_reason(action, core_hits, aux_hits)

    return SellSignalResult(
        triggered=triggered,
        action=action,
        core_hits=core_hits,
        aux_hits=aux_hits,
        score=total_score,
        reason=reason,
    )


def _determine_reason(action: str, core_hits: Dict[str, bool], aux_hits: Dict[str, bool]) -> str:
    if action == "hold":
        return "time"
    for key, hit in core_hits.items():
        if hit:
            return key
    for key, hit in aux_hits.items():
        if hit:
            return key
    return "auxiliary"


def _resolve_price(indicator_row: Optional[pd.Series], daily_row: Optional[pd.Series]) -> Optional[float]:
    price = None
    if daily_row is not None:
        price = daily_row.get("close_front_adj")
        if price is None or pd.isna(price):
            price = daily_row.get("close")
    if (price is None or pd.isna(price)) and indicator_row is not None:
        price = indicator_row.get("close")
    return float(price) if price is not None and not pd.isna(price) else None


def _notna(*values) -> bool:
    return all(value is not None and not pd.isna(value) for value in values)


def _to_float(value) -> Optional[float]:
    if value is None or pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
