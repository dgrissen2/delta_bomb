"""Task 5/4b tests: executor properties, schema-completeness round-trip,
console/CSV identity per event type, crash-resume, instrument selector."""
from __future__ import annotations

import dataclasses
import io

import pytest

from hiro_engine_v2.eventlog import (EventLog, event_from_row, event_to_row,
                                  format_console, rebuild_state, trade_from_entry_event)
from hiro_engine_v2.executor import Executor
from hiro_engine_v2.instruments import InstrumentSelector
from hiro_engine_v2.models import (Bar, EngineState, Event, PendingEntry, SimTrade, TIER_FULL)
from hiro_engine_v2.rules import RuleEngine

from helpers import b_fire_row, mk_row, qv, resting_trade


def _exec(config):
    from hiro_engine_v2.models import TIER_FULL
    return Executor(config, InstrumentSelector(config), tier=TIER_FULL)


PE = dict(k1=7500.0, k2=7505.0)          # v3: instruments resolved at signal


# ---- 4b InstrumentSelector -------------------------------------------------------
def test_expiry_picker_across_month_boundary(config):
    sel = InstrumentSelector(config)
    listed = ["2026-09-04", "2026-09-18", "2026-09-30", "2026-10-16"]
    assert sel.pick_expiry("2026-08-21", listed) == "2026-09-18"    # 28 dte, nearest 30
    # tie -> shorter: 25 vs 35 dte around target 30
    assert sel.pick_expiry("2026-08-21", ["2026-09-15", "2026-09-25"]) == "2026-09-15"
    assert sel.pick_expiry("2026-08-21", ["2026-08-25", "2026-12-01"]) is None  # none in 20-40


def test_delta_tiebreak_and_width(config):
    sel = InstrumentSelector(config)
    chain = [{"strike": 7700, "delta": -0.24}, {"strike": 7710, "delta": -0.18},
             {"strike": 7705, "delta": -0.18}]
    assert sel.pick_strike(chain) == 7705                            # tie -> lower strike
    assert sel.legs("sell_first", 7700.0) == (7700.0, 7705.0)
    assert sel.legs("long_first", 7700.0) == (7700.0, 7695.0)
    assert sel.size == 1


# ---- executor properties ------------------------------------------------------------
def test_pending_entry_executes_exactly_once_books_leg1_nbbo(config):
    """v3 MIGRATION: leg 1 books at the bar's closing NBBO bid (sell-first);
    the resting limit is created at fill1 - 0.10; S0 is context only."""
    ex = _exec(config)
    st = EngineState(pending_entry=PendingEntry("B", "sell_first", 700, 1, entry_L=1.0, **PE))
    evs = ex.execute_pending(Bar(701, 100.5, 101.0, 100.0, 100.8), st,
                             quotes=qv(701, leg1=(40.0, 40.3), leg2=(40.2, 40.5)))
    assert [e.event_type for e in evs] == ["entry"]
    assert st.open_trade.leg1_fill == 40.0 and st.open_trade.limit.price == 39.9
    assert st.open_trade.s0 == 100.5 and st.open_trade.target is None
    assert st.pending_entry is None and st.entries_today == 1
    assert ex.execute_pending(Bar(702, 101, 101, 100, 101), st,
                              quotes=qv(702)) == []                     # never twice


def test_fill_books_at_limit_with_credit(config):
    """v3 MIGRATION (SUPERSEDED touch semantics; fixture S1/S2 are the golden):
    the fill books at L with credit >= 0.10; pnl_usd = +$10."""
    ex = _exec(config)
    st = EngineState(pending_entry=PendingEntry("B", "sell_first", 700, 1, entry_L=1.0, **PE))
    ex.execute_pending(Bar(701, 100.0, 100.2, 99.0, 100.0), st,
                       quotes=qv(701, leg1=(40.0, 40.3), leg2=(40.2, 40.5)))
    rules = RuleEngine(config, TIER_FULL)
    row2 = mk_row(702, close=102.9, quote_view=qv(702, leg2=(39.5, 39.9)))
    out = ex.apply(rules.evaluate(row2, st), row2, st)
    assert out[0].outcome_type == "fill" and out[0].exit_ref == 39.9
    assert out[0].credit == pytest.approx(0.10) and out[0].pnl_usd == pytest.approx(10.0)
    assert out[0].outcome_minutes == 1


