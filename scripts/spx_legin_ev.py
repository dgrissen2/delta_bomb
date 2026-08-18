"""Leg-in timing evidence for SPX delta bombs — stall trigger vs clock-matched anytime baseline, and range/ER conditioning.

Reproduces docs/specs/spx_1min_delta_bomb_leg_in_strategy.md §2c/§2d on real SPX 1-min OHLC
(~/Dev/central_trade_data/thetadata/spx_index_1m_ohlc, one parquet per session; cols min, open, high, low, close).

Spot proxy only: "needed move" = SPX travels x_bp (default 4 ≈ 3 pts at 21Δ / 32 DTE / IV 14) in the direction that
fills the second leg; adverse excursion = how far SPX went the other way before that touch (bp, ≥ 0, touch bar
excluded because intrabar order is unknown). Option-level outcomes are NOT modelled here.

Run:
  ~/Dev/virtualenvs/gamma_chaser/bin/python scripts/spx_legin_ev.py [--x-bp 4] [--window 60] [--pull 8] [--stall-bars 5]
Outputs (docs/replay/, parametrised names, params stored as columns):
  spx_legin_trigger_x{X}_w{W}_p{P}_s{S}.parquet   trigger fires + outcomes
  spx_legin_anytime_x{X}_w{W}.parquet             every-minute anytime outcomes 10:00–14:00 (for clock matching)
  spx_legin_chop_x{X}.parquet                     15-min starts 10:30–14:00 with prior-window features
"""
from __future__ import annotations

import argparse
import glob
import os
import sys

import numpy as np
import pandas as pd

STORE = os.path.expanduser("~/Dev/central_trade_data/thetadata/spx_index_1m_ohlc")
OUT = "docs/replay"
MIN_BARS = 380          # exclude half-days
LEG_OPEN_FIRST = 600    # 10:00 ET
LEG_OPEN_LAST = 840     # 14:00 ET
REFIRE_MIN = 15         # one trigger fire per 15 min


def load_sessions() -> pd.DataFrame:
    files = sorted(glob.glob(f"{STORE}/*.parquet"))
    if not files:
        sys.exit(f"no parquet files under {STORE}")
    return pd.concat([pd.read_parquet(f).assign(date=os.path.basename(f)[:10]) for f in files])


def outcome(hi: np.ndarray, lo: np.ndarray, p0: float, i0: int, x_bp: float, n_min: int) -> dict:
    """Entry at close of bar i0; look at exactly the next n_min bars (i0+1 .. i0+n_min).
    up_hit: high ≥ p0(1+x); dn_hit: low ≤ p0(1−x); alt: after the up-touch, a low ≤ up_level(1−x) (round trip);
    ttf: bars to up-touch; mae_up: max drop (bp, ≥ 0) over bars strictly BEFORE the touch bar; seg_low: that min."""
    up, dn = p0 * (1 + x_bp / 1e4), p0 * (1 - x_bp / 1e4)
    i_end = min(len(hi), i0 + 1 + n_min)
    h, l = hi[i0 + 1:i_end], lo[i0 + 1:i_end]
    iu = int(np.argmax(h >= up)) if (h >= up).any() else -1
    idn = int(np.argmax(l <= dn)) if (l <= dn).any() else -1
    seg = l[:iu] if iu >= 0 else l
    seg_low = float(seg.min()) if len(seg) else np.nan
    mae_up = max(0.0, (p0 - seg_low) / p0 * 1e4) if len(seg) else 0.0
    alt = bool((l[iu + 1:] <= up * (1 - x_bp / 1e4)).any()) if iu >= 0 else False
    return dict(up_hit=iu >= 0, dn_hit=idn >= 0, both=(iu >= 0 and idn >= 0), alt=alt,
                ttf=(iu + 1) if iu >= 0 else np.nan, mae_up=mae_up, seg_low=seg_low)


