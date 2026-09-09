"""Supported, prior-only call richness; no data requests, forward inference, or trade gates.

Inputs are one ticker's raw ORATS strike dictionaries. IV is decimal, delta is 0–1,
and DTE is calendar days from quoteDate to expirDate. The caller supplies verified
forwards keyed by (quote_date, expiry); rates/yields/residual yields are not interpreted
here. Provider ATM fields are deliberately unused: matched ATM is callMidIv at K=F.

Freeze: adjacent-coordinate linear smile interpolation, followed by linear total-
variance interpolation in DTE. Both bid and ATM use the same adjacent expiry pair.
An invalid nearest endpoint is not skipped to obtain a more convenient bracket.
These daily quote-derived measurements do not establish live fills or quote freshness.
Midrank ties and zero variance use a 1e-12 volatility-point numerical tolerance.
"""

from __future__ import annotations

import bisect
import math
import statistics
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any

Row = Mapping[str, Any]
ForwardMap = Mapping[tuple[str, str], float]
MODES = ("delta_dte", "forward_moneyness_dte")
LOOKBACK_SESSIONS = 126
MINIMUM_OBSERVATIONS = 60
NUMERICAL_TOLERANCE = 1e-12


class Unsupported(ValueError):
    """A measurement cannot be formed without inventing support or an executable quote."""


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _day(value: Any) -> str:
    return date.fromisoformat(str(value)[:10]).isoformat()


def _dte(day: str, expiry: str) -> int:
    return (date.fromisoformat(expiry) - date.fromisoformat(day)).days


def _brackets(x: Sequence[float], target: float) -> tuple[int, int]:
    if not x or not math.isfinite(target):
        raise Unsupported("missing_coordinate")
    if target < x[0] or target > x[-1]:
        raise Unsupported("smile_outside_support")
    right = bisect.bisect_left(x, target)
    left = right if x[right] == target else right - 1
    if any(x.count(x[index]) > 1 for index in (left, right)):
        raise Unsupported("duplicate_coordinate")
    return left, right


def interpolate_inside(x: Sequence[float], y: Sequence[float], target: float) -> float:
    """Interpolate adjacent finite coordinates; reject ambiguity at either endpoint."""
    if len(x) != len(y):
        raise ValueError("coordinate/value lengths differ")
    pairs = [(_number(a), _number(b)) for a, b in zip(x, y, strict=True)]
    if any(a is None or b is None for a, b in pairs):
        raise Unsupported("nonfinite_coordinate_or_value")
    pairs.sort()
    left, right = _brackets([pair[0] for pair in pairs], target)
    x0, y0 = pairs[left]
    x1, y1 = pairs[right]
    return y0 if left == right else y0 + (y1 - y0) * (target - x0) / (x1 - x0)


def _executable(row: Row) -> bool:
    values = {key: _number(row.get(key)) for key in (
        "callBidPrice", "callAskPrice", "callBidIv", "callMidIv", "callBidSize", "callAskSize"
    )}
    return all(value is not None for value in values.values()) and (
        values["callBidPrice"] > 0
        and values["callAskPrice"] >= values["callBidPrice"]
        and values["callBidIv"] > 0
        and values["callMidIv"] > 0
        and values["callBidSize"] >= 1
        and values["callAskSize"] >= 1
    )


def _expiries(rows: Sequence[Row], quote_date: str) -> dict[str, list[Row]]:
    if not rows:
        raise Unsupported("missing_session")
    if len({row.get("ticker") for row in rows}) > 1:
        raise Unsupported("mixed_tickers")
    groups: dict[str, list[Row]] = {}
    seen: set[tuple[str, float]] = set()
    for row in rows:
        try:
            if _day(row.get("quoteDate")) != quote_date:
                raise Unsupported("quote_date_mismatch")
            expiry = _day(row.get("expirDate"))
        except ValueError as exc:
            if isinstance(exc, Unsupported):
                raise
            raise Unsupported("invalid_quote_or_expiry_date") from exc
        strike = _number(row.get("strike"))
        if strike is None or strike <= 0:
            raise Unsupported("invalid_strike")
        if (expiry, strike) in seen:
            raise Unsupported("duplicate_contract")
        seen.add((expiry, strike))
        if _dte(quote_date, expiry) > 0:
            groups.setdefault(expiry, []).append(row)
    return groups


