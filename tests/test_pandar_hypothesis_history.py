"""Carry-model construction and independent support boundaries; no provider I/O."""

import math
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from pandar_hypothesis_history import build_forwards


KEY = ("TEST", "2026-01-02", "2027-01-02")


def carry_inputs(
    *, rate: float = .05, dividend_yield: float = .02, residual_yield: float = .01,
    parity_forward: float | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """One-year fixture with two distinct model put/call parity observations."""
    forward = 100 * math.exp(rate - dividend_yield - residual_yield)
    model_forward = forward if parity_forward is None else parity_forward
    money = pd.DataFrame([{
        "ticker": KEY[0], "tradeDate": KEY[1], "expirDate": KEY[2],
        "quoteDate": KEY[1] + "T15:50:00-05:00", "stockPrice": 100.,
        "riskFreeRate": rate, "yieldRate": dividend_yield,
        "residualYieldRate": residual_yield,
    }])
    quotes = []
    for strike, delta in [(100., .6), (105., .4)]:
        discounted_difference = math.exp(-rate) * (model_forward - strike)
        put = max(-discounted_difference, 0) + 5
        quotes.append({
            "ticker": KEY[0], "tradeDate": KEY[1], "expirDate": KEY[2],
            "quoteDate": KEY[1] + "T15:50:00-05:00", "strike": strike,
            "delta": delta, "callValue": put + discounted_difference, "putValue": put,
        })
    return money, pd.DataFrame(quotes)


@pytest.mark.parametrize(
    ("rate", "dividend_yield", "residual_yield", "expected_growth"),
    [(.05, .02, .01, .02), (.05, .03, .04, -.02), (.05, .02, -.01, .04)],
)
def test_decimal_carry_with_additive_residual_yield(
    rate: float, dividend_yield: float, residual_yield: float, expected_growth: float,
) -> None:
    money, quotes = carry_inputs(
        rate=rate, dividend_yield=dividend_yield, residual_yield=residual_yield,
    )
    forwards, audit = build_forwards(money, quotes)
    assert forwards[KEY] == pytest.approx(100 * math.exp(expected_growth))
    assert audit.iloc[0].calendar_time_years == 1
    assert audit.iloc[0].status == "model_carry_parity_consistent"
    assert audit.iloc[0].parity_deviation_spot_fraction == pytest.approx(0, abs=1e-12)


def test_model_disagreement_does_not_fall_back_to_spot_or_parity() -> None:
    money, quotes = carry_inputs(parity_forward=106.)
    forwards, audit = build_forwards(money, quotes)
    assert forwards == {}
    assert audit.iloc[0].status == "carry_parity_disagreement"
    assert audit.iloc[0].parity_forward_median == pytest.approx(106.)


@pytest.mark.parametrize("missing", [None, math.nan, math.inf])
def test_missing_or_nonfinite_carry_never_becomes_zero(missing: float | None) -> None:
    money, quotes = carry_inputs()
    money.loc[0, "residualYieldRate"] = missing
    forwards, audit = build_forwards(money, quotes)
    assert forwards == {}
    assert audit.iloc[0].status == "missing_carry_inputs"


def test_single_model_contract_is_insufficient_support() -> None:
    money, quotes = carry_inputs()
    forwards, audit = build_forwards(money, quotes.iloc[:1])
    assert forwards == {}
    assert audit.iloc[0].status == "missing_parity_support"


def test_duplicate_contract_does_not_create_two_independent_support_points() -> None:
    money, quotes = carry_inputs()
    duplicate = pd.concat([quotes.iloc[:1], quotes.iloc[:1]], ignore_index=True)
    forwards, _ = build_forwards(money, duplicate)
    assert forwards == {}, "Repeated copies of one strike cannot satisfy two-point support"


def test_stale_carry_quote_date_cannot_support_current_coordinate() -> None:
    money, quotes = carry_inputs()
    money.loc[0, "quoteDate"] = "2025-12-31T15:50:00-05:00"
    forwards, _ = build_forwards(money, quotes)
    assert forwards == {}, "tradeDate must not conceal a stale underlying carry observation"


def test_stale_model_quote_date_cannot_support_current_coordinate() -> None:
    money, quotes = carry_inputs()
    quotes["quoteDate"] = "2025-12-31T15:50:00-05:00"
    forwards, _ = build_forwards(money, quotes)
    assert forwards == {}, "A prior quote-date model must not validate the current carry"


def test_internal_model_check_does_not_establish_exact_observed_forward() -> None:
    money, quotes = carry_inputs(parity_forward=102.5)
    forwards, audit = build_forwards(money, quotes)
    assert forwards[KEY] != pytest.approx(102.5)
    assert audit.iloc[0].status == "model_carry_parity_consistent"
    # The 1%-of-spot tolerance intentionally permits different model forwards.
    assert audit.iloc[0].parity_deviation_spot_fraction > 0
