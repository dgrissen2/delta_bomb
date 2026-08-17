"""Multi-day BUY-FIRST Delta Bomb cycles on NVDA 1-min data.

cycle(): at entry (date, time) buy the long leg (strike chosen by target delta) at the ask, rest the short leg
(+w for calls / -w for puts) at cost + credit, scan forward across sessions for the first minute the short's bid >= limit,
then track the resulting spread's bid-side value (what you can sell it for) daily and its intraday max, the first day it
trades >= 1.00 / 2.00 / 3.00, and the terminal value. Also reports the 'buy the spread outright' alternative.
"""
from __future__ import annotations
import glob, os, sys
import pandas as pd
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from nvda_load import load, ROOT

def sessions_for(exp: str):
    e = exp.replace("-", "")
    return sorted(os.path.basename(f).split("_")[2][:10] for f in glob.glob(f"{ROOT}/NVDA_{e}_*.parquet"))

def cycle(right, exp, entry_date, entry_time="15:55", target_delta=0.15, width=5.0, credit=0.10, strike=None, verbose=True):
    sess = [d for d in sessions_for(exp) if d >= entry_date]
    if not sess or sess[0] != entry_date: return None
    G = {}
    def g(d):
        if d not in G: G[d] = load(exp, d)
        return G[d]
    g0 = g(entry_date); b = g0[(g0.t == entry_time) & (g0.right == right)]
    if b.empty: return None
    if strike is None:
        tgt = target_delta if right == "CALL" else -target_delta
        strike = float(b.iloc[(b.delta - tgt).abs().argsort()[:1]].strike.iloc[0])
    sk = strike + width if right == "CALL" else strike - width
    L = b[b.strike == strike].iloc[0]; S0 = b[b.strike == sk]
    if S0.empty: return None
    S0 = S0.iloc[0]
    cost = float(L.ask); limit = round(cost + credit, 2); u0 = float(L.underlying_price)
    outright = float(L.ask - S0.bid)
    res = dict(right=right, exp=exp, entry=f"{entry_date} {entry_time}", u0=round(u0, 2), long_k=strike, short_k=sk, long_delta=round(float(L.delta), 3),
               otm_pct=round((strike / u0 - 1) * 100, 1), cost=round(cost, 2), limit=limit, outright_cost=round(outright, 2), fill=None, days_to_fill=None)
    # 1) find the fill
    fill = None
    for i, d in enumerate(sess):
        gg = g(d); s = gg[(gg.strike == sk) & (gg.right == right)].sort_values("timestamp")
        if d == entry_date: s = s[s.t > entry_time]
        hit = s[s.bid >= limit]
        if not hit.empty:
            h = hit.iloc[0]; fill = (d, h.t, float(h.bid), float(h.underlying_price)); res.update(fill=f"{d} {h.t}", fill_u=round(float(h.underlying_price), 2), days_to_fill=i); break
    # 2) track values forward (spread bid-side if paired, else the long's bid)
    track = []
    for d in sess:
        gg = g(d); ts = sorted(gg.t.unique())
        def sb(t):
            a = gg[(gg.t == t) & (gg.strike == strike) & (gg.right == right)]; c2 = gg[(gg.t == t) & (gg.strike == sk) & (gg.right == right)]
            if a.empty or c2.empty: return None
            return float(a.iloc[0].bid - c2.iloc[0].ask)
        vals = [sb(t) for t in ts[::5]]; vals = [v for v in vals if v is not None]
        if not vals: continue
        u = gg.underlying_price.dropna(); track.append(dict(date=d, u_close=round(float(u.iloc[-1]), 2), spread_close=round(vals[-1], 2), spread_hi=round(max(vals), 2)))
    tr = pd.DataFrame(track); res["track"] = tr
    if fill:
        after = tr[tr.date >= fill[0]]
        for lvl in (1.0, 2.0, 3.0, 4.0):
            hit = after[after.spread_hi >= lvl]; res[f"hit_{lvl:.0f}"] = hit.iloc[0].date if not hit.empty else None
        res["max_after_fill"] = round(float(after.spread_hi.max()), 2); res["last"] = round(float(after.spread_close.iloc[-1]), 2); res["last_date"] = after.date.iloc[-1]; res["last_u"] = after.u_close.iloc[-1]
    else:
        # unpaired: mark the long
        lastg = g(sess[-1]); lb = lastg[(lastg.strike == strike) & (lastg.right == right)]
        res["long_last_bid"] = round(float(lb.bid.iloc[-1]), 2) if not lb.empty else None; res["last_date"] = sess[-1]
    if verbose:
        f = res["fill"]
        print(f"{right:4s} {exp} entry {res['entry']} NVDA {u0:.2f}: BTO {strike:g} @ {cost:.2f} (d{res['long_delta']:.2f}, {res['otm_pct']:+.0f}%), rest STO {sk:g} @ {limit:.2f} | outright spread {outright:.2f}"
              + (f" -> PAIRED {f} (NVDA {res['fill_u']}, {res['days_to_fill']} sessions) | after: hit1 {res.get('hit_1')} hit2 {res.get('hit_2')} hit3 {res.get('hit_3')} max {res['max_after_fill']} last {res['last']} @ {res['last_date']} (NVDA {res['last_u']})"
                 if f else f" -> NOT PAIRED by {res['last_date']}; long bid {res.get('long_last_bid')}"))
    return res

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("right"); ap.add_argument("exp"); ap.add_argument("dates", nargs="+"); ap.add_argument("--time", default="15:55"); ap.add_argument("--delta", type=float, default=0.15); ap.add_argument("--credit", type=float, default=0.10); ap.add_argument("--width", type=float, default=5.0)
    a = ap.parse_args()
    for d in a.dates: cycle(a.right, a.exp, d, a.time, a.delta, a.width, a.credit)
