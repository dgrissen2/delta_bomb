"""B10: frozen first-five-minute opening range, paired breakout and retest.

The opening range is 09:30 through 09:34 inclusive, known at 09:35. Its full
observed high/low stay fixed for the day. This changes B06's reference only:
the first eligible completed five-minute close above the fixed high gets one
daily attempt. A pre-10:00 break does not consume it, and a fresh crossing is
not required. Such earlier breaks and fresh crossing are diagnostics only.
No options, exits, outcomes, or performance from the source study are supplied.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from signals import _check_bars

OR_START_MIN = 570
OR_END_MIN = 575
FIRST_KNOWN_MIN = 600
CUTOFF_KNOWN_MIN = 870
EPISODE_MINUTES = 30
REFERENCE_COLUMNS = [
    "date", "episode_id", "boundary", "or_high", "or_low", "or_start_min",
    "or_end_min", "or_known_min", "reference_start_min5", "reference_end_min5",
    "breakout_min", "breakout_known_min", "breakout_close", "fresh_cross", "prewindow_above",
]
LEDGER_COLUMNS = REFERENCE_COLUMNS + [
    "status", "terminal_min", "terminal_signal_min", "terminal_close",
    "retest_known_min", "wait_minutes",
]


def _check_day(raw: pd.DataFrame, five: pd.DataFrame) -> str:
    """Validate native contiguous OHLC and matching completed five-minute bins."""
    _check_bars(five)
    required = {"min", "open", "high", "low", "close"}
    if missing := required.difference(raw.columns):
        raise ValueError(f"Missing one-minute columns: {sorted(missing)}")
    if raw.empty:
        raise ValueError("B10 requires observed one-minute bars")
    if not np.isfinite(raw[list(required)].to_numpy(dtype=float)).all():
        raise ValueError("One-minute bars must be finite")
    if not np.array_equal(raw["min"].to_numpy(), np.arange(570, 570 + len(raw))):
        raise ValueError("One-minute input must start at 570 and be contiguous and unique")
    if raw["min"].iloc[-1] >= 960:
        raise ValueError("One-minute input must exclude 16:00 and later observations")
    prices = raw[["open", "high", "low", "close"]]
    if not (prices > 0).all().all() or not (
        raw.high.ge(raw[["open", "close"]].max(axis=1))
        & raw.low.le(raw[["open", "close"]].min(axis=1))
        & raw.high.ge(raw.low)
    ).all():
        raise ValueError("One-minute OHLC bounds are inconsistent")
    dates = five.date if not five.empty else raw.get("date", pd.Series(dtype=str))
    if dates.nunique() != 1 or dates.isna().any():
        raise ValueError("B10 requires exactly one date in the context or raw bars")
    date = str(dates.iloc[0])
    if not pd.Series([date]).str.fullmatch(r"\d{4}-\d{2}-\d{2}").all():
        raise ValueError("B10 date must use YYYY-MM-DD")
    pd.to_datetime(date, format="%Y-%m-%d", errors="raise")
    if "date" in raw and not raw.date.astype(str).eq(date).all():
        raise ValueError("One-minute and five-minute dates differ")
    if not np.array_equal(five.min5.to_numpy(), np.arange(570, 570 + 5 * len(five), 5)):
        raise ValueError("Five-minute context must start at 570 and be contiguous")
    completed = len(raw) // 5
    if len(five) < completed:
        raise ValueError("Five-minute context does not cover all completed minute bins")
    if completed:
        native = raw.iloc[:completed * 5].copy()
        native["min5"] = native["min"] // 5 * 5
        observed = native.groupby("min5").agg(
            open=("open", "first"), high=("high", "max"),
            low=("low", "min"), close=("close", "last"),
        )
        if not np.array_equal(
            observed.to_numpy(), five.iloc[:completed][["open", "high", "low", "close"]].to_numpy()
        ):
            raise ValueError("Five-minute OHLC must match completed native-minute bins")
    return date


def evaluate_b10_day(
    raw: pd.DataFrame, five_df: pd.DataFrame,
) -> tuple[pd.DataFrame, list[dict[str, object]], pd.DataFrame]:
    """Evaluate the opening-range replacement with B06's timing and retest rule.

    Args:
        raw: Contiguous observed start-labelled one-minute RTH bars from 09:30.
            A prefix is allowed; before 09:35, a date must be present in either
            this frame or supplied future context.
        five_df: Same-date chronological complete five-minute OHLC from 09:30.
            Extra future rows are allowed but used only once they become known.

    Returns:
        Minute diagnostics, paired immediate/retest events, and one ledger row
        for the day once its opening range is complete. A day without an admitted
        breakout remains ``no_breakout``. An active prefix remains ``pending``.

    Admission is the first close above ORH known from 10:00 to before 14:30,
    even if earlier closes were already above ORH. Retest bars must start at or
    after breakout availability, touch ORH and close above both ORH and the
    prior native-minute high. Cutoff, newly completed five-minute close at/below
    ORH, then 30-minute expiry cancel before a retest. The day never rearms.
    """
    date = _check_day(raw, five_df)
    bars = raw.reset_index(drop=True)
    five = five_df.reset_index(drop=True)
    available = five.min5.to_numpy(dtype=int) + 5
    episode: dict[str, object] | None = None
    events: list[dict[str, object]] = []
    diagnostics: list[dict[str, object]] = []
    attempted = False
    prewindow_above = False

    for i, row in bars.iterrows():
        minute = int(row["min"])
        known = minute + 1
        j = int(np.searchsorted(available, known, side="right") - 1)
        context = five.iloc[j] if j >= 0 else None
        new_context = j >= 0 and int(available[j]) == known
        prior_high = float(bars.high.iloc[i - 1]) if i else np.nan
        breakout_entry = False
        retest_entry = False
        transitions: list[str] = []

        def finish(reason: str) -> None:
            if episode is None:
                raise RuntimeError("Cannot finish an opening range before it exists")
            breakout_known = episode["breakout_known_min"]
            episode.update({
                "status": reason, "terminal_min": known,
                "terminal_signal_min": minute, "terminal_close": float(row.close),
                "wait_minutes": known - int(breakout_known) if breakout_known is not None else None,
            })
            transitions.append(f"{episode['episode_id']}:{reason}")

        if known == OR_END_MIN:
            opening = bars.iloc[:OR_END_MIN - OR_START_MIN]
            high, low = float(opening.high.max()), float(opening.low.min())
            episode = {
                "date": date, "episode_id": f"{date}_b10_{OR_END_MIN}",
                "boundary": high, "or_high": high, "or_low": low,
                "or_start_min": OR_START_MIN, "or_end_min": OR_END_MIN,
                "or_known_min": OR_END_MIN,
                "reference_start_min5": OR_START_MIN, "reference_end_min5": OR_START_MIN,
                "breakout_min": None, "breakout_known_min": None, "breakout_close": None,
                "fresh_cross": None, "prewindow_above": False, "status": "no_breakout",
                "terminal_min": None, "terminal_signal_min": None, "terminal_close": None,
                "retest_known_min": None, "wait_minutes": None,
            }
            transitions.append(f"{episode['episode_id']}:opening_range_complete")

        if episode is not None:
            boundary = float(episode["boundary"])
            if new_context and known < FIRST_KNOWN_MIN and context.close > boundary:
                prewindow_above = True
                episode["prewindow_above"] = True

            # Match B06's cancellation priority; a terminal day never rearms.
            if episode["status"] == "pending":
                if known >= CUTOFF_KNOWN_MIN:
                    finish("cutoff")
                elif new_context and context.close <= boundary:
                    finish("breakout_lost")
                elif known >= int(episode["breakout_known_min"]) + EPISODE_MINUTES:
                    finish("timeout")
            elif episode["status"] == "no_breakout" and known == CUTOFF_KNOWN_MIN:
                finish("no_breakout")

            if (
                not attempted and new_context
                and FIRST_KNOWN_MIN <= known < CUTOFF_KNOWN_MIN
                and context.close > boundary
            ):
                attempted = True
                episode.update({
                    "breakout_min": int(context.min5), "breakout_known_min": known,
                    "breakout_close": float(context.close), "status": "pending",
                    "fresh_cross": bool(five.close.iloc[j - 1] <= boundary),
                    "prewindow_above": prewindow_above,
                })
                events.append({key: episode[key] for key in REFERENCE_COLUMNS} | {
                    "variant": "b10_breakout", "kind": "b10_breakout",
                    "signal_min": int(context.min5), "known_min": known,
                    "close": float(context.close), "wait_minutes": 0,
                    "prior_minute_high": prior_high,
                })
                breakout_entry = True
                transitions.append(f"{episode['episode_id']}:breakout")

            if (
                episode["status"] == "pending"
                and minute >= int(episode["breakout_known_min"])
                and row.low <= boundary and row.close > boundary and row.close > prior_high
            ):
                events.append({key: episode[key] for key in REFERENCE_COLUMNS} | {
                    "variant": "b10_retest", "kind": "b10_retest",
                    "signal_min": minute, "known_min": known, "close": float(row.close),
                    "wait_minutes": known - int(episode["breakout_known_min"]),
                    "prior_minute_high": prior_high,
                })
                retest_entry = True
                episode["retest_known_min"] = known
                finish("trigger")

        active = episode is not None and episode["status"] == "pending"
        diagnostics.append(row.to_dict() | {
            "date": date, "known_min": known,
            "context_min5": float(context.min5) if context is not None else np.nan,
            "prior_minute_high": prior_high,
            "or_high": float(episode["or_high"]) if episode is not None else np.nan,
            "or_low": float(episode["or_low"]) if episode is not None else np.nan,
            "or_available": episode is not None, "attempt_consumed": attempted,
            "prewindow_above": prewindow_above,
            "fresh_cross": episode["fresh_cross"] if episode is not None else None,
            "b10_breakout_entry": breakout_entry, "b10_retest_entry": retest_entry,
            "breakout_episode_ids": str(episode["episode_id"]) if breakout_entry else "",
            "retest_episode_ids": str(episode["episode_id"]) if retest_entry else "",
            "active_episode_ids": str(episode["episode_id"]) if active else "",
            "active_episode_count": int(active), "transition": ";".join(transitions),
        })

    result = pd.DataFrame(diagnostics)
    result["fresh_cross"] = result.fresh_cross.astype("boolean")
    result.index = raw.index
    ledger = pd.DataFrame([episode] if episode is not None else [], columns=LEDGER_COLUMNS)
    return result, events, ledger
