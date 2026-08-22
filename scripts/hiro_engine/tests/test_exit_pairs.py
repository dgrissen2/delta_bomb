"""Fix for red-team finding 10: EVERY feasible pair of simultaneously-firing
exits — the higher-precedence one wins (R7.0 order: fill > scratch > cap >
veto_exit > state_flip > clock > resolution). Infeasible pairs are documented."""
from __future__ import annotations

import pytest

from hiro_engine.models import EngineState, SimTrade, TIER_FULL, Vetoes
from hiro_engine.rules import RuleEngine

from helpers import mk_row


def _trade(side, branch, entry_min, s0, **kw):
    d = dict(id=1, branch=branch, side=side, signal_min=entry_min - 1, entry_min=entry_min,
             s0=s0, expiry=None, leg_strikes=None, entry_option_mid=None,
             resting_limit_ref=None,
             target=s0 + 3 if side == "sell_first" else s0 - 3,
             bh_level=None, entry_L=None, cap_source="proxy", cap_value=15.0, episode=1)
    d.update(kw)
    return SimTrade(**d)


# Each case: (name, expected_winner, trade_kwargs, row_kwargs)
# The row is constructed so that BOTH named exit conditions hold at that bar.
CASES = [
    # ---- fill beats everything it can co-occur with
    ("fill+scratchB", "fill",
     dict(side="sell_first", branch="B", entry_min=700, s0=100.0, entry_L=1.0),
     dict(m=701, close=101.0, high=103.5, L=0.5)),
    ("fill+scratchA_bh", "fill",
     dict(side="long_first", branch="A", entry_min=700, s0=100.0, bh_level=100.5),
     dict(m=705, close=98.0, high=101.0, low=96.9)),
    ("fill+cap", "fill",
     dict(side="sell_first", branch="B", entry_min=700, s0=100.0),
     dict(m=710, close=84.0, high=103.2, low=83.0)),          # touch AND 16 pts against at close
    ("fill+veto_exit", "fill",
     dict(side="sell_first", branch="B", entry_min=700, s0=100.0),
     dict(m=710, close=101.0, high=103.2, vetoes=Vetoes(flow_veto=True))),
    ("fill+state_flip", "fill",
     dict(side="sell_first", branch="B", entry_min=777, s0=100.0),
     dict(m=780, close=101.0, high=103.1, context_1300="DOWN")),
    ("fill+clock", "fill",
     dict(side="sell_first", branch="B", entry_min=700, s0=100.0),
     dict(m=760, close=101.0, high=103.4)),
    ("fill+resolution", "fill",
     dict(side="sell_first", branch="B", entry_min=869, s0=100.0),
     dict(m=930, close=101.0, high=103.4)),
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
    ("scratchA+clock", "scratch",                              # A-scratch has no window
     dict(side="long_first", branch="A", entry_min=700, s0=100.0, bh_level=100.5),
     dict(m=760, close=100.0, high=100.9, low=99.5)),
    ("scratchA+resolution", "scratch",
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
