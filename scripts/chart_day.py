"""Inline-SVG chart of a replay day: SPX 1-min closes with fills, and the two 20d legs with resting limits."""
from __future__ import annotations
import math, sys, warnings
import pandas as pd
warnings.filterwarnings("ignore")
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from replay_50_20 import replay, load

def tm(s): h, m = map(int, s.split(":")); return h * 60 + m
COL = {"anchor": "var(--ink-3)", "sell": "var(--put)", "buy": "var(--call)"}
FONT = "-apple-system,Segoe UI,Helvetica,Arial,sans-serif"; MONO = "SF Mono,Menlo,monospace"

def build(date, credit, out_prefix):
    r = replay(date, credit, 5.0, verbose=False)
    t = pd.read_parquet(f"/Users/dgrissen/Dev/central_trade_data/thetadata/spx_index_1m_ohlc/{date}.parquet")
    g = load(date)
    W, H, H2, ml, mr, mt, mb = 760, 230, 190, 44, 10, 10, 22
    sx = lambda m: ml + (m - 570) / (960 - 570) * (W - ml - mr)
    lo, hi = t.close.min(), t.close.max(); pad = (hi - lo) * 0.08; lo -= pad; hi += pad
    sy = lambda v: mt + (hi - v) / (hi - lo) * (H - mt - mb)
    path = " ".join(f"{'M' if i == 0 else 'L'}{sx(m):.1f},{sy(c):.1f}" for i, (m, c) in enumerate(zip(t["min"], t["close"])))
    step = 10 if hi - lo < 80 else 20
    grid = [(sy(v), v) for v in range(int(math.ceil(lo / step)) * step, int(hi) + 1, step)]
    xt = [(sx(tm(s)), s) for s in ["10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00"]]
    marks, labels = [], []
    seen_anchor = False
    for e in r["log"]:
        m = tm(e["t"]); c = t[t["min"] == m].close
        if c.empty: c = t.iloc[(t["min"] - m).abs().argsort()[:1]].close
        kind = "sell" if e["action"].startswith("STO") else ("anchor" if "anchor" in e["action"] else "buy")
        x, y = sx(m), sy(float(c.iloc[0]))
        if kind == "anchor" and e["t"] == r["log"][0]["t"]:
            if seen_anchor: continue
            seen_anchor = True
        marks.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{COL[kind]}" stroke="var(--surface)" stroke-width="1.5"/>')
        dy = -10 if kind in ("buy", "anchor") else 16
        an = "end" if e["t"] >= "15:40" else ("start" if e["t"] <= "09:40" else "middle")
        lab = e["action"].split("(")[0].strip().split()[0] + " " + e["action"].split()[1]
        labels.append(f'<text x="{x:.1f}" y="{y + dy:.1f}" text-anchor="{an}" font-size="10" fill="{COL[kind]}" font-family="{MONO}">{e["t"]} {lab}</text>')
    svg1 = f'''<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="SPX 1-minute closes on {date} with the fills marked">
<g font-family="{FONT}" font-size="10" fill="var(--ink-3)">
{''.join(f'<line x1="{ml}" x2="{W-mr}" y1="{y:.1f}" y2="{y:.1f}" stroke="var(--rule)" stroke-width="1"/><text x="{ml-4}" y="{y+3:.1f}" text-anchor="end">{v}</text>' for y, v in grid)}
{''.join(f'<text x="{x:.1f}" y="{H-6}" text-anchor="middle">{s}</text>' for x, s in xt)}
</g>
<path d="{path}" fill="none" stroke="var(--ink)" stroke-width="1.4"/>
{''.join(marks)}
{''.join(labels)}
</svg>'''
    k20 = r["k20"]; w = 5.0
    p2 = g[g.strike.isin([k20, k20 + w])].pivot_table(index="t", columns="strike", values=["bid", "ask"])
    b = p2[("bid", k20)]; a = p2[("ask", k20 + w)]
    lo2 = min(b.min(), a.min()) - 0.5; hi2 = max(b.max(), a.max()) + 0.5
    sy2 = lambda v: mt + (hi2 - v) / (hi2 - lo2) * (H2 - mt - mb)
    pb = " ".join(f"{'M' if i == 0 else 'L'}{sx(tm(s)):.1f},{sy2(v):.1f}" for i, (s, v) in enumerate(b.items()))
    pa = " ".join(f"{'M' if i == 0 else 'L'}{sx(tm(s)):.1f},{sy2(v):.1f}" for i, (s, v) in enumerate(a.items()))
    st = 1 if hi2 - lo2 < 8 else 2
    grid2 = [(sy2(v), v) for v in range(int(math.ceil(lo2 / st)) * st, int(hi2) + 1, st)]
    sell_lim = r["log"][1]["px"]; buy_lim = sell_lim - credit
    svg2 = f'''<svg viewBox="0 0 {W} {H2}" width="100%" role="img" aria-label="{int(k20)} put bid and {int(k20+w)} put ask, 5-minute, with resting limits">
<g font-family="{FONT}" font-size="10" fill="var(--ink-3)">
{''.join(f'<line x1="{ml}" x2="{W-mr}" y1="{y:.1f}" y2="{y:.1f}" stroke="var(--rule)" stroke-width="1"/><text x="{ml-4}" y="{y+3:.1f}" text-anchor="end">{v}</text>' for y, v in grid2)}
{''.join(f'<text x="{x:.1f}" y="{H2-6}" text-anchor="middle">{s}</text>' for x, s in xt)}
</g>
<line x1="{ml}" x2="{W-mr}" y1="{sy2(sell_lim):.1f}" y2="{sy2(sell_lim):.1f}" stroke="var(--put)" stroke-dasharray="4 3"/>
<line x1="{ml}" x2="{W-mr}" y1="{sy2(buy_lim):.1f}" y2="{sy2(buy_lim):.1f}" stroke="var(--call)" stroke-dasharray="4 3"/>
<text x="{ml+4}" y="{sy2(sell_lim)-4:.1f}" font-size="10" fill="var(--put)" font-family="{MONO}">rest STO {int(k20)}P @ {sell_lim:.2f} (fills when bid ≥)</text>
<text x="{ml+4}" y="{sy2(buy_lim)+12:.1f}" font-size="10" fill="var(--call)" font-family="{MONO}">rest BTO {int(k20+w)}P @ {buy_lim:.2f} (fills when ask ≤)</text>
<path d="{pb}" fill="none" stroke="var(--put)" stroke-width="1.4"/>
<path d="{pa}" fill="none" stroke="var(--call)" stroke-width="1.4"/>
<text x="{W-mr}" y="14" text-anchor="end" font-size="10" fill="var(--put)" font-family="{FONT}">— {int(k20)}P bid</text>
<text x="{W-mr}" y="27" text-anchor="end" font-size="10" fill="var(--call)" font-family="{FONT}">— {int(k20+w)}P ask</text>
</svg>'''
    open(out_prefix + "_spx.svg", "w").write(svg1); open(out_prefix + "_legs.svg", "w").write(svg2)
    return r

if __name__ == "__main__":
    build(sys.argv[1], float(sys.argv[2]), sys.argv[3])
