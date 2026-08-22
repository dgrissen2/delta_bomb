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
                   minutes=None, episode=1):
        nonlocal tid
        tid += 1
        evs.append(_ev(session_date=date, event_type="signal", branch=branch, side=side,
                       signal_min=sig, episode=episode))
        evs.append(_ev(session_date=date, event_type="entry", branch=branch, side=side,
                       trade_id=tid, signal_min=sig, entry_min=sig + 1, s0=s0,
                       episode=episode, target=s0 + 3 if side == "sell_first" else s0 - 3,
                       cap_source="proxy", cap_value=15.0))
        evs.append(_ev(session_date=date, event_type="exit", branch=branch, side=side,
                       trade_id=tid, signal_min=sig, entry_min=sig + 1, s0=s0,
                       episode=episode, outcome_type=exit_type, exit_ref=exit_ref,
                       outcome_minutes=minutes, adverse=adverse))

    # Branch B: 10 executable entries across the 10 days
    #  6 fills, 2 scratches, 1 timeout, 1 censored  -> fill rate 6/9 (censored excluded)
    for i, d in enumerate(DAYS[:6]):                       # 6 fills, one per day
        entry_exit(d, "B", "sell_first", 700 + i, 100.0, "fill", 103.0, 1.0, minutes=5)
    # scratch #1: S0 far BELOW the tape -> +3 touch would certainly have printed
    entry_exit(DAYS[6], "B", "sell_first", 700, 1000.0, "scratch", 999.0, 1.0)
    # scratch #2: S0 far ABOVE the tape -> would never fill;  loss 2 pts
    entry_exit(DAYS[7], "B", "sell_first", 700, 99999.0, "scratch", 99997.0, 2.0)
    entry_exit(DAYS[8], "B", "sell_first", 700, 100.0, "timeout", 99.0, 11.5)  # 1 adverse>10
    entry_exit(DAYS[9], "B", "sell_first", 700, 100.0, "censored", 100.5, 0.5)
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
    rows, entries, qualify, metrics = graded
    assert len(entries) == 12
    assert metrics["B_entries"] == 10 and metrics["B_fills"] == 6
    assert metrics["B_censored"] == 1
    assert metrics["B_fill_rate"] == pytest.approx(6 / 9)      # censored out of denominator
    assert metrics["A_fill_rate"] == pytest.approx(1.0)
    assert metrics["adverse_gt10_n"] == 1
    assert metrics["median_scratch_loss"] == pytest.approx(1.5)  # losses 1.0 and 2.0
    assert metrics["would_have_filled_scratches"] == 1           # only the S0=1000 one


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
    assert t[">=8 fills total"].status == "PASS"                            # 8 fills
    assert t["<=3 entries/session"].status == "PASS"
    assert t["Branch B qualifying signals"].status == "PASS"                # 22 >= 20
    assert t["Branch B fill rate"].status == "PASS"                         # 0.667 >= 0.45
    assert t["Branch A qualifying episodes"].status == "PASS"               # 8
    assert t["Branch A fill rate"].status == "PASS"                         # 1.0
    assert t["adverse > 10 pts"].status == "PASS"                           # exactly 1, 1/11<=10%... 
    assert t["median scratch loss"].status == "PASS"
    assert t["would-have-completed scratches"].status == "PASS"             # 1 <= 1
    # re-check rows exist and drop DAYS[0]
    assert any("re-check (drop 2026-08-05)" in c for c in t)


def test_mixed_hashes_refused(config, graded, tmp_path):
    rows, *_ = graded
    log = rows.copy()
    log.loc[log.index[-1], "config_hash"] = "f" * 64
    sessions = pd.DataFrame([{"date": d, "disposition": "countable", "outage_min": 0,
                              "mode": "live", "config_hash": H} for d in DAYS])
    with pytest.raises(ScorecardError, match="different CONFIG_HASH"):
        stage1_filter(config, log, sessions, False, None, None)
