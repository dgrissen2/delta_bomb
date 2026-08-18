"""SPX 1-min touch / adverse-excursion statistics for delta-bomb leg-in timing.

For every session in the real SPX 1-min OHLC store and every start minute (10:00–14:30, 15-min step),
measure whether SPX moves ≥ X bp up (down) within N minutes, the adverse excursion before that touch,
and whether an alternating X move (up then back down) also occurs. Reproduces the tables in
docs/specs/spx_1min_delta_bomb_leg_in_strategy.md (§1 supporting table, §1.0a items 2/7/8).

Run: ~/Dev/virtualenvs/gamma_chaser/bin/python scripts/spx_touch_stats.py
Outputs: docs/replay/spx_touch_stats_full.parquet (up-oriented) and spx_touch_stats_full_dn.parquet (down-oriented).
"""
from __future__ import annotations

import glob
import os

import numpy as np
import pandas as pd

STORE = os.path.expanduser("~/Dev/central_trade_data/thetadata/spx_index_1m_ohlc")
SG = os.path.expanduser("~/Dev/central_trade_data/spotgamma_fixed/offset_historical_FIXED_2026-06-14.csv")
STARTS = range(600, 871, 15)  # 10:00 .. 14:30 ET, minutes from midnight
X_BP = (4, 8)
WINDOWS = (60, 120)
MIN_BARS = 380


def load() -> pd.DataFrame:
    files = sorted(glob.glob(f"{STORE}/*.parquet"))
    return pd.concat([pd.read_parquet(f).assign(date=os.path.basename(f)[:10]) for f in files])


def touch_rows(day: str, g: pd.DataFrame, regime: str) -> list[dict]:
    g = g.sort_values("min")
    m, hi, lo, cl = g["min"].values, g.high.values, g.low.values, g.close.values
    out = []
    for t0 in STARTS:
        i0 = np.searchsorted(m, t0)
        p0 = cl[i0]
        for X in X_BP:
            up, dn = p0 * (1 + X / 1e4), p0 * (1 - X / 1e4)
            for N in WINDOWS:
                iN = min(len(m), i0 + 1 + N)   # exactly N future bars
                H, L = hi[i0 + 1:iN], lo[i0 + 1:iN]
                iu = int(np.argmax(H >= up)) if (H >= up).any() else -1
                idn = int(np.argmax(L <= dn)) if (L <= dn).any() else -1
                seg_u = L[:iu] if iu >= 0 else L   # exclude the touch bar (intrabar order unknown)
                seg_d = H[:idn] if idn >= 0 else H
                out.append(
                    dict(
                        day=day, regime=regime, t0=t0, X=X, N=N,
                        up_hit=iu >= 0, dn_hit=idn >= 0,
                        alt=bool((L[iu + 1:] <= up * (1 - X / 1e4)).any()) if iu >= 0 else False,
                        mae_up=max(0.0, (p0 - seg_u.min()) / p0 * 1e4) if len(seg_u) else 0.0,
                        mae_dn=max(0.0, (seg_d.max() - p0) / p0 * 1e4) if len(seg_d) else 0.0,
                    )
                )
    return out


def main() -> None:
    d = load()
    sg = pd.read_csv(SG, parse_dates=["Date"])
    vt = sg.assign(date=sg.Date.dt.strftime("%Y-%m-%d")).set_index("date")["Vol Trigger"].to_dict()
    rows, excluded = [], []
    for day, g in d.groupby("date"):
        if len(g) < MIN_BARS:
            excluded.append((day, len(g)))
            continue
        v = vt.get(day)
        op = g.sort_values("min").open.values[0]
        regime = "na" if v is None or np.isnan(v) else ("above_VT" if op > v else "below_VT")
        rows.extend(touch_rows(day, g, regime))
    r = pd.DataFrame(rows)
    r.drop(columns=["mae_dn"]).to_parquet("docs/replay/spx_touch_stats_full.parquet")
    r[["day", "X", "N", "dn_hit", "mae_dn"]].to_parquet("docs/replay/spx_touch_stats_full_dn.parquet")
    print("excluded", excluded)
    summ = r.groupby(["X", "N"]).agg(
        up=("up_hit", "mean"), dn=("dn_hit", "mean"), alt=("alt", "mean"),
        mae_up_gt20=("mae_up", lambda s: (s > 20).mean()), mae_up_gt40=("mae_up", lambda s: (s > 40).mean()),
        mae_dn_gt20=("mae_dn", lambda s: (s > 20).mean()), mae_dn_gt40=("mae_dn", lambda s: (s > 40).mean()),
    )
    print(summ.round(3).to_string())


if __name__ == "__main__":
    main()
