"""Task 10 end-to-end: two full replayed sessions live-style (wall-clock
compressed), with a forced crash+resume in the middle of session 2. The
crashed+resumed run must produce the same trades and dispositions as an
uninterrupted two-session run."""
from __future__ import annotations

import io

import pandas as pd

from hiro_engine.eventlog import EventLog
from hiro_engine.feeds import ReplayFeed
from hiro_engine.models import TIER_FULL
from hiro_engine.session import Session, build_range60_history

DAYS = ["2026-08-19", "2026-08-20"]


def _run_two(config, tmp_path, name, crash_at=None):
    """Replays both days tick-by-tick through Session (live-style loop);
    optionally 'crashes' session 2 after `crash_at` bars and resumes."""
    log_p = tmp_path / f"{name}.csv"
    era = str(config.get("data", "hiro_era_start"))
    from hiro_engine.backtest import available_spx_days
    dispos = []
    for i, day in enumerate(DAYS):
        prior = [d for d in available_spx_days(config, era, day) if d < day]
        hist = build_range60_history(config, TIER_FULL, prior)
        feed = ReplayFeed(config, [day])
        ticks = list(feed.iter_day(day))
        log = EventLog(log_p, console=io.StringIO())
        from hiro_engine.chains import ChainStore
        s = Session(config, TIER_FULL, day, "live", log, range60_history=hist,
                    chains=ChainStore())
        s._write_session_row = lambda row: dispos.append(row)
        log.emit(s._stamp(s.startup_events(), None))
        if i == 1 and crash_at is not None:
            for t in ticks[:crash_at]:
                s.process_tick(t)
            log.close()                                   # CRASH
            log = EventLog(log_p, console=io.StringIO())  # restart
            s = Session(config, TIER_FULL, day, "live", log, range60_history=hist,
                        chains=ChainStore())
            s._write_session_row = lambda row: dispos.append(row)
            s.warm_replay(ticks[:crash_at])
            for t in ticks[crash_at:]:
                s.process_tick(t)
            s.finish()
        else:
            for t in ticks:
                s.process_tick(t)
            s.finish()
        log.close()
    return log_p, dispos


def test_two_sessions_with_forced_crash_resume(config, tmp_path):
    p_ref, d_ref = _run_two(config, tmp_path, "ref")
    p_crash, d_crash = _run_two(config, tmp_path, "crash", crash_at=250)
    ref = pd.read_csv(p_ref)
    got = pd.read_csv(p_crash)
    assert "RESUME WARNING" not in (tmp_path / "crash.csv").read_text()
    for cols in (["entry"], ["exit"], ["disposition"]):
        a = ref[ref.event_type.isin(cols)].reset_index(drop=True)
        b = got[got.event_type.isin(cols)].reset_index(drop=True)
        pd.testing.assert_frame_equal(a, b), cols
    assert [d.disposition for d in d_ref] == [d.disposition for d in d_crash]
    assert all(d.mode == "live" for d in d_ref)