def stall_trigger_day(g: pd.DataFrame, day: str, x_bp: float, n_min: int, pull: float, stall_bars: int) -> list[dict]:
    """Causal stall ∧ TPM-reclaim trigger. Running high since 10:00; running low since that high (the pullback);
    fire when pullback ≥ pull pts, no new low for stall_bars completed bars, and close > mean typical price since the low."""
    m, hi, lo, cl = g["min"].values, g.high.values, g.low.values, g.close.values
    tp = (hi + lo + cl) / 3
    run_hi, run_lo, lo_idx, last_fire = -1e9, 1e9, 0, -999
    fires = []
    for i in range(len(m)):
        t = m[i]
        if t < LEG_OPEN_FIRST:
            continue
        if hi[i] > run_hi:
            run_hi, run_lo, lo_idx = hi[i], lo[i], i
        if lo[i] < run_lo:
            run_lo, lo_idx = lo[i], i
        if t > LEG_OPEN_LAST:
            break
        if run_hi - run_lo < pull or lo_idx > i - stall_bars or cl[i] <= tp[lo_idx:i + 1].mean() or i - last_fire < REFIRE_MIN:
            continue
        last_fire = i
        o = outcome(hi, lo, cl[i], i, x_bp, n_min)
        fires.append(dict(day=day, t=int(t), pull=run_hi - run_lo, up_hit=o["up_hit"], ttf=o["ttf"], mae=o["mae_up"],
                          broke_low=bool(o["seg_low"] < run_lo) if not np.isnan(o["seg_low"]) else False))
    return fires


def anytime_day(g: pd.DataFrame, day: str, x_bp: float, n_min: int) -> list[dict]:
    """Anytime baseline at EVERY minute 10:00–14:00 (so it can be re-weighted to the trigger's clock distribution)."""
    m, hi, lo, cl = g["min"].values, g.high.values, g.low.values, g.close.values
    rows = []
    for i in range(len(m)):
        t = m[i]
        if t < LEG_OPEN_FIRST or t > LEG_OPEN_LAST:
            continue
        o = outcome(hi, lo, cl[i], i, x_bp, n_min)
        rows.append(dict(day=day, t=int(t), up_hit=o["up_hit"], ttf=o["ttf"], mae=o["mae_up"]))
    return rows


def chop_day(g: pd.DataFrame, day: str, x_bp: float) -> list[dict]:
    """15-min starts 10:30–14:00 with causal prior-30/60-bar features: Kaufman ER (w returns), realized range over
    exactly w bars (bp), and 5-bar direction flips ignoring zero returns; outcomes at 60 and 120 min."""
    m, hi, lo, cl = g["min"].values, g.high.values, g.low.values, g.close.values
    rows = []
    for t0 in range(630, 841, 15):
        i0 = int(np.searchsorted(m, t0))
        p0 = cl[i0]
        feats = {}
        for w in (30, 60):
            seg = cl[i0 - w:i0 + 1]                                   # w+1 closes → w returns
            feats[f"er{w}"] = abs(seg[-1] - seg[0]) / max(np.abs(np.diff(seg)).sum(), 1e-9)
            feats[f"rng{w}"] = (hi[i0 - w + 1:i0 + 1].max() - lo[i0 - w + 1:i0 + 1].min()) / p0 * 1e4   # exactly w bars
            r5 = np.sign(seg[5:] - seg[:-5])
            r5 = r5[r5 != 0]
            feats[f"fl{w}"] = int((np.diff(r5) != 0).sum()) if len(r5) > 1 else 0
        for n_min in (60, 120):
            o = outcome(hi, lo, p0, i0, x_bp, n_min)
            rows.append(dict(day=day, t0=t0, N=n_min, **feats, up=o["up_hit"], dn=o["dn_hit"], both=o["both"],
                             alt=o["alt"], mae=o["mae_up"]))
    return rows


