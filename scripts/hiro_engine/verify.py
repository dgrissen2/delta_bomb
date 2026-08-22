"""R12.1 verification — the golden gate (task 6).

Reproduces `docs/replay/hiro/verification_trades_v1.csv` (the 27-trade research
sequential result) through the ENGINE'S ported core: engine loaders (feeds),
engine run machine (features.apply_run_machine) and engine condition predicates
(rules.b_aligned / b_gates / late_state). The sequential trade loop below is the
pinned RESEARCH semantics (hiro_uptrend_confirm.sequential): fire window
09:35-15:00, one-trade-at-a-time busy logic, +5-touch completion, 3-bar
invalidation, 60-min horizon — these deliberately differ from the live R5/R6.4
windows and caps (artifact-rot guard note in docs/hiro_engine/build_notes.md).
Any mismatch is a DEFECT, not a tolerance (spec AC).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import Config
from .features import apply_run_machine
from .feeds import load_hiro_day, load_spx_day
from .models import TIER_FULL
from .rules import Core, b_aligned, b_gates, late_state

FIRST_MIN, LAST_ENTRY_MIN = 575, 900     # research constants (pinned)
HORIZON = 60


def _day_frame(cfg: Config, day: str) -> pd.DataFrame:
    hiro = load_hiro_day(cfg.path_of("hiro_root"), day)
    spx = load_spx_day(cfg.path_of("spx_dir"), day)
    df = hiro.merge(spx, on="min", how="inner").reset_index(drop=True)
    df = apply_run_machine(df, cfg.num("r3_derived", "run_break_dd"))
    df["r15"] = df.all_L.diff(15)
    df["r30"] = df.all_L.diff(30)
    df["pull30"] = df.close.rolling(30, min_periods=30).max() - df.close
    return df


def _core(row, pull30) -> Core:
    return Core(min=int(row["min"]), close=float(row.close),
                r15=None if np.isnan(row.r15) else float(row.r15),
                r30=None if np.isnan(row.r30) else float(row.r30),
                r15n=None, run=float(row.run), dur=float(row.dur), rate=float(row.rate),
                dC=float(row.dC), dP=float(row.dP), dN=float(row.dN),
                cpr=float(row.cpr) if row.cpr == row.cpr else float("nan"),
                share=None if row.share != row.share else float(row.share),
                dd=float(row.dd), weak_side=float(min(row.dC, row.dP)),
                pull30=None if np.isnan(pull30) else float(pull30),
                bounce30=None, mid30=None, range60=None, range60_pct=None,
                warmup=False, hiro_fresh=True)


def sequential_day(cfg: Config, day: str) -> list[dict]:
    """Verbatim port of hiro_uptrend_confirm.sequential() over engine-built frames."""
    g = _day_frame(cfg, day)
    pull_min = cfg.num("r6_entries", "b_pull_min_pts")
    inval_drop = cfg.num("r7_exits", "scratch_drop_bps")
    inval_bars = cfg.i("r7_exits", "scratch_window_min")
    trades: list[dict] = []
    busy_until = -1
    for i in range(len(g)):
        r = g.iloc[i]
        t = int(r["min"])
        c = _core(r, g.pull30.iloc[i])
        fire = b_aligned(c, cfg) and c.pull30 is not None and c.pull30 >= pull_min
        if not fire or t < FIRST_MIN or t > LAST_ENTRY_MIN or t <= busy_until:
            continue
        if not b_gates(c, cfg):
            continue
        if i + 1 >= len(g):
            continue
        steep = b_aligned(c, cfg) and late_state(c, cfg)
        entry_px = float(g.open.iloc[i + 1]); L0 = float(g.all_L.iloc[i])
        hit3 = hit5 = exit_m = None; scratch = False; low_seen = entry_px
        for j in range(i + 1, min(i + 1 + HORIZON, len(g))):
            low_seen = min(low_seen, float(g.low.iloc[j]))
            if hit3 is None and g.high.iloc[j] >= entry_px + 3:
                hit3 = j - i
            if g.high.iloc[j] >= entry_px + 5:
                hit5 = j - i; exit_m = j; break
            if hit3 is None and (j - i) <= inval_bars and (
                    g.all_L.iloc[j] <= L0 - inval_drop or bool(g.broke.iloc[j])):
                scratch = True; exit_m = j; break
        if exit_m is None:
            exit_m = min(i + HORIZON, len(g) - 1)
        busy_until = int(g["min"].iloc[exit_m])
        exit_type = "scratch" if scratch else ("fill" if hit5 is not None else "timeout_or_other")
        trades.append(dict(day=day, t=t, entry=entry_px, steep=bool(steep),
                           exit_type=exit_type,
                           win3=bool(hit3 is not None and hit3 <= 30),
                           win5=bool(hit5 is not None),
                           ttf5=float(hit5) if hit5 is not None else None,
                           adverse=entry_px - low_seen))
    return trades


@dataclass
class VerifyResult:
    ok: bool
    n_engine: int
    n_artifact: int
    mismatches: list[str]
    artifact_hash_ok: bool


def run_verification(cfg: Config) -> VerifyResult:
    art_path = cfg.verification_artifact
    data = art_path.read_bytes()
    hash_ok = hashlib.sha256(data).hexdigest() == cfg.verification_hash
    ref = pd.read_csv(art_path)
    rows: list[dict] = []
    for day in cfg.control_days:
        rows.extend(sequential_day(cfg, day))
    got = pd.DataFrame(rows)
    mismatches: list[str] = []
    if not hash_ok:
        mismatches.append("artifact hash mismatch vs CONFIG pin (R8.2)")
    if len(got) != len(ref):
        mismatches.append(f"trade count {len(got)} != artifact {len(ref)}")
    else:
        for i in range(len(ref)):
            a, b = ref.iloc[i], got.iloc[i]
            bad = []
            if a.day != b.day or int(a.t) != int(b.t):
                bad.append("day/t")
            if abs(float(a.entry) - float(b.entry)) > 1e-9:
                bad.append("entry")
            if bool(a.steep) != bool(b.steep) or a.exit_type != b.exit_type:
                bad.append("steep/exit_type")
            if bool(a.win3) != bool(b.win3) or bool(a.win5) != bool(b.win5):
                bad.append("win flags")
            ttf_a = None if pd.isna(a.ttf5) else float(a.ttf5)
            ttf_b = None if pd.isna(b.ttf5) else float(b.ttf5)
            if (ttf_a is None) != (ttf_b is None) or (
                    ttf_a is not None and abs(ttf_a - ttf_b) > 1e-9):
                bad.append("ttf5")
            if abs(float(a.adverse) - float(b.adverse)) > 1e-9:
                bad.append("adverse")
            if bad:
                mismatches.append(f"row {i} ({a.day} t={a.t}): " + ",".join(bad))
    return VerifyResult(ok=hash_ok and not mismatches, n_engine=len(got),
                        n_artifact=len(ref), mismatches=mismatches,
                        artifact_hash_ok=hash_ok)
