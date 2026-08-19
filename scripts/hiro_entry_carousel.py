"""HIRO early-turn setup — entry-days carousel, in the spy_chaser `build_entry_carousel.py` style
(appendix_separate_l1_l2, 2026-07-13): white Plotly theme, dark header, sticky filter bar, 1060-px chart + sticky
300-px diagnostics panel, one figure per ENTRY on the FULL-DAY SPX 1-min chart, green ▼ at the entry minute with time
label, red band while the leg is live (entry → +5 fill / 60-min clock), VT and open drawn as level shapes, EMA 5/9/20
context, categorical x-axis at −45°, prev/next + arrow keys, winner/loser and early/steep filters.
Bottom panel = HIRO cumulative since 09:30 (all total / calls / puts / nextExp) instead of RSI.

Inputs: docs/dashboard/hiro_setup_<date>.parquet (from scripts/hiro_setup_dashboard.py), SG levels.
Run: ~/Dev/virtualenvs/gamma_chaser/bin/python scripts/hiro_entry_carousel.py
Out: docs/dashboard/hiro_entry_carousel.html
"""
import glob
import json
import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import plotly.offline as pyo
from plotly.subplots import make_subplots

OUT = "docs/dashboard/hiro_entry_carousel.html"
SG = "/Users/dgrissen/Dev/core_spotgamma_spx_vix_data/offset_historical_spotgamma_data.csv"
sg = pd.read_csv(SG).set_index("Date")


def tm(m):
    return f"{int(m) // 60:02d}:{int(m) % 60:02d}"


