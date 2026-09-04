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

from helpers import b_fire_row


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


# ---- a_r30_max -----------------------------------------------------------------
def test_a_r30_max_at_v1_value_matches_strict_negative(config):
    assert config.num("r6_entries", "a_r30_max") == 0.0
    assert a_conditions(_core(-0.01), config, TIER_FULL)
    assert not a_conditions(_core(0.01), config, TIER_FULL)
    assert not a_conditions(_core(None), config, TIER_FULL)      # NaN r30 never passes


def test_a_r30_max_minus4_gates_shallow_flow(config):
    cfg = _cfg_with(config, "r6_entries", "a_r30_max", -4.0)
    assert not a_conditions(_core(-3.9), cfg, TIER_FULL)
    assert a_conditions(_core(-4.0), cfg, TIER_FULL)             # boundary inclusive
    assert a_conditions(_core(-5.2), cfg, TIER_FULL)


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
def test_baseline_byte_identity_with_v1_logs(config, tmp_path):
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
    run_backtest(config, TIER_FULL, days, log)
    log.close()
    v2 = pd.read_csv(log_path, dtype=str, keep_default_na=False)
    mask = lambda s: s.str.replace(r"CONFIG_HASH=[0-9a-f]+…", "CONFIG_HASH=…", regex=True)
    a = v1.drop(columns=["config_hash"]).assign(notes=mask(v1.notes)).reset_index(drop=True)
    b = v2.drop(columns=["config_hash"]).assign(notes=mask(v2.notes)).reset_index(drop=True)
    want = [f for f in EVENT_FIELDS if f != "config_hash"]
    assert list(a.columns) == want == list(b.columns)
    assert len(a) == len(b) and a.equals(b), "v2 baseline drifted from v1's log (W0.2)"
