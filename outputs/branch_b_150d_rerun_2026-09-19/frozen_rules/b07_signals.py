"""B07: failed breakdown of a range frozen before its one-minute probe.

The range recipe is Brent's corrected six-bar seed followed by two distinct
assessment closes. It does not infer pivots or add an EMA admission gate. Every
numeric low/high pair has one thirty-minute attempt per session; overlapping
ranges remain separate research episodes, not independent trades or positions.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from signals import _check_bars

FIRST_KNOWN_MIN = 600
CUTOFF_KNOWN_MIN = 870
RANGE_BARS = 6
ASSESSMENT_BARS = 2
EPISODE_MINUTES = 30
LEDGER_COLUMNS = [
    "episode_id", "date", "range_low", "range_high", "reference_start_min5",
    "reference_end_min5", "assessment_start_min5", "range_min5", "range_known_min",
    "probe_low", "probe_min", "probe_known_min", "reclaim_high", "reclaim_min",
    "reclaim_known_min", "status", "terminal_min", "terminal_signal_min",
    "terminal_close", "wait_minutes",
]
EVENT_FIELDS = [
    "episode_id", "date", "range_low", "range_high", "reference_start_min5",
    "reference_end_min5", "assessment_start_min5", "range_min5", "range_known_min",
    "probe_low", "probe_min", "probe_known_min", "reclaim_high", "reclaim_min",
    "reclaim_known_min",
]


def _check_day(raw: pd.DataFrame, five: pd.DataFrame) -> str:
    """Reject missing native observations and inconsistent completed context."""
    _check_bars(five)
    if five.empty or five.date.nunique() != 1:
        raise ValueError("B07 requires five-minute context from exactly one date")
    date = str(five.date.iloc[0])
    if not pd.Series([date]).str.fullmatch(r"\d{4}-\d{2}-\d{2}").all():
        raise ValueError("B07 date must use YYYY-MM-DD")
    pd.to_datetime(date, format="%Y-%m-%d", errors="raise")
    if not np.array_equal(five.min5.to_numpy(), np.arange(570, 570 + 5 * len(five), 5)):
        raise ValueError("Five-minute context must start at 570 and be contiguous")
    required = {"min", "open", "high", "low", "close"}
    if missing := required.difference(raw.columns):
        raise ValueError(f"Missing one-minute columns: {sorted(missing)}")
    if raw.empty or not np.isfinite(raw[list(required)].to_numpy(dtype=float)).all():
        raise ValueError("B07 requires finite observed one-minute bars")
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
    complete_count = len(raw) // 5
    if len(five) < complete_count:
        raise ValueError("Five-minute context does not cover all completed minute bins")
    if complete_count:
        completed = raw.iloc[:complete_count * 5].copy()
        completed["min5"] = completed["min"] // 5 * 5
        expected = completed.groupby("min5", sort=True).agg(
            open=("open", "first"), high=("high", "max"),
            low=("low", "min"), close=("close", "last"),
        )
        if not np.allclose(
            five.iloc[:complete_count][["open", "high", "low", "close"]].to_numpy(),
            expected.to_numpy(), rtol=0, atol=1e-9,
        ):
            raise ValueError("Five-minute context disagrees with completed native minute bars")
    return date


def evaluate_b07_day(
    raw: pd.DataFrame, five_df: pd.DataFrame,
) -> tuple[pd.DataFrame, list[dict[str, object]], pd.DataFrame]:
    """Evaluate fixed-range probes, reclaims and later upward close breaks.

    Args:
        raw: Contiguous observed start-labelled one-minute RTH bars from 09:30.
            A prefix is allowed; later supplied context cannot affect output.
        five_df: Same-day complete five-minute OHLC bars, beginning at 09:30.
            These must agree with completed native-minute bins.

    Returns:
        Native-minute diagnostics, emitted ``b07`` event dictionaries, and all
        range episodes, including failed, untouched and still-pending ranges.

    At completed five-minute bar j, freeze seed highs/lows from j-7 through j-2
    only when assessment closes j-1 and j are inside inclusively. The earliest
    same-day confirmation is 10:10. Watch bars starting at/after confirmation.
    The first strict low undercut fixes the probe extreme; the first subsequent
    close above the range low and at/below its high fixes the reclaim high.
    Probe and reclaim may share a completed bar; the upward close break must be
    on a strictly later minute. Cancellation precedes entry: 14:30 cutoff,
    thirty minutes from range confirmation, close below the first probe low,
    or close above the range before any probe. No reference is redrawn.
    """
    date = _check_day(raw, five_df)
    bars = raw.reset_index(drop=True)
    five = five_df.reset_index(drop=True)
    available = five.min5.to_numpy(dtype=int) + 5
    range_lows = five.low.shift(ASSESSMENT_BARS).rolling(RANGE_BARS).min()
    range_highs = five.high.shift(ASSESSMENT_BARS).rolling(RANGE_BARS).max()
    attempted: set[tuple[float, float]] = set()
    episodes: list[dict[str, object]] = []
    pending: list[dict[str, object]] = []
    events: list[dict[str, object]] = []
    diagnostics: list[dict[str, object]] = []

    for _, row in bars.iterrows():
        minute = int(row["min"])
        known = minute + 1
        # No post-cutoff five-minute bar is admitted as a new setup context.
        context_time = min(known, CUTOFF_KNOWN_MIN - 1)
        j = int(np.searchsorted(available, context_time, side="right") - 1)
        new_context = j >= 0 and int(available[j]) == known
        confirmed_ids: list[str] = []
        probe_ids: list[str] = []
        reclaim_ids: list[str] = []
        entry_ids: list[str] = []
        transitions: list[str] = []

        def finish(episode: dict[str, object], reason: str) -> None:
            episode.update({
                "status": reason, "terminal_min": known,
                "terminal_signal_min": minute, "terminal_close": float(row.close),
                "wait_minutes": known - int(episode["range_known_min"]),
            })
            transitions.append(f"{episode['episode_id']}:{reason}")

        for episode in pending:
            if known >= CUTOFF_KNOWN_MIN:
                finish(episode, "cutoff")
            elif known >= int(episode["range_known_min"]) + EPISODE_MINUTES:
                finish(episode, "timeout")
            elif episode["probe_min"] is not None and row.close < float(episode["probe_low"]):
                finish(episode, "probe_lost")
            elif episode["probe_min"] is None and row.close > float(episode["range_high"]):
                finish(episode, "range_ran_away")
        pending = [episode for episode in pending if episode["status"] == "pending"]

        if (
            new_context and FIRST_KNOWN_MIN <= known < CUTOFF_KNOWN_MIN
            and j >= RANGE_BARS + ASSESSMENT_BARS - 1
        ):
            low, high = float(range_lows.iloc[j]), float(range_highs.iloc[j])
            assessments = five.close.iloc[j - 1:j + 1]
            if assessments.between(low, high, inclusive="both").all() and (low, high) not in attempted:
                attempted.add((low, high))
                episode = {
                    "episode_id": f"{date}_b07_{known}_{len(episodes) + 1}",
                    "date": date, "range_low": low, "range_high": high,
                    "reference_start_min5": int(five.min5.iloc[j - 7]),
                    "reference_end_min5": int(five.min5.iloc[j - 2]),
                    "assessment_start_min5": int(five.min5.iloc[j - 1]),
                    "range_min5": int(five.min5.iloc[j]), "range_known_min": known,
                    "probe_low": None, "probe_min": None, "probe_known_min": None,
                    "reclaim_high": None, "reclaim_min": None, "reclaim_known_min": None,
                    "status": "pending", "terminal_min": None,
                    "terminal_signal_min": None, "terminal_close": None, "wait_minutes": None,
                }
                episodes.append(episode)
                pending.append(episode)
                confirmed_ids.append(str(episode["episode_id"]))
                transitions.append(f"{episode['episode_id']}:range_confirmed")

        for episode in pending:
            if minute < int(episode["range_known_min"]):
                continue
            episode_id = str(episode["episode_id"])
            if episode["probe_min"] is None and row.low < float(episode["range_low"]):
                episode.update({
                    "probe_min": minute, "probe_known_min": known, "probe_low": float(row.low),
                })
                probe_ids.append(episode_id)
                transitions.append(f"{episode_id}:probe")
            if (
                episode["probe_min"] is not None and episode["reclaim_min"] is None
                and float(episode["range_low"]) < row.close <= float(episode["range_high"])
            ):
                episode.update({
                    "reclaim_min": minute, "reclaim_known_min": known,
                    "reclaim_high": float(row.high),
                })
                reclaim_ids.append(episode_id)
                transitions.append(f"{episode_id}:reclaim")
            if (
                episode["reclaim_min"] is not None and minute > int(episode["reclaim_min"])
                and row.close > float(episode["reclaim_high"])
            ):
                events.append({key: episode[key] for key in EVENT_FIELDS} | {
                    "variant": "b07", "kind": "b07", "signal_min": minute,
                    "known_min": known, "close": float(row.close),
                    "wait_minutes": known - int(episode["range_known_min"]),
                })
                entry_ids.append(episode_id)
                finish(episode, "trigger")
        pending = [episode for episode in pending if episode["status"] == "pending"]

        diagnostics.append(row.to_dict() | {
            "date": date, "known_min": known,
            "context_min5": int(five.min5.iloc[j]) if j >= 0 else None,
            "b07_entry": bool(entry_ids), "b07_count": len(entry_ids),
            "range_confirmed_count": len(confirmed_ids), "probe_count": len(probe_ids),
            "reclaim_count": len(reclaim_ids), "entry_episode_ids": "|".join(entry_ids),
            "confirmed_episode_ids": "|".join(confirmed_ids),
            "probe_episode_ids": "|".join(probe_ids),
            "reclaim_episode_ids": "|".join(reclaim_ids),
            "active_episode_ids": "|".join(str(episode["episode_id"]) for episode in pending),
            "active_episode_count": len(pending), "transition": ";".join(transitions),
        })

    result = pd.DataFrame(diagnostics)
    result.index = raw.index
    return result, events, pd.DataFrame(episodes, columns=LEDGER_COLUMNS)
