"""Fix for red-team finding 3: warm crash-resume rebuilds features/vetoes/
episode state by muted replay; state equals an uninterrupted run's state."""
from __future__ import annotations

import io

import pandas as pd
import pytest

from hiro_engine_v2.eventlog import EventLog
from hiro_engine_v2.feeds import ReplayFeed
from hiro_engine_v2.models import TIER_FULL
from hiro_engine_v2.session import Session

DAY = "2026-08-12"     # a day with real B entries in the stored data


def _session(config, log):
    from hiro_engine_v2.chains import ChainStore
    s = Session(config, TIER_FULL, DAY, "backtest", log, range60_history=[0.5] * 300,
                chains=ChainStore())
    s._write_session_row = lambda row: None
    return s


def test_warm_resume_equals_uninterrupted_run(config, tmp_path):
    feed = ReplayFeed(config, [DAY])
    ticks = list(feed.iter_day(DAY))
    cut = 200                                    # crash after bar 200 (~12:50)

    # uninterrupted reference run
    log_a = EventLog(tmp_path / "a.csv", console=io.StringIO())
    ref = _session(config, log_a)
    for t in ticks:
        ref.process_tick(t)

    # crashed run: process to cut, "crash", new session warm-replays the same bars
    log_b = EventLog(tmp_path / "b.csv", console=io.StringIO())
    s1 = _session(config, log_b)
    for t in ticks[:cut]:
        s1.process_tick(t)
    log_b.close()
    log_b2 = EventLog(tmp_path / "b.csv", console=io.StringIO())
    s2 = _session(config, log_b2)
    s2.warm_replay(ticks[:cut])
    assert "RESUME WARNING" not in (tmp_path / "b.csv").read_text()

    # warm state matches the crashed session exactly
    assert s2.vt_broken == s1.vt_broken
    assert s2.features.open_0930 == s1.features.open_0930
    assert s2.features.ema == s1.features.ema
    assert len(s2.features.closes) == cut
    assert s2.state.entries_today == s1.state.entries_today
    assert (s2.state.open_trade is None) == (s1.state.open_trade is None)
    assert s2.features.ep_b.next_id == s1.features.ep_b.next_id
    assert s2.rules._skip_logged == s1.rules._skip_logged

    # continuing the resumed session reproduces the reference stream exactly
    for t in ticks[cut:]:
        s2.process_tick(t)
    a = pd.read_csv(tmp_path / "a.csv")
    b = pd.read_csv(tmp_path / "b.csv")
    ea = a[a.event_type.isin(["entry", "exit"])].reset_index(drop=True)
    eb = b[b.event_type.isin(["entry", "exit"])].reset_index(drop=True)
    pd.testing.assert_frame_equal(ea, eb)
