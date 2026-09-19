"""B09: short native-minute staircase in completed-five-minute bullish context.

Frozen transfer seed: Brent's independent design, sections 4 and 5. Three
strictly rising minute closes and a final close above the prior two full highs
are evaluated independently of the older five-minute staircase package. EMA20
slope spans TWO completed five-minute bars; T's three-bar slope is not reused.
No fills, outcome statistics, pullback condition, or extra indicator gates.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from signals import _check_bars

FIRST_KNOWN_MIN = 600
LAST_KNOWN_MIN = 870
PREHISTORY_BARS = 100


def _check_features(five: pd.DataFrame) -> None:
    """Require finite EMA observations and integer preceding-bar counts."""
    required = {"teeth", "jaw", "t_history_count"}
    if missing := required.difference(five.columns):
        raise ValueError(f"Missing B09 feature columns: {sorted(missing)}")
    values = five[["teeth", "jaw", "t_history_count"]].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("B09 EMA and history values must be finite")
    count = five.t_history_count.to_numpy(dtype=float)
    if (count < 0).any() or (count % 1 != 0).any():
        raise ValueError("B09 history count must be nonnegative integers")


def add_b09_features(features: pd.DataFrame) -> pd.DataFrame:
    """Add the strict, warmed two-bar EMA20-slope context to full history.

    Args:
        features: Chronological complete five-minute RTH bars with continuous
            EMA9/20 (``teeth``/``jaw``) and ``t_history_count``. The preceding
            history is supplied before slicing out individual sessions.

    Returns:
        A copy with ``b09_ema20_lag2`` and ``b09_bull``. The current completed
        bar is eligible only after 100 preceding bars; the lag crosses sessions.
    """
    _check_bars(features)
    _check_features(features)
    result = features.copy()
    result["b09_ema20_lag2"] = result.jaw.shift(2)
    result["b09_bull"] = (
        result.teeth.gt(result.jaw) & result.jaw.gt(result.b09_ema20_lag2)
        & result.t_history_count.ge(PREHISTORY_BARS)
    )
    return result


def _check_day(raw: pd.DataFrame, five: pd.DataFrame) -> str:
    """Validate observed minute prefixes and their completed context bins."""
    _check_bars(five)
    _check_features(five)
    if five.empty or five.date.nunique() != 1:
        raise ValueError("B09 requires five-minute context from exactly one date")
    date = str(five.date.iloc[0])
    if not pd.Series([date]).str.fullmatch(r"\d{4}-\d{2}-\d{2}").all():
        raise ValueError("B09 date must use YYYY-MM-DD")
    pd.to_datetime(date, format="%Y-%m-%d", errors="raise")
    if not np.array_equal(five.min5.to_numpy(), np.arange(570, 570 + 5 * len(five), 5)):
        raise ValueError("B09 context must start at 570 and be contiguous")
    if missing := {"b09_bull", "b09_ema20_lag2"}.difference(five.columns):
        raise ValueError(f"Missing B09 context features: {sorted(missing)}")
    if not five.b09_bull.map(lambda value: isinstance(value, (bool, np.bool_))).all():
        raise ValueError("B09 bullish state must be boolean")
    lag = five.b09_ema20_lag2.to_numpy(dtype=float)
    if np.isinf(lag).any() or not np.isfinite(
        lag[five.t_history_count.ge(PREHISTORY_BARS).to_numpy()]
    ).all():
        raise ValueError("B09 warmed context requires finite lagged EMA20")
    expected_state = (
        five.teeth.gt(five.jaw) & five.jaw.gt(five.b09_ema20_lag2)
        & five.t_history_count.ge(PREHISTORY_BARS)
    )
    if not five.b09_bull.eq(expected_state).all():
        raise ValueError("B09 bullish state disagrees with its EMA/history inputs")
    required = {"min", "open", "high", "low", "close"}
    if missing := required.difference(raw.columns):
        raise ValueError(f"Missing one-minute columns: {sorted(missing)}")
    if raw.empty or not np.isfinite(raw[list(required)].to_numpy(dtype=float)).all():
        raise ValueError("B09 requires finite observed one-minute bars")
    if len(raw) > 390 or not np.array_equal(
        raw["min"].to_numpy(), np.arange(570, 570 + len(raw))
    ):
        raise ValueError("B09 RTH minutes must start at 570 and be contiguous and unique")
    if not (raw[["open", "high", "low", "close"]] > 0).all().all() or not (
        raw.high.ge(raw[["open", "close"]].max(axis=1))
        & raw.low.le(raw[["open", "close"]].min(axis=1)) & raw.high.ge(raw.low)
    ).all():
        raise ValueError("B09 native-minute OHLC bounds are inconsistent")
    if "date" in raw and not raw.date.astype(str).eq(date).all():
        raise ValueError("B09 native-minute and five-minute dates differ")
    complete_count = len(raw) // 5
    if len(five) < complete_count:
        raise ValueError("B09 context does not cover every completed five-minute bin")
    if complete_count:
        completed = raw.iloc[:complete_count * 5].copy()
        completed["min5"] = completed["min"] // 5 * 5
        expected_ohlc = completed.groupby("min5", sort=True).agg(
            open=("open", "first"), high=("high", "max"),
            low=("low", "min"), close=("close", "last"),
        )
        if not np.allclose(
            five.iloc[:complete_count][["open", "high", "low", "close"]].to_numpy(),
            expected_ohlc.to_numpy(), rtol=0, atol=1e-9,
        ):
            raise ValueError("B09 context disagrees with completed native-minute OHLC")
    return date


def evaluate_b09_day(
    raw: pd.DataFrame, five_day: pd.DataFrame,
) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    """Emit the first qualifying minute of each distinct B09 run in one day.

    A start-labelled minute m is known at m+1. Context uses the latest five-minute
    bar with min5+5 <= that decision time, including a newly completed bar at an
    exact boundary. Only the final decision needs bullish context. The three
    closes and two prior highs are actual same-day minute observations. Any
    failed condition rearms; the 10:00–14:30 decision window is inclusive and
    starts fresh even if the staircase already qualified before 10:00.

    Returns:
        One diagnostic row per observed minute and event dictionaries containing
        signal-close references. No future quote or executable fill is inferred.
    """
    date = _check_day(raw, five_day)
    bars = raw.reset_index(drop=True)
    five = five_day.reset_index(drop=True)
    available = five.min5.to_numpy(dtype=int) + 5
    prior_highs = bars.high.shift(1).rolling(2).max()
    prior_close = bars.close.shift(1)
    earlier_close = bars.close.shift(2)
    events: list[dict[str, object]] = []
    records: list[dict[str, object]] = []
    in_run = False
    episode_id: str | None = None

    for i, row in bars.iterrows():
        minute, known = int(row["min"]), int(row["min"]) + 1
        j = int(np.searchsorted(available, known, side="right") - 1)
        context = five.iloc[j] if j >= 0 else None
        bullish = bool(context is not None and context.b09_bull)
        in_window = FIRST_KNOWN_MIN <= known <= LAST_KNOWN_MIN
        rising_closes = bool(earlier_close.iloc[i] < prior_close.iloc[i] < row.close)
        high_break = bool(row.close > prior_highs.iloc[i])
        qualified = bool(in_window and bullish and rising_closes and high_break)
        entry = qualified and not in_run
        if entry:
            episode_id = f"{date}_b09_{known}_{len(events) + 1}"
            events.append({
                "date": date, "variant": "b09", "kind": "b09",
                "signal_min": minute, "known_min": known, "close": float(row.close),
                "episode_id": episode_id, "step_start_min": minute - 2,
                "close_2": float(earlier_close.iloc[i]),
                "close_1": float(prior_close.iloc[i]),
                "prior_two_high": float(prior_highs.iloc[i]),
                "context_min5": int(context.min5),
                "trend_ema9": float(context.teeth), "trend_ema20": float(context.jaw),
                "trend_ema20_lag2": float(context.b09_ema20_lag2),
            })
        elif not qualified:
            episode_id = None
        in_run = qualified
        records.append(row.to_dict() | {
            "date": date, "known_min": known,
            "context_min5": float(context.min5) if context is not None else np.nan,
            "b09_history_count": float(context.t_history_count) if context is not None
            else np.nan,
            "b09_bull": bullish, "b09_in_window": in_window,
            "b09_rising_closes": rising_closes, "b09_high_break": high_break,
            "b09_qualified": qualified, "b09_entry": entry, "episode_id": episode_id,
            "step_start_min": float(minute - 2) if i >= 2 else np.nan,
            "close_2": float(earlier_close.iloc[i]), "close_1": float(prior_close.iloc[i]),
            "prior_two_high": float(prior_highs.iloc[i]),
            "trend_ema9": float(context.teeth) if context is not None else np.nan,
            "trend_ema20": float(context.jaw) if context is not None else np.nan,
            "trend_ema20_lag2": float(context.b09_ema20_lag2) if context is not None
            else np.nan,
        })
    result = pd.DataFrame(records)
    result["episode_id"] = pd.Series([record["episode_id"] for record in records], dtype=object)
    result.index = raw.index
    return result, events
