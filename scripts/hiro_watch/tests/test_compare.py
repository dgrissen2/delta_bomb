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
    assert r.reason.tolist() == ["vt_broken"] and int(r.episode.iloc[0]) == 2


def test_refusals_keep_every_reason_of_a_setup():
    ev = _base_log()
    extra = _log([_ev(session_date=D2, event_type="late_no_entry", rule_id="R6.3", branch="B", signal_min=719,
                      episode=2, notes="LATE — NO ENTRY")])
    r = C.refusals(pd.concat([ev, extra], ignore_index=True))
    assert sorted(r.reason.tolist()) == ["late", "vt_broken"] and r.episode.nunique() == 1


def test_firewall_label_and_countable_only():
    sess = pd.DataFrame(dict(date=[D1, D2, "2026-09-10", "2026-09-11"],
                             disposition=["countable", "countable", "partial", "countable"]))
    conf = C.confirmation_dates(sess, registered=D1)
    assert conf == [D2, "2026-09-11"]                              # partial excluded (W5.1)
    lab = C.label(pd.Series([D1, D2, "2026-09-10", "2026-09-11"]), D1, conf)
    assert lab.tolist() == ["DISCOVERY", "CONFIRMATION", "EXCLUDED", "CONFIRMATION"]


def test_confirmation_dates_stop_at_the_terminal_checkpoint():
    sess = pd.DataFrame(dict(date=[f"2026-{9 + i // 28:02d}-{1 + i % 28:02d}" for i in range(45)],
                             disposition=["countable"] * 45))
    assert len(C.confirmation_dates(sess, registered="2026-08-31")) == C.TERMINAL


def test_checkpoint_guard():
    assert not C.checkpoint(9) and C.checkpoint(10) and not C.checkpoint(11) and C.checkpoint(40)


def test_lb95_bounds_and_zero_trade_sessions_in_the_unit():
    ten_of_ten = pd.DataFrame(dict(session_date=[f"d{i}" for i in range(10)], fills=[1] * 10, n=[1] * 10))
    assert 0.7 < C.lb95(ten_of_ten) < 1.0                     # Clopper-Pearson floors the 1.0 artefact
    none = pd.DataFrame(dict(session_date=["d0", "d1"], fills=[0, 0], n=[5, 5]))
    assert C.lb95(none) == 0.0
    assert C.lb95(pd.DataFrame(dict(session_date=[], fills=[], n=[]))) == 0.0
    t = C.trades(_base_log())
    ps = C.per_session(t, [D1, D2, "2026-09-10"])
    assert ps.n.tolist() == [1, 1, 0] and ps.fills.tolist() == [1, 0, 0]


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
    pd.DataFrame(dict(min=[930], close=[7397.0])).to_parquet(tmp_path / "2026-09-05.parquet")
    with pytest.raises(SystemExit):
        C.spx_close("2026-09-05", tmp_path)                    # incomplete asof session refused
    assert C.spx_close("2026-09-05", tmp_path, require_complete=False) == 7397.0   # half-day expiry settles
    b = C.book(t, asof=D2, marks=_Marks({7500.0: 40.0, 7495.0: 38.5}), spx_dir=tmp_path)
    assert b["cash"] == -100.0
    early = C.book(t, asof=D1, marks=_Marks({7500.0: 40.0, 7495.0: 38.5}), spx_dir=tmp_path)
    assert early["cash"] == 10.0 and early["n_bombs"] == 1                # D2's trade is after asof
    assert b["table"].state.tolist() == ["MARKED", "SETTLED"]
    assert b["table"].value_usd.tolist() == [150.0, 200.0]     # 1.5 mid × 100; (7400−7398) − 0 = 2 × 100
    assert b["mtm"] == -100.0 + 350.0 and b["unmarked"] == []
    b2 = C.book(t, asof=D2, marks=_Marks({}), spx_dir=tmp_path)
    assert len(b2["unmarked"]) == 1 and np.isnan(b2["table"].value_usd.iloc[0])


def test_verdict_credit_lost_fill_is_immediate_reject():
    bt = C.trades(_base_log())
    ct = bt.copy(); ct.loc[0, "bomb"] = False                   # the candidate lost the D1 fill
    nobook = dict(unmarked=[], mtm=0.0, inventory=0.0)
    text, immediate = C.verdict_credit(bt, ct, "A", nobook, nobook)
    assert text.startswith("REJECT (A) — 1 baseline fill(s) lost") and immediate
    text, immediate = C.verdict_credit(bt, bt, "A", nobook, nobook)
    assert text.startswith("INCONCLUSIVE (A) — baseline A fills 1/15") and not immediate


def test_lost_fill_join_survives_a_later_signal_minute():
    """The candidate re-signals the same episode 6 minutes later (capacity) — still the same setup."""
    bt = C.trades(_base_log())
    ct = bt.copy(); ct.loc[0, ["signal_min", "entry_min"]] = [646, 647]
    assert len(C.lost_fills(bt, ct, "A")) == 0


def _many_days(n: int):
    """n confirmation days, each with the two fixture A setups (episodes 1 and 2, both passed)."""
    bt, sig = C.trades(_base_log()), C.signals(_base_log())
    bt.loc[bt.session_date == D2, "episode"] = 2
    sig.loc[sig.session_date == D2, "episode"] = 2
    days = [f"2026-10-{i:02d}" for i in range(1, n + 1)]
    big_sig = pd.concat([sig.assign(session_date=d, r30=-4.5) for d in days], ignore_index=True)
    big_t = pd.concat([bt.assign(session_date=d) for d in days], ignore_index=True)
    return days, big_sig, big_t


