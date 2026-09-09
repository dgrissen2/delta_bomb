"""Strike identities must depend only on frozen signal-time rules."""

from scripts.pandar_hypothesis_contracts import select_contracts


def row(strike, delta, expiry="2026-06-26", bid=0.10):
    return {"ticker": "AAPL", "tradeDate": "2026-06-15", "expirDate": expiry,
            "strike": strike, "delta": delta, "stockPrice": 100,
            "callBidPrice": bid, "callAskPrice": bid + 0.05}


def test_freezes_nearest_delta_without_choosing_better_premium():
    result = select_contracts([row(110, .1), row(115, .05), row(120, .025, bid=3)],
                              "2026-06-15")
    assert result["far_strike"] == 115
    assert result["near_strike"] == 110
    assert result["signal_bid"] == .1


def test_nearer_must_be_adjacent_listed_and_otm_no_substitution():
    result = select_contracts([row(99, .55), row(115, .05)], "2026-06-15")
    assert result["selection_status"] == "nearer_not_otm"


def test_expiry_uses_calendar_dte_and_no_fallback_when_primary_fails():
    rows = [row(105, .3, "2026-06-24"), row(110, .2, "2026-06-24"),
            row(110, .1), row(115, .05)]
    result = select_contracts(rows, "2026-06-15")
    assert result["selection_status"] == "no_call_in_delta_band"
    assert result["expiry"] == "2026-06-24"


def test_higher_delta_arm_keeps_five_percent_distance_floor():
    result = select_contracts([row(103, .10), row(110, .08), row(115, .05)],
                              "2026-06-15", delta_min=.05, delta_max=.15,
                              target_delta=.10, minimum_otm_pct=5)
    assert result["far_strike"] == 110
    assert result["near_strike"] == 103