def fig_for(ds, g, row, vt):
    idxs = list(g["min"]); tv = [tm(m) for m in idxs]
    entry_m = int(row["min"]) + 1                              # leg placed at the NEXT bar's open
    entry_px = float(row.p_entry)
    fill5 = row.min_to_5; fill3 = row.min_to_3
    exit_m = entry_m + (int(fill5) if not np.isnan(fill5) else 60)   # band = live window: entry → +5 fill, else 60-min clock
    exit_m = min(exit_m, idxs[-1])
    opn = float(g.open.iloc[0])
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.74, 0.26], vertical_spacing=0.04)
    # levels as explicit shapes (add_hline is dropped on categorical x)
    for y, c, dash, nm in ((vt, "#1e88e5", "solid", "VT"), (opn, "#9e9e9e", "dot", "open"), (entry_px + 5, "#2e7d32", "dash", "+5 target"), (entry_px - 15, "#c62828", "dash", "cap ≈ sale+3.5 (~15 pt)")):
        if y is None or np.isnan(y):
            continue
        fig.add_shape(type="line", x0=tv[0], x1=tv[-1], y0=y, y1=y, xref="x", yref="y", line=dict(color=c, width=1.3, dash=dash), row=1, col=1)
        fig.add_annotation(x=tv[-1], y=y, text=nm, showarrow=False, xanchor="left", font=dict(size=10, color=c), row=1, col=1)
    # live band: entry → exit, between entry price and +5 target
    x0 = tm(entry_m); x1 = tm(exit_m)
    fig.add_shape(type="rect", x0=x0, x1=x1, y0=entry_px, y1=entry_px + 5, xref="x", yref="y",
                  fillcolor="rgba(46,125,50,0.15)" if not np.isnan(fill5) else "rgba(239,83,80,0.18)", line_width=0, layer="below", row=1, col=1)
    # steep/late shading for the whole day (context)
    st = g.steep.values; i = 0
    while i < len(st):
        if st[i]:
            j = i
            while j + 1 < len(st) and st[j + 1]:
                j += 1
            fig.add_shape(type="rect", x0=tv[i], x1=tv[j], y0=0, y1=1, xref="x", yref="paper", fillcolor="rgba(239,83,80,0.10)", line_width=0, layer="below")
            i = j + 1
        else:
            i += 1
    fig.add_trace(go.Candlestick(x=tv, open=g.open, high=g.high, low=g.low, close=g.close, name="SPX",
                                 increasing_line_color="#26a69a", decreasing_line_color="#ef5350", showlegend=False), row=1, col=1)
    for span, color in ((5, "#f6c945"), (9, "#42a5f5"), (20, "#ab47bc")):
        fig.add_trace(go.Scatter(x=tv, y=g.close.ewm(span=span, adjust=False).mean(), mode="lines", name=f"EMA{span} (context)", line=dict(width=1.2, color=color)), row=1, col=1)
    # all other fires of the day (small), this one emphasized
    others = g[g.fire_first & (g["min"] != row["min"])]
    if len(others):
        fig.add_trace(go.Scatter(x=[tm(m + 1) for m in others["min"]], y=others.high + 1.0, mode="markers", name="other fires",
                                 marker=dict(symbol="triangle-down", size=9, color="#9e9e9e", line=dict(width=1, color="#fff")), showlegend=True), row=1, col=1)
    fig.add_vline(x=x0, line=dict(color="#1b5e20", width=2), row=1, col=1)
    fig.add_trace(go.Scatter(x=[x0], y=[float(g.loc[g["min"] == entry_m, "high"].iloc[0]) + 1.5], mode="markers+text", text=[f"SELL {x0} @ {entry_px:.1f}"], textposition="top center",
                             marker=dict(symbol="triangle-down", size=16, color="#1b5e20", line=dict(width=1, color="#fff")),
                             textfont=dict(size=11, color="#1b5e20"), showlegend=False), row=1, col=1)
    if not np.isnan(fill5):
        fm = tm(min(entry_m + int(fill5) - 1, idxs[-1]))
        fig.add_trace(go.Scatter(x=[fm], y=[entry_px + 5], mode="markers+text", text=[f"+5 ({int(fill5)}m)"], textposition="top center",
                                 marker=dict(symbol="circle", size=9, color="#2e7d32"), showlegend=False), row=1, col=1)
    if not np.isnan(fill3):
        fm = tm(min(entry_m + int(fill3) - 1, idxs[-1]))
        fig.add_trace(go.Scatter(x=[fm], y=[entry_px + 3], mode="markers", marker=dict(symbol="circle-open", size=8, color="#2e7d32"), showlegend=False), row=1, col=1)
    # HIRO panel
    for col, nm, c, w, dash in (("all_L", "HIRO all total", "#1565c0", 1.8, "solid"), ("all_Lc", "calls", "#2e7d32", 1.1, "solid"), ("all_Lp", "puts", "#ef6c00", 1.1, "solid"), ("nextExp_L", "nextExp total", "#0097a7", 1.4, "dot")):
        fig.add_trace(go.Scatter(x=tv, y=g[col], mode="lines", name=nm, line=dict(width=w, color=c, dash=dash)), row=2, col=1)
    fig.add_vline(x=x0, line=dict(color="#1b5e20", width=2), row=2, col=1)
    bk = g[g.broke & (g["min"] >= 575)]
    if len(bk):
        fig.add_trace(go.Scatter(x=[tm(m) for m in bk["min"]], y=bk.all_L, mode="markers", name="run broken (−0.6$B)", marker=dict(symbol="x", size=7, color="#c62828")), row=2, col=1)
    win = not np.isnan(fill5) and fill5 <= 60
    fig.update_layout(title=dict(text=f"<b>{ds}</b> · HIRO early-turn setup · {'+5 FILLED' if win else ('+3 only' if not np.isnan(fill3) else 'NO FILL')} · sell-first SPX delta bomb (spot proxy)", font=dict(size=14)),
                      width=1060, height=690, template="plotly_white", dragmode="pan", margin=dict(l=54, r=150, t=46, b=70), showlegend=True,
                      legend=dict(orientation="h", y=-0.14, x=0, font=dict(size=11)), xaxis_rangeslider_visible=False)
    fig.update_xaxes(type="category", nticks=27, tickangle=-45, showgrid=True, gridcolor="#eee")
    fig.update_yaxes(title_text="SPX", showgrid=True, gridcolor="#eee", row=1, col=1)
    fig.update_yaxes(title_text="HIRO $B (cum 09:30)", showgrid=True, gridcolor="#eee", row=2, col=1)
    return fig


