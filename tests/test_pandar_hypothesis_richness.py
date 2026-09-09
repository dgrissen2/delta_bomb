"""Prior-only, executable, supported-coordinate richness measurements."""

import math
import statistics
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from pandar_hypothesis_richness import evaluate_richness, interpolate_inside, surface_at


def chain(day: str, *, days: int = 10, wing: float = 0.25) -> list[dict]:
    expiry = (date.fromisoformat(day) + timedelta(days=days)).isoformat()
    rows = []
    for strike, delta, bid_iv in [(90, .8, .23), (100, .5, .20),
                                   (110, .1, wing), (120, .03, .30)]:
        rows.append({"ticker": "TEST", "quoteDate": day + "T15:50:00-04:00",
                     "expirDate": expiry, "strike": strike, "stockPrice": 98,
                     "delta": delta, "callBidIv": bid_iv, "callMidIv": bid_iv + .02,
                     "callBidPrice": 1, "callAskPrice": 1.1,
                     "callBidSize": 1, "callAskSize": 1})
    return rows


def input_data(n: int = 65):
    dates = [(date(2026, 1, 1) + timedelta(days=i)).isoformat() for i in range(n + 1)]
    history = {day: chain(day, wing=.25 + i * .001) for i, day in enumerate(dates[:-1])}
    current = chain(dates[-1], wing=.32)
    forwards = {(day, rows[0]["expirDate"]): 100. for day, rows in history.items()}
    forwards[(dates[-1], current[0]["expirDate"])] = 100.
    return current, history, {"signal_date": dates[-1], "expiry": current[0]["expirDate"],
                              "strike": 110., "session_dates": dates, "forwards": forwards}


def test_smile_inside_only_and_no_ambiguous_coordinate_average():
    assert interpolate_inside([0, 1], [.2, .4], .5) == pytest.approx(.3)
    with pytest.raises(ValueError, match="outside"):
        interpolate_inside([0, 1], [.2, .4], 1.01)
    with pytest.raises(ValueError, match="duplicate"):
        interpolate_inside([0, 0, 1], [.2, .3, .4], .5)


def test_unrelated_deep_delta_duplicates_do_not_destroy_supported_local_bracket():
    rows = chain("2026-01-01")
    for strike, delta in [(20, 1), (30, 1), (200, 0), (210, 0)]:
        rows.append({**rows[0], "strike": strike, "delta": delta})
    result = surface_at(rows, quote_date="2026-01-01", coordinate=.1, target_dte=10,
                        mode="delta_dte", forwards={("2026-01-01", "2026-01-11"): 100})
    assert result["status"] == "ok"
    assert result["bid_excess_vol_points"] == pytest.approx(3)


def test_exact_current_uses_forward_atm_not_spot_or_fifty_delta():
    current, history, kwargs = input_data()
    for row in current:
        row["delta"] = {90: .8, 100: .6, 110: .1, 120: .03}[row["strike"]]
        row["atmiv"] = 99
    result = evaluate_richness(current, history, **kwargs)
    assert result["current"]["atm_mid_iv"] == pytest.approx(.22)
    assert result["current"]["bid_excess_vol_points"] == pytest.approx(10)
    assert result["current"]["log_forward_moneyness"] == pytest.approx(math.log(1.1))


def test_60_observations_sample_std_and_strict_prior_exclusion():
    current, history, kwargs = input_data(60)
    history[kwargs["signal_date"]] = chain(kwargs["signal_date"], wing=99)
    history["2099-01-01"] = chain("2099-01-01", wing=99)
    result = evaluate_richness(current, history, **kwargs)
    values = [3 + i * .1 for i in range(60)]
    for stats in result["coordinates"].values():
        assert stats["n"] == 60
        assert stats["mean"] == pytest.approx(statistics.mean(values))
        assert stats["sample_std"] == pytest.approx(statistics.stdev(values))
        assert stats["z"] == pytest.approx((10 - statistics.mean(values)) / statistics.stdev(values))
        assert stats["midrank_percentile"] == 100
        assert stats["status"] == "ok"


def test_minimum_60_and_coordinate_support_are_independent():
    current, history, kwargs = input_data(60)
    first = history[sorted(history)[0]]
    for row in first:
        row["delta"] = .3 + row["strike"] / 1000
    result = evaluate_richness(current, history, **kwargs)
    delta = result["coordinates"]["delta_dte"]
    money = result["coordinates"]["forward_moneyness_dte"]
    assert delta["n"] == 59 and delta["status"] == "insufficient_history"
    assert delta["z"] is None and delta["midrank_percentile"] is None
    assert delta["support_failures"]["smile_outside_support"] == 1
    assert money["n"] == 60 and money["status"] == "ok"


