"""Task 4 tests — table-driven: one fixture per rule; exit precedence pairs;
entry blocked by each veto; one entry per episode."""
from __future__ import annotations

import pytest

from hiro_engine_v2.models import (EngineState, SimTrade, TIER_FULL, TIER_PRICE, Vetoes)
from hiro_engine_v2.rules import RuleEngine

from helpers import a_fire_row, b_fire_row, mk_row, qv, resting_trade


def _engine(config, tier=TIER_FULL):
    return RuleEngine(config, tier)


def _types(evs):
    return [e.event_type for e in evs]


def _open_trade(side="sell_first", branch="B", entry_min=700, s0=100.0, **kw) -> SimTrade:
    d = dict(id=1, branch=branch, side=side, signal_min=entry_min - 1, entry_min=entry_min,
             s0=s0, expiry=None, leg_strikes=None, entry_option_mid=None,
             resting_limit_ref=None, target=s0 + 3 if side == "sell_first" else s0 - 3,
             bh_level=None, entry_L=1.0, cap_source="proxy", cap_value=15.0, episode=1)
    d.update(kw)
    return SimTrade(**d)


# ---- entries ------------------------------------------------------------------
def test_branch_b_signal_fires(config):
    evs = _engine(config).evaluate(b_fire_row(700), EngineState())
    assert "signal" in _types(evs) and "pending_entry" in _types(evs)
    sig = next(e for e in evs if e.event_type == "signal")
    assert sig.branch == "B" and sig.side == "sell_first" and sig.s0 is None  # S0 unknowable


def test_branch_a_signal_fires_and_beats_b(config):
    row = a_fire_row(700, b_armed=True, b_gates=True, episode_b=4)
    evs = _engine(config).evaluate(row, EngineState())
    sig = [e for e in evs if e.event_type == "signal"]
    assert len(sig) == 1 and sig[0].branch == "A"
    assert any("A beats B" in e.notes for e in evs if e.event_type == "skip")


def test_windows(config):
    eng = _engine(config)
    assert "signal" not in _types(eng.evaluate(b_fire_row(599), EngineState()))   # observe-only
    assert "signal" in _types(_engine(config).evaluate(b_fire_row(600), EngineState()))
    assert "signal" not in _types(_engine(config).evaluate(b_fire_row(871), EngineState()))
    assert "signal" not in _types(_engine(config).evaluate(a_fire_row(634), EngineState()))  # A >= 10:35
    assert "signal" in _types(_engine(config).evaluate(a_fire_row(635), EngineState()))


@pytest.mark.parametrize("veto", ["vt_broken", "levels_invalid", "flow_veto"])
def test_each_veto_blocks_branch_b(config, veto):
    row = b_fire_row(700, vetoes=Vetoes(**{veto: True}))
    evs = _engine(config).evaluate(row, EngineState())
    assert "signal" not in _types(evs)
    assert any(veto in e.notes for e in evs if e.event_type == "skip")


def test_vetoes_never_block_branch_a(config):
    row = a_fire_row(700, vetoes=Vetoes(vt_broken=True, levels_invalid=True, flow_veto=True))
    evs = _engine(config).evaluate(row, EngineState())
    assert "signal" in _types(evs)          # R4.1-R4.3 only block SHORT legs


def test_late_suppression_one_line_per_episode(config):
    eng = _engine(config)
    row = b_fire_row(700, late_state=True)
    evs1 = eng.evaluate(row, EngineState())
    assert "late_no_entry" in _types(evs1) and "signal" not in _types(evs1)
    evs2 = eng.evaluate(b_fire_row(701, late_state=True), EngineState())
    assert "late_no_entry" not in _types(evs2)                    # same episode, one line
    evs3 = eng.evaluate(b_fire_row(720, episode=2, late_state=True), EngineState())
    assert "late_no_entry" in _types(evs3)                        # new episode


def test_one_entry_per_episode_and_daily_cap(config):
    eng = _engine(config)
    st = EngineState(entered_episode_b=1)
    assert "signal" not in _types(eng.evaluate(b_fire_row(700, episode=1), st))
    assert "signal" in _types(_engine(config).evaluate(b_fire_row(700, episode=2), st))
    st2 = EngineState(entries_today=3)
    evs = _engine(config).evaluate(b_fire_row(700), st2)
    assert "signal" not in _types(evs)
    assert any("3 entries/day" in e.notes for e in evs if e.event_type == "skip")


def test_one_leg_at_a_time_skip(config):
    st = EngineState(open_trade=_open_trade())
    evs = _engine(config).evaluate(b_fire_row(700, episode=2), st)
    assert "signal" not in _types(evs)
    assert any("one unpaired leg" in e.notes for e in evs if e.event_type == "skip")


