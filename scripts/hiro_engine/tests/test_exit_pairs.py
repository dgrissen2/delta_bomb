"""Fix for red-team finding 10: EVERY feasible pair of simultaneously-firing
exits — the higher-precedence one wins (R7.0 order: fill > scratch > cap >
veto_exit > state_flip > clock > resolution). Infeasible pairs are documented."""
from __future__ import annotations

import pytest

from hiro_engine.models import EngineState, SimTrade, TIER_FULL, Vetoes
from hiro_engine.rules import RuleEngine

from helpers import mk_row, qv, resting_trade


def _trade(side, branch, entry_min, s0, **kw):
    """v3 MIGRATION (15g table: RE-PARAMETERIZED): pairs now use a resting-limit
    trade; 'fill' condition = marketable partner quote instead of an SPX touch.
    Old SPX kwargs (target etc.) are mapped onto the v3 trade."""
    kw.pop("target", None)
    entry_L = kw.pop("entry_L", 1.0 if branch == "B" else None)
    bh = kw.pop("bh_level", None)
    return resting_trade(side=side, branch=branch, entry_min=entry_min,
                         entry_L=entry_L, bh_level=bh, s0=s0, cap_source="proxy",
                         cap_value=15.0, **kw)


# Each case: (name, expected_winner, trade_kwargs, row_kwargs)
# The row is constructed so that BOTH named exit conditions hold at that bar.
CASES = [
    # ---- fill beats everything it can co-occur with
    ("fill+scratchB", "fill",
     dict(side="sell_first", branch="B", entry_min=700, s0=100.0, entry_L=1.0),
     dict(m=701, close=101.0, L=0.5, quote_view=qv(701, leg2=(39.5, 39.9)))),
    ("fill+high_above_old_bh (A: no scratch, v2.3)", "fill",
     dict(side="long_first", branch="A", entry_min=700, s0=100.0, bh_level=100.5,
          leg1_fill=40.25, L=40.40, k2=7495.0),
     dict(m=705, close=98.0, high=101.0, low=96.9,
          quote_view=qv(705, k2=7495.0, leg2=(40.4, 40.8)))),
    ("fill+cap", "fill",
     dict(side="sell_first", branch="B", entry_min=700, s0=100.0),
     dict(m=710, close=84.0, low=83.0,
          quote_view=qv(710, leg1=(44.0, 44.4), leg2=(39.5, 39.9)))),  # marketable AND mid 4.2 over fill
    ("fill+veto_exit", "fill",
     dict(side="sell_first", branch="B", entry_min=700, s0=100.0),
     dict(m=710, close=101.0, vetoes=Vetoes(flow_veto=True),
          quote_view=qv(710, leg2=(39.5, 39.9)))),
    ("fill+state_flip", "fill",
     dict(side="sell_first", branch="B", entry_min=777, s0=100.0),
     dict(m=780, close=101.0, context_1300="DOWN",
          quote_view=qv(780, leg2=(39.5, 39.9)))),
    ("fill+clock", "fill",
     dict(side="sell_first", branch="B", entry_min=700, s0=100.0),
     dict(m=760, close=101.0, quote_view=qv(760, leg2=(39.5, 39.9)))),
    ("fill+resolution", "fill",
     dict(side="sell_first", branch="B", entry_min=869, s0=100.0),
     dict(m=930, close=101.0, quote_view=qv(930, leg2=(39.5, 39.9)))),
    # ---- scratch beats cap / veto / flip / clock / resolution
    ("scratchB+cap", "scratch",
     dict(side="sell_first", branch="B", entry_min=700, s0=120.0, entry_L=1.0),
     dict(m=702, close=104.0, high=104.5, L=0.5)),
    ("scratchB+veto_exit", "scratch",
     dict(side="sell_first", branch="B", entry_min=700, s0=100.0, entry_L=1.0),
     dict(m=702, close=99.0, L=0.5, vetoes=Vetoes(flow_veto=True))),
    ("scratchB+state_flip", "scratch",
     dict(side="sell_first", branch="B", entry_min=778, s0=100.0, entry_L=1.0),
     dict(m=780, close=99.0, L=0.5, context_1300="DOWN")),
    ("A_high_above_old_bh+clock -> clock (no A-scratch, v2.3)", "clock",
     dict(side="long_first", branch="A", entry_min=700, s0=100.0, bh_level=100.5),
     dict(m=760, close=100.0, high=100.9, low=99.5)),
    ("A_high_above_old_bh+resolution -> resolution (v2.3)", "resolution",
     dict(side="long_first", branch="A", entry_min=869, s0=100.0, bh_level=100.5),
     dict(m=930, close=100.0, high=100.9, low=99.5)),
    # ---- cap beats veto / flip / clock / resolution
    ("cap+veto_exit", "cap",
     dict(side="sell_first", branch="B", entry_min=700, s0=120.0),
     dict(m=710, close=104.0, high=104.5, vetoes=Vetoes(flow_veto=True))),
    ("cap+state_flip", "cap",
     dict(side="sell_first", branch="B", entry_min=770, s0=120.0),
     dict(m=780, close=104.0, high=104.5, context_1300="DOWN")),
    ("cap+clock", "cap",
     dict(side="sell_first", branch="B", entry_min=700, s0=120.0),
     dict(m=760, close=104.0, high=104.5)),
    ("cap+resolution", "cap",
     dict(side="sell_first", branch="B", entry_min=869, s0=120.0),
     dict(m=930, close=104.0, high=104.5)),
    # ---- veto_exit beats flip / clock / resolution
    ("veto_exit+state_flip", "veto_exit",
     dict(side="sell_first", branch="B", entry_min=770, s0=100.0),
     dict(m=780, close=99.0, vetoes=Vetoes(flow_veto=True), context_1300="DOWN")),
    ("veto_exit+clock", "veto_exit",
     dict(side="sell_first", branch="B", entry_min=700, s0=100.0),
     dict(m=760, close=99.0, vetoes=Vetoes(flow_veto=True))),
    ("veto_exit+resolution", "veto_exit",
     dict(side="sell_first", branch="B", entry_min=869, s0=100.0),
     dict(m=930, close=99.0, vetoes=Vetoes(flow_veto=True))),
    # ---- state_flip beats clock
    ("state_flip+clock", "state_flip",
     dict(side="sell_first", branch="B", entry_min=720, s0=100.0),
     dict(m=780, close=99.0, context_1300="DOWN")),
    # clock+resolution is infeasible by construction: clock only fires m < 15:30
    # and resolution only at m >= 15:30 (R5.4 override tested in test_rules.py);
    # state_flip+resolution infeasible (13:00 read vs 15:30 bar).
]


