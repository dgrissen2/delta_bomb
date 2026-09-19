"""Frozen T: completed-five-minute trend, half-ATR pullback, one-minute break.

Contract: OHLCV_BRANCH_COMBINATIONS.md section 8 and quant_crossreview.md:19–25.
This independent entry candidate does not change the thrust/staircase rules.
Prices are observed signal references, not fills; no exit or return is simulated.

Daily prototype conventions: arm no earlier than 10:00; initialize the anchor
from the latest 30 same-day completed minutes INCLUDING the just-completed bar;
no overnight episode carry. Expiry at 14:30 is processed before any trigger.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from signals import _check_bars

FIRST_KNOWN_MIN = 600
CUTOFF_KNOWN_MIN = 870
EPISODE_MINUTES = 30
RETRACE_ATR = 0.5
PREHISTORY_BARS = 100
LEDGER_COLUMNS = [
    "episode_id", "date", "anchor", "anchor_min", "arm_min", "arm_close",
    "arm_atr", "pullback_pts", "pullback_atr", "episode_low", "status",
    "terminal_min", "terminal_signal_min", "terminal_close", "context_min5_at_arm",
]


def add_t_features(features: pd.DataFrame) -> pd.DataFrame:
    """Add SMA-seeded Wilder14 ATR and a warmed, strict EMA9/20 trend state.

    Args:
        features: Complete chronological RTH five-minute bars, with the existing
            continuous undisplaced EMA9/20 columns ``teeth`` and ``jaw``.

    Returns:
        A copy with ``t_atr``, ``t_bull``, and ``t_history_count``. History count
        excludes the current five-minute bar. Opening gaps enter true range.
    """
    _check_bars(features)
    if missing := {"teeth", "jaw"}.difference(features.columns):
        raise ValueError(f"Missing EMA columns: {sorted(missing)}")
    if not np.isfinite(features[["teeth", "jaw"]].to_numpy(dtype=float)).all():
        raise ValueError("EMA features must be finite")
    result = features.copy()
    previous = result.close.shift(1)
    tr = pd.concat([
        result.high - result.low,
        (result.high - previous).abs(),
        (result.low - previous).abs(),
    ], axis=1).max(axis=1).to_numpy(dtype=float)
    atr = np.full(len(result), np.nan)
    if len(result) >= 14:
        atr[13] = tr[:14].mean()
        for i in range(14, len(result)):
            atr[i] = (13 * atr[i - 1] + tr[i]) / 14
    result["t_atr"] = atr
    result["t_history_count"] = np.arange(len(result))
    result["t_bull"] = (
        result.teeth.gt(result.jaw) & result.jaw.gt(result.jaw.shift(3))
        & result.t_history_count.ge(PREHISTORY_BARS)
        & result.t_atr.gt(0) & np.isfinite(result.t_atr)
    )
    return result


def _check_day(raw: pd.DataFrame, five: pd.DataFrame) -> str:
    """Require ordered, contiguous observed minutes and one valid context date."""
    _check_bars(five)
    if five.empty or five.date.nunique() != 1:
        raise ValueError("T requires five-minute features from exactly one date")
    required = {"teeth", "jaw", "t_atr", "t_bull", "t_history_count"}
    if missing := required.difference(five.columns):
        raise ValueError(f"Missing T feature columns: {sorted(missing)}")
    if five[["teeth", "jaw", "t_history_count", "t_bull"]].isna().any().any():
        raise ValueError("T context fields must not be missing")
    if not np.isfinite(five[["teeth", "jaw", "t_history_count"]].to_numpy()).all():
        raise ValueError("T context fields must be finite")
    if not five.t_bull.isin([True, False]).all():
        raise ValueError("t_bull must be a boolean state")
    if (five.t_history_count < 0).any():
        raise ValueError("T history count cannot be negative")
    required = {"min", "open", "high", "low", "close"}
    if missing := required.difference(raw.columns):
        raise ValueError(f"Missing one-minute columns: {sorted(missing)}")
    if raw.empty:
        raise ValueError("T requires observed one-minute bars")
    values = raw[["min", "open", "high", "low", "close"]].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("One-minute bars must be finite")
    mins = raw["min"].to_numpy()
    if mins[0] != 570 or not np.array_equal(mins, np.arange(570, 570 + len(raw))):
        raise ValueError("One-minute RTH input must start at 570 and be contiguous and unique")
    if mins[-1] >= 960:
        raise ValueError("One-minute input must exclude 16:00 and later observations")
    prices = raw[["open", "high", "low", "close"]]
    if not (prices > 0).all().all() or not (
        raw.high.ge(raw[["open", "close"]].max(axis=1))
        & raw.low.le(raw[["open", "close"]].min(axis=1))
        & raw.high.ge(raw.low)
    ).all():
        raise ValueError("One-minute OHLC bounds are inconsistent")
    date = str(five.date.iloc[0])
    if "date" in raw and not raw.date.astype(str).eq(date).all():
        raise ValueError("One-minute and five-minute dates differ")
    return date


def evaluate_t_day(
    raw: pd.DataFrame, day_features: pd.DataFrame,
) -> tuple[pd.DataFrame, list[dict[str, object]], pd.DataFrame]:
    """Evaluate causal T episodes on one session, without reading any files.

    ``raw`` has a ``min`` column of contiguous start-labelled RTH minutes from
    09:30; a prefix is allowed for causality checks. ``day_features`` is that
    date's slice of ``add_t_features``. A minute m is known at m+1; a five-minute
    interval is available at min5+5. No future feature row is consulted.

    Returns:
        Minute diagnostics, immutable emitted-event dictionaries, and a ledger
        containing every armed episode. A truncated prefix can leave a ledger
        episode ``pending``; a full day resolves all arms by the 14:30 cutoff.
    """
    date = _check_day(raw, day_features)
    bars = raw.reset_index(drop=True)
    five = day_features.reset_index(drop=True)
    available = five.min5.to_numpy(dtype=int) + 5
    prior_highs = bars.high.shift(1).rolling(3).max()
    anchor: float | None = None
    anchor_min: int | None = None
    consumed = False
    pending: dict[str, object] | None = None
    episodes: list[dict[str, object]] = []
    events: list[dict[str, object]] = []
    diagnostics: list[dict[str, object]] = []

    for i, row in bars.iterrows():
        minute, known = int(row["min"]), int(row["min"]) + 1
        j = int(np.searchsorted(available, known, side="right") - 1)
        context = five.iloc[j] if j >= 0 else None
        atr = float(context.t_atr) if context is not None else np.nan
        ready = bool(
            context is not None and context.t_history_count >= PREHISTORY_BARS
            and np.isfinite(atr) and atr > 0
        )
        bullish = bool(ready and context.t_bull)
        entry = False
        action = ""

        def finish(reason: str) -> None:
            """Terminate the current ledger episode at the observed minute."""
            nonlocal pending, consumed, action
            if pending is None:
                return
            pending.update({
                "status": reason, "terminal_min": known,
                "terminal_signal_min": minute, "terminal_close": float(row.close),
            })
            pending = None
            consumed = True
            action = reason

        if pending is not None:
            pending["episode_low"] = min(float(pending["episode_low"]), float(row.low))

        if known >= CUTOFF_KNOWN_MIN:
            finish("cutoff")
        elif known >= FIRST_KNOWN_MIN:
            if not bullish:
                finish("trend_lost")
                anchor, anchor_min, consumed = None, None, False
            else:
                if anchor is None:
                    window = bars.iloc[max(0, i - 29):i + 1]
                    if len(window) != 30:
                        raise ValueError("T anchor requires 30 completed same-day minutes")
                    # The most recent occurrence represents an equal initial maximum.
                    anchor = float(window.high.max())
                    anchor_min = int(window.loc[window.high.eq(anchor), "min"].iloc[-1])
                    consumed = False
                elif row.high > anchor:
                    finish("new_high")
                    anchor, anchor_min, consumed = float(row.high), minute, False

                if pending is not None and known >= int(pending["arm_min"]) + EPISODE_MINUTES:
                    finish("timeout")

                if (
                    pending is not None and known > int(pending["arm_min"])
                    and row.close > prior_highs.iloc[i] and row.close > context.jaw
                ):
                    event = {
                        "date": date, "variant": "t", "kind": "t",
                        "signal_min": minute, "known_min": known,
                        "close": float(row.close), "atr": float(pending["arm_atr"]),
                        "arm_min": int(pending["arm_min"]), "anchor": float(anchor),
                        "anchor_min": anchor_min, "arm_close": float(pending["arm_close"]),
                        "pullback_pts": float(pending["pullback_pts"]),
                        "arm_atr": float(pending["arm_atr"]),
                        "pullback_atr": float(pending["pullback_atr"]),
                        "trigger_high": float(prior_highs.iloc[i]),
                        "trend_ema20": float(context.jaw),
                        "context_min5": int(context.min5),
                        "episode_low": float(pending["episode_low"]),
                        "episode_id": str(pending["episode_id"]),
                        "wait_minutes": known - int(pending["arm_min"]),
                    }
                    events.append(event)
                    entry = True
                    finish("trigger")

                if pending is None and not consumed and anchor - row.close >= RETRACE_ATR * atr:
                    pending = {
                        "episode_id": f"{date}_t_{known}_{len(episodes) + 1}",
                        "date": date, "anchor": anchor, "anchor_min": anchor_min,
                        "arm_min": known, "arm_close": float(row.close), "arm_atr": atr,
                        "pullback_pts": float(anchor - row.close),
                        "pullback_atr": float((anchor - row.close) / atr),
                        "episode_low": float(row.low), "status": "pending",
                        "terminal_min": None, "terminal_signal_min": None,
                        "terminal_close": None, "context_min5_at_arm": int(context.min5),
                    }
                    episodes.append(pending)
                    action = f"{action};arm" if action else "arm"

        record = row.to_dict()
        record.update({
            "date": date, "known_min": known,
            "context_min5": int(context.min5) if context is not None else None,
            "t_atr": atr, "t_bull": bullish,
            "t_history_count": int(context.t_history_count) if context is not None else 0,
            "trend_ema9": float(context.teeth) if context is not None else np.nan,
            "trend_ema20": float(context.jaw) if context is not None else np.nan,
            "prior_three_high": float(prior_highs.iloc[i]),
            "anchor": anchor, "anchor_min": anchor_min,
            "arm_min": pending["arm_min"] if pending is not None else None,
            "arm_atr": pending["arm_atr"] if pending is not None else None,
            "episode_id": pending["episode_id"] if pending is not None else None,
            "state": "armed" if pending is not None else (
                "consumed" if consumed else "tracking" if anchor is not None else "inactive"
            ),
            "transition": action, "t_entry": entry,
        })
        diagnostics.append(record)

    result = pd.DataFrame(diagnostics)
    result.index = raw.index
    return result, events, pd.DataFrame(episodes, columns=LEDGER_COLUMNS)
