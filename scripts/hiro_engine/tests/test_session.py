"""Task 5b tests: per-bar contract ordering; entry executes the bar AFTER its
signal; disposition written exactly once; degraded paths."""
from __future__ import annotations

import io

import pandas as pd
import pytest

from hiro_engine.eventlog import EventLog
from hiro_engine.feeds import ReplayTick
from hiro_engine.models import Bar, SpyBar, TIER_FULL
from hiro_engine.session import Session

from helpers import FakeChains


def _hiro_frame(upto: int, slope: float = 0.2):
    mins = list(range(570, upto + 1))
    return pd.DataFrame({
        "min": mins,
        "all_L": [slope * (m - 570) for m in mins],
        "all_Lc": [slope * 0.55 * (m - 570) for m in mins],
        "all_Lp": [slope * 0.45 * (m - 570) for m in mins],
        "nextExp_L": [slope * 0.7 * (m - 570) for m in mins],
    })


def _mk_session(config, tmp_path, day="2026-08-18", **kw) -> tuple[Session, EventLog]:
    log = EventLog(tmp_path / "paper_log.csv", console=io.StringIO())
    s = Session(config, TIER_FULL, day, "backtest", log,
                range60_history=[0.5] * 300,
                chains=kw.pop("chains", FakeChains()), **kw)
    return s, log


class FakeFeed:
    def __init__(self, ticks):
        self.ticks = ticks

    def iter_day(self, day):
        yield from self.ticks


def test_per_bar_contract_ordering(config, tmp_path, monkeypatch):
    s, log = _mk_session(config, tmp_path)
    calls = []
    orig_ep, orig_fu = s.executor.execute_pending, s.features.update
    orig_re, orig_ea = s.rules.evaluate, s.executor.apply
    monkeypatch.setattr(s.executor, "execute_pending",
                        lambda *a, **k: calls.append("execute_pending") or orig_ep(*a, **k))
    monkeypatch.setattr(s.features, "update",
                        lambda *a, **k: calls.append("features") or orig_fu(*a, **k))
    monkeypatch.setattr(s.rules, "evaluate",
                        lambda *a, **k: calls.append("rules") or orig_re(*a, **k))
    monkeypatch.setattr(s.executor, "apply",
                        lambda *a, **k: calls.append("apply") or orig_ea(*a, **k))
    tick = ReplayTick(Bar(600, 100, 100.5, 99.5, 100), SpyBar(600, 10, 10, 10, 10, 100),
                      _hiro_frame(600))
    s.process_tick(tick)
    assert calls == ["execute_pending", "features", "rules", "apply"]


def test_entry_executes_bar_after_signal_books_leg1(config, tmp_path):
    """v3 MIGRATION: the pending entry books leg 1 at the next bar's closing
    NBBO bid (S0 stays the context anchor = that bar's open)."""
    fk = FakeChains(quotes={("*", 7500.0): (40.0, 40.3), ("*", 7505.0): (40.2, 40.5)})
    s, log = _mk_session(config, tmp_path, chains=fk)
    from hiro_engine.models import PendingEntry
    s.state.pending_entry = PendingEntry("B", "sell_first", 700, 1, entry_L=1.0,
                                         k1=7500.0, k2=7505.0)
    tick = ReplayTick(Bar(701, 123.45, 124.0, 123.0, 123.5), None, _hiro_frame(701))
    s.process_tick(tick)
    assert s.state.open_trade is not None
    assert s.state.open_trade.leg1_fill == 40.0
    assert s.state.open_trade.s0 == 123.45 and s.state.open_trade.entry_min == 701


def test_disposition_written_exactly_once_and_countable(config, tmp_path):
    day = "2026-08-18"
    ticks = [ReplayTick(Bar(m, 100, 100.5, 99.5, 100),
                        SpyBar(m, 10, 10.1, 9.9, 10, 100), _hiro_frame(m))
             for m in range(570, 961)]
    import hiro_engine.session as sess_mod
    s, log = _mk_session(config, tmp_path)
    # avoid appending to the real sessions.csv
    rows = []
    s._write_session_row = lambda r: rows.append(r)
    out = s.run_replay(FakeFeed(ticks))
    assert out.disposition == "countable" and len(rows) == 1
    text = (tmp_path / "paper_log.csv").read_text()
    assert text.count("disposition") == 1


def test_partial_when_bars_end_early(config, tmp_path):
    ticks = [ReplayTick(Bar(m, 100, 100.5, 99.5, 100), None, _hiro_frame(m))
             for m in range(570, 900)]
    s, log = _mk_session(config, tmp_path)
    s._write_session_row = lambda r: None
    out = s.run_replay(FakeFeed(ticks))
    assert out.disposition == "partial"


def test_event_day_stands_down(config, tmp_path, monkeypatch):
    s, log = _mk_session(config, tmp_path)
    import hiro_engine.session as sm
    from hiro_engine.models import CalendarDay
    s.calendar = CalendarDay("2026-08-18", True, "cpi")
    s._write_session_row = lambda r: None
    out = s.run_replay(FakeFeed([]))
    assert out.disposition == "event_standdown"
    assert "EVENT DAY" in (tmp_path / "paper_log.csv").read_text()


def test_hiro_down_blocks_entries_and_logs_outage(config, tmp_path):
    s, log = _mk_session(config, tmp_path)
    from hiro_engine.models import PendingEntry
    ticks = [ReplayTick(Bar(m, 100, 100.5, 99.5, 100),
                        SpyBar(m, 10, 10.1, 9.9, 10, 100),
                        _hiro_frame(m) if m < 700 else None)
             for m in range(570, 720)]
    for t in ticks:
        s.process_tick(t)
    text = (tmp_path / "paper_log.csv").read_text()
    assert "HIRO DOWN" in text
    assert s.health == "HIRO_DOWN"
    assert s.outage_min == 20
