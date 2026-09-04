"""compare.py on a hand-written two-session log: joins, firewall, LB95, checkpoint guard, book, verdict paths."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from hiro_engine.models import EVENT_FIELDS
from hiro_watch import compare as C


def _ev(**kw) -> dict:
    row = {f: "" for f in EVENT_FIELDS}
    row.update(mode="backtest", tier="full", config_hash="h", schema_v="2", health="OK")
    row.update({k: str(v) for k, v in kw.items()})
    return row


def _log(rows: list[dict]) -> pd.DataFrame:
    ev = pd.DataFrame(rows, columns=EVENT_FIELDS)
    for c in C.NUM:
        ev[c] = pd.to_numeric(ev[c], errors="coerce")
    return ev


D1, D2 = "2026-09-08", "2026-09-09"


def _base_log() -> pd.DataFrame:
    """D1: A signal (r30 -4.5) → entry 1 → fill. D2: A signal (r30 -0.3) → entry 1 → timeout −110;
    B setup refused vt_broken (episode 2)."""
    return _log([
        _ev(session_date=D1, event_type="banner", rule_id="R8.2"),
        _ev(session_date=D1, event_type="signal", rule_id="R6.1", branch="A", signal_min=640, episode=1, r15=-1.2,
            notes="SIGNAL A LONG-FIRST | range60=30>=p75 12 r30=-4.50 bounce30=4 close<mid30"),
        _ev(session_date=D1, event_type="entry", rule_id="R1.4", branch="A", side="long_first", signal_min=640,
            entry_min=641, episode=1, trade_id=1, k1=7500.0, k2=7495.0, expiry="2026-10-09", leg1_fill=30.0),
        _ev(session_date=D1, event_type="exit", rule_id="R7.1", branch="A", trade_id=1, leg2_fill=30.1,
            outcome_type="fill", outcome_minutes=12, pnl_usd=10.0, leg_liq_loss_usd=40.0),
        _ev(session_date=D1, event_type="disposition", rule_id="R10.3", notes="session countable | outage 0m"),
        _ev(session_date=D2, event_type="banner", rule_id="R8.2"),
        _ev(session_date=D2, event_type="signal", rule_id="R6.1", branch="A", signal_min=700, episode=1, r15=-0.1,
            notes="SIGNAL A LONG-FIRST | range60=30>=p75 12 r30=-0.30 bounce30=4 close<mid30"),
        _ev(session_date=D2, event_type="entry", rule_id="R1.4", branch="A", side="long_first", signal_min=700,
            entry_min=701, episode=1, trade_id=1, k1=7400.0, k2=7395.0, expiry="2026-10-09", leg1_fill=28.0),
        _ev(session_date=D2, event_type="exit", rule_id="R7.5", branch="A", trade_id=1, outcome_type="timeout",
            pnl_usd=-110.0, leg_liq_loss_usd=140.0),
        _ev(session_date=D2, event_type="skip", rule_id="R4.1", branch="B", signal_min=720, episode=2,
            notes="skip: short blocked: vt_broken (R4.1)"),
        _ev(session_date=D2, event_type="disposition", rule_id="R10.3", notes="session countable | outage 0m"),
    ])


def test_trades_joins_entry_and_exit():
    t = C.trades(_base_log())
    assert len(t) == 2 and t.bomb.tolist() == [True, False]
    assert t.k_long.tolist() == [7500.0, 7400.0] and t.k_short.tolist() == [7495.0, 7395.0]
    assert t.mae.tolist() == [-40.0, -140.0] and t.pnl_usd.sum() == -100.0


def test_trades_refuses_entry_without_exit():
    ev = _base_log()
    with pytest.raises(SystemExit):
        C.trades(ev[ev.event_type != "exit"])


def test_signals_parse_r30_and_refusals_reasons():
    s = C.signals(_base_log())
    assert s.r30.tolist() == [-4.5, -0.3]
    r = C.refusals(_base_log())
    assert r.reason.tolist() == ["vt_broken"] and int(r.signal_min.iloc[0]) == 720


def test_firewall_label():
    lab = C.label(pd.Series([D1, D2]), registered=D1)
    assert lab.tolist() == ["DISCOVERY", "CONFIRMATION"]


def test_checkpoint_guard():
    assert not C.checkpoint(9) and C.checkpoint(10) and not C.checkpoint(11) and C.checkpoint(40)


def test_lb95_bounds():
    ten_of_ten = pd.DataFrame(dict(session_date=[f"d{i}" for i in range(10)], fills=[1] * 10, n=[1] * 10))
    assert 0.7 < C.lb95(ten_of_ten) < 1.0                     # Clopper-Pearson floors the 1.0 artefact
    none = pd.DataFrame(dict(session_date=["d0", "d1"], fills=[0, 0], n=[5, 5]))
    assert C.lb95(none) == 0.0
    assert C.lb95(pd.DataFrame(dict(session_date=[], fills=[], n=[]))) == 0.0


class _Marks:
    def __init__(self, mids):
        self.mids = mids

    def close_mid(self, date, expiry, strike):
        return self.mids.get(strike)


def test_book_marks_settles_and_flags_unmarked(tmp_path):
    t = C.trades(_base_log())
    t.loc[1, ["bomb", "expiry"]] = [True, "2026-09-04"]        # pretend the D2 trade filled and has expired
    spx = tmp_path / "2026-09-04.parquet"
    pd.DataFrame(dict(min=[959, 960], close=[7397.0, 7398.0])).to_parquet(spx)
    b = C.book(t, asof="2026-09-08", marks=_Marks({7500.0: 40.0, 7495.0: 38.5}), spx_dir=tmp_path)
    assert b["cash"] == -100.0
    assert b["table"].state.tolist() == ["MARKED", "SETTLED"]
    assert b["table"].value_usd.tolist() == [150.0, 200.0]     # 1.5 mid × 100; (7400−7398) − 0 = 2 × 100
    assert b["mtm"] == -100.0 + 350.0 and b["unmarked"] == []
    b2 = C.book(t, asof="2026-09-08", marks=_Marks({}), spx_dir=tmp_path)
    assert len(b2["unmarked"]) == 1 and np.isnan(b2["table"].value_usd.iloc[0])


def test_verdict_credit_lost_fill_is_immediate_reject():
    bt = C.trades(_base_log()); bt["set"] = "CONFIRMATION"
    ct = bt.copy(); ct.loc[0, "bomb"] = False                   # the candidate lost the D1 fill
    nobook = dict(unmarked=[], mtm=0.0, inventory=0.0)
    assert C.verdict_credit(bt, ct, "A", nobook, nobook).startswith("REJECT — 1 baseline A fill(s) lost")
    assert C.verdict_credit(bt, bt, "A", nobook, nobook).startswith("INCONCLUSIVE — baseline A fills 1/15")


def test_verdict_a_depth_needs_counts_then_defers_on_unmarked():
    bt = C.trades(_base_log()); bt["set"] = "CONFIRMATION"
    sig = C.signals(_base_log()); sig["set"] = "CONFIRMATION"
    ok = dict(unmarked=[], mtm=0.0, inventory=0.0)
    assert C.verdict_a_depth(bt, sig, bt, ok, ok).startswith("INCONCLUSIVE — A signals 2/20")
    big_sig = pd.concat([sig.assign(session_date=f"2026-10-{i:02d}", r30=-4.5) for i in range(1, 21)])
    big_t = pd.concat([bt.assign(session_date=f"2026-10-{i:02d}") for i in range(1, 21)])
    bad = dict(unmarked=["x"], mtm=0.0, inventory=0.0)
    assert C.verdict_a_depth(big_t, big_sig, big_t, bad, ok).startswith("DEFERRED")


def test_diag_table_sole_blocker():
    ref = C.refusals(_base_log())
    entered = pd.DataFrame(dict(session_date=[D2], branch=["B"], signal_min=[720], episode=[2], bomb=[True],
                                pnl_usd=[10.0], mae=[-20.0], outcome_type=["fill"], set=["CONFIRMATION"]))
    d = C.diag_table(ref, entered, "vt_broken")
    assert d.scored.tolist() == [True]
    d2 = C.diag_table(ref, entered.iloc[0:0], "vt_broken")
    assert d2.scored.tolist() == [False]
