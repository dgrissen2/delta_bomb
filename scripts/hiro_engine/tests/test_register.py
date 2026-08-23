"""Task 16 tests: the frozen R9a derivation vs hand-computed values; refusals."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from hiro_engine.register import (derive_thresholds, formulas_hash, run_register)


def _entries(rows):
    df = pd.DataFrame(rows, columns=["date", "branch", "exit_type", "pnl_usd"])
    df["data_invalid"] = False
    return df


def test_formulas_hash_pinned_in_config(config):
    assert str(config.get("chains", "r9a_formulas_hash")) == formulas_hash()


def test_derivation_hand_computed_simple():
    """2 sessions, deterministic: hand-check the floors and caps."""
    days = ["d1", "d2"]
    e = _entries([("d1", "A", "fill", 10.0), ("d1", "A", "fill", 10.0),
                  ("d2", "A", "scratch", -60.0), ("d2", "A", "fill", 10.0)])
    th = derive_thresholds(e, days)
    # fills: d1=2, d2=1. Draws over {d1,d2}: fills_proj in {2,3,4}*10/2 = {10,15,20}
    assert 5 <= th["fills_total_floor"] <= 15
    # every session has >= 1 fill -> prop == 1 always -> SD 0 -> floor = 10... min(10,10)=10
    assert th["sessions_with_fill_floor"] == 10
    # A point = 3/4; floors on the 0.05 grid, >= 0.10
    assert th["a_point_estimate"] == pytest.approx(0.75)
    assert th["a_fill_rate_floor"] % 0.05 == pytest.approx(0.0, abs=1e-9)
    assert th["a_fill_rate_floor"] >= 0.10
    # B has zero entries in EVERY draw -> underpowered + hard floor 0.10
    assert th["b_underpowered"] is True and th["b_fill_rate_floor"] == 0.10
    assert th["empty_resample_share"]["B"] == 1.0
    # losses: only 60 -> p95 = 60 -> cap = ceil(60/25)*25 = 75
    assert th["max_single_trade_loss_usd"] == 75
    # median scratch loss 60 * 1.5 = 90 -> cap 90
    assert th["median_scratch_loss_cap_usd"] == 90


def test_derivation_edge_rules():
    days = ["d1"]
    e = _entries([("d1", "B", "fill", 10.0)])
    th = derive_thresholds(e, days)
    assert th["median_scratch_loss_cap_usd"] == 50        # no scratches -> $50 flat
    assert th["max_single_trade_loss_usd"] == 25          # no losses -> $25 min
    # censored/data_invalid excluded from scoring
    e2 = _entries([("d1", "B", "fill", 10.0), ("d1", "B", "censored", -5.0)])
    th2 = derive_thresholds(e2, days)
    assert th2["b_point_estimate"] == 1.0                 # censored out of denominator
    e3 = _entries([("d1", "B", "fill", 10.0), ("d1", "B", "timeout", -500.0)])
    e3.loc[1, "data_invalid"] = True
    th3 = derive_thresholds(e3, days)
    assert th3["b_point_estimate"] == 1.0 and th3["max_single_trade_loss_usd"] == 25


def test_derivation_deterministic():
    days = [f"d{i}" for i in range(8)]
    rows = []
    rng = np.random.default_rng(7)
    for d in days:
        for _ in range(3):
            ok = rng.random() < 0.6
            rows.append((d, "B", "fill" if ok else "timeout", 10.0 if ok else -80.0))
    e = _entries(rows)
    assert derive_thresholds(e, days) == derive_thresholds(e.copy(), list(days))


def test_run_register_refusals(config, tmp_path, capsys, monkeypatch):
    # (a) registration already pinned -> refuse
    import hiro_engine.register as R
    class Cfg1:
        config_hash = "x"
        def get(self, s, k):
            return {"r9a_formulas_hash": "f", "r9a_registration_hash": "nonempty"}[k]
    assert R.run_register(Cfg1()) == 1
    assert "already pinned" in capsys.readouterr().out
    # (b) formulas pin empty -> refuse
    class Cfg2(Cfg1):
        def get(self, s, k):
            return {"r9a_formulas_hash": "", "r9a_registration_hash": ""}[k]
    assert R.run_register(Cfg2()) == 1
    assert "EMPTY" in capsys.readouterr().out
    # (c) formulas pin mismatch -> refuse
    class Cfg3(Cfg1):
        def get(self, s, k):
            return {"r9a_formulas_hash": "deadbeef", "r9a_registration_hash": ""}[k]
    assert R.run_register(Cfg3()) == 1
    assert "does not match" in capsys.readouterr().out
