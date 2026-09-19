"""B06: paired five-minute channel breakout and later one-minute retest.

The frozen boundary is the maximum high of the six same-day five-minute bars
before the breakout. Every distinct numerical boundary gets one attempt per day;
overlapping attempts remain separate, paired research episodes, not positions.
The early completed-retest recipe follows OHLCV_BRANCH_COMBINATIONS.md Family D
and section 8. Equality at a later five-minute close loses the strict breakout.
No option fills, exits, P&L, or independent-sample interpretation is supplied.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from signals import _check_bars

FIRST_KNOWN_MIN = 600
CUTOFF_KNOWN_MIN = 870
EPISODE_MINUTES = 30
CHANNEL_BARS = 6
LEDGER_COLUMNS = [
    "episode_id", "date", "boundary", "reference_start_min5", "reference_end_min5",
    "breakout_min", "breakout_known_min", "breakout_close", "status", "terminal_min",
    "terminal_signal_min", "terminal_close", "retest_known_min", "wait_minutes",
]


def _check_day(raw: pd.DataFrame, five: pd.DataFrame) -> str:
    """Validate observed ordered OHLC and contiguous same-day context bars."""
    _check_bars(five)
    if five.empty or five.date.nunique() != 1:
        raise ValueError("B06 requires five-minute bars from exactly one date")
    date = str(five.date.iloc[0])
    if not pd.Series([date]).str.fullmatch(r"\d{4}-\d{2}-\d{2}").all():
        raise ValueError("B06 date must use YYYY-MM-DD")
    pd.to_datetime(date, format="%Y-%m-%d", errors="raise")
    if not np.array_equal(five.min5.to_numpy(), np.arange(570, 570 + 5 * len(five), 5)):
        raise ValueError("Five-minute context must start at 570 and be contiguous")
    required = {"min", "open", "high", "low", "close"}
    if missing := required.difference(raw.columns):
        raise ValueError(f"Missing one-minute columns: {sorted(missing)}")
    if raw.empty:
        raise ValueError("B06 requires observed one-minute bars")
    if not np.isfinite(raw[list(required)].to_numpy(dtype=float)).all():
        raise ValueError("One-minute bars must be finite")
    if not np.array_equal(raw["min"].to_numpy(), np.arange(570, 570 + len(raw))):
        raise ValueError("One-minute RTH input must start at 570 and be contiguous and unique")
    if raw["min"].iloc[-1] >= 960:
        raise ValueError("One-minute input must exclude 16:00 and later observations")
    prices = raw[["open", "high", "low", "close"]]
    if not (prices > 0).all().all() or not (
        raw.high.ge(raw[["open", "close"]].max(axis=1))
        & raw.low.le(raw[["open", "close"]].min(axis=1))
        & raw.high.ge(raw.low)
    ).all():
        raise ValueError("One-minute OHLC bounds are inconsistent")
    if "date" in raw and not raw.date.astype(str).eq(date).all():
        raise ValueError("One-minute and five-minute dates differ")
    if len(five) < len(raw) // 5:
        raise ValueError("Five-minute context does not cover all completed minute bins")
    return date


def evaluate_b06_day(
    raw: pd.DataFrame, five_df: pd.DataFrame,
) -> tuple[pd.DataFrame, list[dict[str, object]], pd.DataFrame]:
    """Evaluate one session's immediate and retest entries on paired episodes.

    Args:
        raw: Contiguous observed start-labelled one-minute RTH bars from 09:30.
            A prefix is allowed. Future context rows do not affect past output.
        five_df: That date's chronological complete five-minute OHLC feature
            frame, starting at 09:30; extra feature columns are ignored.

    Returns:
        Native-minute diagnostics, immutable event dictionaries, and a ledger
        of every breakout episode. Immediate ``signal_min`` is its five-minute
        interval start; retest ``signal_min`` is its one-minute interval start.
        Both become known at their interval end. The breakout close is never
        assigned to an earlier minute. Pending prefix episodes stay pending.

    A retest bar must start at or after breakout availability, touch the frozen
    boundary with its low, and close strictly above both that boundary and the
    previous observed minute's high. Cutoff, a newly completed five-minute close
    at/below the boundary, then thirty-minute expiry are processed before entry.
    """
    date = _check_day(raw, five_df)
    bars = raw.reset_index(drop=True)
    five = five_df.reset_index(drop=True)
    available = five.min5.to_numpy(dtype=int) + 5
    boundaries = five.high.shift(1).rolling(CHANNEL_BARS).max()
    attempted: set[float] = set()
    episodes: list[dict[str, object]] = []
    pending: list[dict[str, object]] = []
    events: list[dict[str, object]] = []
    diagnostics: list[dict[str, object]] = []

    for i, row in bars.iterrows():
        minute = int(row["min"])
        known = minute + 1
        j = int(np.searchsorted(available, known, side="right") - 1)
        context = five.iloc[j] if j >= 0 else None
        new_context = j >= 0 and int(available[j]) == known
        prior_high = float(bars.high.iloc[i - 1]) if i else np.nan
        breakout_ids: list[str] = []
        retest_ids: list[str] = []
        transitions: list[str] = []

        def finish(episode: dict[str, object], reason: str) -> None:
            episode.update({
                "status": reason, "terminal_min": known,
                "terminal_signal_min": minute, "terminal_close": float(row.close),
                "wait_minutes": known - int(episode["breakout_known_min"]),
            })
            transitions.append(f"{episode['episode_id']}:{reason}")

        # Cancel every old episode independently before any current-bar trigger.
        for episode in pending:
            if known >= CUTOFF_KNOWN_MIN:
                finish(episode, "cutoff")
            elif new_context and context.close <= float(episode["boundary"]):
                finish(episode, "breakout_lost")
            elif known >= int(episode["breakout_known_min"]) + EPISODE_MINUTES:
                finish(episode, "timeout")
        pending = [episode for episode in pending if episode["status"] == "pending"]

        if (
            new_context and FIRST_KNOWN_MIN <= known < CUTOFF_KNOWN_MIN
            and j >= CHANNEL_BARS and context.close > boundaries.iloc[j]
        ):
            boundary = float(boundaries.iloc[j])
            if boundary not in attempted:
                attempted.add(boundary)
                episode = {
                    "episode_id": f"{date}_b06_{known}_{len(episodes) + 1}",
                    "date": date, "boundary": boundary,
                    "reference_start_min5": int(five.min5.iloc[j - CHANNEL_BARS]),
                    "reference_end_min5": int(five.min5.iloc[j - 1]),
                    "breakout_min": int(context.min5), "breakout_known_min": known,
                    "breakout_close": float(context.close), "status": "pending",
                    "terminal_min": None, "terminal_signal_min": None,
                    "terminal_close": None, "retest_known_min": None, "wait_minutes": None,
                }
                episodes.append(episode)
                pending.append(episode)
                breakout_ids.append(str(episode["episode_id"]))
                transitions.append(f"{episode['episode_id']}:breakout")
                events.append({
                    key: episode[key] for key in (
                        "date", "episode_id", "boundary", "reference_start_min5",
                        "reference_end_min5", "breakout_min", "breakout_known_min",
                        "breakout_close",
                    )
                } | {
                    "variant": "b06_breakout", "kind": "b06_breakout",
                    "signal_min": int(context.min5), "known_min": known,
                    "close": float(context.close), "wait_minutes": 0,
                    "prior_minute_high": prior_high,
                })

        for episode in pending:
            boundary = float(episode["boundary"])
            if (
                minute >= int(episode["breakout_known_min"])
                and row.low <= boundary and row.close > boundary and row.close > prior_high
            ):
                events.append({
                    key: episode[key] for key in (
                        "date", "episode_id", "boundary", "reference_start_min5",
                        "reference_end_min5", "breakout_min", "breakout_known_min",
                        "breakout_close",
                    )
                } | {
                    "variant": "b06_retest", "kind": "b06_retest",
                    "signal_min": minute, "known_min": known, "close": float(row.close),
                    "wait_minutes": known - int(episode["breakout_known_min"]),
                    "prior_minute_high": prior_high,
                })
                retest_ids.append(str(episode["episode_id"]))
                episode["retest_known_min"] = known
                finish(episode, "trigger")
        pending = [episode for episode in pending if episode["status"] == "pending"]

        diagnostics.append(row.to_dict() | {
            "date": date, "known_min": known,
            "context_min5": int(context.min5) if context is not None else None,
            "prior_minute_high": prior_high,
            "channel_boundary": float(boundaries.iloc[j]) if j >= 0 else np.nan,
            "b06_breakout_entry": bool(breakout_ids), "b06_retest_entry": bool(retest_ids),
            "b06_breakout_count": len(breakout_ids), "b06_retest_count": len(retest_ids),
            "breakout_episode_ids": "|".join(breakout_ids),
            "retest_episode_ids": "|".join(retest_ids),
            "active_episode_ids": "|".join(str(episode["episode_id"]) for episode in pending),
            "active_episode_count": len(pending), "transition": ";".join(transitions),
        })

    result = pd.DataFrame(diagnostics)
    result.index = raw.index
    return result, events, pd.DataFrame(episodes, columns=LEDGER_COLUMNS)