def _forward(forwards: ForwardMap, quote_date: str, expiry: str) -> float:
    value = _number(forwards.get((quote_date, expiry)))
    if value is None or value <= 0:
        raise Unsupported("missing_forward")
    return value


def _smile(rows: Sequence[Row], target: float, coordinate: str,
           field: str, forward: float) -> float:
    points = []
    for row in rows:
        if coordinate == "delta_dte":
            x = _number(row.get("delta"))
            if x is None or not 0 <= x <= 1:
                raise Unsupported("invalid_delta_coordinate")
        else:
            strike = float(row["strike"])
            x = math.log(strike / forward) if coordinate == "forward_moneyness_dte" else strike
        points.append((x, row))
    points.sort(key=lambda item: item[0])
    left, right = _brackets([point[0] for point in points], target)
    endpoints = [points[left]] if left == right else [points[left], points[right]]
    if any(not _executable(row) for _, row in endpoints):
        raise Unsupported("nonexecutable_bracket")
    return interpolate_inside([x for x, _ in endpoints],
                              [float(row[field]) for _, row in endpoints], target)


def surface_at(rows: Sequence[Row], *, quote_date: str, coordinate: float,
               target_dte: float, mode: str, forwards: ForwardMap) -> dict[str, Any]:
    """Measure one date at fixed coordinate/DTE; return the support failure explicitly."""
    if mode not in MODES:
        raise ValueError(f"unknown coordinate mode: {mode}")
    try:
        groups = _expiries(rows, quote_date)
        tenors = sorted((_dte(quote_date, expiry), expiry) for expiry in groups)
        if target_dte <= 0 or not tenors:
            raise Unsupported("term_outside_support")
        try:
            left, right = _brackets([tenor for tenor, _ in tenors], target_dte)
        except Unsupported as exc:
            raise Unsupported("term_outside_support") from exc
        needed = [tenors[left]] if left == right else [tenors[left], tenors[right]]
        values = []
        for dte, expiry in needed:
            forward = _forward(forwards, quote_date, expiry)
            bid = _smile(groups[expiry], coordinate, mode, "callBidIv", forward)
            atm = _smile(groups[expiry], forward, "strike", "callMidIv", forward)
            values.append((dte, bid, atm))
        target = {}
        for index, field in ((1, "bid_iv"), (2, "atm_mid_iv")):
            total_variance = interpolate_inside([v[0] for v in values],
                                               [v[index] ** 2 * v[0] for v in values],
                                               target_dte)
            target[field] = math.sqrt(total_variance / target_dte)
        return {"status": "ok", **target,
                "bid_excess_vol_points": 100 * (target["bid_iv"] - target["atm_mid_iv"]),
                "expiry_brackets": [expiry for _, expiry in needed]}
    except Unsupported as exc:
        return {"status": str(exc), "bid_iv": None, "atm_mid_iv": None,
                "bid_excess_vol_points": None, "expiry_brackets": []}


def _current(rows: Sequence[Row], signal_date: str, expiry: str, strike: float,
             forwards: ForwardMap) -> dict[str, Any]:
    result = {"status": "unavailable", "delta": None, "log_forward_moneyness": None,
              "dte": _dte(signal_date, expiry), "forward": None, "bid_iv": None,
              "atm_mid_iv": None, "bid_excess_vol_points": None}
    try:
        groups = _expiries(rows, signal_date)
        chain = groups.get(expiry, [])
        exact = [row for row in chain if float(row["strike"]) == strike]
        if len(exact) != 1:
            raise Unsupported("missing_current_contract")
        selected = exact[0]
        delta = _number(selected.get("delta"))
        result["delta"] = delta if delta is not None and 0 < delta < 1 else None
        result["forward"] = _forward(forwards, signal_date, expiry)
        result["log_forward_moneyness"] = math.log(strike / result["forward"])
        if not _executable(selected):
            raise Unsupported("nonexecutable_current")
        result["bid_iv"] = float(selected["callBidIv"])
        result["atm_mid_iv"] = _smile(chain, result["forward"], "strike", "callMidIv",
                                       result["forward"])
        result["bid_excess_vol_points"] = 100 * (result["bid_iv"] - result["atm_mid_iv"])
        result["status"] = "ok"
    except Unsupported as exc:
        result["status"] = str(exc)
    return result