def test_verdict_a_depth_needs_counts_then_defers_on_unmarked():
    bt = C.trades(_base_log())
    sig = C.signals(_base_log())
    ok = dict(unmarked=[], mtm=0.0, inventory=0.0)
    text, immediate = C.verdict_a_depth(bt, sig, bt, ok, ok, ok, ok, [D1, D2])
    assert text.startswith("INCONCLUSIVE — A signals 2/20") and not immediate
    days, big_sig, big_t = _many_days(15)                                          # 30 signals: counts met, not expired
    bad = dict(unmarked=["x"], mtm=0.0, inventory=0.0)
    text, immediate = C.verdict_a_depth(big_t, big_sig, big_t, bad, ok, ok, ok, days)
    assert text.startswith("DEFERRED") and not immediate
    text, immediate = C.verdict_a_depth(big_t, big_sig, big_t, ok, ok, ok, ok, days)
    assert text.startswith("REJECT — passed completion LB95") and not immediate   # half the trades timed out


def test_verdict_a_depth_scores_only_the_passed_cohort_and_expires():
    ok = dict(unmarked=[], mtm=0.0, inventory=0.0)
    days, big_sig, big_t = _many_days(20)                                          # 40 signals = the expiry budget
    ct = big_t.copy(); ct.loc[ct.index[0], "pnl_usd"] = -500.0                          # a big loss is NOT a bar (v2.1)
    text, immediate = C.verdict_a_depth(big_t, big_sig, ct, ok, ok, ok, ok, days)
    assert not immediate and "REJECT — passed loss" not in text
    stray_sig = big_sig.copy(); stray_sig.loc[stray_sig.index[0], "r30"] = -3.0          # first setup NOT passed
    text, immediate = C.verdict_a_depth(big_t, stray_sig, ct, ok, ok, ok, ok, days)
    assert not immediate and "1 candidate A trade(s) outside the passed cohort" in text   # the -500 is unscored
    assert text.startswith("REJECT — passed completion LB95")                           # a real REJECT is not an expiry
    bad = dict(unmarked=["x"], mtm=0.0, inventory=0.0)
    text, immediate = C.verdict_a_depth(big_t, big_sig, big_t, bad, ok, ok, ok, days)
    assert text.startswith("REJECT-EXPIRED") and "DEFERRED" in text                     # 40 signals + no verdict → expired


def test_diag_table_sole_blocker():
    ref = C.refusals(_base_log())
    entered = pd.DataFrame(dict(session_date=[D2], branch=["B"], signal_min=[720], episode=[2], bomb=[True],
                                pnl_usd=[10.0], mae=[-20.0], outcome_type=["fill"], set=["CONFIRMATION"]))
    none_ref = ref.iloc[0:0]
    base_t = C.trades(_base_log())
    d = C.diag_table(ref, base_t, none_ref, entered, "vt_broken")
    assert d.scored.tolist() == [True] and d.other_reasons.tolist() == [""]
    d2 = C.diag_table(ref, base_t, none_ref, entered.iloc[0:0], "vt_broken")
    assert d2.scored.tolist() == [False]
    both = pd.concat([ref, ref.assign(reason="late")], ignore_index=True)
    d3 = C.diag_table(both, base_t, none_ref, entered, "vt_broken")
    assert d3.other_reasons.tolist() == ["late"]
    d4 = C.diag_table(ref, base_t, ref.assign(reason="flow_veto"), entered, "vt_broken")
    assert d4.other_reasons.tolist() == ["flow_veto"]                 # second veto seen only in the diag log
    base_entered_later = pd.concat([base_t, entered.assign(trade_id=9, side="sell_first", k1=7400.0, k2=7405.0,
                                                           expiry="2026-10-09", leg1_fill=30.0, k_long=7405.0,
                                                           k_short=7400.0, signal_min=730, entry_min=731,
                                                           leg2_fill=None, outcome_minutes=None, leg_liq_loss_usd=20.0)],
                                   ignore_index=True)
    d5 = C.diag_table(ref, base_entered_later, none_ref, entered, "vt_broken")
    assert len(d5) == 0                                                # baseline entered the episode later → not refused


def test_registry_refuses_a_yaml_pointing_at_the_baseline_ledger(tmp_path, monkeypatch):
    from hiro_watch import registry as R
    good = (R.CONFIGS / "baseline_v2.yaml").read_text()
    bad = good.replace("docs/replay/hiro_watch/baseline_v2/", "docs/replay/hiro/").replace("name: baseline_v2", "name: evil")
    (tmp_path / "evil.yaml").write_text(bad)
    monkeypatch.setattr(R, "CONFIGS", tmp_path)
    with pytest.raises(SystemExit, match="never the baseline ledger"):
        R.candidates()


def test_load_log_refuses_a_hash_mismatch(tmp_path):
    ev = _base_log().astype(str)
    p = tmp_path / "log.csv"; ev.to_csv(p, index=False)
    with pytest.raises(SystemExit, match="config_hash"):
        C.load_log([p], expect_hash="deadbeef")
