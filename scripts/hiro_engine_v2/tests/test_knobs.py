"""hiro_watch W2.1 knobs — each knob at its v1-equivalent value changes nothing; flipped, it
admits exactly the entry v1 refused. Plus the W0.2 byte-identity control over the stored sessions."""
from __future__ import annotations

import copy
import glob
import io
import re
from pathlib import Path

import pandas as pd
import pytest

from hiro_engine_v2.config import REPO_ROOT, Config
from hiro_engine_v2.models import EngineState, TIER_FULL, Vetoes
from hiro_engine_v2.rules import Core, RuleEngine, a_conditions

from helpers import a_fire_row, b_fire_row


def _cfg_with(config: Config, section: str, key: str, value) -> Config:
    raw = copy.deepcopy(config.raw)
    raw[section][key] = value
    return Config(raw=raw, config_hash="test", path=config.path)


def _core(r30: float) -> Core:
    return Core(min=700, close=100.0, r15=-0.5, r30=r30, r15n=-0.4, run=1.0, dur=15.0, rate=2.4,
                dC=0.6, dP=0.4, dN=0.7, cpr=0.6, share=0.7, dd=0.0, weak_side=0.4, pull30=4.0,
                bounce30=4.0, mid30=101.0, range60=5.0, range60_pct=3.0, warmup=False,
                hiro_fresh=True)


def _types(evs):
    return [e.event_type for e in evs]


# ---- a_r30_lt ------------------------------------------------------------------
def test_a_conditions_unchanged_from_v1(config):
    assert config.num("r6_entries", "a_r30_lt") == 0.0
    assert a_conditions(_core(-0.01), config, TIER_FULL)
    assert not a_conditions(_core(0.0), config, TIER_FULL)        # v1: strict r30 < 0
    assert not a_conditions(_core(None), config, TIER_FULL)


def test_a_r30_lt_minus4_gates_the_signal_not_the_episode(config):
    cfg = _cfg_with(config, "r6_entries", "a_r30_lt", -4.0)
    eng = RuleEngine(cfg, TIER_FULL)
    shallow = eng.evaluate(a_fire_row(700, r30=-3.9), EngineState())
    assert "signal" not in _types(shallow)
    deep = RuleEngine(cfg, TIER_FULL).evaluate(a_fire_row(700, r30=-4.1), EngineState())
    assert "signal" in _types(deep) and next(e for e in deep if e.event_type == "signal").branch == "A"
    boundary = RuleEngine(cfg, TIER_FULL).evaluate(a_fire_row(700, r30=-4.0), EngineState())
    assert "signal" not in _types(boundary)                      # strict: -4.0 is not < -4.0
    nan = RuleEngine(cfg, TIER_FULL).evaluate(a_fire_row(700, r30=None), EngineState())
    assert "signal" not in _types(nan)


# ---- late_enabled --------------------------------------------------------------
def test_late_enabled_false_admits_the_suppressed_b_entry(config):
    row = b_fire_row(700, late_state=True)
    on = RuleEngine(config, TIER_FULL).evaluate(row, EngineState())
    assert "late_no_entry" in _types(on) and "signal" not in _types(on)
    off = RuleEngine(_cfg_with(config, "r6_entries", "late_enabled", False), TIER_FULL)
    evs = off.evaluate(row, EngineState())
    assert "signal" in _types(evs) and "late_no_entry" not in _types(evs)


# ---- vt_broken_enabled / levels_invalid_enabled (applied in Session._vetoes) ----
@pytest.mark.parametrize("knob,veto", [("vt_broken_enabled", "vt_broken"),
                                       ("levels_invalid_enabled", "levels_invalid")])
def test_veto_knob_off_clears_that_veto_only(config, knob, veto):
    from hiro_engine_v2.session import Session
    cfg = _cfg_with(config, "r4_vetoes", knob, False)
    s = Session.__new__(Session)                      # only _vetoes is exercised
    s.cfg, s.tier = cfg, TIER_FULL
    s.vt_broken = True

    class _Levels:
        valid = False
        vt = None
    s.levels = _Levels()
    v = s._vetoes(b_fire_row(700, r15=0.5, r15n=0.5))
    other = "levels_invalid" if veto == "vt_broken" else "vt_broken"
    assert getattr(v, veto) is False and getattr(v, other) is True and v.flow_veto is False


