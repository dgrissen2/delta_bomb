"""Task 6 tests: determinism (byte-identical streams), THE golden gate, refusal."""
from __future__ import annotations

import io

import pytest

from hiro_engine.backtest import run_backtest
from hiro_engine.eventlog import EventLog
from hiro_engine.models import TIER_FULL, TIER_PRICE


def _run_day(config, tmp_path, name, tier=TIER_FULL, day="2026-08-18"):
    p = tmp_path / f"{name}.csv"
    log = EventLog(p, console=io.StringIO(), echo=True)
    import hiro_engine.session as sm
    orig = sm.Session._write_session_row
    sm.Session._write_session_row = lambda self, row: None
    try:
        run_backtest(config, tier, [day], log)
    finally:
        sm.Session._write_session_row = orig
    log.close()
    return p.read_bytes(), log.console.getvalue()


def test_determinism_same_day_twice_byte_identical(config, tmp_path):
    b1, c1 = _run_day(config, tmp_path, "a")
    b2, c2 = _run_day(config, tmp_path, "b")
    assert b1 == b2 and c1 == c2 and len(b1) > 1000


def test_golden_gate_verification_artifact(config):
    """R12.1: frozen-config full-tier reproduction of verification_trades_v1.csv,
    row-for-row. Do not proceed past task 6 until this passes."""
    from hiro_engine.verify import run_verification
    r = run_verification(config)
    assert r.artifact_hash_ok, "verification artifact bytes changed vs pinned hash"
    assert r.ok, "GOLDEN GATE FAIL:\n" + "\n".join(r.mismatches)
    assert r.n_engine == 27


def test_price_tier_runs_and_stamps(config, tmp_path):
    b, c = _run_day(config, tmp_path, "p", tier=TIER_PRICE, day="2026-08-18")
    text = b.decode()
    assert ",price," in text and ",full," not in text
    assert "SIGNAL B" not in c                     # Branch B disabled in price tier


def test_full_tier_refuses_pre_hiro_dates(config, tmp_path):
    from hiro_engine.feeds import FeedError
    log = EventLog(tmp_path / "x.csv", console=io.StringIO())
    with pytest.raises(FeedError) as ei:
        run_backtest(config, TIER_FULL, ["2024-01-03"], log)
    assert "2024-01-03" in str(ei.value)