def test_non_fill_exit_books_next_close_nbbo_and_censored(config):
    """v3 MIGRATION: scratch books at the NEXT bar's closing ASK (sell-first);
    censored books at the last bar's NBBO (fixture S5/S10 are the golden)."""
    ex = _exec(config)
    st = EngineState(pending_entry=PendingEntry("B", "sell_first", 700, 1, entry_L=1.0, **PE))
    ex.execute_pending(Bar(701, 100.0, 100.2, 99.5, 100.0), st,
                       quotes=qv(701, leg1=(40.0, 40.3), leg2=(40.2, 40.5)))
    rules = RuleEngine(config, TIER_FULL)
    row = mk_row(702, close=99.5, L=0.5, quote_view=qv(702))
    ex.apply(rules.evaluate(row, st), row, st)
    assert st.pending_exit == "scratch"
    evs = ex.execute_pending(Bar(703, 99.2, 99.4, 99.0, 99.3), st,
                             quotes=qv(703, leg1=(40.3, 40.6)))
    assert evs[0].outcome_type == "scratch" and evs[0].exit_ref == 40.6
    assert evs[0].pnl_usd == pytest.approx(-60.0)
    assert st.open_trade is None
    st2 = EngineState(pending_entry=PendingEntry("B", "sell_first", 600, 2, entry_L=1.0, **PE))
    ex.execute_pending(Bar(601, 100.0, 100.1, 99.9, 100.0), st2,
                       quotes=qv(601, leg1=(40.0, 40.3), leg2=(40.2, 40.5)))
    evs2 = ex.end_of_session(Bar(610, 100.0, 100.1, 99.9, 99.95), st2,
                             quotes=qv(610, leg1=(40.3, 40.6)))
    assert evs2[0].outcome_type == "censored" and evs2[0].exit_ref == 40.6


def test_at_most_one_open_trade_and_daily_cap_holds(config):
    """Property over a scripted day: <=1 open, <=3 entries."""
    ex = _exec(config)
    rules = RuleEngine(config, TIER_FULL)
    st = EngineState()
    entries = 0
    for m in range(600, 960):
        evs_open = ex.execute_pending(Bar(m, 100.0, 100.4, 99.6, 100.0), st,
                                      quotes=qv(m))
        entries += sum(1 for e in evs_open if e.event_type == "entry")
        assert (st.open_trade is None) or (st.pending_entry is None)
        row = b_fire_row(m, episode=m, quote_view=qv(m))  # fire every bar, never marketable
        evs = rules.evaluate(row, st)
        for e in evs:                                      # stand-in for Session resolve (R1.2)
            if e.event_type == "pending_entry":
                e.k1, e.k2 = 7500.0, 7505.0
        ex.apply(evs, row, st)
        assert st.entries_today <= 3
    assert entries == 3


# ---- schema completeness (task 5 blocker test) -----------------------------------------
def test_entry_exit_round_trip_reconstructs_simtrade_field_for_field(config):
    ex = _exec(config)
    st = EngineState(pending_entry=PendingEntry("A", "long_first", 700, 3,
                                                bh_level=None, entry_L=None,
                                                k1=7500.0, k2=7495.0))
    entry_evs = ex.execute_pending(Bar(701, 100.0, 100.2, 99.5, 100.0), st,
                                   quotes=qv(701, k2=7495.0, leg1=(39.95, 40.25),
                                             leg2=(39.5, 39.9)))
    original = dataclasses.replace(st.open_trade)
    rules = RuleEngine(config, TIER_FULL)
    row = mk_row(710, close=96.9,
                 quote_view=qv(710, k2=7495.0, leg2=(40.40, 40.80)))  # bid>=L=40.40 -> fill
    exit_evs = ex.apply(rules.evaluate(row, st), row, st)
    # serialize -> CSV row -> back -> rebuild
    e_in = event_from_row(event_to_row(entry_evs[0]))
    x_in = event_from_row(event_to_row(exit_evs[0]))
    rebuilt = trade_from_entry_event(e_in)
    from hiro_engine_v2.eventlog import apply_exit_event
    apply_exit_event(rebuilt, x_in)
    closed = original
    closed.state, closed.exit_type, closed.exit_ref = "closed", "fill", 40.40
    closed.minutes, closed.adverse = 9, exit_evs[0].adverse
    closed.leg2_fill, closed.credit, closed.pnl_usd = 40.40, exit_evs[0].credit, exit_evs[0].pnl_usd
    for f in dataclasses.fields(SimTrade):
        if f.name == "limit":
            assert rebuilt.limit.price == closed.limit.price
            assert rebuilt.limit.status == "filled"
            continue
        got, want = getattr(rebuilt, f.name), getattr(closed, f.name)
        assert got == want or (got is None and want is None), \
            f"{f.name}: {got} != {want}"


