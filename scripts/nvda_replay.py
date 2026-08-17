"""Replay Delta Bomb planting sequences on NVDA 1-min quotes, put side and call side.

Put bomb  = long K+w / short K      (K ~ 20d put).   short-first: STO K on a dip, rest BTO K+w @ s-c.  long-first: BTO K+w, rest STO K @ b+c.
Call bomb = long K / short K+w      (K+w ~ 20d call). short-first: STO K+w on a rip, rest BTO K @ s-c.  long-first: BTO K, rest STO K+w @ b+c.
Variants: anchor (50d long as backstop, serial short-first), long_first, ladder3 (3 parallel long-first), short3 (3 parallel short-first, naked).
Fills at the limit on 1-min NBBO; initial legs cross the spread. Day P&L = cash + 15:59 marks (bombs mid, unpaired long bid, unpaired short ask, anchor bid).
"""
from __future__ import annotations
import argparse, sys, warnings
import pandas as pd
warnings.filterwarnings("ignore")
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from nvda_load import load

class Ladder:
    """One ping-pong. For puts: lo=K (short), hi=K+w (long). For calls: hi=K+w (short), lo=K (long)."""
    def __init__(self, right, short_k, long_k, c, first, px, t):
        self.right, self.sk, self.lk, self.c = right, short_k, long_k, c
        self.bombs, self.log = [], []
        if first == "short":
            self.state, self.short_px, self.limit = "short_open", px, px - c; self.log.append((t, "STO", short_k, px))
        else:
            self.state, self.long_px, self.limit = "long_open", px, px + c; self.log.append((t, "BTO", long_k, px))
    def step(self, Q, t):
        if self.state == "short_open":
            r = Q.get((t, self.lk, self.right))
            if r and r[1] <= self.limit:
                self.bombs.append(self.short_px - self.limit); self.log.append((t, "BTO", self.lk, self.limit)); self.state, self.limit = "flat_after_long", self.limit + self.c
        elif self.state == "long_open":
            r = Q.get((t, self.sk, self.right))
            if r and r[0] >= self.limit:
                self.bombs.append(self.limit - self.long_px); self.log.append((t, "STO", self.sk, self.limit)); self.state, self.limit = "flat_after_short", self.limit - self.c
        elif self.state == "flat_after_long":
            r = Q.get((t, self.sk, self.right))
            if r and r[0] >= self.limit:
                self.short_px = self.limit; self.log.append((t, "STO", self.sk, self.limit)); self.state, self.limit = "short_open", self.limit - self.c
        elif self.state == "flat_after_short":
            r = Q.get((t, self.lk, self.right))
            if r and r[1] <= self.limit:
                self.long_px = self.limit; self.log.append((t, "BTO", self.lk, self.limit)); self.state, self.limit = "long_open", self.limit + self.c
    @property
    def unpaired(self): return {"short_open": "short", "long_open": "long"}.get(self.state)

def build_Q(g):
    return {(r.t, r.strike, r.right): (r.bid, r.ask, r.delta) for r in g.itertuples()}

