"""B05: the existing eight-point stall and typical-price-mean reclaim trigger.

Condition and 15-minute refire thinning reproduce ``scripts/spx_legin_ev.py``
``stall_trigger_day``. The dashboard uses the shared 14:30 decision cutoff and
sets its own next-minute-open spot reference; this module computes no fills or
outcomes. Repeated entries against the same high/low anchor share an episode ID.
"""

from __future__ import annotations

from datetime import date as calendar_date

import numpy as np
import pandas as pd


FIRST_SIGNAL_MIN = 600
LAST_KNOWN_MIN = 870
PULLBACK_POINTS = 8.0
STALL_BARS = 5
REFIRE_BARS = 15


def _check_minutes(raw: pd.DataFrame, date: str) -> None:
    """Reject missing or reordered observations rather than synthesizing them."""
    try:
        parsed_date = calendar_date.fromisoformat(date)
    except (TypeError, ValueError) as exc:
        raise ValueError("B05 requires an ISO session date (YYYY-MM-DD)") from exc
    if parsed_date.isoformat() != date:
        raise ValueError("B05 requires an ISO session date (YYYY-MM-DD)")
    required = {"min", "open", "high", "low", "close"}
    if missing := required.difference(raw.columns):
        raise ValueError(f"Missing one-minute columns: {sorted(missing)}")
    if raw.empty:
        raise ValueError("B05 requires observed one-minute bars")
    try:
        values = raw[["min", "open", "high", "low", "close"]].to_numpy(dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("One-minute bars must contain numeric values") from exc
    if not np.isfinite(values).all():
        raise ValueError("One-minute bars must be finite")
    minutes = values[:, 0]
    if not np.array_equal(minutes, np.arange(570, 570 + len(raw))):
        raise ValueError("One-minute RTH input must start at 570 and be contiguous and unique")
    if minutes[-1] >= 960:
        raise ValueError("One-minute input must exclude 16:00 and later observations")
    opens, highs, lows, closes = values[:, 1:].T
    if not (values[:, 1:] > 0).all() or not (
        (highs >= np.maximum(opens, closes))
        & (lows <= np.minimum(opens, closes)) & (highs >= lows)
    ).all():
        raise ValueError("One-minute OHLC bounds are inconsistent")
    if "date" in raw and not raw.date.astype(str).eq(date).all():
        raise ValueError("One-minute bars contain a different session date")


def evaluate_b05_day(
    raw1m: pd.DataFrame, date: str,
) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    """Evaluate the causal B05 condition on observed one-minute session bars.

    Args:
        raw1m: Contiguous start-labelled RTH OHLC minutes beginning at 09:30;
            a prefix is permitted for causal checks. Volume is not consulted.
        date: ISO session date. Running state starts afresh at the 10:00 bar.

    Returns:
        One diagnostic row per observation and emitted entry dictionaries.
        ``b05_qualified`` is the price condition inside the decision window,
        before refire thinning; ``b05_entry`` / ``emitted`` identify actual
        emissions. The low bar and current bar both enter the unweighted mean
        of typical price. A bar at minute m is observed at m+1; the latest
        accepted signal bar starts at 14:29 and is known at 14:30.

    Equal highs/lows do not reset state. A strictly new high anchors its own
    bar's low; a strictly lower subsequent low restarts the five-bar wait.
    Reclaim is a strict close-above-mean condition, not a crossing requirement.
    The 15-bar refire timer is global within the day, including new anchors.
    """
    _check_minutes(raw1m, date)
    bars = raw1m.reset_index(drop=True)
    highs = bars.high.to_numpy(dtype=float)
    lows = bars.low.to_numpy(dtype=float)
    closes = bars.close.to_numpy(dtype=float)
    typical_prices = (highs + lows + closes) / 3
    running_high: float | None = None
    running_low: float | None = None
    high_min: int | None = None
    low_index: int | None = None
    last_fire_index: int | None = None
    events: list[dict[str, object]] = []
    diagnostics: list[dict[str, object]] = []

    for index, minute_value in enumerate(bars["min"]):
        minute = int(minute_value)
        known_min = minute + 1
        initialized = minute >= FIRST_SIGNAL_MIN
        in_window = initialized and known_min <= LAST_KNOWN_MIN
        new_high = False
        new_low = False
        if initialized:
            if running_high is None or highs[index] > running_high:
                running_high, running_low = float(highs[index]), float(lows[index])
                high_min, low_index = minute, index
                new_high = True
            if lows[index] < running_low:
                running_low, low_index = float(lows[index]), index
                new_low = True

        if initialized:
            assert running_high is not None and running_low is not None
            assert high_min is not None and low_index is not None
            low_min = int(bars["min"].iloc[low_index])
            pullback = running_high - running_low
            stall_bars = index - low_index
            # Keep the source's inclusive slice and arithmetic, without volume weights.
            tpm = float(typical_prices[low_index:index + 1].mean())
            episode_id: str | None = f"{date}-b05-{high_min}-{low_min}"
        else:
            low_min, episode_id = None, None
            pullback, tpm, stall_bars = np.nan, np.nan, 0

        pullback_ok = bool(initialized and pullback >= PULLBACK_POINTS)
        stall_ok = bool(initialized and stall_bars >= STALL_BARS)
        reclaim_ok = bool(initialized and closes[index] > tpm)
        refire_ready = bool(
            initialized and (last_fire_index is None or index - last_fire_index >= REFIRE_BARS)
        )
        qualified = bool(in_window and pullback_ok and stall_ok and reclaim_ok)
        emitted = bool(qualified and refire_ready)
        if emitted:
            last_fire_index = index
            events.append({
                "date": date, "variant": "b05", "kind": "b05",
                "signal_min": minute, "known_min": known_min,
                "close": float(closes[index]), "episode_id": episode_id,
                "running_high": running_high, "running_high_min": high_min,
                "running_low": running_low, "low_min": low_min,
                "pullback_pts": float(pullback), "stall_bars": stall_bars,
                "tpm": tpm,
            })

        diagnostics.append({
            "date": date, "min": minute, "known_min": known_min,
            "open": float(bars.open.iloc[index]), "high": float(highs[index]),
            "low": float(lows[index]), "close": float(closes[index]),
            "initialized": initialized, "in_window": in_window,
            "new_high": new_high, "new_low": new_low,
            "episode_id": episode_id,
            "running_high": running_high, "running_high_min": high_min,
            "running_low": running_low, "low_min": low_min,
            "pullback_pts": float(pullback), "stall_bars": stall_bars, "tpm": tpm,
            "pullback_ok": pullback_ok, "stall_ok": stall_ok,
            "reclaim_ok": reclaim_ok, "refire_ready": refire_ready,
            "b05_qualified": qualified, "b05_entry": emitted, "emitted": emitted,
        })

    return pd.DataFrame(diagnostics), events