def _stats(history: list[dict[str, Any]], current: float | None) -> dict[str, Any]:
    values = [row["bid_excess_vol_points"] for row in history if row["status"] == "ok"]
    count = len(values)
    mean = statistics.mean(values) if values else None
    std = statistics.stdev(values) if count >= 2 else None
    enough = count >= MINIMUM_OBSERVATIONS
    percentile = None
    z = None
    if current is None:
        status = "current_unavailable"
    elif not enough:
        status = "insufficient_history"
    else:
        tied = [math.isclose(value, current, rel_tol=0, abs_tol=NUMERICAL_TOLERANCE)
                for value in values]
        below = sum(value < current and not tie for value, tie in zip(values, tied, strict=True))
        percentile = 100 * (below + .5 * sum(tied)) / count
        status = "ok" if std and std > NUMERICAL_TOLERANCE else "zero_variance"
        if status == "ok":
            z = (current - mean) / std
    return {"n": count, "mean": mean, "sample_std": std, "z": z,
            "midrank_percentile": percentile, "status": status,
            "history_minimum_met": enough, "lookback_sessions": len(history),
            "support_failures": dict(Counter(row["status"] for row in history
                                             if row["status"] != "ok")),
            "history": history}


def evaluate_richness(current_rows: Sequence[Row], history_by_date: Mapping[str, Sequence[Row]],
                      *, signal_date: str, expiry: str, strike: float,
                      session_dates: Sequence[str], forwards: ForwardMap) -> dict[str, Any]:
    """Return two independent histories over at most 126 strictly prior exchange sessions.

    The supplied session calendar defines the window, including missing-data sessions.
    Repeated dates and ambiguous contracts cannot increase the observation count.
    Unavailable measurements remain in the output; this function never filters trades.
    Historical and current rows must already be restricted to the same ticker.
    """
    signal_date, expiry = _day(signal_date), _day(expiry)
    sessions = [_day(day) for day in session_dates]
    if len(sessions) != len(set(sessions)):
        raise ValueError("duplicate session dates")
    if _number(strike) is None or strike <= 0:
        raise ValueError("strike must be a positive finite number")
    prior_dates = sorted(day for day in sessions if day < signal_date)[-LOOKBACK_SESSIONS:]
    current = _current(current_rows, signal_date, expiry, strike, forwards)
    ticker = current_rows[0].get("ticker") if current_rows else None
    targets = {"delta_dte": current["delta"],
               "forward_moneyness_dte": current["log_forward_moneyness"]}
    coordinates = {}
    for mode, coordinate in targets.items():
        history = []
        for day in prior_dates:
            rows = history_by_date.get(day, [])
            if coordinate is None:
                point = {"status": "missing_current_coordinate", "bid_excess_vol_points": None}
            elif any(row.get("ticker") != ticker for row in rows):
                point = {"status": "ticker_mismatch", "bid_excess_vol_points": None}
            else:
                point = surface_at(rows, quote_date=day, coordinate=coordinate,
                                   target_dte=current["dte"], mode=mode, forwards=forwards)
            history.append({"date": day, **point})
        coordinates[mode] = {"target_coordinate": coordinate, "target_dte": current["dte"],
                             **_stats(history, current["bid_excess_vol_points"])}
    return {"signal_date": signal_date, "expiry": expiry, "strike": strike,
            "ticker": ticker, "iv_units": "decimal", "richness_units": "volatility_points",
            "history_definition": "comparable_surface_not_exact_strike_lifetime",
            "atm_definition": "call_mid_iv_at_verified_forward",
            "interpolation": "adjacent_smile_linear_then_total_variance_in_calendar_dte",
            "current": current, "coordinates": coordinates}
