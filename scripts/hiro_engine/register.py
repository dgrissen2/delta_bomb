"""R9a threshold pre-registration (task 16) — the mechanical, run-once machine.

The DERIVATION below is frozen BEFORE the first v3 rehearsal: its source text
is hashed into CONFIG as `r9a_formulas_hash`. `register-thresholds` refuses to
run unless that pin is present and matches, and refuses to run twice
(`r9a_registration_hash` non-empty). A disliked number is not a defect.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import math
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from .config import REPO_ROOT, Config

DRAWS = 2000
SEED = 42
EMPTY_RESAMPLE_LIMIT = 0.30


# =============================================================================
# THE FROZEN DERIVATION (R9a). Hash of this function's source == the formulas
# pin. Any edit changes the hash and voids the pre-registration.
# =============================================================================
def derive_thresholds(entries: pd.DataFrame, countable_sessions: list[str]) -> dict:
    """entries: one row per executable entry with columns
    [date, branch, exit_type, pnl_usd, data_invalid]; countable_sessions: the
    rehearsal's countable session dates. Returns the R9a threshold dict.

    Formulas (frozen):
    - ONE bootstrap: resample countable sessions with replacement, 2000 draws,
      numpy default_rng(42). Per draw: fills_projected = fills_in_draw * 10 /
      sessions_per_draw; prop = share of drawn sessions with >= 1 fill.
      fills_total_floor = floor(mean(fills_projected) - 1*SD(fills_projected)),
      min 5. sessions_with_fill_floor = floor(10 * (mean(prop) - 1*SD(prop))),
      min 5.
    - Branch fill-rate floors: floor = max(0.10, point - 1*SD_branch) rounded
      DOWN to 0.05, where SD_branch is the day-clustered bootstrap SD of that
      branch's fill rate (scored entries only: censored/data_invalid excluded
      from both sides); draws with zero scored entries for the branch are
      DROPPED from the SD; if > 30% of draws are empty the branch is
      pre-declared underpowered (floor still emitted, flag raised).
    - Max single-trade loss cap = p95 of realized losses (losses only,
      numpy quantile linear) rounded UP to the next $25, minimum $25.
    - Median scratch loss cap = median scratch loss * 1.5 rounded UP to the
      next $10, minimum $10 (no scratches -> $10 * 1.5 -> $20? NO: no
      scratches -> cap = $50 flat, stated here to be deterministic).
    """
    rng = np.random.default_rng(SEED)
    scored = entries[~entries.data_invalid.fillna(False)
                     & (entries.exit_type != "censored")]
    sessions = list(countable_sessions)
    n = len(sessions)
    by_day_fills = {d: int((scored[(scored.date == d)
                                   & (scored.exit_type == "fill")]).shape[0])
                    for d in sessions}
    by_day = {d: scored[scored.date == d] for d in sessions}

    fills_proj, props = [], []
    b_rates, a_rates = [], []
    b_empty = a_empty = 0
    for _ in range(DRAWS):
        draw = rng.choice(sessions, size=n, replace=True)
        fills = sum(by_day_fills[d] for d in draw)
        fills_proj.append(fills * 10.0 / n)
        props.append(np.mean([1.0 if by_day_fills[d] > 0 else 0.0 for d in draw]))
        frames = [by_day[d] for d in draw]
        dd = pd.concat(frames) if frames else scored.iloc[0:0]
        for br, rates, counter in (("B", b_rates, "b"), ("A", a_rates, "a")):
            e = dd[dd.branch == br]
            if not len(e):
                if br == "B":
                    b_empty += 1
                else:
                    a_empty += 1
                continue
            rates.append(float((e.exit_type == "fill").mean()))

    def _count_floor(vals, scale=1.0, mult=1.0):
        v = np.asarray(vals, float)
        return max(5, math.floor((v.mean() - v.std(ddof=0)) * mult))

    fills_total_floor = max(5, math.floor(np.mean(fills_proj) - np.std(fills_proj)))
    sessions_with_fill_floor = max(5, math.floor(10 * (np.mean(props) - np.std(props))))

    def _rate_floor(rates, point):
        if not rates:
            return 0.10, True
        sd = float(np.std(np.asarray(rates, float), ddof=0))
        raw = max(0.10, point - sd)
        return math.floor(raw / 0.05) * 0.05, False

    b_scored = scored[scored.branch == "B"]
    a_scored = scored[scored.branch == "A"]
    b_point = float((b_scored.exit_type == "fill").mean()) if len(b_scored) else 0.0
    a_point = float((a_scored.exit_type == "fill").mean()) if len(a_scored) else 0.0
    b_floor, _ = _rate_floor(b_rates, b_point)
    a_floor, _ = _rate_floor(a_rates, a_point)
    b_under = (b_empty / DRAWS) > EMPTY_RESAMPLE_LIMIT
    a_under = (a_empty / DRAWS) > EMPTY_RESAMPLE_LIMIT

    # R11.3: realized loss of a trade = max(0, -pnl$) — defined for EVERY
    # trade, so the p95 population INCLUDES zero-loss winners (codex BP2 F1)
    losses = (-scored.pnl_usd).clip(lower=0)
    if len(losses):
        p95 = float(np.quantile(losses, 0.95))
        max_loss_cap = max(25, math.ceil(p95 / 25.0) * 25)
    else:
        max_loss_cap = 25
    scr = scored[scored.exit_type == "scratch"]
    if len(scr):
        med = float((-scr.pnl_usd).clip(lower=0).median())   # realized loss, R11.3
        median_scratch_cap = max(10, math.ceil(med * 1.5 / 10.0) * 10)
    else:
        median_scratch_cap = 50

    return dict(
        fills_total_floor=int(fills_total_floor),
        sessions_with_fill_floor=int(sessions_with_fill_floor),
        b_fill_rate_floor=round(b_floor, 2),
        a_fill_rate_floor=round(a_floor, 2),
        b_underpowered=bool(b_under),
        a_underpowered=bool(a_under),
        max_single_trade_loss_usd=int(max_loss_cap),
        median_scratch_loss_cap_usd=int(median_scratch_cap),
        b_point_estimate=round(b_point, 4),
        a_point_estimate=round(a_point, 4),
        draws=DRAWS, seed=SEED,
        empty_resample_share=dict(B=round(b_empty / DRAWS, 4),
                                  A=round(a_empty / DRAWS, 4)),
    )
# =============================================================================


def formulas_hash() -> str:
    """sha256 of the frozen derivation source text AND its module constants."""
    blob = (inspect.getsource(derive_thresholds)
            + f"|DRAWS={DRAWS}|SEED={SEED}|EMPTY={EMPTY_RESAMPLE_LIMIT}")
    return hashlib.sha256(blob.encode()).hexdigest()


def run_register(cfg: Config, log_path: Optional[Path] = None,
                 out_path: Optional[Path] = None) -> int:
    pin = str(cfg.get("chains", "r9a_formulas_hash"))
    reg = str(cfg.get("chains", "r9a_registration_hash"))
    if reg:
        print("REFUSED: r9a_registration_hash is already pinned — the rehearsal "
              "was registered once and may not run again (R9a).")
        return 1
    if pin == "":
        print("REFUSED: r9a_formulas_hash is EMPTY — freeze the pre-registration "
              "(task 16) before running the rehearsal (R9a).")
        return 1
    if pin != formulas_hash():
        print("REFUSED: r9a_formulas_hash does not match this derivation code — "
              "the formulas changed after the freeze (R9a).")
        return 1
    from .scorecard import stage2_entries
    if log_path is None:
        p = Path(cfg.get("logging", "paper_log"))
        log_path = (p if p.is_absolute() else REPO_ROOT / p).with_name("paper_log_backtest.csv")
    ev = pd.read_csv(log_path, dtype={"session_date": str})
    ev = ev[(ev.config_hash == cfg.config_hash) & (ev.tier == "full")]
    entries = stage2_entries(ev)
    dispo = ev[(ev.event_type == "disposition")
               & ev.notes.str.contains("countable", na=False)]
    sessions = sorted(dispo.session_date.unique()) if len(dispo) else []
    if not len(entries) or not sessions:
        print("REFUSED: no rehearsal entries/countable sessions in the log.")
        return 1
    th = derive_thresholds(entries, sessions)
    payload = dict(formulas_hash=pin, thresholds=th,
                   inputs=dict(log=str(log_path), config_hash=cfg.config_hash,
                               sessions=sessions, entries=len(entries)))
    out_path = out_path or (REPO_ROOT / "docs/hiro_engine/registration.json")
    out_path.write_text(json.dumps(payload, indent=1, sort_keys=True))
    reg_hash = hashlib.sha256(out_path.read_bytes()).hexdigest()
    print(json.dumps(th, indent=1))
    print(f"\nregistration.json written -> {out_path}")
    print(f"PIN THIS (config chains.r9a_registration_hash): {reg_hash}")
    print("Then populate the «16b» markers in requirements.md R9 from the values above.")
    return 0