def run(g, right, variant, c, w=5.0, start="09:35", end="15:59", verbose=False, date=""):
    Q = build_Q(g); times = sorted(t for t in g.t.unique() if start <= t <= end); t0 = times[0]
    b0 = g[(g.t == t0) & (g.right == right)]
    if right == "PUT":
        k50 = b0.iloc[(b0.delta + 0.50).abs().argsort()[:1]].strike.iloc[0]; k20 = b0.iloc[(b0.delta + 0.20).abs().argsort()[:1]].strike.iloc[0]
        pairs = [(k20, k20 + w), (k20 + 10, k20 + 15), (k20 + 20, k20 + 25)]   # (short, long)
    else:
        k50 = b0.iloc[(b0.delta - 0.50).abs().argsort()[:1]].strike.iloc[0]; k20 = b0.iloc[(b0.delta - 0.20).abs().argsort()[:1]].strike.iloc[0]
        pairs = [(k20, k20 - w), (k20 - 10, k20 - 15), (k20 - 20, k20 - 25)]   # (short=K20 call, long=K20-w call)
    for sk, lk in pairs[: (3 if variant in ("ladder3", "short3") else 1)]:
        if (t0, sk, right) not in Q or (t0, lk, right) not in Q: return None
    ladders, anchor_px = [], None
    if variant == "anchor":
        if (t0, k50, right) not in Q: return None
        anchor_px = Q[(t0, k50, right)][1]
        sk, lk = pairs[0]; ladders.append(Ladder(right, sk, lk, c, "short", Q[(t0, sk, right)][0], t0))
    elif variant == "long_first":
        sk, lk = pairs[0]; ladders.append(Ladder(right, sk, lk, c, "long", Q[(t0, lk, right)][1], t0))
    elif variant == "ladder3":
        for sk, lk in pairs: ladders.append(Ladder(right, sk, lk, c, "long", Q[(t0, lk, right)][1], t0))
    elif variant == "short3":
        for sk, lk in pairs: ladders.append(Ladder(right, sk, lk, c, "short", Q[(t0, sk, right)][0], t0))
    for t in times[1:]:
        for L in ladders: L.step(Q, t)
    tl = times[-1]
    def mid(k): r = Q.get((tl, k, right)); return None if r is None else (r[0] + r[1]) / 2
    cash = book = 0.0; bombs = 0; credits = []; log = []; unpaired_short = unpaired_long = 0
    for L in ladders:
        for (t, act, k, px) in L.log:
            cash += px if act == "STO" else -px; log.append((t, act, k, px))
        bombs += len(L.bombs); credits += [round(x, 2) for x in L.bombs]
        for _ in L.bombs:
            m1, m2 = mid(L.lk), mid(L.sk)
            if m1 is not None and m2 is not None: book += (m1 - m2)
        if L.unpaired == "long":
            unpaired_long += 1; r = Q.get((tl, L.lk, right)); book += r[0] if r else 0
        if L.unpaired == "short":
            unpaired_short += 1; r = Q.get((tl, L.sk, right)); book -= r[1] if r else 0
    anchor_pnl = None
    if anchor_px is not None:
        r = Q.get((tl, k50, right)); cash -= anchor_px; cash += r[0]; anchor_pnl = round(r[0] - anchor_px, 2)
    u = g.dropna(subset=["underlying_price"]).groupby("t").underlying_price.first()
    res = dict(date=date, right=right, variant=variant, c=c, k50=k50, k20=k20, bombs=bombs, credits=credits, total_credit=round(sum(credits), 2), anchor_pnl=anchor_pnl,
               unpaired_short=unpaired_short, unpaired_long=unpaired_long, cash=round(cash, 2), book=round(book, 2), day_pnl=round(cash + book, 2),
               u_open=round(float(u.iloc[0]), 2), u_lo=round(float(u.min()), 2), u_hi=round(float(u.max()), 2), u_last=round(float(u.iloc[-1]), 2), log=sorted(log))
    if verbose:
        print(f"\n=== {date} {right} {variant} c={c}  k50 {k50} k20 {k20}  NVDA {res['u_open']} lo {res['u_lo']} hi {res['u_hi']} last {res['u_last']}")
        for (t, act, k, px) in res["log"]:
            uu = g[g.t == t].underlying_price.dropna(); print(f"  {t}  NVDA {float(uu.iloc[0]) if len(uu) else float('nan'):7.2f}  {act} {k:g}{'P' if right=='PUT' else 'C'} @ {px:.2f}")
        print(f"  bombs {bombs} credits {credits} anchor {anchor_pnl} unpaired S/L {unpaired_short}/{unpaired_long} cash {res['cash']} book {res['book']} dayPnL {res['day_pnl']}")
    return res

DATES = ['2026-08-03','2026-08-04','2026-08-05','2026-08-06','2026-08-07','2026-08-10','2026-08-11','2026-08-12','2026-08-13','2026-08-14']
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--exp", default="2026-09-18"); ap.add_argument("--dates", nargs="*", default=DATES)
    ap.add_argument("--rights", nargs="+", default=["PUT", "CALL"]); ap.add_argument("--variants", nargs="+", default=["anchor", "long_first", "ladder3", "short3"])
    ap.add_argument("--credits", nargs="+", type=float, default=[0.05, 0.10, 0.25]); ap.add_argument("--width", type=float, default=5.0); ap.add_argument("--verbose", action="store_true"); ap.add_argument("--out")
    a = ap.parse_args(); rows = []
    for d in a.dates:
        g = load(a.exp, d)
        for right in a.rights:
            for v in a.variants:
                for c in a.credits:
                    r = run(g, right, v, c, a.width, verbose=a.verbose, date=d)
                    if r: rows.append({k: r[k] for k in r if k != "log"})
    df = pd.DataFrame(rows)
    if a.out: df.to_csv(a.out, index=False)
    pd.set_option("display.width", 250)
    for (right, v, c), s in df.groupby(["right", "variant", "c"]):
        print(f"{right:4s} {v:10s} c={c:.2f} n={len(s):2d} bombs {s.bombs.value_counts().sort_index().to_dict()} mean {s.bombs.mean():.2f} credit {s.total_credit.mean():.2f} anchor {s.anchor_pnl.mean() if s.anchor_pnl.notna().any() else 0:.2f} dayPnL mean {s.day_pnl.mean():.2f} med {s.day_pnl.median():.2f} min {s.day_pnl.min():.1f} max {s.day_pnl.max():.1f} unpS {s.unpaired_short.mean():.2f}")
