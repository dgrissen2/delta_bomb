"""Task 8 golden test: scorecard over a synthetic 10-session fixture log ==
hand-computed R9 expectations (qualifying vs executable, censored denominators,
A-over-B dedupe, best-session tie-breaks, would-have-filled re-check)."""
from __future__ import annotations

import csv
import io

import pandas as pd
import pytest

from hiro_engine.eventlog import EventLog, event_to_row
from hiro_engine.models import EVENT_FIELDS, Event
from hiro_engine.scorecard import (ScorecardError, stage1_filter, stage2_entries,
                                   stage3_qualify, stage4_metrics, stage6_criteria,
                                   _best_session, run_scorecard)

DAYS = ["2026-08-05", "2026-08-06", "2026-08-07", "2026-08-10", "2026-08-11",
        "2026-08-12", "2026-08-13", "2026-08-14", "2026-08-17", "2026-08-18"]
H = "cafe" * 16


def _ev(**kw) -> Event:
    base = dict(mode="live", tier="full", config_hash=H, schema_v=1, health="OK")
    base.update(kw)
    e = Event(**base)
    return e


def _fixture_events() -> list[Event]:
    evs: list[Event] = []
    tid = 0

    def entry_exit(date, branch, side, sig, s0, exit_type, exit_ref, adverse,
                   minutes=None, episode=1, pnl_usd=None, k2=None, limit_price=None,
                   data_invalid=False):
        """v3 MIGRATION (15g UPDATED): events carry $ economics + limit fields."""
        nonlocal tid
        tid += 1
        if pnl_usd is None:
            pnl_usd = 10.0 if exit_type == "fill" else -50.0
        evs.append(_ev(session_date=date, event_type="signal", branch=branch, side=side,
                       signal_min=sig, episode=episode))
        evs.append(_ev(session_date=date, event_type="entry", branch=branch, side=side,
                       trade_id=tid, signal_min=sig, entry_min=sig + 1, s0=s0,
                       episode=episode, k1=7500.0, k2=k2, leg1_fill=40.0,
                       limit_price=limit_price, cap_source="chain", cap_value=3.5))
        evs.append(_ev(session_date=date, event_type="exit", branch=branch, side=side,
                       trade_id=tid, signal_min=sig, entry_min=sig + 1, s0=s0,
                       episode=episode, outcome_type=exit_type, exit_ref=exit_ref,
                       outcome_minutes=minutes, adverse=adverse, pnl_usd=pnl_usd,
                       k2=k2, limit_price=limit_price, data_invalid=data_invalid,
                       credit=0.10 if exit_type == "fill" else None))

    # Branch B: 10 executable entries across the 10 days
    #  6 fills, 2 scratches, 1 timeout, 1 censored  -> fill rate 6/9 (censored excluded)
    for i, d in enumerate(DAYS[:6]):                       # 6 fills, one per day
        entry_exit(d, "B", "sell_first", 700 + i, 100.0, "fill", 103.0, 1.0, minutes=5)
    # scratch #1 on a CACHED day (2026-08-13) with an absurd-high buy limit ->
    # the limit replay finds ask <= 1000 immediately -> would-have-filled TRUE
    entry_exit("2026-08-13", "B", "sell_first", 700, 100.0, "scratch", 40.4, 1.0,
               pnl_usd=-40.0, k2=7575.0, limit_price=1000.0)
    # scratch #2 on an UNCACHED day -> chain replay unavailable -> INDETERMINATE
    entry_exit(DAYS[1], "B", "sell_first", 705, 100.0, "scratch", 40.7, 2.0,
               pnl_usd=-70.0, k2=7505.0, limit_price=39.9, episode=2)
    entry_exit(DAYS[8], "B", "sell_first", 700, 100.0, "timeout", 40.8, 11.5,
               pnl_usd=-80.0)
    entry_exit(DAYS[9], "B", "sell_first", 700, 100.0, "censored", 40.5, 0.5,
               pnl_usd=-50.0)
    # Branch A: 2 executable entries, both fill -> rate 1.0
    entry_exit(DAYS[0], "A", "long_first", 720, 100.0, "fill", 97.0, 0.5, minutes=7, episode=11)
    entry_exit(DAYS[1], "A", "long_first", 720, 100.0, "fill", 97.0, 0.4, minutes=9, episode=11)
    # extra qualifying-but-blocked B episodes: 12 skips (distinct episodes) -> B qualifying = 10+12=22
    for i, d in enumerate(DAYS):
        evs.append(_ev(session_date=d, event_type="skip", branch="B", episode=50 + i,
                       signal_min=800, notes="skip: one unpaired leg at a time"))
    evs.append(_ev(session_date=DAYS[0], event_type="skip", branch="B", episode=90,
                   signal_min=805, notes="skip: 3 entries/day reached"))
    evs.append(_ev(session_date=DAYS[1], event_type="skip", branch="B", episode=91,
                   signal_min=806, notes="skip: short blocked: vt_broken (R4)"))
    # A-beats-B dedupe: this one must NOT count toward B qualifying
    evs.append(_ev(session_date=DAYS[2], event_type="skip", branch="B", episode=92,
                   signal_min=807, notes="skip: A beats B on the same bar"))
    # A qualifying episodes: 2 entered + 6 blocked = 8
    for i, d in enumerate(DAYS[2:8]):
        evs.append(_ev(session_date=d, event_type="skip", branch="A", episode=60 + i,
                       signal_min=810, notes="skip: one unpaired leg at a time"))
    return evs


