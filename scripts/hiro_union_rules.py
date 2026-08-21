"""Union rules U1–U6 (Brent/Charlie daily-production designs, 2026-08-21) — exact executor on the 8-session lab table.

Notation from the design: H/C/P{w} = HIRO all-total/call/put rolling w-min flows (lab r{w}, r{w}c, r{w}p);
R{w} = SPX w-min return (ret{w}); Range60 = prior-60-min range; PB30/BN30 = 30-bar pullback/bounce; C = SPX close;
S0 = entry bar's open. Entries and exits at next-bar open. Completion (±3 pts from S0, touch) beats scratch beats
timeout. One leg at a time; 30-min cooldown after any exit; simultaneous triggers → lowest U number.

Run: ~/Dev/virtualenvs/gamma_chaser/bin/python scripts/hiro_union_rules.py
Out: docs/replay/hiro/union_trades.csv + printed per-rule and portfolio tables.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

LAB = "docs/replay/hiro/hiro_lab_minute.parquet"
COOLDOWN = 30


def prep(df: pd.DataFrame) -> pd.DataFrame:
    g = df.sort_values("min").reset_index(drop=True)
    g["hi30"] = g.high.rolling(30, min_periods=30).max()
    g["up2"] = (g.close > g.close.shift(1)) & (g.close.shift(1) > g.close.shift(2))
    g["dn2"] = (g.close < g.close.shift(1)) & (g.close.shift(1) < g.close.shift(2))
    g["h5_min15"] = g.r5.rolling(15, min_periods=15).min()
    return g


def arm_trigger(g: pd.DataFrame, i: int, U: int) -> bool:
    r = g.iloc[i]; p = g.iloc[i - 1] if i >= 1 else r; p2 = g.iloc[i - 2] if i >= 2 else r
    t = r["min"]
    if U == 1:
        return (585 <= t <= 660 and r.pull30 >= 6 and r.ret15 <= -4 and r.r15 < 0
                and r.r5 > p.r5 > p2.r5 and r.r5 < 0 and r.close > p.close)
    if U == 2:
        return (660 <= t <= 870 and r.rng60 >= 12 and r.bounce30 >= 6 and r.ret30 < 0
                and p.r5c <= 0 < r.r5c and p.r5p >= 0 > r.r5p and r.close >= r.hi30 - 2)
    if U == 3:
        return (870 <= t <= 940 and r.ret15 <= -5 and r.pull30 >= 8 and r.r15 < 0
                and p.r5 <= 0 < r.r5 and r.close > max(p.high, p2.high))
    if U == 4:
        return (585 <= t <= 660 and r.ret15 <= -0.25 * r.rng60 and r.r15 < 0 and r.r15p < 0
                and bool(r.up2) and r.r5 >= 0 and r.r5p >= 0)
    if U == 5:
        return (660 <= t <= 870 and r.ret15 >= 0.25 * r.rng60 and r.r15 > 0 and r.r15c > 0 and r.r15p > 0
                and bool(r.dn2) and r.r5c <= 0)
    if U == 6:
        return (810 <= t <= 930 and r.rng60 >= 12 and r.ret30 < 0 and r.L < 0 and r.bounce30 >= 3
                and r.close < p.close and r.r5c > 0 and r.r5p < 0)
    return False


SIDE = {1: "sell", 2: "long", 3: "sell", 4: "sell", 5: "long", 6: "long"}
TIMEOUT = {1: 60, 2: 45, 3: 30, 4: 45, 5: 60, 6: 45}


def scratch_hit(g: pd.DataFrame, U: int, i0: int, j: int, S0: float) -> bool:
    r = g.iloc[j]; p = g.iloc[j - 1]
    if U == 1:
        return r.close <= S0 - 3 or r.r5 <= r.h5_min15
    if U == 2:
        if j - i0 == 3:                                   # 3rd completed bar: flow persistence check
            w = g.iloc[i0 + 1:j + 1]
            return not bool(((w.r5c > 0) & (w.r5p < 0)).all())
        return False
    if U == 3:
        return r.close <= S0 - 3 or (r.r5 < 0 and p.r5 < 0)
    if U == 4:
        return (r.r5 < 0 and r.r5p < 0) and (p.r5 < 0 and p.r5p < 0)
    if U == 5:
        return (r.r5 > 0 and r.r5c > 0) and (p.r5 > 0 and p.r5c > 0)
    if U == 6:
        return (r.r5c <= 0 and r.r5p >= 0) and (p.r5c <= 0 and p.r5p >= 0)
    return False


def run_day(g: pd.DataFrame, rules: list[int]) -> list[dict]:
    trades = []
    free_at = -1
    n = len(g)
    for i in range(2, n - 1):
        t = int(g["min"].iloc[i])
        if t <= free_at:
            continue
        fired = next((U for U in sorted(rules) if arm_trigger(g, i, U)), None)
        if fired is None:
            continue
        U = fired; side = SIDE[U]
        S0 = float(g.open.iloc[i + 1]); worst = S0
        end = min(i + 1 + TIMEOUT[U], n - 1)
        result, texit, exit_px = "timeout", None, None
        for j in range(i + 1, end + 1):
            hi, lo = float(g.high.iloc[j]), float(g.low.iloc[j])
            worst = min(worst, lo) if side == "sell" else max(worst, hi)
            done = (hi >= S0 + 3) if side == "sell" else (lo <= S0 - 3)
            if done:
                result, texit = "fill", j - i; exit_px = S0 + 3 if side == "sell" else S0 - 3
                break
            if j > i + 1 and scratch_hit(g, U, i, j, S0):
                result, texit = "scratch", j - i
                exit_px = float(g.open.iloc[j + 1]) if j + 1 < n else float(g.close.iloc[j])
                break
        if texit is None:
            texit = end - i; exit_px = float(g.close.iloc[end])
        adverse = (S0 - worst) if side == "sell" else (worst - S0)
        pnl_pts = (exit_px - S0) if side == "sell" else (S0 - exit_px)     # leg-level move to exit (proxy)
        trades.append(dict(day=g.day.iloc[0], U=U, side=side, t=t, S0=S0, result=result,
                           mins=texit, adverse=round(adverse, 2), move=round(pnl_pts, 2)))
        free_at = int(g["min"].iloc[min(i + texit, n - 1)]) + COOLDOWN
    return trades


def main() -> None:
    df = pd.read_parquet(LAB)
    days = sorted(df.day.unique())
    pd.set_option("display.width", 240)
    all_rules = [1, 2, 3, 4, 5, 6]
    # per-rule solo stats
    rows = []
    for U in all_rules:
        tr = []
        for d in days:
            tr += run_day(prep(df[df.day == d]), [U])
        tr = pd.DataFrame(tr)
        if not len(tr):
            rows.append(dict(U=U, n=0)); print(f"U{U}: no trades"); continue
        byday = tr.groupby("day").size()
        rows.append(dict(U=U, side=SIDE[U], n=len(tr), days_fired=len(byday), days_2plus=int((byday >= 2).sum()),
                         fill=float((tr.result == "fill").mean()), scratch=float((tr.result == "scratch").mean()),
                         med_min=float(tr[tr.result == "fill"].mins.median()) if (tr.result == "fill").any() else np.nan,
                         adv_max=float(tr.adverse.max()), adv10=float((tr.adverse > 10).mean())))
        print(f"U{U} {SIDE[U]:4s} n={len(tr):2d} days={len(byday)}/{len(days)} ≥2/day on {int((byday>=2).sum())} | "
              f"fill {(tr.result=='fill').mean():.2f} scratch {(tr.result=='scratch').mean():.2f} | "
              f"med fill {tr[tr.result=='fill'].mins.median() if (tr.result=='fill').any() else float('nan'):.0f}m | "
              f"adv>10 {(tr.adverse>10).mean():.2f} max adv {tr.adverse.max():.1f}")
    # portfolio: all six with priority + one-leg + cooldown
    port = []
    for d in days:
        port += run_day(prep(df[df.day == d]), all_rules)
    port = pd.DataFrame(port); port.to_csv("docs/replay/hiro/union_trades.csv", index=False)
    byday = port.groupby("day").agg(n=("U", "size"), fills=("result", lambda s: (s == "fill").sum()),
                                    scr=("result", lambda s: (s == "scratch").sum()), adv=("adverse", "max"))
    print("\nPORTFOLIO (U1–U6, one leg, 30-min cooldown):")
    print(byday.to_string())
    f = port[port.result == "fill"]
    print(f"\ntotal {len(port)} trades / {len(days)} days = {len(port)/len(days):.1f} per day | fills {len(f)} "
          f"({(port.result=='fill').mean():.2f}) | plantings/day: min {byday.fills.min()} med {byday.fills.median():.0f} max {byday.fills.max()} | "
          f"days with 1–3 plantings: {int(byday.fills.between(1,3).sum())}/{len(days)} | adv>10 {(port.adverse>10).mean():.2f} max {port.adverse.max():.1f}")
    print("\nby rule inside portfolio:"); print(port.groupby('U').agg(n=('U','size'),fills=('result',lambda s:(s=='fill').sum())).to_string())
    print("\ntrade log:"); print(port.assign(t=port.t.map(lambda x: f"{x//60:02d}:{x%60:02d}")).to_string(index=False))


if __name__ == "__main__":
    main()