@pytest.mark.parametrize("name,winner,tkw,rkw", CASES, ids=[c[0] for c in CASES])
def test_exit_pair(config, name, winner, tkw, rkw):
    st = EngineState(open_trade=_trade(**tkw))
    m = rkw.pop("m")
    row = mk_row(m, **rkw)
    evs = RuleEngine(config, TIER_FULL).evaluate(row, st)
    decisions = [e for e in evs if e.event_type == "exit_decision"]
    assert len(decisions) == 1, f"{name}: expected one decision"
    assert decisions[0].outcome_type == winner, name


def test_a_breach_plus_cap_cap_wins(config):
    """codex v2.3 finding 3: with no A-scratch, the cap is the load-bearing
    protective exit on an A leg — a bounce-high breach AND a 15-pt adverse
    close on the same bar -> cap fires (nothing else)."""
    tr = _trade(side="long_first", branch="A", entry_min=700, s0=100.0,
                target=97.0, bh_level=100.5)
    st = EngineState(open_trade=tr)
    row = mk_row(710, close=116.0, high=116.5, low=99.0)   # breach + 16 pts against
    evs = RuleEngine(config, TIER_FULL).evaluate(row, st)
    d = [e for e in evs if e.event_type == "exit_decision"]
    assert len(d) == 1 and d[0].outcome_type == "cap"


def test_bh_level_telemetry_split(config):
    """v2.3 telemetry contract: the A SIGNAL event carries bh_level as a
    diagnostic; the pending entry (and therefore the trade) does NOT."""
    from helpers import a_fire_row
    evs = RuleEngine(config, TIER_FULL).evaluate(a_fire_row(700, bh_level=101.25),
                                                 EngineState())
    sig = next(e for e in evs if e.event_type == "signal")
    pend = next(e for e in evs if e.event_type == "pending_entry")
    assert sig.bh_level == 101.25
    assert pend.bh_level is None
