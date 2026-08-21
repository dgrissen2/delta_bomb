"""Local dashboard: where the 'early synchronized HIRO turn on a pullback' setup fires, per session.

Rules (docs/specs/spx_1min_delta_bomb_leg_in_strategy.md §5.9 / §6): L = cumulative all-total ($B) since 09:30, Lc/Lp, N = nextExp;
trough-anchored run broken by a 0.6 $B drawdown; FIRE when dur ≥ 10, rate ≥ 2 $B/hr, ΔC>0 & ΔP>0 with min/max ≥ 0.25,
ΔN>0 & ΔN/run ≥ 0.5, drawdown < 0.6, 30-bar price pullback ≥ 3, clock 09:35–15:45. STEEP/LATE = rate ≥ 4 & 30-min flow ≥ 1 $B.
Outcomes from the next bar's open: +3/+5 within 30/60 min, adverse before.

Style: TradingView-ish dark Plotly (as in spy_chaser down_trend_selling carousels); one tab per session; offline single HTML.
Run: ~/Dev/virtualenvs/gamma_chaser/bin/python scripts/hiro_setup_dashboard.py
Out: docs/dashboard/hiro_setup_dashboard.html (open locally)
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

V = "/Users/dgrissen/Dev/central_trade_data/spotgamma/hiro/sp500_basket/v1"
SPX = os.path.expanduser("~/Dev/central_trade_data/thetadata/spx_index_1m_ohlc")
OUT = "docs/dashboard/hiro_setup_dashboard.html"
DAYS = ["2026-08-12", "2026-08-13", "2026-08-14", "2026-08-17", "2026-08-18", "2026-08-19", "2026-08-20", "2026-08-21"]
REV, DUR_MIN, RATE_MIN, CPR_MIN, SHARE_MIN, PULL_MIN, STEEP_RATE, STEEP_FLOW = 0.6, 10, 2.0, 0.25, 0.5, 3.0, 4.0, 1.0
FIRST, LAST = 575, 945

BG, GRID, TXT = "#131722", "#2a2e39", "#d1d4dc"
UP, DN = "#26a69a", "#ef5350"
C_ALL, C_CALL, C_PUT, C_NEXT, C_FLOW = "#42a5f5", "#66bb6a", "#ffa726", "#29b6f6", "#ab47bc"


def load_day(day: str) -> pd.DataFrame:
    h = pd.read_csv(f"{V}/date={day}/normalized/hiro_series.csv")
    h["ts"] = pd.to_datetime(h.utc_iso, utc=True).dt.tz_convert("America/New_York")
    h["min"] = h.ts.dt.hour * 60 + h.ts.dt.minute
    h = h[(h["min"] >= 570) & (h["min"] <= 960)]
    out = pd.DataFrame({"min": range(570, 961)})
    for grp, g in h.groupby("series_group"):
        mm = g.groupby("min").agg(dT=("delta_total", "sum"), dC=("delta_call", "sum"), dP=("delta_put", "sum")).reindex(range(570, 961), fill_value=0.0) / 1e9
        out[f"{grp}_L"] = mm.dT.cumsum().values; out[f"{grp}_Lc"] = mm.dC.cumsum().values; out[f"{grp}_Lp"] = mm.dP.cumsum().values
    px = pd.read_parquet(f"{SPX}/{day}.parquet").sort_values("min")
    df = out.merge(px, on="min", how="inner").reset_index(drop=True)
    df["r15"] = df.all_L.diff(15); df["r30"] = df.all_L.diff(30); df["n_r15"] = df.nextExp_L.diff(15)
    df["pull"] = df.close.rolling(30, min_periods=5).max() - df.close
    return df


def detect(df: pd.DataFrame) -> pd.DataFrame:
    L, Lc, Lp, N, t = df.all_L.values, df.all_Lc.values, df.all_Lp.values, df.nextExp_L.values, df["min"].values
    lo = hi = 0
    run = np.zeros(len(df)); dur = np.zeros(len(df)); dC = np.zeros(len(df)); dP = np.zeros(len(df)); dN = np.zeros(len(df)); dd = np.zeros(len(df)); broke = np.zeros(len(df), bool)
    for i in range(len(df)):
        if L[i] < L[lo]:
            lo = hi = i
        if L[i] > L[hi]:
            hi = i
        d = L[hi] - L[i]
        if d >= REV:
            lo = hi = i; d = 0.0; broke[i] = True
        run[i] = L[i] - L[lo]; dur[i] = t[i] - t[lo]; dC[i] = Lc[i] - Lc[lo]; dP[i] = Lp[i] - Lp[lo]; dN[i] = N[i] - N[lo]; dd[i] = d
    df = df.assign(run=run, dur=dur, dC=dC, dP=dP, dN=dN, dd=dd, broke=broke)
    df["rate"] = df.run / df.dur.clip(lower=1) * 60
    df["cpr"] = np.minimum(df.dC, df.dP) / np.maximum(df.dC, df.dP).replace(0, np.nan)
    df["share"] = df.dN / df.run.replace(0, np.nan)
    aligned = (df.dur >= DUR_MIN) & (df.rate >= RATE_MIN) & (df.dC > 0) & (df.dP > 0) & (df.cpr >= CPR_MIN) & (df.dN > 0) & (df.share >= SHARE_MIN) & (df.dd < REV)
    df["steep"] = aligned & (df.rate >= STEEP_RATE) & (df.r30 >= STEEP_FLOW)
    df["fire"] = aligned & (df.pull >= PULL_MIN) & (df["min"] >= FIRST) & (df["min"] <= LAST)
    # one entry per episode: first minute of each run of fires (gap ≤ 2 min)
    f = df.index[df.fire].to_numpy()
    first = np.zeros(len(df), bool)
    if len(f):
        first[f[0]] = True
        for a, b in zip(f[:-1], f[1:]):
            if df["min"][b] - df["min"][a] > 2:
                first[b] = True
    df["fire_first"] = first
    # outcomes from next bar open
    o = df.open.values; H = df.high.values; Lw = df.low.values
    up3 = []; up5 = []; adv = []; pe = []
    for i in range(len(df)):
        if i + 1 >= len(df):
            up3.append(np.nan); up5.append(np.nan); adv.append(np.nan); pe.append(np.nan); continue
        p = o[i + 1]; h = H[i + 1:i + 61]; l = Lw[i + 1:i + 61]
        i3 = int(np.argmax(h >= p + 3)) + 1 if (h >= p + 3).any() else np.nan
        i5 = int(np.argmax(h >= p + 5)) + 1 if (h >= p + 5).any() else np.nan
        seg = l[: int(i3) - 1] if not np.isnan(i3) else l
        up3.append(i3); up5.append(i5); adv.append(max(0.0, p - seg.min()) if len(seg) else 0.0); pe.append(p)
    df["min_to_3"] = up3; df["min_to_5"] = up5; df["adv_before_3"] = adv; df["p_entry"] = pe
    return df


def hhmm(m: int) -> str:
    return f"{int(m) // 60:02d}:{int(m) % 60:02d}"


def day_fig(day: str, df: pd.DataFrame) -> go.Figure:
    x = [f"{day} {hhmm(m)}" for m in df["min"]]
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.50, 0.30, 0.20], vertical_spacing=0.03,
                        subplot_titles=(f"SPX 1-min — {day}   ▲ = setup fires (first minute of episode)   shaded = steep/late state (no entry)",
                                        "HIRO cumulative since 09:30 ($B) — all total / calls / puts / nextExp total",
                                        "Rolling 15-min flow ($B): all and nextExp   |   run rate ($B/hr, dashed)"))
    fig.add_trace(go.Candlestick(x=x, open=df.open, high=df.high, low=df.low, close=df.close, name="SPX",
                                 increasing_line_color=UP, decreasing_line_color=DN, increasing_fillcolor=UP, decreasing_fillcolor=DN, showlegend=False), 1, 1)
    # steep/late shading
    st = df.steep.values
    i = 0
    while i < len(st):
        if st[i]:
            j = i
            while j + 1 < len(st) and st[j + 1]:
                j += 1
            fig.add_vrect(x0=x[i], x1=x[j], fillcolor="rgba(239,83,80,0.18)", line_width=0, row="all", col=1)
            i = j + 1
        else:
            i += 1
    # fires
    ff = df[df.fire_first]
    if len(ff):
        txt = [f"{hhmm(m)} entry {p:.1f}<br>run {r:.2f}$B/{int(d)}m rate {ra:.1f}<br>ΔC {c:.2f} ΔP {pp:.2f} ΔN {n:.2f} share {s:.2f}<br>pullback {pl:.1f} | +3 in {('%.0f' % m3) if not np.isnan(m3) else '—'}m, +5 in {('%.0f' % m5) if not np.isnan(m5) else '—'}m, adverse {a:.1f}"
               for m, p, r, d, ra, c, pp, n, s, pl, m3, m5, a in zip(ff["min"], ff.p_entry, ff.run, ff.dur, ff.rate, ff.dC, ff.dP, ff.dN, ff.share, ff.pull, ff.min_to_3, ff.min_to_5, ff.adv_before_3)]
        col = [UP if not np.isnan(m5) else ("#f6c945" if not np.isnan(m3) else DN) for m3, m5 in zip(ff.min_to_3, ff.min_to_5)]
        fig.add_trace(go.Scatter(x=[f"{day} {hhmm(m)}" for m in ff["min"]], y=ff.low - 1.5, mode="markers", name="setup fires",
                                 marker=dict(symbol="triangle-up", size=14, color=col, line=dict(width=1, color="#fff")), text=txt, hoverinfo="text"), 1, 1)
        # all fire minutes (small dots)
        fa = df[df.fire & ~df.fire_first]
        if len(fa):
            fig.add_trace(go.Scatter(x=[f"{day} {hhmm(m)}" for m in fa["min"]], y=fa.low - 1.0, mode="markers", name="setup holds",
                                     marker=dict(symbol="circle", size=5, color="#9e9e9e"), hoverinfo="skip"), 1, 1)
    # run-break markers (flow shut-off)
    bk = df[df.broke & (df["min"] >= FIRST)]
    if len(bk):
        fig.add_trace(go.Scatter(x=[f"{day} {hhmm(m)}" for m in bk["min"]], y=bk.all_L, mode="markers", name="run broken (−0.6$B)",
                                 marker=dict(symbol="x", size=8, color=DN)), 2, 1)
    for col_, name, c in (("all_L", "all total", C_ALL), ("all_Lc", "calls", C_CALL), ("all_Lp", "puts", C_PUT), ("nextExp_L", "nextExp total", C_NEXT)):
        fig.add_trace(go.Scatter(x=x, y=df[col_], mode="lines", name=name, line=dict(color=c, width=1.6 if col_ in ("all_L", "nextExp_L") else 1.1, dash="dot" if col_ == "nextExp_L" else "solid")), 2, 1)
    fig.add_trace(go.Bar(x=x, y=df.r15, name="all 15-min flow", marker_color=[UP if v >= 0 else DN for v in df.r15.fillna(0)], opacity=0.7), 3, 1)
    fig.add_trace(go.Scatter(x=x, y=df.n_r15, mode="lines", name="nextExp 15-min flow", line=dict(color=C_NEXT, width=1.2)), 3, 1)
    fig.add_trace(go.Scatter(x=x, y=df.rate.where(df.dur >= 5), mode="lines", name="run rate $B/hr", line=dict(color=C_FLOW, width=1.2, dash="dash"), yaxis="y4"), 3, 1)
    fig.add_hline(y=RATE_MIN, line=dict(color=C_FLOW, width=0.8, dash="dot"), row=3, col=1, secondary_y=False)
    fig.update_layout(template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=BG, font=dict(color=TXT, size=11), height=900,
                      margin=dict(l=50, r=20, t=60, b=30), legend=dict(orientation="h", y=1.02, x=0), xaxis_rangeslider_visible=False, dragmode="pan", hovermode="x unified")
    fig.update_xaxes(showgrid=True, gridcolor=GRID, nticks=26, type="category")
    fig.update_yaxes(showgrid=True, gridcolor=GRID, zeroline=False)
    fig.update_yaxes(title_text="SPX", row=1, col=1); fig.update_yaxes(title_text="$B cum", row=2, col=1); fig.update_yaxes(title_text="$B / 15m", row=3, col=1)
    return fig


def main() -> None:
    figs, stats = {}, []
    for d in DAYS:
        df = detect(load_day(d))
        figs[d] = json.loads(pio.to_json(day_fig(d, df)))
        ff = df[df.fire_first]
        stats.append(dict(day=d, episodes=int(len(ff)), hit3_30=float((ff.min_to_3 <= 30).mean()) if len(ff) else np.nan,
                          hit5_30=float((ff.min_to_5 <= 30).mean()) if len(ff) else np.nan, hit5_60=float((ff.min_to_5 <= 60).mean()) if len(ff) else np.nan,
                          adv10=float((ff.adv_before_3 > 10).mean()) if len(ff) else np.nan, steep_min=int(df.steep.sum())))
        df.to_parquet(f"docs/dashboard/hiro_setup_{d}.parquet")
    st = pd.DataFrame(stats)
    rows = "".join(f"<tr><td>{r.day}</td><td>{r.episodes}</td><td>{r.hit3_30:.2f}</td><td>{r.hit5_30:.2f}</td><td>{r.hit5_60:.2f}</td><td>{r.adv10:.2f}</td><td>{r.steep_min}</td></tr>" for r in st.itertuples())
    from plotly.offline import get_plotlyjs
    plotly_js = "<script>" + get_plotlyjs() + "</script>"   # full inline bundle → works offline
    html = f"""<!doctype html><html><head><meta charset="utf-8"><title>HIRO setup dashboard — SPX delta-bomb sell-first</title>
