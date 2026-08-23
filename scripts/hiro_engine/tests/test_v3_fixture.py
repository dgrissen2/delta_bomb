"""R12.2 Gate 2: drive the v3 pricing layer through the HAND-COMPUTED fixture.
The expected values in fixtures/v3_quotes_fixture.py are FROZEN — a mismatch
here is a defect investigation, never a fixture edit."""
from __future__ import annotations

import pytest

from hiro_engine.executor import Executor
from hiro_engine.instruments import InstrumentSelector
from hiro_engine.models import (Bar, EngineState, PendingEntry, QuoteSnap, QuoteView,
                                TIER_FULL, Vetoes)
from hiro_engine.rules import RuleEngine

from fixtures.v3_quotes_fixture import K, K2S, K2L, SCENARIOS
from helpers import mk_row


def _snap(quotes: dict, strike: float, m: int):
    q = quotes.get(strike, {}).get(m)
    if q is None:
        return None
    bid, ask = q
    return QuoteSnap(strike=strike, bid=bid, ask=ask, valid=(bid > 0 and ask >= bid))


def _run_scenario(config, sc):
    side = sc["side"]
    k2 = K2S if side == "sell_first" else K2L
    signal = sc.get("override_signal_min", sc["signal_min"])
    entry = sc.get("override_entry_min", signal + 1)
    last_min = sc.get("session_last_min", 965)
    quotes = sc["quotes"]

    eng = RuleEngine(config, TIER_FULL)
    ex = Executor(config, InstrumentSelector(config), tier=TIER_FULL)
    st = EngineState(pending_entry=PendingEntry(
        branch=sc.get("branch", "A" if side == "long_first" else "B"), side=side,
        signal_min=signal, episode=1, entry_L=(1.0 if side == "sell_first" else None),
        k1=K, k2=k2))
    events_all = []

    def collect(evs, minute):
        for e in evs:
            e._at_min = minute                     # harness tag: WHEN it happened
        events_all.extend(evs)

    streak = 0
    m = entry
    while m <= min(last_min, 962):
        qv = QuoteView(minute=m, leg1=_snap(quotes, K, m), leg2=_snap(quotes, k2, m))
        collect(ex.execute_pending(Bar(m, 100.0, 100.2, 99.8, 100.0), st, quotes=qv), m)
        tr = st.open_trade
        if tr is None and st.pending_entry is None:
            break
        # Session's streak rule
        if tr is not None and tr.limit is not None and tr.limit.status == "resting":
            streak = 0 if (qv.leg2 is not None and qv.leg2.valid) else streak + 1
        else:
            streak = 0
        row_kw = dict(quote_view=qv, quote_gap_streak=streak)
        if sc.get("scratch_trigger_min") == m:
            row_kw["L"] = 0.5                                    # >= 0.3 below entry_L
        if sc.get("veto_trigger_min") == m:
            row_kw["vetoes"] = Vetoes(flow_veto=True)
        if sc.get("state_flip_min") == m:
            row_kw["context_1300"] = "UP" if side == "long_first" else "DOWN"
        row = mk_row(m, close=100.0, **row_kw)
        evs = eng.evaluate(row, st)
        collect(evs, m)
        collect(ex.apply(evs, row, st), m)
        if st.open_trade is None and st.pending_exit is None and st.pending_entry is None:
            break
        m += 1
    if st.open_trade is not None:                                 # session end path
        qv = QuoteView(minute=last_min, leg1=_snap(quotes, K, last_min),
                       leg2=_snap(quotes, k2, last_min))
        collect(ex.end_of_session(Bar(last_min, 100, 100.2, 99.8, 100.0), st, quotes=qv),
                last_min)
    return events_all


@pytest.mark.parametrize("sc", SCENARIOS, ids=[s["name"] for s in SCENARIOS])
def test_v3_fixture_scenario(config, sc):
    evs = _run_scenario(config, sc)
    exp = sc["expect"]
    types = [e.event_type for e in evs]
    if exp.get("trade_opened") is False:
        assert "entry" not in types
        assert "entry_aborted_no_quote" in types
        return
    entry = next(e for e in evs if e.event_type == "entry")
    exit_ev = next(e for e in evs if e.event_type == "exit")
    if "leg1_fill" in exp:
        assert entry.leg1_fill == pytest.approx(exp["leg1_fill"]), "leg1_fill"
    if "limit_price" in exp:
        assert entry.limit_price == pytest.approx(exp["limit_price"]), "limit_price"
    assert exit_ev.outcome_type == exp["outcome"], f"outcome: {exit_ev.outcome_type}"
    if "fill_min" in exp:
        assert exit_ev.outcome_minutes == exp["fill_min"] - (sc.get("override_entry_min", sc["signal_min"] + 1))
        assert exit_ev.outcome_minutes == exp["minutes"]
    if "credit" in exp:
        assert exit_ev.credit == pytest.approx(exp["credit"]), "credit"
    if "pnl_usd" in exp:
        assert exit_ev.pnl_usd == pytest.approx(exp["pnl_usd"]), \
            f"pnl_usd {exit_ev.pnl_usd} != {exp['pnl_usd']}"
    if "exit_price" in exp:
        assert exit_ev.exit_ref == pytest.approx(exp["exit_price"]), "exit_price"
    if "scratch_loss_usd" in exp:
        assert -exit_ev.pnl_usd == pytest.approx(exp["scratch_loss_usd"])
    if exp.get("data_invalid"):
        assert exit_ev.data_invalid is True
        assert any(e.event_type == "limit_canceled"
                   and e.limit_cancel_reason == "quote_gap" for e in evs)
    if exp.get("no_scratch"):
        assert not any(e.outcome_type == "scratch" for e in evs if e.event_type == "exit")
    if "cap_source" in exp:
        assert any(e.event_type == "exit_decision" and e.cap_source == exp["cap_source"]
                   for e in evs) or exit_ev.outcome_type == "cap"
    # ---- MINUTE-LEVEL assertions (red-team/codex BP1: the hand-derived
    # minutes are LOAD-BEARING, not decorative) ----
    if "exit_book_min" in exp:
        assert exit_ev._at_min == exp["exit_book_min"], \
            f"exit booked at {exit_ev._at_min}, expected {exp['exit_book_min']}"
    if "cap_min" in exp:
        cap_dec = next(e for e in evs if e.event_type == "exit_decision"
                       and e.outcome_type == "cap")
        assert cap_dec._at_min == exp["cap_min"], \
            f"cap decided at {cap_dec._at_min}, expected {exp['cap_min']}"
    if "limit_canceled_min" in exp:
        cans = [e for e in evs if e.event_type == "limit_canceled"]
        assert cans, "no limit_canceled event emitted"
        assert cans[0]._at_min == exp["limit_canceled_min"], \
            f"cancel at {cans[0]._at_min}, expected {exp['limit_canceled_min']}"
    if "cancel_reason" in exp:
        assert any(e.event_type == "limit_canceled"
                   and e.limit_cancel_reason == exp["cancel_reason"] for e in evs)
    if "fill_min" in exp:
        assert exit_ev._at_min == exp["fill_min"]
