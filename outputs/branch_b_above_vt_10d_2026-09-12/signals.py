"""Entry-only SPX transfer of the legacy five-minute thrust/staircase package.

Source: spy_chaser's bvt_5m_expand_probe.py and bvt_5m_ride.py at
6c15500a4776a4b1f48c62d8cc7c7dcecf7fd52a. VWAP is explicitly removed;
there is no proxy VWAP, ADX admission gate, exit, fill simulation or P&L.
Input bars are complete start-labelled regular-session five-minute candles.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

BODYBREAK_BPS = 10.0
FAN_MIN_ATR = 0.10
MAX_EXT_ATR = 1.5
STEEP_EMA5_ATR = 0.60
FIRST_KNOWN_MIN = 600
LAST_KNOWN_MIN = 870


def _check_bars(bars: pd.DataFrame) -> None:
    """Reject silently reordered, duplicated or malformed source observations."""
    required = {"date", "min5", "open", "high", "low", "close"}
    if missing := required.difference(bars.columns):
        raise ValueError(f"Missing bar columns: {sorted(missing)}")
    if bars.empty:
        return
    if bars[list(required)].isna().any().any():
        raise ValueError("Bar keys and OHLC must not be missing")
    keys = pd.MultiIndex.from_frame(bars[["date", "min5"]])
    if not keys.is_unique or not keys.is_monotonic_increasing:
        raise ValueError("Bars must be unique and sorted by date, min5")
    if not ((bars.min5 % 5 == 0) & bars.min5.between(570, 955)).all():
        raise ValueError("min5 must identify a regular-session five-minute start")
    prices = bars[["open", "high", "low", "close"]]
    if not np.isfinite(prices.to_numpy(dtype=float)).all() or not (prices > 0).all().all():
        raise ValueError("OHLC must be finite positive prices")
    if not (
        (bars.high >= prices[["open", "close"]].max(axis=1))
        & (bars.low <= prices[["open", "close"]].min(axis=1))
        & (bars.high >= bars.low)
    ).all():
        raise ValueError("OHLC bounds are inconsistent")


def _rma(values: pd.Series, period: int) -> pd.Series:
    """Match the source's first-observation-seeded, undisplaced RMA."""
    return values.ewm(alpha=1.0 / period, adjust=False).mean()


def add_features(bars: pd.DataFrame) -> pd.DataFrame:
    """Add causal indicators continuously across the supplied session history.

    The caller supplies any prehistory and complete bins. Overnight gaps enter
    true range; neither EMA nor RMA resets at a date boundary. Returned rows,
    index and existing columns retain input order. Diagnostics never gate entry.
    """
    _check_bars(bars)
    result = bars.copy()
    close, high, low = result.close, result.high, result.low
    for name, span in (("lips", 5), ("teeth", 9), ("jaw", 20)):
        result[name] = close.ewm(span=span, adjust=False).mean()
    previous_close = close.shift(1)
    tr = pd.concat(
        [high - low, (high - previous_close).abs(), (low - previous_close).abs()], axis=1
    ).max(axis=1)
    up, down = high.diff(), -low.diff()
    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=result.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=result.index)
    result["tr"] = tr
    result["atr"] = _rma(tr, 14)
    result["plus_di"] = 100 * _rma(plus_dm, 14) / result.atr
    result["minus_di"] = 100 * _rma(minus_dm, 14) / result.atr
    dx = 100 * (result.plus_di - result.minus_di).abs() / (
        result.plus_di + result.minus_di
    ).replace(0, np.nan)
    result["adx"] = _rma(dx.fillna(0.0), 14)
    result["adx14"] = result.adx
    result["adx_s3"] = result.adx.diff(3) / 3
    result["er"] = (close - close.shift(10)).abs() / (
        close.diff().abs().rolling(10).sum().replace(0, np.nan)
    )
    delta = close.diff()
    avg_gain = _rma(delta.clip(lower=0), 9)
    avg_loss = _rma((-delta).clip(lower=0), 9)
    result["rsi9"] = (100 - 100 / (1 + avg_gain / avg_loss)).fillna(50.0)
    result["rsi9_sma14"] = result.rsi9.rolling(14).mean()
    return result


