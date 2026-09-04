"""Task 1 tests: config loads, hash sensitivity, fail-closed on missing keys."""
from __future__ import annotations

import pytest

from hiro_engine_v2.config import ConfigError, load_config


def test_config_loads_and_has_hash(config):
    assert len(config.config_hash) == 64
    assert config.num("r1_instruments", "fill_touch_pts") == 3.0
    assert config.num("r7_exits", "cap_option_pts") == 3.5
    assert config.i("r5_clock", "entry_end_min") == 870
    assert len(config.control_days) == 8


def test_editing_any_value_changes_hash(config, tmp_path):
    text = config.path.read_text()
    mutated = text.replace("cap_option_pts: 3.5", "cap_option_pts: 3.75")
    assert mutated != text
    p = tmp_path / "config.yaml"
    p.write_text(mutated)
    assert load_config(p).config_hash != config.config_hash
    # even whitespace changes the hash (byte contract)
    p.write_text(text + "\n")
    assert load_config(p).config_hash != config.config_hash


def test_missing_key_raises(config, tmp_path):
    text = config.path.read_text()
    p = tmp_path / "config.yaml"
    p.write_text(text.replace("  scratch_drop_bps: 0.3       # R7.2 L drop below entry value ($B)\n", ""))
    cfg = load_config(p)
    with pytest.raises(ConfigError):
        cfg.num("r7_exits", "scratch_drop_bps")


def test_missing_section_raises(tmp_path):
    p = tmp_path / "config.yaml"
    p.write_text("r1_instruments: {width_strikes: 5}\n")
    with pytest.raises(ConfigError):
        load_config(p)
