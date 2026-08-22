"""UP-trend HIRO confirmation for the sell-first SPX delta bomb — consolidated, reviewable pipeline.

Reproduces §6–§6.2 of docs/specs/spx_1min_delta_bomb_leg_in_strategy.md end-to-end on the five captured sessions:
1. Per-day minute frame from scripts/hiro_setup_dashboard.py parquets (fire rule, steep flag, outcomes at next-bar open).
2. Charlie diagnostics per fire (causal): accel = rate(t..t-5) − rate(t-5..t-10); resp_full = SPX pts since trough / run $B;
   resp_recent = 5-min pts / max(5-min flow, 0.05); giveback = (run peak − L)/run; run consistency.
3. Gates: base fire; simple gates (r15 > 0, clock ≤ 14:30, weak side ≥ 0.15); steep_ok; Q score; early invalidation
   (L ≤ fire-level − 0.3 $B or run break within 3 min, before the +3 touch).
4. Episode-level outcome table + gate comparison vs the clock-matched every-minute baseline.

UP/sell-first only. Spot proxy (+3/+5 SPX touches), five positive-gamma sessions — exploratory.
Run: ~/Dev/virtualenvs/gamma_chaser/bin/python scripts/hiro_uptrend_confirm.py
Out: docs/replay/hiro/hiro_uptrend_fires.csv + printed tables.
"""
from __future__ import annotations

import glob

import numpy as np
import pandas as pd

SETUP_GLOB = "docs/dashboard/hiro_setup_2026-*.parquet"
FIRST_MIN, LATE_MIN = 575, 870          # 09:35 fire window start; 14:30 late cut
INVAL_DROP, INVAL_BARS = 0.3, 3         # early invalidation
REV = 0.6                               # run-break drawdown ($B), must match hiro_setup_dashboard.detect()


def load_frames() -> pd.DataFrame:
    frames = []
    for f in sorted(glob.glob(SETUP_GLOB)):
        g = pd.read_parquet(f).assign(day=f.split("_")[-1][:10]).sort_values("min").reset_index(drop=True)
        L, px = g.all_L.values, g.close.values
        lo = hi = 0
        lo_i = np.zeros(len(g), int); pk = np.zeros(len(g))
        for i in range(len(g)):                       # same trough/peak state machine as detect()
            if L[i] < L[lo]:
                lo = hi = i
            if L[i] > L[hi]:
                hi = i
            if L[hi] - L[i] >= REV:
                lo = hi = i
            lo_i[i] = lo; pk[i] = L[hi]
        Ls = pd.Series(L)
        g["lo_i"] = lo_i; g["L_pk"] = pk
        g["rate_now"] = (Ls - Ls.shift(5)) / 5 * 60
        g["rate_prev"] = (Ls.shift(5) - Ls.shift(10)) / 5 * 60
        g["accel"] = g.rate_now - g.rate_prev
        g["resp_full"] = (px - px[lo_i]) / g.run.replace(0, np.nan)
        g["resp_recent"] = (pd.Series(px) - pd.Series(px).shift(5)) / (Ls - Ls.shift(5)).clip(lower=0.05)
        g["responding"] = g.resp_recent >= 0.5 * g.resp_full
        g["giveback"] = (g.L_pk - g.all_L) / g.run.replace(0, np.nan)
        inc = np.diff(L, prepend=L[0])
        cons = np.full(len(g), np.nan)
        for i in range(len(g)):
            a = lo_i[i]
            if i > a:
                cons[i] = float((np.sign(inc[a + 1:i + 1]) == np.sign(L[i] - L[a])).mean())
        g["cons"] = cons
        frames.append(g)
    return pd.concat(frames).reset_index(drop=True)


def invalidated(fr: pd.DataFrame, r: pd.Series) -> bool:
    g = fr[fr.day == r.day].reset_index(drop=True)
    i = int(g.index[g["min"] == r["min"]][0])
    L0 = g.all_L.iloc[i]
    for j in range(i + 1, min(i + 1 + INVAL_BARS, len(g))):
        if (not np.isnan(r.min_to_3)) and (j - i) >= r.min_to_3:
            break
        if g.all_L.iloc[j] <= L0 - INVAL_DROP or bool(g.broke.iloc[j]):
            return True
    return False


def clock_matched(fr: pd.DataFrame, e: pd.DataFrame, col: str) -> float:
    from hiro_engine.control import clock_weighted_mean   # single home of the weighting (DRY)
    return clock_weighted_mean(fr, e["min"], col)


