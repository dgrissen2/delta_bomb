"""Task 9 tests: tier differences, unknown knob rejected, leaderboard grey-out,
bootstrap determinism, cap-variant config plumbing."""
from __future__ import annotations

import io

import numpy as np
import pandas as pd
import pytest

from hiro_engine.summarize import bootstrap_fill_ci, leaderboard
from hiro_engine.sweep import WHITELIST, _variant_config, run_sweep


def _entries(n_days=6, fills=12, scratches=4, censored=2):
    rows = []
    days = [f"2026-08-{d:02d}" for d in range(5, 5 + n_days)]
    i = 0
    for k in range(fills + scratches + censored):
        et = "fill" if k < fills else ("scratch" if k < fills + scratches else "censored")
        rows.append(dict(date=days[k % n_days], trade_id=k, branch="B", side="sell_first",
                         signal_min=700 + k, entry_min=701 + k, s0=100.0, episode=k,
                         exit_type=et, exit_ref=103.0 if et == "fill" else 99.0,
                         minutes=5.0 if et == "fill" else None, adverse=1.0, pnl=3.0))
    return pd.DataFrame(rows)


def test_bootstrap_deterministic_and_sane():
    e = _entries()
    lo1, hi1 = bootstrap_fill_ci(e)
    lo2, hi2 = bootstrap_fill_ci(e)
    assert (lo1, hi1) == (lo2, hi2)                    # seed 42 fixed
    rate = 12 / 16                                     # censored excluded
    assert lo1 <= rate <= hi1


def test_leaderboard_greys_small_cells(capsys):
    rows = [dict(variant="v_big", trades=20, days=6, fills=12, fill_rate=0.6,
                 fill_ci90_lo=0.4, fill_ci90_hi=0.8, censored=0, episodes=20),
            dict(variant="v_small", trades=5, days=6, fills=5, fill_rate=1.0,
                 fill_ci90_lo=1.0, fill_ci90_hi=1.0, censored=0, episodes=5),
            dict(variant="v_fewdays", trades=30, days=3, fills=30, fill_rate=1.0,
                 fill_ci90_lo=1.0, fill_ci90_hi=1.0, censored=0, episodes=30)]
    df = leaderboard(rows)
    out = capsys.readouterr().out
    assert "3 cells examined" in out and "2 greyed out" in out
    assert list(df[df.eligible].variant) == ["v_big"]  # perfect small cells excluded from ranking


def test_unknown_knob_rejected(config):
    assert run_sweep(config, "fill_touch_pts") == 2    # not in the R13.2 whitelist


def test_whitelist_is_exactly_r13_2():
    assert set(WHITELIST) == {"scratch_drop", "scratch_window", "pullback", "cap", "clock"}
    assert WHITELIST["scratch_drop"]["values"] == [0.2, 0.3, 0.4, 0.5, 0.6]
    assert WHITELIST["scratch_window"]["values"] == [2, 3, 4, 5]
    assert WHITELIST["pullback"]["values"] == [3, 5, 8]
    assert WHITELIST["cap"]["values"] == [3.0, 3.25, 3.5, 3.75, 4.0]
    assert WHITELIST["clock"]["values"] == [45, 60, 75]


def test_variant_config_changes_hash_and_value(config):
    v = _variant_config(config, "clock", 45)
    assert v.i("r5_clock", "clock_minutes") == 45
    assert v.config_hash != config.config_hash
    c = _variant_config(config, "cap", 4.0)
    assert c.num("r7_exits", "cap_option_pts") == 4.0
    assert c.num("r7_exits", "cap_spot_pts") == pytest.approx(4.0 * 15.0 / 3.5)


def test_tier_differences_enumerated(config, tmp_path):
    """Same fixture day under full vs price shows exactly the R13.1 differences."""
    from hiro_engine.backtest import run_backtest
    from hiro_engine.eventlog import EventLog
    from hiro_engine.models import TIER_FULL, TIER_PRICE
    import hiro_engine.session as sm
    outs = {}
    orig = sm.Session._write_session_row
    sm.Session._write_session_row = lambda self, r: None
    try:
        for tier in (TIER_FULL, TIER_PRICE):
            p = tmp_path / f"{tier.name}.csv"
            log = EventLog(p, console=io.StringIO(), echo=False)
            run_backtest(config, tier, ["2026-08-19"], log, prereg_override=True)
            log.close()
            outs[tier.name] = pd.read_csv(p)
    finally:
        sm.Session._write_session_row = orig
    full, price = outs["full"], outs["price"]
    assert set(full.tier) == {"full"} and set(price.tier) == {"price"}
    # Branch B disabled in price tier
    assert not len(price[(price.event_type == "signal") & (price.branch == "B")])
    # R4.3 flow veto disabled in price tier: no flow_veto veto_change lines
    assert not any("flow_veto=True" in str(n) for n in price[price.event_type == "veto_change"].notes)
    assert price.iloc[0].schema_v == 2   # v3 MIGRATION (15g: UPDATED): schema bumped, additive
