"""Regime tags (owner ask 2026-09-09): mark sessions with a REAL break of the Vol Trigger, or a very low
SG Index at the open, so the below-VT thesis (short-gamma tape → bigger moves, louder HIRO, whipsaw) can
be tested on those sessions alone once we have some. Reporting only — never a bar, never a rule.

    vt_break   opened at/above the Vol Trigger and closed >= VT_BREAK_PCT below it (a break DURING the session)
    vt_deep    opened >= VT_DEEP_PCT below the Vol Trigger (already in the short-gamma zone at the bell)
    sgi_low    SG Index (from the day's levels row) <= SGI_LOW — bottom 20 % of 2025-01 → 2026-09 (421 rows)

Inputs are the engine's own sources: the levels CSV (VT, sg_index — never `Ref Px`) and SPX 1-min bars.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hiro_engine.config import load_config     # noqa: E402  (frozen; read-only)
from hiro_engine.levels import LevelsLoader    # noqa: E402

VT_BREAK_PCT = 0.0025      # ≈ 19 pts at 7700
VT_DEEP_PCT = 0.005        # ≈ 38 pts
SGI_LOW = -1.4


def tags(day: str, cfg=None) -> list[str]:
    cfg = cfg or load_config(None)
    lv = LevelsLoader(cfg.path_of("levels_csv")).load(day)
    f = Path(cfg.path_of("spx_dir")) / f"{day}.parquet"
    if not lv.valid or not f.exists():
        return []
    bars = pd.read_parquet(f).sort_values("min")
    o, c = float(bars.open.iloc[0]), float(bars.close.iloc[-1])
    out = []
    if o >= lv.vt and c <= lv.vt * (1 - VT_BREAK_PCT):
        out.append("vt_break")
    if o <= lv.vt * (1 - VT_DEEP_PCT):
        out.append("vt_deep")
    if lv.sg_index is not None and lv.sg_index <= SGI_LOW:
        out.append("sgi_low")
    return out


def tag(day: str, cfg=None) -> str:
    return "+".join(tags(day, cfg))


if __name__ == "__main__":
    from hiro_watch.compare import V1_SESSIONS, load_sessions
    cfg = load_config(None)
    for d in load_sessions(V1_SESSIONS).date:
        if d >= "2026-08-12":
            print(d, tag(d, cfg) or "-")
