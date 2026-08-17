"""Variants of the Delta Bomb planting sequence, replayed on real SPXW 5-min quotes.

Variants
  anchor        : baseline 50/20 anchor, short-first at K(20d), alternate, STC anchor 15:50 (same as replay_50_20)
  anchor_bomb   : same, but whenever the book is flat (no unpaired 20d short) rest STO (K50-5) @ anchor_cost + c;
                  if it fills the anchor becomes a bomb and the 20d loop stops (no more covered shorts available)
  anchor_bomb_late : same, but only allow bombing the anchor after 14:30 (keep the backstop for the ping-pong first)
  long_first    : NO anchor. BTO K+5 at 09:35 ask, rest STO K @ cost + c, then alternate. Never a naked short.
  ladder3       : NO anchor. Three parallel long-first ladders at (K+5/K), (K+15/K+10), (K+25/K+20).
  fade          : anchor; first leg decided at 10:00 by the 09:35->10:00 move: down -> short-first, up -> long-first
Fill logic identical to replay_50_20: resting limits evaluated on 5-min bid/ask, fill at limit.
"""
from __future__ import annotations
import argparse, sys, warnings
import pandas as pd
warnings.filterwarnings("ignore")
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from replay_50_20 import load  # noqa: E402
from types import SimpleNamespace as _NS

_CACHE = {}
def q(g, t, k):
    """Fast (t, strike) lookup: dict built once per DataFrame."""
    key = id(g)
    if key not in _CACHE:
        _CACHE.clear()
        _CACHE[key] = {(r.t, r.strike): _NS(bid=r.bid, ask=r.ask, delta=r.delta) for r in g.itertuples()}
    return _CACHE[key].get((t, k))


class Ladder:
    """One long-first or short-first ping-pong at strikes (hi=K+w, lo=K)."""
    def __init__(self, lo, hi, c, first, px, t):
        self.lo, self.hi, self.c = lo, hi, c
        self.bombs = []; self.log = []
        if first == "short":
            self.state = "short_open"; self.short_px = px; self.limit = px - c
            self.log.append((t, f"STO {int(lo)}P", px))
        else:
            self.state = "long_open"; self.long_px = px; self.limit = px + c
            self.log.append((t, f"BTO {int(hi)}P", px))
        self.first = first
    def step(self, g, t):
        if self.state == "short_open":
            r = q(g, t, self.hi)
            if r is not None and r.ask <= self.limit:
                self.bombs.append(self.short_px - self.limit); self.log.append((t, f"BTO {int(self.hi)}P", self.limit))
                self.state = "flat_after_long"; self.limit = self.limit + self.c
        elif self.state == "long_open":
            r = q(g, t, self.lo)
            if r is not None and r.bid >= self.limit:
                self.bombs.append(self.limit - self.long_px); self.log.append((t, f"STO {int(self.lo)}P", self.limit))
                self.state = "flat_after_short"; self.limit = self.limit - self.c
        elif self.state == "flat_after_long":   # last fill was a buy at b; rest sell K @ b + c  (short-first family)
            r = q(g, t, self.lo)
            if r is not None and r.bid >= self.limit:
                self.short_px = self.limit; self.log.append((t, f"STO {int(self.lo)}P", self.limit))
                self.state = "short_open"; self.limit = self.short_px - self.c
        elif self.state == "flat_after_short":  # last fill was a sell at s; rest buy K+w @ s - c (long-first family)
            r = q(g, t, self.hi)
            if r is not None and r.ask <= self.limit:
                self.long_px = self.limit; self.log.append((t, f"BTO {int(self.hi)}P", self.limit))
                self.state = "long_open"; self.limit = self.long_px + self.c
    @property
    def unpaired(self):
        return {"short_open": "short", "long_open": "long"}.get(self.state)


