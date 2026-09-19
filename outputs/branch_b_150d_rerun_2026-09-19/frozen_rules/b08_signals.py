"""B08: frozen five-minute lower-band excursion and paired minute recoveries.

This is the fixed Rank 3 hypothesis in ``quant_independent.md``. Bollinger20,2
uses population standard deviation. Flat means absolute three-bar SMA20 change
at most 0.25 times SMA-seeded Wilder14 ATR, with 100 preceding five-minute bars.
Price and RSI alternatives share one frozen excursion; they are not positions.

The completed dip may already close above the band. Both alternatives still
wait for a later observed one-minute bar; no intra-five-minute path is inferred.
Only the first later RSI14 upcross through 30 is attempted. A cross below/equal
to the frozen band consumes that alternative without an entry. No option fills,
exits, return estimates, or empirically selected parameters are supplied here.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from signals import _check_bars

FIRST_KNOWN_MIN = 600
CUTOFF_KNOWN_MIN = 870
EPISODE_MINUTES = 30
PREHISTORY_BARS = 100
LEDGER_COLUMNS = [
    "episode_id", "date", "band_lower", "arm_min5", "arm_known_min", "arm_low",
    "arm_close", "arm_atr", "arm_sma", "flat_change", "price_known_min", "price_status",
    "rsi_known_min", "rsi_cross_min", "rsi_status", "status", "terminal_min",
    "terminal_signal_min", "terminal_close",
]


def _check_atr_history(five: pd.DataFrame) -> None:
    """Allow ATR warmup NaNs, rejecting invalid established ATR/history values."""
    required = {"t_atr", "t_history_count"}
    if missing := required.difference(five.columns):
        raise ValueError(f"Missing B08 ATR/history columns: {sorted(missing)}")
    atr = five.t_atr.to_numpy(dtype=float)
    count = five.t_history_count.to_numpy(dtype=float)
    if np.isinf(atr).any() or (atr < 0).any():
        raise ValueError("B08 ATR must be nonnegative and finite where present")
    if not np.isfinite(count).all() or (count < 0).any() or (count % 1 != 0).any():
        raise ValueError("B08 history count must be finite nonnegative integers")


def add_b08_features(five_all_history: pd.DataFrame) -> pd.DataFrame:
    """Add continuous, completed-five-minute BB20,2 and the fixed flat state.

    Args:
        five_all_history: Chronological complete five-minute RTH bars with
            ``t_atr`` and ``t_history_count`` from ``add_t_features``.

    Returns:
        A copy with ``b08_mid/lower/upper``, signed ``b08_flat_change``, and
        boolean ``b08_flat``. Current completed close enters its own bands;
        no future close or intrabar band estimate is used.
    """
    _check_bars(five_all_history)
    _check_atr_history(five_all_history)
    result = five_all_history.copy()
    result["b08_mid"] = result.close.rolling(20).mean()
    std = result.close.rolling(20).std(ddof=0)
    result["b08_lower"] = result.b08_mid - 2 * std
    result["b08_upper"] = result.b08_mid + 2 * std
    result["b08_flat_change"] = result.b08_mid - result.b08_mid.shift(3)
    result["b08_flat"] = (
        result.b08_flat_change.abs().le(0.25 * result.t_atr)
        & result.t_atr.gt(0) & np.isfinite(result.t_atr)
        & result.t_history_count.ge(PREHISTORY_BARS)
    )
    return result


def _check_minutes(raw: pd.DataFrame, *, complete_sessions: bool) -> None:
    """Require ordered, genuine RTH OHLC; never sort, fill, or invent rows."""
    required = {"date", "min", "open", "high", "low", "close"}
    if missing := required.difference(raw.columns):
        raise ValueError(f"Missing B08 minute columns: {sorted(missing)}")
    if raw.empty:
        raise ValueError("B08 requires observed one-minute bars")
    if raw.date.isna().any() or not raw.date.astype(str).str.fullmatch(
        r"\d{4}-\d{2}-\d{2}"
    ).all():
        raise ValueError("B08 dates must use YYYY-MM-DD")
    pd.to_datetime(raw.date, format="%Y-%m-%d", errors="raise")
    keys = pd.MultiIndex.from_frame(raw[["date", "min"]])
    if not keys.is_unique or not keys.is_monotonic_increasing:
        raise ValueError("B08 minutes must be unique and chronological by date, min")
    if not np.isfinite(raw[["min", "open", "high", "low", "close"]].to_numpy(
        dtype=float
    )).all():
        raise ValueError("B08 minute values must be finite")
    prices = raw[["open", "high", "low", "close"]]
    if not (prices > 0).all().all() or not (
        raw.high.ge(raw[["open", "close"]].max(axis=1))
        & raw.low.le(raw[["open", "close"]].min(axis=1)) & raw.high.ge(raw.low)
    ).all():
        raise ValueError("B08 minute OHLC bounds are inconsistent")
    for _, group in raw.groupby("date", sort=False):
        expected = np.arange(570, 960 if complete_sessions else 570 + len(group))
        if len(group) > 390 or not np.array_equal(group["min"].to_numpy(), expected):
            requirement = (
                "complete 390-minute sessions" if complete_sessions else "contiguous prefixes"
            )
            raise ValueError(f"B08 RTH requires {requirement} starting at 570")


def add_b08_minute_features(raw_all_history: pd.DataFrame) -> pd.DataFrame:
    """Add continuous Wilder RSI14 using observed close-to-close changes.

    The first RSI uses the first fourteen actual changes, at observation 15.
    Smoothing then continues across complete RTH sessions, including the next
    opening change; no synthetic overnight observations or daily resets occur.
    Both zero averages yield 50, gain-only yields 100, and loss-only yields 0.
    Returns a copy with ``b08_rsi14`` and its lag ``b08_rsi_previous``.
    """
    _check_minutes(raw_all_history, complete_sessions=True)
    result = raw_all_history.copy()
    delta = result.close.diff().to_numpy(dtype=float)
    rsi = np.full(len(result), np.nan)
    if len(result) >= 15:
        gains = np.maximum(delta, 0)
        losses = np.maximum(-delta, 0)
        gain, loss = float(gains[1:15].mean()), float(losses[1:15].mean())
        for i in range(14, len(result)):
            if i > 14:
                gain = (13 * gain + gains[i]) / 14
                loss = (13 * loss + losses[i]) / 14
            if gain == loss == 0:
                rsi[i] = 50.0
            elif loss == 0:
                rsi[i] = 100.0
            elif gain == 0:
                rsi[i] = 0.0
            else:
                rsi[i] = 100 * gain / (gain + loss)
    result["b08_rsi14"] = rsi
    result["b08_rsi_previous"] = result.b08_rsi14.shift(1)
    return result


def _check_day(raw: pd.DataFrame, five: pd.DataFrame) -> str:
    """Validate a day's observed minute prefix and available context features."""
    _check_bars(five)
    _check_atr_history(five)
    if five.empty or five.date.nunique() != 1:
        raise ValueError("B08 requires five-minute context from exactly one date")
    date = str(five.date.iloc[0])
    _check_minutes(raw if "date" in raw else raw.assign(date=date), complete_sessions=False)
    if "date" in raw and not raw.date.astype(str).eq(date).all():
        raise ValueError("B08 minute and five-minute dates differ")
    if not np.array_equal(five.min5.to_numpy(), np.arange(570, 570 + 5 * len(five), 5)):
        raise ValueError("B08 five-minute context must start at 570 and be contiguous")
    if len(five) < len(raw) // 5:
        raise ValueError("B08 context does not cover every completed five-minute bin")
    required = {"b08_lower", "b08_mid", "b08_upper", "b08_flat", "b08_flat_change"}
    if missing := required.difference(five.columns):
        raise ValueError(f"Missing B08 context features: {sorted(missing)}")
    if not five.b08_flat.isin([True, False]).all():
        raise ValueError("B08 flat state must be boolean")
    metrics = five[["b08_lower", "b08_mid", "b08_upper", "b08_flat_change"]].to_numpy(
        dtype=float
    )
    if np.isinf(metrics).any() or not np.isfinite(metrics[five.b08_flat.to_numpy(
        dtype=bool
    )]).all():
        raise ValueError("B08 active flat states require finite bands and slope")
    if (
        five.b08_flat & (five.t_atr.le(0) | five.t_atr.isna()
                         | five.t_history_count.lt(PREHISTORY_BARS))
    ).any():
        raise ValueError("B08 flat state requires a positive ATR and 100 preceding bars")
    if (five.b08_lower.gt(five.b08_mid) | five.b08_mid.gt(five.b08_upper)).any():
        raise ValueError("B08 bands must satisfy lower <= mid <= upper")
    rsi_columns = {"b08_rsi14", "b08_rsi_previous"}
    if missing := rsi_columns.difference(raw.columns):
        raise ValueError(f"Missing B08 minute RSI features: {sorted(missing)}")
    rsi = raw[list(rsi_columns)].to_numpy(dtype=float)
    if np.isinf(rsi).any() or (rsi < 0).any() or (rsi > 100).any():
        raise ValueError("B08 RSI values must lie in [0, 100] where present")
    return date