figs, diags, meta = [], [], []
for f in sorted(glob.glob("docs/dashboard/hiro_setup_2026-*.parquet")):
    ds = os.path.basename(f)[11:21]
    g = pd.read_parquet(f).sort_values("min").reset_index(drop=True)
    vt = float(sg.loc[ds, "Vol Trigger"]) if ds in sg.index else np.nan
    for _, row in g[g.fire_first].iterrows():
        fig = fig_for(ds, g, row, vt)
        win = (not np.isnan(row.min_to_5)) and row.min_to_5 <= 60
        figs.append(pio.to_json(fig))
        meta.append({"win": int(win), "steep": int(bool(row.steep)), "ds": ds})
        diags.append(
            f'<div class="dh {"ent" if win else "no"}">{"+5 FILLED" if win else ("+3 ONLY" if not np.isnan(row.min_to_3) else "NO FILL")} <span class="sub">{ds}</span></div>'
            f'<div class="row"><b>Entry (sell) time</b><span class="big">{tm(row["min"] + 1)}</span></div>'
            f'<div class="row"><b>Entry price (next open)</b><span>{row.p_entry:.1f}</span></div>'
            f'<div class="row"><b>Price pullback (30-bar)</b><span class="big">{row.pull:.1f} pt</span></div><hr>'
            f'<div class="row"><b>HIRO run</b><span>{row.run:.2f} $B / {int(row.dur)} m</span></div>'
            f'<div class="row"><b>rate</b><span>{row.rate:.1f} $B/hr {"<span class=sub>(steep)</span>" if row.steep else ""}</span></div>'
            f'<div class="row"><b>Δcalls / Δputs</b><span>{row.dC:+.2f} / {row.dP:+.2f} <span class="sub">ratio {row.cpr:.2f}</span></span></div>'
            f'<div class="row"><b>ΔnextExp / share</b><span>{row.dN:+.2f} / {row.share:.2f}</span></div>'
            f'<div class="row"><b>15-min flow (all)</b><span>{row.r15:+.2f} $B</span></div><hr>'
            f'<div class="row"><b>+3 pts</b><span class="{"g" if not np.isnan(row.min_to_3) else "r"}">{("%d min" % row.min_to_3) if not np.isnan(row.min_to_3) else "—"}</span></div>'
            f'<div class="row"><b>+5 pts</b><span class="{"g" if win else "r"}">{("%d min" % row.min_to_5) if not np.isnan(row.min_to_5) else "— (60m)"}</span></div>'
            f'<div class="row"><b>Adverse before +3</b><span class="{"r" if row.adv_before_3 > 10 else ""}">{row.adv_before_3:.1f} pt</span></div><hr>'
            f'<div class="row"><b>Vol Trigger</b><span>{vt:.0f}</span></div>'
            f'<div class="row"><b>Open</b><span>{g.open.iloc[0]:.0f} <span class="sub">({g.open.iloc[0]-vt:+.0f} vs VT)</span></span></div>')

