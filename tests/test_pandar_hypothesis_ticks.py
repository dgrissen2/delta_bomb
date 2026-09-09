"""Outcome-independent request scope and expiry boundary."""

import pandas as pd

from scripts.pandar_hypothesis_ticks import request_plan


def test_scope_fixed_pairs_both_legs_and_expiry_cap():
    common = {"tradeDate": "2026-06-11", "expiry": "2026-06-16", "selection_status": "selected",
              "far_strike": 100.0, "near_strike": 95.0,
              **{f"holding_session_{n}": d for n, d in enumerate(
                  ["2026-06-12", "2026-06-15", "2026-06-16", "2026-06-17", "2026-06-18"], 1)}}
    cases = pd.DataFrame([common | {"ticker": "AAA"}, common | {"ticker": "BBB"}])
    gates = pd.DataFrame([{"ticker": "AAA", "pass_basic": True},
                          {"ticker": "AAA", "pass_basic": True},
                          {"ticker": "BBB", "pass_basic": False}])
    plan = request_plan(cases, gates)
    assert len(plan) == 6
    assert {r["ticker"] for r in plan} == {"AAA"}
    assert {r["strike"] for r in plan} == {100.0, 95.0}
    assert max(r["session"] for r in plan) == "2026-06-16"