# ---- W0.2 byte-identity control ------------------------------------------------
@pytest.mark.integration
def test_baseline_byte_identity_with_v1_logs(config, tmp_path, monkeypatch):
    """v2 at v1 knob values over every stored session == v1's own logs, except config_hash."""
    from hiro_engine_v2.backtest import available_spx_days, run_backtest
    from hiro_engine_v2.eventlog import EventLog
    from hiro_engine_v2.models import EVENT_FIELDS
    v1_files = [REPO_ROOT / "docs/replay/hiro/paper_log_backtest.csv"] + sorted(
        Path(p) for p in glob.glob(str(REPO_ROOT / "docs/replay/hiro/paper_log_oos_*.csv")))
    if not v1_files[0].exists() or not config.path_of("spx_dir").exists():
        pytest.skip("stored sessions / v1 logs not available")
    v1 = pd.concat([pd.read_csv(f, dtype=str, keep_default_na=False) for f in v1_files],
                   ignore_index=True)
    era = str(config.get("data", "hiro_era_start"))
    v1 = v1[v1.session_date >= era].reset_index(drop=True)
    days = [d for d in available_spx_days(config, era, "9999-99-99")
            if d in set(v1.session_date)]
    log_path = tmp_path / "v2.csv"
    log = EventLog(log_path, echo=False)
    from hiro_engine_v2.session import Session
    monkeypatch.setattr(Session, "_write_session_row", lambda self, row: None)   # never touch the ledger
    run_backtest(config, TIER_FULL, days, log)
    log.close()
    v2 = pd.read_csv(log_path, dtype=str, keep_default_na=False)
    mask = lambda s: s.str.replace(r"CONFIG_HASH=[0-9a-f]+…", "CONFIG_HASH=…", regex=True)
    a = v1.drop(columns=["config_hash"]).assign(notes=mask(v1.notes)).reset_index(drop=True)
    b = v2.drop(columns=["config_hash"]).assign(notes=mask(v2.notes)).reset_index(drop=True)
    want = [f for f in EVENT_FIELDS if f != "config_hash"]
    assert list(a.columns) == want == list(b.columns)
    assert len(a) == len(b) and a.equals(b), "v2 baseline drifted from v1's log (W0.2)"


def test_package_config_is_the_baseline_yaml(config):
    """scripts/hiro_engine_v2/config.yaml must be byte-identical to docs/hiro_watch/configs/baseline_v2.yaml."""
    a = (REPO_ROOT / "scripts/hiro_engine_v2/config.yaml").read_bytes()
    b = (REPO_ROOT / "docs/hiro_watch/configs/baseline_v2.yaml").read_bytes()
    assert a == b


# ---- Branch-B knobs (2026-09-05): b_enabled, b_run_max, b_dur_max, late_sticky, credit_b ----------
def test_b_enabled_false_refuses_every_b_entry(config):
    off = RuleEngine(_cfg_with(config, "r6_entries", "b_enabled", False), TIER_FULL)
    evs = off.evaluate(b_fire_row(700), EngineState())
    assert "signal" not in _types(evs) and "pending_entry" not in _types(evs)
    assert "signal" in _types(RuleEngine(config, TIER_FULL).evaluate(b_fire_row(700), EngineState()))


def test_b_run_max_and_b_dur_max_gate_the_b_signal(config):
    assert config.num("r6_entries", "b_run_max") >= 1e8 and config.num("r6_entries", "b_dur_max") >= 1e8
    size = RuleEngine(_cfg_with(config, "r6_entries", "b_run_max", 1.0), TIER_FULL)
    assert "signal" not in _types(size.evaluate(b_fire_row(700, run=1.3), EngineState()))
    assert "signal" in _types(RuleEngine(_cfg_with(config, "r6_entries", "b_run_max", 1.0), TIER_FULL)
                              .evaluate(b_fire_row(700, run=1.0), EngineState()))       # boundary inclusive
    age = RuleEngine(_cfg_with(config, "r6_entries", "b_dur_max", 15), TIER_FULL)
    assert "signal" not in _types(age.evaluate(b_fire_row(700, dur=34.0), EngineState()))
    assert "signal" in _types(RuleEngine(_cfg_with(config, "r6_entries", "b_dur_max", 15), TIER_FULL)
                              .evaluate(b_fire_row(700, dur=15.0), EngineState()))


def test_late_sticky_keeps_the_episode_suppressed(config):
    assert config.get("r6_entries", "late_sticky") is False
    eng = RuleEngine(_cfg_with(config, "r6_entries", "late_sticky", True), TIER_FULL)
    assert "late_no_entry" in _types(eng.evaluate(b_fire_row(700, late_state=True), EngineState()))
    later = eng.evaluate(b_fire_row(703, late_state=False), EngineState())      # LATE cleared 3 min later
    assert "signal" not in _types(later)                                          # sticky: still suppressed
    fresh = eng.evaluate(b_fire_row(720, episode=2, late_state=False), EngineState())
    assert "signal" in _types(fresh)                                              # new episode is free
    v1 = RuleEngine(config, TIER_FULL)
    v1.evaluate(b_fire_row(700, late_state=True), EngineState())
    assert "signal" in _types(v1.evaluate(b_fire_row(703, late_state=False), EngineState()))   # v1 re-admits


def test_credit_b_applies_to_branch_b_only(config):
    from hiro_engine_v2.executor import Executor
    assert config.num("r1v3_limits", "credit_b") == config.num("r1v3_limits", "credit")
    ex = Executor(_cfg_with(config, "r1v3_limits", "credit_b", 0.0), TIER_FULL)
    assert ex.credit == config.num("r1v3_limits", "credit") and ex.credit_b == 0.0
