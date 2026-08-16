"""Replay the white paper's 50/20-anchor Delta Bomb sequence on real SPXW 5-min quotes.

Data: ~/Dev/central_trade_data/thetadata/lrrf_spxw_1550_5m_2026-08-10-v1/raw/greeks/<date>/
(ThetaData option_history_greeks_first_order, 5-min bars 09:30-15:50 ET, all PUT strikes
of the 25-40 DTE expiry nearest 30 DTE, with bid/ask/delta/IV/underlying).

Rules (mechanical, conservative):
  t0 (first bar with quotes, 09:35): BTO the ~50d put at ASK, STO the ~20d put (K) at BID.
  Then alternate resting limit orders, evaluated on 5-min bar quotes:
    - short leg open at price s  -> rest BTO K+5 @ (s - c); fills when ask(K+5) <= limit
    - long K+5 filled at price b -> rest STO K   @ (b + c); fills when bid(K)   >= limit
  Fill price = the limit. Only one unpaired short at any time (anchor covers it).
  15:50: STC the anchor at BID. Anything unpaired is reported as-is.
"""
from __future__ import annotations
import argparse, glob, json, os, sys
import pandas as pd

ROOT = os.path.expanduser("~/Dev/central_trade_data/thetadata/lrrf_spxw_1550_5m_2026-08-10-v1/raw/greeks")


def load(date: str) -> pd.DataFrame:
    f = glob.glob(f"{ROOT}/{date}/*.parquet")
    if not f:
        raise SystemExit(f"no greeks file for {date}")
    g = pd.read_parquet(f[0])
    g = g[(g.bid > 0) & (g.ask > 0)].copy()
    g["t"] = g.timestamp.dt.strftime("%H:%M")
    return g


def q(g: pd.DataFrame, t: str, k: float):
    r = g[(g.t == t) & (g.strike == k)]
    return None if r.empty else r.iloc[0]


def replay(date: str, credit: float, width: float = 5.0, start: str = "09:35", verbose: bool = True):
    g = load(date)
    times = sorted(g.t.unique())
    times = [t for t in times if t >= start]
    exp = g.expiration.iloc[0]
    t0 = times[0]
    bar0 = g[g.t == t0]
    k50 = bar0.iloc[(bar0.delta + 0.50).abs().argsort()[:1]].strike.iloc[0]
    k20 = bar0.iloc[(bar0.delta + 0.20).abs().argsort()[:1]].strike.iloc[0]
    if q(g, t0, k20 + width) is None:
        raise SystemExit(f"{date}: no strike {k20+width}")
    a = q(g, t0, k50); s = q(g, t0, k20)
    log = []
    def ev(t, action, px, note, book):
        u = g[g.t == t].underlying_price.dropna()
        log.append(dict(t=t, spx=round(float(u.iloc[0]), 2) if len(u) else None, action=action, px=px, note=note, book=book))
    anchor_px = float(a.ask); short_px = float(s.bid)
    ev(t0, f"BTO {int(k50)}P (anchor, {a.delta:.2f}d)", anchor_px, f"bid/ask {a.bid}/{a.ask}", f"+{int(k50)}P")
    ev(t0, f"STO {int(k20)}P ({s.delta:.2f}d)", short_px, f"bid/ask {s.bid}/{s.ask}", f"+{int(k50)}P -{int(k20)}P")
    bombs = []           # list of (short_px, long_px)
    state = "short_open"  # or "flat"
    limit = short_px - credit
    for t in times[1:]:
        if state == "short_open":
            r = q(g, t, k20 + width)
            if r is not None and r.ask <= limit:
                bombs.append((short_px, limit))
                ev(t, f"BTO {int(k20+width)}P  (limit {limit:.2f}, ask {r.ask})", limit,
                   f"bomb #{len(bombs)} planted: {int(k20+width)}/{int(k20)} for +{short_px-limit:.2f} credit",
                   f"+{int(k50)}P + {len(bombs)} bombs")
                state = "flat"; limit = limit + credit
        else:
            r = q(g, t, k20)
            if r is not None and r.bid >= limit:
                short_px = limit
                ev(t, f"STO {int(k20)}P  (limit {limit:.2f}, bid {r.bid})", limit,
                   "covered by anchor (wide debit spread) until the K+5 fills",
                   f"+{int(k50)}P -{int(k20)}P + {len(bombs)} bombs")
                state = "short_open"; limit = short_px - credit
    tl = times[-1]
    a_end = q(g, tl, k50)
    anchor_close = float(a_end.bid) if a_end is not None else None
    ev(tl, f"STC {int(k50)}P (anchor)", anchor_close, f"anchor P&L {anchor_close-anchor_px:+.2f}", f"{len(bombs)} bombs" + (f" + unpaired short {int(k20)}P" if state=="short_open" else ""))
    # marks
    m_long = q(g, tl, k20 + width); m_short = q(g, tl, k20)
    bomb_mark = None
    if m_long is not None and m_short is not None:
        bomb_mark = round((m_long.bid + m_long.ask) / 2 - (m_short.bid + m_short.ask) / 2, 2)
    u = g.dropna(subset=["underlying_price"]).groupby("t").underlying_price.first()
    res = dict(date=date, exp=exp, dte=(pd.Timestamp(exp) - pd.Timestamp(date)).days, k50=k50, k20=k20, width=width, credit_target=credit,
               spx_open=round(float(u.iloc[0]), 2), spx_lo=round(float(u.min()), 2), spx_hi=round(float(u.max()), 2), spx_last=round(float(u.iloc[-1]), 2),
               bombs=len(bombs), credits=[round(s_ - l_, 2) for s_, l_ in bombs], total_credit=round(sum(s_ - l_ for s_, l_ in bombs), 2),
               anchor_open=anchor_px, anchor_close=anchor_close, anchor_pnl=round(anchor_close - anchor_px, 2) if anchor_close else None,
               unpaired_short=(state == "short_open"), unpaired_short_px=short_px if state == "short_open" else None,
               bomb_mark_1550=bomb_mark, log=log)
    if verbose:
        print(f"\n=== {date}  exp {exp} ({res['dte']} DTE)  anchor {int(k50)}P  base {int(k20)}P  width {width}  target credit {credit}")
        print(f"SPX open {res['spx_open']} lo {res['spx_lo']} hi {res['spx_hi']} last {res['spx_last']}")
        for e in log:
            print(f"  {e['t']}  SPX {e['spx']:>8}  {e['action']:<38} @ {e['px']:>7.2f}   {e['note']:<55} book: {e['book']}")
        print(f"bombs {len(bombs)}  credits {res['credits']}  total {res['total_credit']}  anchor P&L {res['anchor_pnl']}  bomb mark @15:50 {bomb_mark}  unpaired short: {res['unpaired_short']}")
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("dates", nargs="+")
    ap.add_argument("--credit", type=float, default=0.50)
    ap.add_argument("--width", type=float, default=5.0)
    ap.add_argument("--json", help="write results json here")
    args = ap.parse_args()
    out = [replay(d, args.credit, args.width) for d in args.dates]
    if args.json:
        json.dump(out, open(args.json, "w"), indent=1, default=str)