def main() -> None:
    fr = load_frames()
    fr["w5"] = (fr.min_to_5 <= 60).astype(float)
    fr["w3"] = (fr.min_to_3 <= 30).astype(float)
    fr["a10"] = (fr.adv_before_3 > 10).astype(float)
    e = fr[fr.fire_first & (fr["min"] >= FIRST_MIN)].copy()
    e["minside"] = np.minimum(e.dC, e.dP)
    e["steep_ok"] = (e.accel > 0) & (e.giveback < 0.15) & e.responding.fillna(False)
    e["Q"] = ((e.minside >= 0.15).astype(int) + ((e.dur >= 15) & (e.cons >= 0.6)).astype(int)
              + (e.accel >= 0).astype(int) + (e.giveback < 0.15).astype(int))
    e["inval"] = [invalidated(fr, r) for _, r in e.iterrows()]
    e.to_csv("docs/replay/hiro/hiro_uptrend_fires.csv", index=False)

    pd.set_option("display.width", 240)
    print(f"fires n={len(e)} days={e.day.nunique()} | +5/60 {e.w5.mean():.2f} (clock-matched anytime {clock_matched(fr, e, 'w5'):.2f}) | "
          f"+3/30 {e.w3.mean():.2f} ({clock_matched(fr, e, 'w3'):.2f}) | adverse>10 {e.a10.mean():.2f} ({clock_matched(fr, e, 'a10'):.2f})")
    gates = {
        "r15 > 0": e.r15 > 0,
        "clock ≤ 14:30": e["min"] <= LATE_MIN,
        "weak side ≥ 0.15": e.minside >= 0.15,
        "not invalidated": ~e.inval,
        "SIMPLE (all four)": (e.r15 > 0) & (e["min"] <= LATE_MIN) & (e.minside >= 0.15) & ~e.inval,
        "steep blocked (¬steep ∨ steep_ok)": (~e.steep) | e.steep_ok,
        "Q ≥ 3": e.Q >= 3,
    }
    for name, m in gates.items():
        s, x = e[m], e[~m]
        print(f"{name:34s} keep n={len(s):2d} d={s.day.nunique()} w5={s.w5.mean():.2f} a10={s.a10.mean():.2f} | "
              f"drop n={len(x):2d} w5={x.w5.mean() if len(x) else float('nan'):.2f} a10={x.a10.mean() if len(x) else float('nan'):.2f}")
    s = e[gates["SIMPLE (all four)"]]
    print("\nSIMPLE-gate entries:")
    print(s[["day", "min", "p_entry", "pull", "run", "dur", "rate", "minside", "share", "r15", "accel", "giveback", "steep",
             "min_to_3", "min_to_5", "adv_before_3"]].assign(min=lambda d: d["min"].map(lambda t: f"{t // 60:02d}:{t % 60:02d}")).round(2).to_string(index=False))


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# Executable sequential simulation (added 2026-08-21 after codex-review FAIL):
#  - pre-entry gates only (r15 > 0, clock ≤ 14:30, weak side ≥ 0.15); steep reported both ways (diagnostic);
#  - ONE trade at a time: a fire is skipped while the prior trade is live (until +5 touch, invalidation exit, or 60 min);
#  - invalidation is an EXIT rule: flow ≤ entry-level − 0.3 $B or run break within 3 min of entry and before the +3
#    touch → scratch at that minute's close (outcome recorded as scratch, adverse = adverse-to-exit);
#  - complete horizons only: entries after 15:00 excluded from 60-min statistics;
#  - pullback recomputed with a full 30-bar window (min_periods=30).
# ---------------------------------------------------------------------------
def sequential(fr: pd.DataFrame, use_gates: bool = True, allow_steep: bool = True) -> pd.DataFrame:
    trades = []
    for day, g in fr.groupby("day"):
        g = g.sort_values("min").reset_index(drop=True)
        pull30 = g.close.rolling(30, min_periods=30).max() - g.close      # strict 30-bar pullback
        busy_until = -1
        for i in range(len(g)):
            r = g.iloc[i]
            t = int(r["min"])
            if not bool(r.fire) or t < FIRST_MIN or t > 900:              # complete 60-min horizon required
                continue
            if t <= busy_until:
                continue                                                   # one trade at a time
            if pd.isna(pull30.iloc[i]) or pull30.iloc[i] < 3.0:
                continue
            if use_gates and not ((r.r15 > 0) and (t <= LATE_MIN) and (min(r.dC, r.dP) >= 0.15)):
                continue
            if not allow_steep and bool(r.steep):
                continue
            if i + 1 >= len(g):
                continue
            entry_px = float(g.open.iloc[i + 1]); L0 = float(g.all_L.iloc[i])
            hit3 = hit5 = exit_m = None; scratch = False; low_seen = entry_px
            for j in range(i + 1, min(i + 61, len(g))):
                low_seen = min(low_seen, float(g.low.iloc[j]))
                if hit3 is None and g.high.iloc[j] >= entry_px + 3:
                    hit3 = j - i
                if g.high.iloc[j] >= entry_px + 5:
                    hit5 = j - i; exit_m = j; break
                if hit3 is None and (j - i) <= INVAL_BARS and (g.all_L.iloc[j] <= L0 - INVAL_DROP or bool(g.broke.iloc[j])):
                    scratch = True; exit_m = j; break
            if exit_m is None:
                exit_m = min(i + 60, len(g) - 1)
            busy_until = int(g["min"].iloc[exit_m])
            trades.append(dict(day=day, t=t, entry=entry_px, steep=bool(r.steep), scratch=scratch,
                               win5=hit5 is not None, win3=hit3 is not None and hit3 <= 30,
                               ttf5=hit5, adverse=entry_px - low_seen))
    return pd.DataFrame(trades)


def report_sequential(fr: pd.DataFrame) -> None:
    for lab, kw in (("SEQ no gates", dict(use_gates=False)), ("SEQ pre-entry gates", dict(use_gates=True)),
                    ("SEQ gates, steep excluded", dict(use_gates=True, allow_steep=False))):
        tr = sequential(fr, **kw)
        if not len(tr):
            print(f"{lab}: no trades"); continue
        print(f"{lab:26s} n={len(tr):2d} d={tr.day.nunique()} scratches={int(tr.scratch.sum())} "
              f"win5={tr.win5.mean():.2f} win3_30={tr.win3.mean():.2f} adverse>10={(tr.adverse > 10).mean():.2f} "
              f"med ttf5={tr[tr.win5].ttf5.median() if tr.win5.any() else float('nan')}")
        if kw.get("use_gates") and kw.get("allow_steep", True):
            print(tr.assign(t=tr.t.map(lambda x: f"{x // 60:02d}:{x % 60:02d}")).round(2).to_string(index=False))