nW = sum(m["win"] for m in meta); nL = len(meta) - nW
doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>HIRO early-turn setup — entry days</title>
<script>{pyo.get_plotlyjs()}</script>
<style>
 body{{font-family:-apple-system,Helvetica,Arial,sans-serif;margin:0;background:#fafafa}}
 header{{background:#1b1b2f;color:#fff;padding:10px 16px}} header h1{{margin:0;font-size:16px}} header p{{margin:4px 0 0;font-size:12px;color:#bbb}}
 .bar{{position:sticky;top:0;background:#fff;border-bottom:1px solid #ddd;padding:8px 16px;z-index:9;display:flex;gap:6px;align-items:center;flex-wrap:wrap}}
 button{{font-size:13px;padding:5px 11px;cursor:pointer;border:1px solid #888;border-radius:6px;background:#fff}} button.on{{background:#1b5e20;color:#fff;border-color:#1b5e20}}
 .sep{{width:1px;height:22px;background:#ddd;margin:0 4px}} #counter{{font-size:13px;color:#333;margin-left:auto}}
 #stage{{display:flex;gap:12px;align-items:flex-start;padding:8px 12px}} #chart{{flex:0 0 auto;width:1060px}}
 #panel{{flex:0 0 300px;max-width:300px;position:sticky;top:56px;background:#fff;border:1px solid #e0e0e0;border-radius:8px;padding:12px 14px;font-size:13px}}
 .dh{{font-weight:700;font-size:16px;padding:7px 9px;border-radius:6px;margin-bottom:10px}} .dh.ent{{background:#1b5e20;color:#fff}} .dh.no{{background:#b71c1c;color:#fff}} .dh .sub{{font-weight:400;font-size:12px}}
 .row{{display:flex;justify-content:space-between;align-items:baseline;padding:3px 2px;border-bottom:1px solid #f2f2f2}} .row b{{color:#455a64;font-weight:600}}
 .big{{font-size:18px;font-weight:800;color:#111}} .sub{{color:#888;font-size:11px}} .g{{color:#2e7d32;font-weight:700}} .r{{color:#c62828;font-weight:700}} hr{{border:0;border-top:1px solid #eee;margin:8px 0}}
</style></head><body>
<header><h1>HIRO early-turn setup — entry days (sell-first SPX delta bomb, spot proxy)</h1>
<p>Every fire of the rule (first minute of each episode): trough-anchored HIRO run ≥10 m at ≥2 $B/hr, calls &amp; puts both up (min/max ≥0.25), nextExp up with share ≥0.5, run not broken (−0.6 $B), 30-bar price pullback ≥3 pt, 09:35–15:45; leg placed at the NEXT bar's open. Green &#9660; = the sell (time labeled); green band = live window to the +5 fill (red if no fill, 60-min clock); light-red day shading = steep/late state (no new entry). Blue=VT, grey=open; EMA5/9/20 are context, not rule inputs. Bottom: HIRO cumulative (all total / calls / puts / nextExp), &times; = run broken. {len(meta)} entries · {nW} +5 fills / {nL} not. &larr;/&rarr; to page.</p></header>
<div class="bar">
 <span style="font-size:12px;color:#666">outcome</span>
 <button id="w_all" class="on" onclick="setWL('all')">All</button><button id="w_win" onclick="setWL('1')">+5 filled</button><button id="w_loss" onclick="setWL('0')">Not filled</button>
 <span class="sep"></span><span style="font-size:12px;color:#666">state at fire</span>
 <button id="b_all" class="on" onclick="setBr('all')">All</button><button id="b_o" onclick="setBr('0')">early (moderate)</button><button id="b_v" onclick="setBr('1')">steep</button>
 <span class="sep"></span><button onclick="go(-1)">&larr; Prev</button><button onclick="go(1)">Next &rarr;</button><span id="counter"></span>
</div>
<div id="stage"><div id="chart"></div><div id="panel"></div></div>
<script>
 var FIGS={json.dumps(figs)}, DIAGS={json.dumps(diags)}, META={json.dumps(meta)};
 var wl='all', br='all', i=0, vis=[];
 function recompute(){{vis=[];for(var k=0;k<META.length;k++){{if((wl=='all'||META[k].win==wl)&&(br=='all'||META[k].steep==br))vis.push(k);}}if(i>=vis.length)i=0;}}
 function draw(){{if(!vis.length){{document.getElementById('chart').innerHTML='';document.getElementById('panel').innerHTML='<div class=sub>no entries match</div>';document.getElementById('counter').textContent='0 / 0';return;}}
   var k=vis[i], f=JSON.parse(FIGS[k]);
   Plotly.react('chart', f.data, f.layout, {{scrollZoom:true,displaylogo:false,responsive:false}});
   document.getElementById('panel').innerHTML=DIAGS[k];
   document.getElementById('counter').textContent=(i+1)+' / '+vis.length+'  ·  '+META[k].ds;}}
 function setWL(v){{wl=v;i=0;['w_all','w_win','w_loss'].forEach(function(x){{document.getElementById(x).classList.remove('on');}});document.getElementById(v=='all'?'w_all':v=='1'?'w_win':'w_loss').classList.add('on');recompute();draw();}}
 function setBr(v){{br=v;i=0;['b_all','b_o','b_v'].forEach(function(x){{document.getElementById(x).classList.remove('on');}});document.getElementById(v=='all'?'b_all':v=='0'?'b_o':'b_v').classList.add('on');recompute();draw();}}
 function go(d){{if(!vis.length)return;i=(i+d+vis.length)%vis.length;draw();}}
 document.addEventListener('keydown',function(e){{if(e.key=='ArrowRight')go(1);if(e.key=='ArrowLeft')go(-1);}});
 recompute();draw();
</script></body></html>"""
open(OUT, "w").write(doc)
print(f"wrote {OUT}  ({len(figs)} entries, {nW} filled / {nL} not)  size={os.path.getsize(OUT)/1e6:.1f}MB")
