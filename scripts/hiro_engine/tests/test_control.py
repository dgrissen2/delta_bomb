"""Task 8 tests: control functions — hash guard, research-weighting equality,
pinned golden values over the frozen 8 sessions."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from hiro_engine.control import (ControlDatasetError, build_control_frame,
                                 clock_matched, clock_weighted_mean,
                                 midpoint_matched, verify_control_dataset)


@pytest.fixture(scope="module")
def frame(config):
    verify_control_dataset(config)          # data-hash guard must pass
    return build_control_frame(config, check_hash=False)


def test_weighting_equals_research_form():
    """clock_weighted_mean == the original research math on a synthetic frame."""
    rng = np.random.default_rng(0)
    fr = pd.DataFrame({"min": rng.integers(600, 870, 500),
                       "w": rng.integers(0, 2, 500).astype(float)})
    e = pd.Series(rng.integers(600, 870, 40))
    w = e.value_counts(normalize=True)
    b = fr[fr["min"].isin(w.index) & fr.w.notna()]
    wt = b["min"].map(w) / b.groupby("min")["min"].transform("size")
    expect = float(np.average(b.w.astype(float), weights=wt))
    assert clock_weighted_mean(fr, e, "w") == pytest.approx(expect, abs=1e-12)


def test_research_scripts_import_engine_weighting():
    import sys
    sys.path.insert(0, "scripts")
    import inspect
    import hiro_uptrend_confirm as huc
    import hiro_experiments as he
    assert "clock_weighted_mean" in inspect.getsource(huc.clock_matched)
    assert "clock_weighted_mean" in inspect.getsource(he.cm_base)


def test_golden_control_values(config, frame):
    """Pinned values over the frozen dataset with the 27 verification-trade
    minutes as weights (deterministic; any drift = data or logic change)."""
    ref = pd.read_csv(str(config.verification_artifact))
    assert clock_matched(config, ref.t, frame) == pytest.approx(0.7081, abs=5e-4)  # repinned after fill-window alignment (red-team bp2 #10)
    assert midpoint_matched(config, ref.t, frame) == pytest.approx(1.0, abs=1e-9)


def test_hash_guard_detects_change(config, monkeypatch):
    import hiro_engine.control as ctl
    monkeypatch.setattr(ctl, "control_data_hash", lambda cfg: "0" * 64)
    with pytest.raises(ControlDatasetError):
        verify_control_dataset(config)


def test_complete_horizon_only(frame):
    last = frame.groupby("day")["min"].max().min()
    tail = frame[frame["min"] > last - 60]
    assert tail.touch_up.isna().all() or tail[tail["min"] > 900].touch_up.isna().all()
