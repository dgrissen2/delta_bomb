"""Tasks 3a/3b tests: run machine fixtures + parquet equality; VWAP; context; warmup."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from hiro_engine.features import FeatureEngine, RunMachine, apply_run_machine
from hiro_engine.feeds import ReplayFeed
from hiro_engine.models import Bar, SpyBar, TIER_FULL

DAY = "2026-08-18"


# ---- 3a: run machine ---------------------------------------------------------
def test_run_machine_trough_break_reanchor():
    """Hand-built fixture: rise, then a 0.6 drop breaks the run and re-anchors."""
    rm = RunMachine(rev=0.6)
    seq = [(570, 0.0), (571, 0.2), (572, 0.5), (573, 1.0),   # run building from trough at 570
           (574, 0.5), (575, 0.35),                          # dd 0.65 >= 0.6 -> break at 575
           (576, 0.6), (577, 0.9)]                           # new run from 575
    out = [rm.update(m, L, L / 2, L / 2, L * 0.6) for m, L in seq]
    assert out[3]["run"] == pytest.approx(1.0) and out[3]["dur"] == 3
    assert not out[4]["broke"] and out[4]["dd"] == pytest.approx(0.5)
    assert out[5]["broke"] and out[5]["run"] == 0.0 and out[5]["dd"] == 0.0
    assert out[7]["run"] == pytest.approx(0.55) and out[7]["dur"] == 2  # anchored at 575
    # new trough: falling below the anchor re-anchors both
    rm2 = RunMachine(rev=0.6)
    for m, L in [(570, 1.0), (571, 0.8), (572, 0.7), (573, 1.1)]:
        r = rm2.update(m, L, 0.5, 0.5, 0.5)
    assert r["run"] == pytest.approx(0.4) and r["dur"] == 1              # trough moved to 572


def test_incremental_equals_frame_function(config):
    """RunMachine bar-for-bar == apply_run_machine on a real merged day frame."""
    import sys
    sys.path.insert(0, "scripts")
    feed = ReplayFeed(config, [DAY])
    from hiro_engine.feeds import load_hiro_day, load_spx_day
    hiro = load_hiro_day(config.path_of("hiro_root"), DAY)
    spx = load_spx_day(config.path_of("spx_dir"), DAY)
    df = hiro.merge(spx, on="min", how="inner").reset_index(drop=True)
    frame = apply_run_machine(df.copy(), rev=0.6)
    rm = RunMachine(rev=0.6)
    for i, r in enumerate(df.itertuples()):
        got = rm.update(int(r.min), r.all_L, r.all_Lc, r.all_Lp, r.nextExp_L)
        for k, col in [("run", "run"), ("dur", "dur"), ("dC", "dC"), ("dP", "dP"),
                       ("dN", "dN"), ("dd", "dd"), ("rate", "rate")]:
            assert got[k] == pytest.approx(frame[col].iloc[i], abs=1e-9), (i, k)
        assert got["broke"] == bool(frame.broke.iloc[i]), i


def test_run_values_match_dashboard_parquet(config):
    """Engine features on a stored day == the research dashboard parquet (task 3a golden)."""
    from hiro_engine.config import REPO_ROOT
    ref = pd.read_parquet(REPO_ROOT / f"docs/dashboard/hiro_setup_{DAY}.parquet")
    feed = ReplayFeed(config, [DAY])
    eng = FeatureEngine(config, TIER_FULL, range60_history=[0.0] * 300)
    rows = [eng.update(t.bar, t.hiro, t.spy_bar) for t in feed.iter_day(DAY)]
    by_min = {r.min: r for r in rows}
    ref = ref[ref["min"].isin(by_min)]
    for rec in ref.itertuples():
        row = by_min[int(rec.min)]
        assert row.L == pytest.approx(rec.all_L, abs=1e-9)
        assert row.run == pytest.approx(rec.run, abs=1e-9)
        assert row.dur == pytest.approx(rec.dur, abs=1e-9)
        assert row.dC == pytest.approx(rec.dC, abs=1e-9)
        assert row.dN == pytest.approx(rec.dN, abs=1e-9)
        assert row.run_broke == bool(rec.broke)
        if not np.isnan(rec.r15):
            assert row.r15 == pytest.approx(rec.r15, abs=1e-9)


# ---- 3b: price, VWAP, context, warmup -----------------------------------------
def _bar(m, o, h, l, c):
    return Bar(m, o, h, l, c)


def test_vwap_hand_computed(config):
    eng = FeatureEngine(config, TIER_FULL)
    spy = [SpyBar(570, 10, 12, 8, 10, 100), SpyBar(571, 10, 11, 9, 11, 300)]
    r1 = eng.update(_bar(570, 100, 101, 99, 100), None, spy[0])
    assert r1.vwap == pytest.approx(10.0)                      # tp=10, single bar
    r2 = eng.update(_bar(571, 100, 101, 99, 100), None, spy[1])
    tp2 = (11 + 9 + 11) / 3
    assert r2.vwap == pytest.approx((10 * 100 + tp2 * 300) / 400)


def test_context_reads(config):
    """UP context at 10:30 with IM present; CHOP when IM missing."""
    for im, expect in [(20.0, "UP"), (None, "CHOP")]:
        eng = FeatureEngine(config, TIER_FULL, im=im)
        px = 100.0
        for m in range(570, 631):
            px += 0.2                                          # steady uptrend
            spy = SpyBar(m, px, px + 0.1, px - 0.5, px, 100)   # closes above vwap
            row = eng.update(_bar(m, px - 0.2, px + 0.1, px - 0.3, px), None, spy)
        assert row.context_1030 == expect
        assert row.context_1300 is None


def test_warmup_and_range60_pct(config):
    hist = [1.0] * 299
    eng = FeatureEngine(config, TIER_FULL, range60_history=hist)
    row = eng.update(_bar(570, 100, 101, 99, 100), None, None)
    assert row.warmup and row.range60_pct is None
    eng2 = FeatureEngine(config, TIER_FULL, range60_history=[float(i) for i in range(1, 401)])
    row2 = eng2.update(_bar(570, 100, 101, 99, 100), None, None)
    assert not row2.warmup
    assert row2.range60_pct == pytest.approx(np.quantile(np.arange(1.0, 401.0), 0.75))


def test_strict_30bar_windows(config):
    eng = FeatureEngine(config, TIER_FULL, range60_history=[0.0] * 300)
    rows = [eng.update(_bar(570 + i, 100 + i * 0.1, 100.2 + i * 0.1, 99.8 + i * 0.1,
                            100 + i * 0.1), None, None) for i in range(31)]
    assert rows[28].pull30 is None                             # < 30 bars: undefined
    assert rows[29].pull30 is not None and rows[30].bounce30 == pytest.approx(2.9, abs=1e-9)