<style>:root{{--bg:{BG};--panel:#1e222d;--bd:{GRID};--txt:{TXT};--mut:#868993;--acc:#2962ff}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--txt);font:13px/1.4 -apple-system,Segoe UI,Roboto,Helvetica,Arial}}
.top{{display:flex;gap:14px;align-items:center;padding:10px 14px;border-bottom:1px solid var(--bd)}} h1{{font-size:15px;margin:0 14px 0 0}}
.tabs{{display:flex;gap:6px}} .tab{{padding:6px 12px;border:1px solid var(--bd);border-radius:6px;cursor:pointer;background:var(--panel);color:var(--mut);font-weight:600}} .tab.on{{color:#fff;border-color:var(--acc);background:#0d2440}}
.rules{{padding:8px 14px;color:var(--mut);border-bottom:1px solid var(--bd)}} code{{color:#9ecbff}}
table{{border-collapse:collapse;margin:8px 14px}} td,th{{border:1px solid var(--bd);padding:4px 8px;text-align:right}} th{{color:var(--mut)}} td:first-child,th:first-child{{text-align:left}}
#chart{{height:900px}}</style>{plotly_js}</head><body>
<div class="top"><h1>HIRO early-turn setup — where it fires (sell-first SPX delta bomb)</h1><div class="tabs" id="tabs"></div></div>
<div class="rules">Fire = trough-anchored HIRO run (broken by −0.6 $B) with <code>dur ≥ {DUR_MIN}m</code>, <code>rate ≥ {RATE_MIN} $B/hr</code>, <code>ΔC>0 & ΔP>0, min/max ≥ {CPR_MIN}</code>, <code>ΔnextExp>0, share ≥ {SHARE_MIN}</code>, <code>drawdown < {REV}</code>, <code>30-bar price pullback ≥ {PULL_MIN} pt</code>, 09:35–15:45; act at next bar open. ▲ green = +5 within 60 min, yellow = +3 only, red = neither. Red shading = steep/late state (<code>rate ≥ {STEEP_RATE}</code> & <code>30-min flow ≥ {STEEP_FLOW} $B</code>) — no new entry. × on the HIRO panel = run broken (flow shut-off). Spot proxy; five positive-gamma sessions; exploratory.</div>
<table><tr><th>day</th><th>episodes</th><th>+3 in 30</th><th>+5 in 30</th><th>+5 in 60</th><th>adverse>10 before +3</th><th>steep minutes</th></tr>{rows}</table>
<div id="chart"></div>
<script>const FIGS={json.dumps(figs)};const DAYS={json.dumps(DAYS)};
function show(d){{document.querySelectorAll('.tab').forEach(e=>e.classList.toggle('on',e.dataset.d===d));const f=FIGS[d];Plotly.react('chart',f.data,f.layout,{{responsive:true,scrollZoom:true,displayModeBar:true}});}}
const tabs=document.getElementById('tabs');DAYS.forEach(d=>{{const b=document.createElement('div');b.className='tab';b.dataset.d=d;b.textContent=d;b.onclick=()=>show(d);tabs.appendChild(b);}});show(DAYS[DAYS.length-1]);</script></body></html>"""
    with open(OUT, "w") as fh:
        fh.write(html)
    print(st.round(2).to_string(index=False)); print("wrote", OUT, f"{os.path.getsize(OUT)/1e6:.1f} MB")


if __name__ == "__main__":
    main()