def test_no_term_extrapolation_or_bridging_invalid_nearest_expiry():
    rows = chain("2026-01-01", days=7) + chain("2026-01-01", days=14)
    forwards = {("2026-01-01", row["expirDate"]): 100 for row in rows}
    result = surface_at(rows, quote_date="2026-01-01", coordinate=.1, target_dte=5,
                        mode="delta_dte", forwards=forwards)
    assert result["status"] == "term_outside_support"
    for row in rows:
        if row["expirDate"] == "2026-01-08" and row["strike"] == 110:
            row["callBidSize"] = 0
    rows += chain("2026-01-01", days=3)
    forwards[("2026-01-01", "2026-01-04")] = 100
    result = surface_at(rows, quote_date="2026-01-01", coordinate=.1, target_dte=10,
                        mode="delta_dte", forwards=forwards)
    assert result["status"] == "nonexecutable_bracket"


def test_total_variance_interpolation_uses_matched_expiry_pair():
    rows = chain("2026-01-01", days=5, wing=.2) + chain("2026-01-01", days=15, wing=.4)
    forwards = {("2026-01-01", row["expirDate"]): 100 for row in rows}
    result = surface_at(rows, quote_date="2026-01-01", coordinate=.1, target_dte=10,
                        mode="delta_dte", forwards=forwards)
    assert result["bid_iv"] == pytest.approx(math.sqrt(.13))
    assert result["atm_mid_iv"] == pytest.approx(.22)
    assert result["bid_excess_vol_points"] == pytest.approx(100 * (math.sqrt(.13) - .22))


def test_missing_sessions_count_inside_last_126_not_last_126_observations():
    current, history, kwargs = input_data(140)
    removed = sorted(history)[-1]
    del history[removed]
    result = evaluate_richness(current, history, **kwargs)
    stats = result["coordinates"]["delta_dte"]
    assert stats["n"] == 125 and stats["lookback_sessions"] == 126
    assert stats["history"][0]["date"] == kwargs["session_dates"][14]
    assert stats["support_failures"]["missing_session"] == 1


def test_duplicate_dates_and_duplicate_contracts_never_inflate_n():
    current, history, kwargs = input_data(60)
    kwargs["session_dates"].append(kwargs["session_dates"][0])
    with pytest.raises(ValueError, match="duplicate session"):
        evaluate_richness(current, history, **kwargs)
    kwargs["session_dates"].pop()
    first = sorted(history)[0]
    history[first].append(history[first][0].copy())
    result = evaluate_richness(current, history, **kwargs)
    assert result["coordinates"]["delta_dte"]["n"] == 59
    assert result["coordinates"]["delta_dte"]["support_failures"]["duplicate_contract"] == 1


def test_midrank_ties_and_zero_variance():
    current, history, kwargs = input_data(60)
    current = chain(kwargs["signal_date"], wing=.25)
    history = {day: chain(day, wing=.25) for day in history}
    result = evaluate_richness(current, history, **kwargs)
    stats = result["coordinates"]["delta_dte"]
    assert stats["n"] == 60 and stats["z"] is None
    assert stats["status"] == "zero_variance"
    assert stats["midrank_percentile"] == 50


def test_variance_roundoff_does_not_break_mathematical_midrank_ties():
    current, history, kwargs = input_data(60)
    current = chain(kwargs["signal_date"], wing=.26)
    history = {day: chain(day, days=7, wing=.26) + chain(day, days=14, wing=.26)
               for day in history}
    for day, rows in history.items():
        for row in rows:
            kwargs["forwards"][(day, row["expirDate"])] = 100
    stats = evaluate_richness(current, history, **kwargs)["coordinates"]["delta_dte"]
    assert stats["status"] == "zero_variance" and stats["z"] is None
    assert stats["midrank_percentile"] == 50


def test_no_forward_inference_and_unexecutable_current_is_unavailable():
    current, history, kwargs = input_data(60)
    del kwargs["forwards"][(kwargs["signal_date"], kwargs["expiry"])]
    result = evaluate_richness(current, history, **kwargs)
    assert result["current"]["status"] == "missing_forward"
    assert all(stats["z"] is None for stats in result["coordinates"].values())
    kwargs["forwards"][(kwargs["signal_date"], kwargs["expiry"])] = 100
    current[2]["callAskPrice"] = .5
    result = evaluate_richness(current, history, **kwargs)
    assert result["current"]["status"] == "nonexecutable_current"
    assert all(stats["z"] is None for stats in result["coordinates"].values())