def run(date, variant, c=0.50, w=5.0, start="09:35", verbose=False, g=None):
    g = load(date) if g is None else g
    times = [t for t in sorted(g.t.unique()) if t >= start]
    t0 = times[0]; bar0 = g[g.t == t0]
    k50 = bar0.iloc[(bar0.delta + 0.50).abs().argsort()[:1]].strike.iloc[0]
    k20 = bar0.iloc[(bar0.delta + 0.20).abs().argsort()[:1]].strike.iloc[0]
    need = [k20 + w] + ([k20 + 10, k20 + 15, k20 + 20, k20 + 25] if variant in ("ladder3", "short3") else []) + ([k50 - w] if variant.startswith("anchor_bomb") or variant == "long_atm" else [])
    for k in need:
        if q(g, t0, k) is None:
            return None
    res = dict(date=date, variant=variant, k50=k50, k20=k20, anchor_pnl=0.0, anchor_bombed=False, bombs=0, credits=[], leftover_long_pnl=0.0, unpaired_short=False, log=[])
    ladders = []
    anchor_px = None
    if variant in ("anchor", "anchor_bomb", "anchor_bomb_late", "fade"):
        anchor_px = float(q(g, t0, k50).ask); res["log"].append((t0, f"BTO {int(k50)}P anchor", anchor_px))
    if variant in ("anchor", "anchor_bomb", "anchor_bomb_late"):
        ladders.append(Ladder(k20, k20 + w, c, "short", float(q(g, t0, k20).bid), t0))
    elif variant == "long_first":
        ladders.append(Ladder(k20, k20 + w, c, "long", float(q(g, t0, k20 + w).ask), t0))
    elif variant == "ladder3":
        for lo in (k20, k20 + 10, k20 + 20):
            ladders.append(Ladder(lo, lo + w, c, "long", float(q(g, t0, lo + w).ask), t0))
    elif variant == "short3":
        for lo in (k20, k20 + 10, k20 + 20):
            ladders.append(Ladder(lo, lo + w, c, "short", float(q(g, t0, lo).bid), t0))
    elif variant == "long_atm":
        ladders.append(Ladder(k50 - w, k50, c, "long", float(q(g, t0, k50).ask), t0))
    elif variant == "fade":
        pass  # decided at 10:00
    anchor_state = "long"  # or "bombed" or "closed"
    u0 = float(g[g.t == t0].underlying_price.dropna().iloc[0])
    for t in times[1:]:
        if variant == "fade" and not ladders and t >= "10:00":
            u = float(g[g.t == t].underlying_price.dropna().iloc[0])
            if u < u0:
                ladders.append(Ladder(k20, k20 + w, c, "short", float(q(g, t, k20).bid), t))
            else:
                ladders.append(Ladder(k20, k20 + w, c, "long", float(q(g, t, k20 + w).ask), t))
        # anchor-bomb check first (priority: converting the decaying ATM long into a free ATM spread)
        if variant.startswith("anchor_bomb") and anchor_state == "long" and all(L.unpaired != "short" for L in ladders) \
                and not (variant == "anchor_bomb_late" and t < "14:30"):
            r = q(g, t, k50 - w)
            if r is not None and r.bid >= anchor_px + c:
                anchor_state = "bombed"; res["anchor_bombed"] = True
                res["log"].append((t, f"STO {int(k50-w)}P -> anchor bomb {int(k50)}/{int(k50-w)}", anchor_px + c))
                res["credits"].append(c)
        for L in ladders:
            if variant.startswith("anchor_bomb") and anchor_state == "bombed" and L.unpaired is None:
                continue  # no backstop -> don't open new shorts
            L.step(g, t)
    tl = times[-1]
    if anchor_px is not None:
        if anchor_state == "long":
            bid = float(q(g, tl, k50).bid); res["anchor_pnl"] = round(bid - anchor_px, 2); res["log"].append((tl, f"STC {int(k50)}P anchor", bid))
        else:
            ml = q(g, tl, k50); ms = q(g, tl, k50 - w)
            res["anchor_bomb_mark"] = round((ml.bid + ml.ask) / 2 - (ms.bid + ms.ask) / 2, 2)
    for L in ladders:
        res["bombs"] += len(L.bombs); res["credits"] += [round(x, 2) for x in L.bombs]; res["log"] += L.log
        if L.unpaired == "short": res["unpaired_short"] = True
        if L.unpaired == "long":
            r = q(g, tl, L.hi); res["leftover_long_pnl"] += round(float(r.bid) - L.long_px, 2)
    res["total_credit"] = round(sum(res["credits"]), 2)
    # --- day P&L: cash flows + 15:50 marks (bombs at mid, unpaired long at bid, unpaired short at ask, anchor at bid / bomb at mid)
    cash = 0.0; book = 0.0
    for L in ladders:
        for (t_, act, px) in L.log:
            cash += px if act.startswith("STO") else -px
        for _ in L.bombs:
            mh = q(g, tl, L.hi); ml_ = q(g, tl, L.lo)
            book += (mh.bid + mh.ask) / 2 - (ml_.bid + ml_.ask) / 2
        if L.unpaired == "long": book += float(q(g, tl, L.hi).bid)
        if L.unpaired == "short": book -= float(q(g, tl, L.lo).ask)
    if anchor_px is not None:
        cash -= anchor_px
        if anchor_state == "long":
            cash += float(q(g, tl, k50).bid)   # closed at 15:50
        else:
            cash += anchor_px + c              # the STO of K50-w
            book += res["anchor_bomb_mark"]
    res["cash"] = round(cash, 2); res["book_1550"] = round(book, 2); res["day_pnl"] = round(cash + book, 2)
    res["log"].sort()
    if verbose:
        print(f"\n=== {date} {variant}  k50 {int(k50)} k20 {int(k20)}")
        for e in res["log"]:
            u = g[g.t == e[0]].underlying_price.dropna(); print(f"  {e[0]}  SPX {float(u.iloc[0]) if len(u) else float('nan'):8.2f}  {e[1]:<42} @ {e[2]:7.2f}")
        print(f"  bombs {res['bombs']} credits {res['credits']} anchor_pnl {res['anchor_pnl']} anchor_bombed {res['anchor_bombed']} mark {res.get('anchor_bomb_mark')} leftover_long_pnl {res['leftover_long_pnl']} unpaired_short {res['unpaired_short']}  cash {res['cash']} book@15:50 {res['book_1550']} dayPnL {res['day_pnl']}")
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--dates", nargs="*"); ap.add_argument("--variants", nargs="+", default=["anchor", "anchor_bomb", "anchor_bomb_late", "long_first", "long_atm", "ladder3", "short3", "fade"]); ap.add_argument("--credit", type=float, default=0.5); ap.add_argument("--scan", help="csv of dates (col date)"); ap.add_argument("--out")
    a = ap.parse_args()
    if a.scan:
        days = pd.read_csv(a.scan); days = days[days.has5].date.tolist()
        rows = []
        for d in days:
            g = load(d)
            for v in a.variants:
                r = run(d, v, a.credit, g=g)
                if r: rows.append({k: r[k] for k in ("date", "variant", "bombs", "total_credit", "anchor_pnl", "anchor_bombed", "leftover_long_pnl", "unpaired_short", "cash", "book_1550", "day_pnl")} | {"anchor_bomb_mark": r.get("anchor_bomb_mark")})
        df = pd.DataFrame(rows)
        if a.out: df.to_csv(a.out, index=False)
        for v, s in df.groupby("variant"):
            dist = s.bombs.value_counts().sort_index().to_dict()
            print(f"{v:17s} n={len(s):3d} bombs {dist}  mean {s.bombs.mean():.2f}  P(>=2) {(s.bombs>=2).mean():.2f} P(>=3) {(s.bombs>=3).mean():.2f}  credit {s.total_credit.mean():.2f}  anchor {s.anchor_pnl.mean():.2f}  bombed {s.anchor_bombed.mean():.2f}  unpaired_short {s.unpaired_short.mean():.2f}  dayPnL mean {s.day_pnl.mean():.2f} med {s.day_pnl.median():.2f} min {s.day_pnl.min():.1f} max {s.day_pnl.max():.1f}  book {s.book_1550.mean():.2f}")
    else:
        for d in a.dates:
            for v in a.variants:
                run(d, v, a.credit, verbose=True)
