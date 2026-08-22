"""SweepRunner (R13.2/R13.4): ONE knob per run, whitelist literally from the
spec; any other knob rejected. Each value runs a full backtest under a config
override (its own CONFIG_HASH) and is summarized by the shared summarizer."""
from __future__ import annotations

import io
import tempfile
from pathlib import Path
from typing import Optional

import yaml

from .config import Config, load_config
from .eventlog import EventLog
from .models import TIER_FULL
from .scorecard import stage2_entries, stage3_qualify
from .summarize import leaderboard, print_summary, summarize

# R13.2 — fully enumerated. Changing this dict means editing the SPEC first.
WHITELIST: dict[str, dict] = {
    "scratch_drop": {"section": "r7_exits", "key": "scratch_drop_bps",
                     "values": [0.2, 0.3, 0.4, 0.5, 0.6]},
    "scratch_window": {"section": "r7_exits", "key": "scratch_window_min",
                       "values": [2, 3, 4, 5]},
    "pullback": {"section": "r6_entries", "key": "b_pull_min_pts",
                 "values": [3, 5, 8]},
    "cap": {"section": "r7_exits", "key": "cap_option_pts",
            "values": [3.0, 3.25, 3.5, 3.75, 4.0]},
    "clock": {"section": "r5_clock", "key": "clock_minutes",
              "values": [45, 60, 75]},
}
# Backtests exit caps via the spot proxy (R7.3); the frozen option:spot ratio is
# 3.5:15.0 — a swept cap scales the proxy by the same ratio (build_notes.md).
CAP_SPOT_RATIO = 15.0 / 3.5


class SweepError(Exception):
    pass


def _variant_config(base: Config, knob: str, value) -> Config:
    spec = WHITELIST[knob]
    raw = yaml.safe_load(base.path.read_bytes())
    raw[spec["section"]][spec["key"]] = value
    if knob == "cap":
        raw["r7_exits"]["cap_spot_pts"] = round(value * CAP_SPOT_RATIO, 6)
    tmp = Path(tempfile.mkstemp(suffix=".yaml", prefix=f"sweep_{knob}_")[1])
    tmp.write_text(yaml.safe_dump(raw, sort_keys=False))
    return load_config(tmp)


def run_sweep(cfg: Config, knob: str, d_from: Optional[str] = None,
              d_to: Optional[str] = None) -> int:
    if knob not in WHITELIST:
        print(f"knob {knob!r} is not in the R13.2 whitelist "
              f"({', '.join(WHITELIST)}); changing the list means editing the spec.")
        return 2
    from .backtest import available_spx_days, run_backtest
    days = (available_spx_days(cfg, d_from, d_to) if d_from and d_to
            else list(cfg.control_days))
    if not days:
        print("no stored sessions in range")
        return 2
    import pandas as pd
    rows = []
    for value in WHITELIST[knob]["values"]:
        vcfg = _variant_config(cfg, knob, value)
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tf:
            log = EventLog(Path(tf.name), console=io.StringIO(), echo=False)
            import hiro_engine.session as sm
            orig = sm.Session._write_session_row
            sm.Session._write_session_row = lambda self, r: None
            try:
                run_backtest(vcfg, TIER_FULL, days, log)
            finally:
                sm.Session._write_session_row = orig
            log.close()
            ev = pd.read_csv(tf.name, dtype={"session_date": str})
        entries = stage2_entries(ev)
        qualify = stage3_qualify(ev)
        s = summarize(vcfg, entries, qualify, days,
                      variant=f"{knob}={value}"
                      + (" [frozen]" if value == cfg.get(
                          WHITELIST[knob]["section"], WHITELIST[knob]["key"]) else ""))
        print_summary(s)
        rows.append(s)
    leaderboard(rows)
    print(f"\nsweep done — knob {knob!r}, all other numerics frozen; "
          "backtest rows never count toward the live test.")
    return 0