def day_clustered_diff(a: pd.Series, b: pd.Series, n_boot: int = 2000, seed: int = 0) -> tuple[float, float, float]:
    """Bootstrap over days of the difference in day-means (a − b); returns mean, 5th, 95th pct."""
    days = sorted(set(a.index) & set(b.index))
    rng = np.random.default_rng(seed)
    diffs = [a.loc[s].mean() - b.loc[s].mean() for s in (rng.choice(days, len(days)) for _ in range(n_boot))]
    return float(np.mean(diffs)), float(np.percentile(diffs, 5)), float(np.percentile(diffs, 95))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--x-bp", type=float, default=4.0)
    ap.add_argument("--window", type=int, default=60)
    ap.add_argument("--pull", type=float, default=8.0)
    ap.add_argument("--stall-bars", type=int, default=5)
    a = ap.parse_args()
    if a.x_bp <= 0 or a.window <= 0 or a.pull <= 0 or a.stall_bars < 1:
        sys.exit("x-bp, window, pull must be > 0 and stall-bars ≥ 1")
    tag_t = f"x{a.x_bp:g}_w{a.window}_p{a.pull:g}_s{a.stall_bars}"
    tag_a = f"x{a.x_bp:g}_w{a.window}"

    d = load_sessions()
    fires, base, chop, n_days = [], [], [], 0
    for day, g in d.groupby("date"):
        if len(g) < MIN_BARS:
            continue
        g = g.sort_values("min")
        n_days += 1
        fires.extend(stall_trigger_day(g, day, a.x_bp, a.window, a.pull, a.stall_bars))
        base.extend(anytime_day(g, day, a.x_bp, a.window))
        chop.extend(chop_day(g, day, a.x_bp))
    if not fires:
        sys.exit("trigger produced no fires for these parameters")
    r = pd.DataFrame(fires).assign(x_bp=a.x_bp, window=a.window, pull_thr=a.pull, stall_bars=a.stall_bars)
    b = pd.DataFrame(base).assign(x_bp=a.x_bp, window=a.window)
    c = pd.DataFrame(chop).assign(x_bp=a.x_bp)
    r.to_parquet(f"{OUT}/spx_legin_trigger_{tag_t}.parquet")
    b.to_parquet(f"{OUT}/spx_legin_anytime_{tag_a}.parquet")
    c.to_parquet(f"{OUT}/spx_legin_chop_x{a.x_bp:g}.parquet")

    # clock-matched baseline: weight anytime minutes by the trigger's clock histogram
    w = r.t.value_counts(normalize=True)
    bm = b[b.t.isin(w.index)].copy()
    bm["wt"] = bm.t.map(w) / bm.groupby("t").t.transform("size")
    def wmean(col): return float(np.average(bm[col].fillna(False).astype(float), weights=bm.wt))
    print(f"sessions {n_days}; trigger fires {len(r)} ({len(r) / n_days:.2f}/day); anytime minutes {len(b)}")
    print(f"TRIGGER          P(up) {r.up_hit.mean():.3f}  P(adv>20) {(r.mae > 20).mean():.3f}  P(adv>40) {(r.mae > 40).mean():.3f}  "
          f"P(low broke first) {r.broke_low.mean():.3f}  P(hit≤5m) {(r.ttf <= 5).mean():.3f}  P(hit≤15m) {(r.ttf <= 15).mean():.3f}  median ttf|hit {r.ttf.median():.0f}")
    print(f"ANYTIME (uniform) P(up) {b.up_hit.mean():.3f}  P(adv>20) {(b.mae > 20).mean():.3f}  P(adv>40) {(b.mae > 40).mean():.3f}  "
          f"P(hit≤5m) {(b.ttf <= 5).mean():.3f}  P(hit≤15m) {(b.ttf <= 15).mean():.3f}  median ttf|hit {b.ttf.median():.0f}")
    print(f"ANYTIME (clock-matched to trigger) P(up) {wmean('up_hit'):.3f}  P(hit≤5m) {np.average((bm.ttf <= 5).astype(float), weights=bm.wt):.3f}  "
          f"P(adv>20) {np.average((bm.mae > 20).astype(float), weights=bm.wt):.3f}")
    m_, lo_, hi_ = day_clustered_diff(r.groupby("day").up_hit.mean(), b.groupby("day").up_hit.mean())
    print(f"day-clustered Δ P(up) trigger − anytime: {m_:+.4f}  90% CI [{lo_:+.4f}, {hi_:+.4f}]")
    r["pb"] = pd.cut(r.pull, [a.pull, 12, 20, 40, 1e9], labels=[f"{a.pull:g}-12", "12-20", "20-40", "40+"], duplicates="drop") if a.pull < 12 else "all"
    print(r.groupby("pb", observed=True).agg(n=("up_hit", "size"), up=("up_hit", "mean"), adv20=("mae", lambda s: (s > 20).mean()),
                                             adv40=("mae", lambda s: (s > 40).mean()), broke=("broke_low", "mean")).round(3).to_string())
    for col in ("er60", "rng60", "fl60"):
        s = c[c.N == 60].copy()
        s["b"] = pd.qcut(s[col], 4, duplicates="drop")
        print(f"\n{col} quartiles (N=60)")
        print(s.groupby("b", observed=True).agg(n=("up", "size"), up=("up", "mean"), dn=("dn", "mean"), both=("both", "mean"),
                                                 alt=("alt", "mean"), adv20=("mae", lambda x: (x > 20).mean()),
                                                 adv40=("mae", lambda x: (x > 40).mean())).round(3).to_string())
    # ER effect within range terciles (time-of-day stratified is left to the option-level test)
    s = c[c.N == 60].copy()
    s["erq"] = pd.qcut(s.er60, 3, labels=["lowER", "midER", "highER"]); s["rq"] = pd.qcut(s.rng60, 3, labels=["lowRng", "midRng", "highRng"])
    print("\nER60 × range60 (N=60): P(up) / P(alt)")
    print(s.pivot_table(index="erq", columns="rq", values=["up", "alt"], aggfunc="mean", observed=True).round(3).to_string())


if __name__ == "__main__":
    main()
