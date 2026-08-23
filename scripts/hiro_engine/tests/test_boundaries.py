"""Task 10 boundary table: 14:30 entry -> 15:30 resolution; session-end
censoring; post-15:30 log-only; observe-only window."""
from __future__ import annotations

import io

import pandas as pd
import pytest

from hiro_engine.eventlog import EventLog
from hiro_engine.feeds import ReplayTick
from hiro_engine.models import Bar, EngineState, PendingEntry, SimTrade, TIER_FULL
from hiro_engine.rules import RuleEngine
from hiro_engine.session import Session

from helpers import FakeChains, b_fire_row, mk_row, qv, resting_trade


def test_1430_signal_enters_1431_resolves_1530(config):
    """A signal on the 14:30 bar (last allowed) enters at 14:31; with no fill
    the 15:30 resolution overrides the pending 60-min clock (R5.4)."""
    eng = RuleEngine(config, TIER_FULL)
    st = EngineState()
    evs = eng.evaluate(b_fire_row(870), st)
    assert any(e.event_type == "signal" for e in evs)
    from hiro_engine.executor import Executor
    from hiro_engine.instruments import InstrumentSelector
    ex = Executor(config, InstrumentSelector(config), tier=TIER_FULL)
    for e in evs:                                          # Session-resolve stand-in
        if e.event_type == "pending_entry":
            e.k1, e.k2 = 7500.0, 7505.0
    ex.apply(evs, b_fire_row(870), st)
    ex.execute_pending(Bar(871, 100.0, 100.2, 99.8, 100.0), st,
                       quotes=qv(871, leg1=(40.0, 40.3), leg2=(40.2, 40.5)))
    assert st.open_trade.entry_min == 871
    # 15:30 arrives: clock would fire at 931 (60m) but resolution books AT 930
    row930 = mk_row(930, close=100.0, open_=100.05,
                    quote_view=qv(930, leg1=(40.6, 41.0)))
    evs2 = eng.evaluate(row930, st)
    d = [e for e in evs2 if e.event_type == "exit_decision"]
    assert d and d[0].outcome_type == "resolution"
    out = ex.apply(evs2, row930, st)
    assert out[0].outcome_type == "resolution_close" and out[0].exit_ref == 41.0


def test_no_signal_after_1430_and_before_1000(config):
    eng = RuleEngine(config, TIER_FULL)
    for m in (599, 871, 929):
        evs = eng.evaluate(b_fire_row(m, episode=m), EngineState())
        assert not any(e.event_type == "signal" for e in evs), m


def test_post_1530_log_only(config, tmp_path):
    """After 15:30 the engine tracks/logs state but never enters (R5.4)."""
    log = EventLog(tmp_path / "log.csv", console=io.StringIO())
    s = Session(config, TIER_FULL, "2026-08-18", "backtest", log,
                range60_history=[0.5] * 300, chains=FakeChains())
    s._write_session_row = lambda r: None
    import pandas as pd
    hiro = pd.DataFrame({"min": range(570, 961), "all_L": 0.0, "all_Lc": 0.0,
                         "all_Lp": 0.0, "nextExp_L": 0.0})
    for m in list(range(570, 961)):
        s.process_tick(ReplayTick(Bar(m, 100, 100.5, 99.5, 100), None,
                                  hiro[hiro["min"] <= m]))
    df = pd.read_csv(tmp_path / "log.csv")
    post = df[df.ts >= "2026-08-18 15:31"]
    assert not len(post[post.event_type.isin(["signal", "entry", "pending_entry"])])


def test_session_end_censoring_not_timeout(config):
    """Open trade at the last bar with no exit decision -> censored at close."""
    from hiro_engine.executor import Executor
    from hiro_engine.instruments import InstrumentSelector
    ex = Executor(config, InstrumentSelector(config), tier=TIER_FULL)
    st = EngineState(pending_entry=PendingEntry("B", "sell_first", 600, 1, entry_L=1.0,
                                                k1=7500.0, k2=7505.0))
    ex.execute_pending(Bar(601, 100.0, 100.1, 99.9, 100.0), st,
                       quotes=qv(601, leg1=(40.0, 40.3), leg2=(40.2, 40.5)))
    evs = ex.end_of_session(Bar(610, 100.0, 100.1, 99.9, 99.97), st,
                            quotes=qv(610, leg1=(40.3, 40.6)))
    assert evs[0].outcome_type == "censored" and evs[0].exit_ref == 40.6