def evaluate_b08_day(
    raw: pd.DataFrame, five_day: pd.DataFrame,
) -> tuple[pd.DataFrame, list[dict[str, object]], pd.DataFrame]:
    """Evaluate paired recoveries from fresh, completed-five-minute band dips.

    A dip arms only on completion in [10:00, 14:30). It must follow a completed
    bar that did not touch below its own lower band. Touch state is maintained
    outside both the entry window and the flat state. A dip while an episode
    is pending is consumed, never queued. Each arm freezes its lower band.

    Both alternatives require a later minute starting at/after arm availability.
    Price enters at its first close strictly above the frozen band. RSI attempts
    its first later upward cross (previous <= 30, current > 30), entering only
    if that crossing's close is strictly above the frozen band. Price may fire
    before or after that RSI attempt. Cutoff, new completed context losing flat,
    and thirty-minute expiry cancel pending alternatives before any trigger.

    Returns native-minute diagnostics, immutable entry dictionaries, and all
    armed episodes, including attempts with no entry. Prefixes may stay pending.
    """
    date = _check_day(raw, five_day)
    bars, five = raw.reset_index(drop=True), five_day.reset_index(drop=True)
    available = five.min5.to_numpy(dtype=int) + 5
    previous_touch: bool | None = False
    pending: dict[str, object] | None = None
    episodes: list[dict[str, object]] = []
    events: list[dict[str, object]] = []
    diagnostics: list[dict[str, object]] = []

    for _, row in bars.iterrows():
        minute, known = int(row["min"]), int(row["min"]) + 1
        j = int(np.searchsorted(available, known, side="right") - 1)
        context = five.iloc[j] if j >= 0 else None
        new_context = j >= 0 and int(available[j]) == known
        had_pending = pending is not None
        fresh_dip = False
        price_entry = rsi_entry = False
        transitions: list[str] = []

        def finish(reason: str) -> None:
            nonlocal pending
            if pending is None:
                return
            for status in ("price_status", "rsi_status"):
                if pending[status] == "pending":
                    pending[status] = reason
            pending.update({
                "status": reason, "terminal_min": known,
                "terminal_signal_min": minute, "terminal_close": float(row.close),
            })
            transitions.append(f"{pending['episode_id']}:{reason}")
            pending = None

        if new_context:
            touch = bool(context.low < context.b08_lower) if np.isfinite(
                context.b08_lower
            ) else None
            fresh_dip = touch is True and previous_touch is False
            previous_touch = touch

        if pending is not None:
            if known >= CUTOFF_KNOWN_MIN:
                finish("cutoff")
            elif new_context and not bool(context.b08_flat):
                finish("flat_lost")
            elif known >= int(pending["arm_known_min"]) + EPISODE_MINUTES:
                finish("timeout")

        if fresh_dip and had_pending:
            transitions.append("fresh_dip_suppressed_while_pending")
        if (
            new_context and fresh_dip and not had_pending
            and FIRST_KNOWN_MIN <= known < CUTOFF_KNOWN_MIN and bool(context.b08_flat)
        ):
            pending = {
                "episode_id": f"{date}_b08_{known}_{len(episodes) + 1}", "date": date,
                "band_lower": float(context.b08_lower), "arm_min5": int(context.min5),
                "arm_known_min": known, "arm_low": float(context.low),
                "arm_close": float(context.close), "arm_atr": float(context.t_atr),
                "arm_sma": float(context.b08_mid), "flat_change": float(context.b08_flat_change),
                "price_known_min": None, "price_status": "pending", "rsi_known_min": None,
                "rsi_cross_min": None, "rsi_status": "pending", "status": "pending",
                "terminal_min": None, "terminal_signal_min": None, "terminal_close": None,
            }
            episodes.append(pending)
            transitions.append(f"{pending['episode_id']}:arm")

        if pending is not None and minute >= int(pending["arm_known_min"]):
            above = row.close > float(pending["band_lower"])
            rsi_cross = row.b08_rsi_previous <= 30 and row.b08_rsi14 > 30

            def emit(variant: str) -> None:
                events.append({
                    key: pending[key] for key in (
                        "episode_id", "date", "band_lower", "arm_min5", "arm_known_min",
                        "arm_low", "arm_close", "arm_atr", "arm_sma", "flat_change",
                    )
                } | {
                    "variant": variant, "kind": variant, "signal_min": minute,
                    "known_min": known, "close": float(row.close),
                    "rsi14": float(row.b08_rsi14), "rsi_previous": float(row.b08_rsi_previous),
                    "wait_minutes": known - int(pending["arm_known_min"]),
                })
                transitions.append(f"{pending['episode_id']}:{variant}")

            if pending["price_status"] == "pending" and above:
                emit("b08_price")
                pending["price_known_min"], pending["price_status"] = known, "trigger"
                price_entry = True
            if pending["rsi_status"] == "pending" and rsi_cross:
                pending["rsi_cross_min"] = known
                if above:
                    emit("b08_rsi")
                    pending["rsi_known_min"], pending["rsi_status"] = known, "trigger"
                    rsi_entry = True
                else:
                    pending["rsi_status"] = "cross_below_band"
                    transitions.append(f"{pending['episode_id']}:rsi_cross_below_band")
            if pending["price_status"] != "pending" and pending["rsi_status"] != "pending":
                finish("completed")

        diagnostics.append(row.to_dict() | {
            "date": date, "known_min": known,
            "context_min5": int(context.min5) if context is not None else None,
            "b08_lower": float(context.b08_lower) if context is not None else np.nan,
            "b08_flat": bool(context.b08_flat) if context is not None else False,
            "fresh_dip": fresh_dip, "b08_price_entry": price_entry, "b08_rsi_entry": rsi_entry,
            "episode_id": str(pending["episode_id"]) if pending is not None else None,
            "frozen_lower": pending["band_lower"] if pending is not None else None,
            "price_status": pending["price_status"] if pending is not None else None,
            "rsi_status": pending["rsi_status"] if pending is not None else None,
            "transition": ";".join(transitions),
        })

    result = pd.DataFrame(diagnostics)
    result.index = raw.index
    return result, events, pd.DataFrame(episodes, columns=LEDGER_COLUMNS)
