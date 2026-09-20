"""Sparse 30-day ATM-spot and native 25-delta IV measurements; no strategy outcomes.

Provider IV/model assumptions remain unchanged. Wing interpolation requires a unique
decreasing target crossing in native strike order, never an inferred or sorted surface.
Bid/ask ranges describe quote uncertainty and are not statistical confidence intervals.
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd


ET = "America/New_York"
KEY = ["symbol", "expiration", "strike", "right", "timestamp"]
QUOTE = ["bid", "ask", "underlying_price", "underlying_timestamp"]
IV_FIELDS = ["bid_implied_vol", "implied_vol", "ask_implied_vol"]
COMPONENTS = ["atm_call", "atm_put", "call25", "put25"]
METRICS = COMPONENTS + ["atm", "put_richness", "call_richness", "risk_reversal", "call_put_gap"]


def _times(values: pd.Series, name: str, allow_missing: bool = False) -> pd.Series:
    if isinstance(values.dtype, pd.DatetimeTZDtype):
        result = values.dt.tz_convert(ET)
        if not allow_missing and result.isna().any():
            raise ValueError(f"{name} requires valid timezone-aware timestamps")
        return result
    parsed = [pd.Timestamp(value) for value in values]
    if any(
        (pd.isna(value) and not allow_missing) or (pd.notna(value) and value.tzinfo is None)
        for value in parsed
    ):
        raise ValueError(f"{name} requires valid timezone-aware timestamps")
    return pd.Series(pd.to_datetime(parsed, utc=True).tz_convert(ET), index=values.index)


def _endpoint(source: pd.DataFrame, required: list[str], name: str) -> pd.DataFrame:
    missing = sorted(set(required) - set(source.columns))
    if missing:
        raise ValueError(f"{name} missing columns: {missing}")
    frame = source.copy().reset_index(drop=True)
    for column in ["timestamp", "underlying_timestamp"]:
        frame[column] = _times(
            frame[column], f"{name}.{column}", allow_missing=column == "underlying_timestamp"
        )
    if not frame.timestamp.eq(frame.timestamp.dt.floor("min")).all():
        raise ValueError("Sample timestamps must be aligned to exact minutes")
    frame["symbol"] = frame.symbol.astype("string").str.strip().str.upper()
    frame["right"] = frame.right.astype("string").str.upper().replace({"CALL": "C", "PUT": "P"})
    frame["expiration"] = pd.to_datetime(
        frame.expiration.astype(str), format="mixed", errors="coerce"
    ).dt.strftime("%Y-%m-%d")
    frame["strike"] = pd.to_numeric(frame.strike, errors="coerce")
    if frame[KEY].isna().any(axis=None) or frame.symbol.eq("").any():
        raise ValueError(f"{name} contains invalid contract/sample key")
    if frame.duplicated(KEY).any():
        raise ValueError(f"{name} contains duplicate contract/sample key")
    return frame


def _prepare(iv: pd.DataFrame, greeks: pd.DataFrame) -> pd.DataFrame:
    left = _endpoint(iv, KEY + QUOTE + IV_FIELDS + ["midpoint", "iv_error"], "iv")
    left = left[KEY + QUOTE + IV_FIELDS + ["midpoint", "iv_error"]]
    right = _endpoint(greeks, KEY + QUOTE + ["delta"], "greeks")
    greek_columns = KEY + QUOTE + ["delta"] + (["midpoint"] if "midpoint" in right else [])
    frame = left.merge(
        right[greek_columns], on=KEY, how="outer", validate="one_to_one",
        suffixes=("", "_greek"), indicator=True,
    )
    if not frame._merge.eq("both").all():
        raise ValueError("IV and Greek endpoint key sets must match exactly")
    numeric = ["strike", "bid", "midpoint", "ask", "underlying_price"] + IV_FIELDS
    for column in numeric + [
        "iv_error", "delta", "bid_greek", "ask_greek", "underlying_price_greek"
    ]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    matches = pd.Series(True, index=frame.index)
    for column in QUOTE:
        original, other = frame[column], frame[column + "_greek"]
        matches &= original.eq(other) | (original.isna() & other.isna())
    if "midpoint_greek" in frame:
        other_midpoint = pd.to_numeric(frame.midpoint_greek, errors="coerce")
        matches &= frame.midpoint.eq(other_midpoint) | (
            frame.midpoint.isna() & other_midpoint.isna()
        )
    frame["reported_underlying_age_seconds"] = (
        frame.timestamp - frame.underlying_timestamp
    ).dt.total_seconds()
    frame["session_date"] = frame.timestamp.dt.strftime("%Y-%m-%d")
    frame["dte"] = (
        pd.to_datetime(frame.expiration) - pd.to_datetime(frame.session_date)
    ).dt.days
    valid = (np.isfinite(frame[numeric]) & frame[numeric].gt(0)).all(axis=1)
    valid &= matches & frame.bid.le(frame.midpoint) & frame.midpoint.le(frame.ask)
    valid &= frame.bid_implied_vol.le(frame.implied_vol)
    valid &= frame.implied_vol.le(frame.ask_implied_vol)
    valid &= frame.reported_underlying_age_seconds.between(0, 60)
    valid &= frame.dte.between(8, 65) & frame.right.isin(["C", "P"])
    frame["valid"] = valid
    frame["endpoint_match"] = matches
    return frame.sort_values(["symbol", "timestamp", "dte", "right", "strike"])


def _underlying(data: dict[str, np.ndarray], indices: np.ndarray) -> tuple[float, str] | None:
    if not len(indices):
        return None
    prices = data["underlying_price"][indices]
    times = data["underlying_timestamp"][indices]
    if np.isfinite(prices).all() and np.all(prices == prices[0]) and np.all(times == times[0]):
        return float(prices[0]), times[0].isoformat()
    return None


def _quote(data: dict[str, np.ndarray], index: int) -> dict[str, Any]:
    names = ["strike", "bid", "midpoint", "ask", "delta", "iv_error"] + IV_FIELDS
    result = {
        name: float(data[name][index]) if np.isfinite(data[name][index]) else None
        for name in names
    }
    result["relative_quote_spread"] = float(
        (data["ask"][index] - data["bid"][index]) / data["midpoint"][index]
    )
    return result


def _expiry_coordinate(
    data: dict[str, np.ndarray], indices: np.ndarray, target: float | None,
) -> tuple[dict[str, Any] | None, str]:
    """Select adjacent native-delta nodes, or nearest valid log-strike ATM nodes."""
    if target is None:
        usable = indices[data["valid"][indices]]
        if not len(usable):
            return None, "invalid_quotes"
        x = np.log(data["strike"][usable] / data["underlying_price"][usable])
        exact = np.flatnonzero(x == 0)
        if len(exact):
            selected, weights = usable[exact[:1]], np.array([1.0])
        else:
            below, above = np.flatnonzero(x < 0), np.flatnonzero(x > 0)
            if not len(below) or not len(above):
                return None, "no_strike_bracket"
            lower, upper = below[np.argmax(x[below])], above[np.argmin(x[above])]
            selected = usable[[lower, upper]]
            weights = np.array([x[upper], -x[lower]]) / (x[upper] - x[lower])
    else:
        delta = data["delta"][indices].copy()
        allowed = (delta >= 0) & (delta <= 1) if target > 0 else (delta >= -1) & (delta <= 0)
        delta[~allowed] = np.nan
        exact = np.flatnonzero(delta == target)
        decreasing = (delta[:-1] > target) & (delta[1:] < target)
        increasing = (delta[:-1] < target) & (delta[1:] > target)
        crossing = np.flatnonzero(decreasing | increasing)
        # Count every adjacent crossing, including invalid-quote nodes. Filtering them
        # first could hide a second solution or bridge a missing native strike.
        if len(exact) + len(crossing) > 1:
            return None, "ambiguous_delta_bracket"
        if len(exact):
            position = exact[0]
            neighbors = [
                neighbor for neighbor in [position - 1, position + 1]
                if 0 <= neighbor < len(delta)
            ]
            if not np.isfinite(delta[neighbors]).all():
                return None, "no_delta_bracket"
            if (position > 0 and delta[position - 1] < target) or (
                position + 1 < len(delta) and delta[position + 1] > target
            ):
                return None, "nonmonotonic_delta"
            selected, weights = indices[exact], np.array([1.0])
        else:
            if not len(crossing):
                return None, "no_delta_bracket"
            position = crossing[0]
            if not decreasing[position]:
                return None, "nonmonotonic_delta"
            selected = indices[[position, position + 1]]
            upper, lower = delta[position:position + 2]
            weights = np.array([target - lower, upper - target]) / (upper - lower)
        if not data["valid"][selected].all():
            return None, "invalid_quotes"
    underlying = _underlying(data, selected)
    if underlying is None:
        return None, "inconsistent_underlying"
    variance = np.array([
        np.dot(weights, data[name][selected] ** 2) for name in IV_FIELDS
    ])
    return {
        "variance": variance,
        "underlying": underlying,
        "max_age": float(data["reported_underlying_age_seconds"][selected].max()),
        "max_spread": float(np.max(
            (data["ask"][selected] - data["bid"][selected]) / data["midpoint"][selected]
        )),
        "provenance": {
            "expiration": str(data["expiration"][selected[0]]),
            "dte": int(data["dte"][selected[0]]), "weights": weights.tolist(),
            "quotes": [_quote(data, int(index)) for index in selected],
        },
    }, "ok"


def _tenor_coordinate(
    data: dict[str, np.ndarray], indices: np.ndarray, target: float | None,
) -> tuple[dict[str, Any] | None, str]:
    tenors = np.unique(data["dte"][indices])
    tenors = tenors[(tenors >= 8) & (tenors <= 65)]
    if 30 in tenors:
        selected_tenors, weights = np.array([30]), np.array([1.0])
    else:
        lower, upper = tenors[tenors < 30], tenors[tenors > 30]
        if not len(lower) or not len(upper):
            return None, "no_tenor_bracket"
        front, back = lower[-1], upper[0]
        selected_tenors = np.array([front, back])
        weights = np.array([back - 30, 30 - front]) / (back - front)
    coordinates = []
    for tenor in selected_tenors:
        coordinate, status = _expiry_coordinate(
            data, indices[data["dte"][indices] == tenor], target
        )
        if coordinate is None:
            return None, status
        coordinates.append(coordinate)
    if len({item["underlying"] for item in coordinates}) != 1:
        return None, "inconsistent_underlying"
    return {
        "value": 100 * np.sqrt(sum(
            weight * tenor * coordinate["variance"] / 30
            for weight, tenor, coordinate in zip(weights, selected_tenors, coordinates)
        )),
        "underlying": coordinates[0]["underlying"],
        "max_age": max(item["max_age"] for item in coordinates),
        "max_spread": max(item["max_spread"] for item in coordinates),
        "provenance": {
            "tenor_weights": weights.tolist(),
            "underlying_price": coordinates[0]["underlying"][0],
            "reported_underlying_timestamp": coordinates[0]["underlying"][1],
            "expiries": [item["provenance"] for item in coordinates],
        },
    }, "ok"


def _put_values(row: dict[str, Any], name: str, values: np.ndarray) -> None:
    row[name + "_low"], row[name], row[name + "_high"] = map(float, values)


def _sample(data: dict[str, np.ndarray], indices: np.ndarray) -> dict[str, Any]:
    row: dict[str, Any] = {
        name + suffix: np.nan for name in METRICS for suffix in ["", "_low", "_high"]
    }
    row.update(source_quote_count=len(indices),
               rejected_quote_count=int((~data["valid"][indices]).sum()))
    for component in COMPONENTS:
        row[component + "_max_relative_quote_spread"] = np.nan
        row[component + "_max_reported_underlying_age_seconds"] = np.nan
    common = _underlying(data, indices[data["endpoint_match"][indices]])
    row["spot"] = common[0] if common is not None and common[0] > 0 else np.nan
    coordinates, provenance = {}, {}
    for name, right, target in [
        ("atm_call", "C", None), ("atm_put", "P", None),
        ("call25", "C", 0.25), ("put25", "P", -0.25),
    ]:
        coordinate, status = _tenor_coordinate(
            data, indices[data["right"][indices] == right], target
        )
        row[name + "_status"] = status
        if coordinate is not None:
            coordinates[name] = coordinate
            provenance[name] = coordinate["provenance"]
            _put_values(row, name, coordinate["value"])
            row[name + "_max_relative_quote_spread"] = coordinate["max_spread"]
            row[name + "_max_reported_underlying_age_seconds"] = coordinate["max_age"]
    row["atm_status"] = "missing_component"
    if "atm_call" in coordinates and "atm_put" in coordinates:
        call, put = coordinates["atm_call"], coordinates["atm_put"]
        if call["underlying"] == put["underlying"]:
            atm = {"value": np.sqrt((call["value"] ** 2 + put["value"] ** 2) / 2),
                   "underlying": call["underlying"]}
            coordinates["atm"] = atm
            _put_values(row, "atm", atm["value"])
            row["atm_status"] = "ok"
        else:
            row["atm_status"] = "inconsistent_underlying"
    for name, positive, negative in [
        ("call_put_gap", "atm_call", "atm_put"), ("put_richness", "put25", "atm"),
        ("call_richness", "call25", "atm"), ("risk_reversal", "call25", "put25"),
    ]:
        row[name + "_status"] = "missing_component"
        if positive in coordinates and negative in coordinates:
            first, second = coordinates[positive], coordinates[negative]
            if first["underlying"] == second["underlying"]:
                _put_values(row, name, first["value"] - second["value"][[2, 1, 0]])
                row[name + "_status"] = "ok"
            else:
                row[name + "_status"] = "inconsistent_underlying"
    row["provenance_json"] = json.dumps(provenance, separators=(",", ":"), allow_nan=False)
    return row


def build_surface(iv: pd.DataFrame, greeks: pd.DataFrame) -> pd.DataFrame:
    """Build sparse surface metrics on an unfilled 09:30–14:29 ET minute grid.

    Inputs must have identical unique contract/sample keys and aware timestamps. Greek
    delta is supplied by the provider. Endpoint quote or underlying disagreements reject
    the affected rows; absent/invalid delta only removes affected wing coordinates.
    Returns IV-point metrics with `_low`/`_high` quote ranges and component provenance.
    """
    prepared = _prepare(iv, greeks)
    sessions = []
    for (symbol, session_date), day in prepared.groupby(["symbol", "session_date"], sort=True):
        day = day.reset_index(drop=True)
        data = {column: day[column].to_numpy() for column in day.columns}
        grid = pd.date_range(f"{session_date} 09:30", periods=300, freq="min", tz=ET)
        records = {
            timestamp: _sample(data, indices)
            for timestamp, indices in day.groupby("timestamp", sort=True).indices.items()
            if timestamp in grid
        }
        result = pd.DataFrame.from_dict(records, orient="index").reindex(grid)
        result.index.name = "timestamp"
        for name in METRICS:
            for suffix in ["", "_low", "_high"]:
                if name + suffix not in result:
                    result[name + suffix] = np.nan
            status = name + "_status"
            result[status] = result.get(status, pd.Series(index=grid, dtype="object"))
            result[status] = result[status].fillna("no_observation")
        for column in ["source_quote_count", "rejected_quote_count"]:
            result[column] = result.get(column, pd.Series(0, index=grid)).fillna(0).astype(int)
        if "spot" not in result:
            result["spot"] = np.nan
        result["provenance_json"] = result.get(
            "provenance_json", pd.Series("{}", index=grid)
        ).fillna("{}")
        result["symbol"], result["session_date"] = symbol, session_date
        result["actual_option_quote_age"] = "unknown"
        result["actual_underlying_event_age"] = "unknown"
        result["proxy_measurement_only"] = True
        result["provider_iv_model"] = "unchanged_provider_EU_default_dividend"
        sessions.append(result.reset_index())
    return pd.concat(sessions, ignore_index=True) if sessions else pd.DataFrame()