@pytest.fixture()
def graded(config, tmp_path):
    log_p = tmp_path / "paper_log.csv"
    with open(log_p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=EVENT_FIELDS)
        w.writeheader()
        for e in _fixture_events():
            w.writerow(event_to_row(e))
    sess_p = tmp_path / "sessions.csv"
    with open(sess_p, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "disposition", "outage_min", "mode", "config_hash"])
        for d in DAYS:
            w.writerow([d, "countable", 0, "live", H])
        w.writerow(["2026-08-19", "partial", 30, "live", H])       # excluded
        w.writerow(["2026-08-20", "shakedown", 0, "shakedown", H])  # excluded
    log = pd.read_csv(log_p, dtype={"session_date": str})
    sessions = pd.read_csv(sess_p, dtype={"date": str})
    rows = stage1_filter(config, log, sessions, False, None, None)
    entries = stage2_entries(rows)
    qualify = stage3_qualify(rows)
    metrics = stage4_metrics(config, entries)
    return rows, entries, qualify, metrics


def test_stage2_and_4_hand_computed(config, graded):
    """v3 hand-golden: $ metrics; limit-replay would-have-filled; indeterminate."""
    rows, entries, qualify, metrics = graded
    assert len(entries) == 12
    assert metrics["B_entries"] == 10 and metrics["B_fills"] == 6
    assert metrics["B_censored"] == 1
    assert metrics["B_fill_rate"] == pytest.approx(6 / 9)      # censored out of denominator
    assert metrics["A_fill_rate"] == pytest.approx(1.0)
    assert metrics["max_single_trade_loss_usd"] == pytest.approx(80.0)
    assert metrics["median_scratch_loss_usd"] == pytest.approx(55.0)  # (40+70)/2
    assert metrics["would_have_filled_scratches"] == 1           # cached-day absurd limit
    assert metrics["would_have_filled_indeterminate"] == 1       # uncached day
    assert metrics["credits_usd"] == pytest.approx(80.0)         # 8 fills x $10


def test_stage3_qualify_hand_computed(graded):
    _, _, qualify, _ = graded
    assert int((qualify.branch == "B").sum()) == 22              # 10 entered + 12 blocked, A-beats-B excluded
    assert int((qualify.branch == "A").sum()) == 8
    assert 92 not in set(qualify[qualify.branch == "B"].episode)


def test_best_session_tiebreaks(graded):
    _, entries, _, _ = graded
    # DAYS[0]: B fill + A fill = 2 fills -> unique best
    assert _best_session(entries) == DAYS[0]
    # force a tie on fills: drop the A fill on DAYS[0]; DAYS[0] and DAYS[1] tie at ... 
    e2 = entries[~((entries.date == DAYS[0]) & (entries.branch == "A"))]
    # now DAYS[1] has 2 fills (B+A), all others 1 -> best is DAYS[1]
    assert _best_session(e2) == DAYS[1]
    # full tie (1 fill each, equal pnl 3.0) among DAYS[2..5] -> earliest date wins
    e3 = entries[entries.date.isin(DAYS[2:6])]
    assert _best_session(e3) == DAYS[2]


def test_stage6_criteria_statuses(config, graded):
    rows, entries, qualify, metrics = graded
    from hiro_engine.scorecard import stage5_controls
    controls = stage5_controls(config, entries)
    table = stage6_criteria(config, DAYS, entries, qualify, metrics, controls)
    t = {r.criterion: r for r in table.itertuples()}
    assert t["qualifying signals on >=7/10 sessions"].status == "PASS"     # 10/10
    assert t["1-3 executable entries on >=6/10 sessions"].status == "PASS"
    # v3 post-registration (task 18): thresholds come from CONFIG
    assert t["limit fills total"].status == "FAIL"          # 8 fills < registered floor 11
    assert t["Branch B fill rate"].status == "PASS"         # 0.667 >= registered 0.10
    assert t["<=3 entries/session"].status == "PASS"
    assert t["one leg at a time"].status == "PASS"
    assert t["Branch B qualifying signals"].status == "PASS"                # 22 >= 20
    assert t["Branch A qualifying episodes"].status == "PASS"               # 8
    assert t["would-have-filled scratches (limit replay)"].status == "PASS" # 1 <= 1
    assert "indeterminate" in str(t["would-have-filled scratches (limit replay)"].measured)
    assert t["data_invalid trades (reported, unscored)"].status == "PASS"
    # re-check rows exist and drop DAYS[0] (2 fills there)
    assert any("re-check (drop 2026-08-05)" in c for c in t)


def test_mixed_hashes_refused(config, graded, tmp_path):
    rows, *_ = graded
    log = rows.copy()
    log.loc[log.index[-1], "config_hash"] = "f" * 64
    sessions = pd.DataFrame([{"date": d, "disposition": "countable", "outage_min": 0,
                              "mode": "live", "config_hash": H} for d in DAYS])
    with pytest.raises(ScorecardError, match="different CONFIG_HASH"):
        stage1_filter(config, log, sessions, False, None, None)