def evaluate_day(g: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    """Return rule diagnostics and first signals of each qualifying package run.

    ``thrust_raw`` and ``staircase_raw`` are independent admission shapes.
    ``staircase_ok`` is the enabled package: common gates AND (thrust OR stairs).
    Runs reset at the 10:00 decision-window boundary; a nonqualifying completed
    bar rearms that package. Signal close is an observed price, never a fill.
    """
    _check_bars(g)
    if g.date.nunique() > 1:
        raise ValueError("evaluate_day requires exactly one date")
    required = {"lips", "teeth", "jaw", "atr", "adx"}
    if missing := required.difference(g.columns):
        raise ValueError(f"Missing feature columns: {sorted(missing)}")
    result = g.copy()
    atr = result.atr.where(np.isfinite(result.atr) & (result.atr > 0))
    gap_fast = result.lips - result.teeth
    gap_slow = result.teeth - result.jaw
    body = result.close - result.open
    body_top = result[["open", "close"]].max(axis=1)
    body_bottom = result[["open", "close"]].min(axis=1)
    wicks = result.high - body_top + body_bottom - result.low
    solid = (body > 0) & (body > wicks)
    ready = pd.Series(np.arange(len(result)) >= 2, index=result.index)

    result["known_min"] = result.min5 + 5
    result["in_window"] = result.known_min.between(FIRST_KNOWN_MIN, LAST_KNOWN_MIN)
    result["lt_atr"] = gap_fast / atr
    result["tj_atr"] = gap_slow / atr
    result["fan_atr"] = (result.lips - result.jaw) / atr
    result["ext_atr"] = (result.close - result.lips) / atr
    result["slope2_atr"] = (result.lips - result.lips.shift(2)) / atr
    result["prior_body_top"] = body_top.shift(1).rolling(3, min_periods=1).max()
    result["break_bps"] = (result.close - result.prior_body_top) / result.close * 10000
    result["solid_green"] = solid
    result["stack_up"] = (result.lips > result.teeth) & (result.teeth > result.jaw)
    result["gaps_expanding"] = (gap_fast > gap_fast.shift(1)) & (
        gap_slow > gap_slow.shift(1)
    )
    result["common_ok"] = (
        ready & atr.notna() & result.stack_up & result.gaps_expanding
        & ((result.lips - result.jaw) >= FAN_MIN_ATR * atr)
        & (body > 0) & (result.ext_atr <= MAX_EXT_ATR)
    )
    result["thrust_raw"] = result.break_bps >= BODYBREAK_BPS
    result["staircase_raw"] = (
        ready & (result.break_bps >= 0)
        & (result.close > result.close.shift(1))
        & (result.close.shift(1) > result.close.shift(2))
        & solid.shift(1, fill_value=False) & solid.shift(2, fill_value=False)
        & (result.slope2_atr >= STEEP_EMA5_ATR)
    )
    result["thrust_ok"] = result.in_window & result.common_ok & result.thrust_raw
    result["staircase_ok"] = result.in_window & result.common_ok & (
        result.thrust_raw | result.staircase_raw
    )
    for variant in ("thrust", "staircase"):
        qualified = result[f"{variant}_ok"]
        result[f"{variant}_entry"] = qualified & ~qualified.shift(1, fill_value=False)

    metric_names = (
        "atr", "adx", "break_bps", "fan_atr", "lt_atr", "tj_atr", "ext_atr", "slope2_atr"
    )
    events: list[dict[str, object]] = []
    for _, row in result.iterrows():
        for variant in ("thrust", "staircase"):
            if not row[f"{variant}_entry"]:
                continue
            event: dict[str, object] = {
                "date": str(row.date), "variant": variant,
                "signal_min": int(row.min5), "known_min": int(row.known_min),
                "kind": "thrust" if row.thrust_raw else "staircase",
                "close": float(row.close),
            }
            event.update({name: float(row[name]) for name in metric_names})
            events.append(event)
    return result, events