def test_gate_fail_once_per_armed_episode(config):
    eng = _engine(config)
    row = b_fire_row(700, b_gates=False, r15=-0.1)
    evs = eng.evaluate(row, EngineState())
    assert "gate_fail" in _types(evs)
    assert "r15<=0" in next(e for e in evs if e.event_type == "gate_fail").notes
    assert "gate_fail" not in _types(eng.evaluate(b_fire_row(701, b_gates=False, r15=-0.1),
                                                  EngineState()))


def test_price_tier_disables_branch_b(config):
    evs = _engine(config, TIER_PRICE).evaluate(b_fire_row(700), EngineState())
    assert "signal" not in _types(evs)


# ---- exits: precedence pairs -----------------------------------------------------
def _exit_type(evs):
    e = [e for e in evs if e.event_type == "exit_decision"]
    return e[0].outcome_type if e else None


def test_fill_beats_scratch(config):
    """v3 MIGRATION (15g: RE-PARAMETERIZED): marketable partner quote AND a
    flow drop on the same close -> fill wins (fixture S4 covers the full path)."""
    tr = resting_trade(entry_min=700, entry_L=1.0)
    st = EngineState(open_trade=tr)
    row = mk_row(701, close=101.0, L=0.6, run_broke=True,
                 quote_view=qv(701, leg2=(39.5, 39.9)))
    assert _exit_type(_engine(config).evaluate(row, st)) == "fill"


def test_scratch_beats_cap(config):
    tr = _open_trade(entry_min=700, s0=120.0, entry_L=1.0,
                     target=123.0)
    st = EngineState(open_trade=tr)
    row = mk_row(702, close=104.0, high=104.5, L=0.6)     # 16 pts against AND flow drop
    assert _exit_type(_engine(config).evaluate(row, st)) == "scratch"


def test_cap_beats_veto_exit(config):
    tr = _open_trade(entry_min=700, s0=120.0, target=123.0)
    st = EngineState(open_trade=tr)
    row = mk_row(710, close=104.0, high=104.5, r15=-1.0, r15n=-1.0,
                 vetoes=Vetoes(flow_veto=True))
    assert _exit_type(_engine(config).evaluate(row, st)) == "cap"


def test_veto_exit_beats_state_flip(config):
    tr = _open_trade(entry_min=770, s0=100.0)
    st = EngineState(open_trade=tr)
    row = mk_row(780, close=99.0, vetoes=Vetoes(flow_veto=True), context_1300="DOWN")
    assert _exit_type(_engine(config).evaluate(row, st)) == "veto_exit"


def test_state_flip_beats_clock(config):
    tr = _open_trade(entry_min=720, s0=100.0)
    st = EngineState(open_trade=tr)
    row = mk_row(780, close=99.0, context_1300="DOWN")
    assert _exit_type(_engine(config).evaluate(row, st)) == "state_flip"


def test_state_flip_side_mapping(config):
    st = EngineState(open_trade=_open_trade(side="long_first", branch="A", entry_min=770,
                                            target=97.0))
    row = mk_row(780, close=101.0, context_1300="UP", low=100.5)
    assert _exit_type(_engine(config).evaluate(row, st)) == "state_flip"
    # CHOP never triggers it
    st2 = EngineState(open_trade=_open_trade(entry_min=770))
    row2 = mk_row(780, close=100.0, context_1300="CHOP")
    assert _exit_type(_engine(config).evaluate(row2, st2)) is None


def test_clock_beats_resolution_only_before_1530(config):
    st = EngineState(open_trade=_open_trade(entry_min=700, s0=100.0))
    assert _exit_type(_engine(config).evaluate(mk_row(760, close=100.0), st)) == "clock"
    # a 14:30 entry: at 15:30 the resolution overrides the pending clock (R5.4)
    st2 = EngineState(open_trade=_open_trade(entry_min=871, s0=100.0))
    assert _exit_type(_engine(config).evaluate(mk_row(930, close=100.0), st2)) == "resolution"


def test_branch_a_has_no_scratch(config):
    """v2.3: Branch A has NO scratch — a high above the old bounce high does
    NOTHING; only fill/cap/clock/resolution exit an A leg (R7.2)."""
    tr = _open_trade(side="long_first", branch="A", entry_min=700, s0=100.0,
                     target=97.0, bh_level=101.0, entry_L=None)
    st = EngineState(open_trade=tr)
    row = mk_row(710, close=100.9, high=101.2, low=100.5)
    assert _exit_type(_engine(config).evaluate(row, st)) is None


def test_b_scratch_window_closes(config):
    tr = _open_trade(entry_min=700, s0=100.0, entry_L=1.0)
    st = EngineState(open_trade=tr)
    row = mk_row(704, close=100.0, L=0.6)                 # 4 min after entry: window shut
    assert _exit_type(_engine(config).evaluate(row, st)) is None


def test_heartbeat_every_5_min(config):
    st = EngineState(open_trade=_open_trade(entry_min=700, s0=100.0))
    evs = _engine(config).evaluate(mk_row(705, close=100.0), st)
    assert "heartbeat" in _types(evs)
    assert "heartbeat" not in _types(_engine(config).evaluate(mk_row(706, close=100.0), st))