# ---- console/CSV identity per event type (R8.1 matrix) ----------------------------------
EVENT_SAMPLES = [
    Event(event_type="signal", rule_id="R6.2", branch="B", side="sell_first",
          signal_min=700, episode=1, run=1.0, rate=2.4, dC=0.6, dP=0.4, share=0.7,
          r15=0.5, notes="SIGNAL B SELL-FIRST"),
    Event(event_type="entry", rule_id="R1.4", branch="B", side="sell_first", s0=100.0,
          trade_id=1, entry_min=701, signal_min=700, target=103.0, cap_source="proxy",
          cap_value=15.0, entry_L=1.0, notes="ENTRY B"),
    Event(event_type="exit", rule_id="R7", branch="B", side="sell_first", s0=100.0,
          trade_id=1, outcome_type="fill", outcome_minutes=4, exit_ref=103.0,
          adverse=1.2, notes="EXIT fill"),
    Event(event_type="veto_change", rule_id="R4", notes="vetoes: flow_veto=True"),
    Event(event_type="skip", rule_id="R6.4", branch="B", episode=2, notes="skip: cap"),
    Event(event_type="gate_fail", rule_id="R6.2", branch="B", episode=2, notes="gates failed: r15<=0"),
    Event(event_type="late_no_entry", rule_id="R6.3", branch="B", episode=2, notes="LATE — NO ENTRY"),
    Event(event_type="outage", rule_id="R10", notes="HIRO DOWN — no new entries"),
    Event(event_type="heartbeat", rule_id="R8.1", branch="B", trade_id=1, notes="open 5m"),
    Event(event_type="state_line", rule_id="R3.4", context="UP", notes="10:30 context read: UP"),
    Event(event_type="banner", rule_id="R8.2", notes="session start"),
    Event(event_type="disposition", rule_id="R10.3", notes="session countable"),
    Event(event_type="pending_entry", rule_id="R6.2", branch="B", side="sell_first",
          signal_min=700, episode=1, entry_L=1.0),
    Event(event_type="exit_decision", rule_id="R7.2", branch="B", outcome_type="scratch",
          trade_id=1),
]


@pytest.mark.parametrize("ev", EVENT_SAMPLES, ids=lambda e: e.event_type)
def test_csv_round_trip_and_console_render(ev):
    back = event_from_row(event_to_row(ev))
    assert back == ev                                     # lossless per event type
    line = format_console(ev)
    assert ev.event_type.upper() in line
    if ev.notes:
        assert ev.notes in line


# ---- crash-resume -------------------------------------------------------------------------
def test_crash_resume_reconstructs_open_trade(config, tmp_path):
    log = EventLog(tmp_path / "log.csv", console=io.StringIO())
    ex = _exec(config)
    st = EngineState(pending_entry=PendingEntry("B", "sell_first", 700, 1, entry_L=1.0, **PE))
    evs = ex.execute_pending(Bar(701, 100.0, 100.2, 99.5, 100.0), st,
                             quotes=qv(701, leg1=(40.0, 40.3), leg2=(40.2, 40.5)))
    for e in evs:
        e.session_date = "2026-08-18"
    log.emit(evs)
    log.close()
    st2 = rebuild_state(tmp_path / "log.csv", "2026-08-18")
    assert st2.open_trade is not None
    for f in dataclasses.fields(SimTrade):
        assert getattr(st2.open_trade, f.name) == getattr(st.open_trade, f.name), f.name
    assert st2.entries_today == 1 and st2.entered_episode_b == 1
    # after an exit row, resume shows flat
    row = mk_row(702, close=102.9, quote_view=qv(702, leg2=(39.5, 39.9)))
    rules = RuleEngine(config, TIER_FULL)
    exit_evs = ex.apply(rules.evaluate(row, st), row, st)
    log2 = EventLog(tmp_path / "log.csv", console=io.StringIO())
    for e in exit_evs:
        e.session_date = "2026-08-18"
    log2.emit(exit_evs)
    log2.close()
    st3 = rebuild_state(tmp_path / "log.csv", "2026-08-18")
    assert st3.open_trade is None and st3.entries_today == 1
