"""HIRO smooth-trend experiment (v1.1 — trend-local pullback geometry, 2026-08-19) — does an established, smooth HIRO trend raise the odds of filling a delta bomb
directionally in the MIDDLE of the trend (sell-first on pullbacks in TREND_UP; long-first on bounces in TREND_DOWN)?

Designed 2026-08-19 with Brent Kochuba / Charlie McElligott persona reviews (see docs/specs/spx_1min_delta_bomb_leg_in_strategy.md §5).
Data: HIRO S&P 500 basket v1 (all/nextExp/retail; call/put), real SPX 1-min OHLC. Exploratory on 5 sessions; re-run as sessions accumulate.

State (per minute, causal): L = cumulative `all` total since 09:30 ($B); over lookback W: sign-consistency of 1-min deltas,
R² of L vs time, drawdown of L from its running extreme within W (turn-over), magnitude |ΔL_W|, EMA_s slope over k;
agreement: sign ΔL_call == sign ΔL_put; sign ΔnextExp == sign ΔL; price confirmation sign ΔSPX_W == sign ΔL.
Entry: TREND_UP and SPX pulled back ≥ p pts from running high → sell-first at this minute's close; TREND_DOWN mirror.
Outcome: fixed-point fill in trend direction (+3/+5/+7 pts) within 15/30/60 min; adverse (pts) before fill; time to fill.
Controls: every-minute baseline (clock-matched); price-only trend state (same persistence/R² on SPX close line); HIRO trend
with price NOT confirming; call-only vs call&put-agreeing UP.

Run: ~/Dev/virtualenvs/gamma_chaser/bin/python scripts/hiro_trend_experiment.py
Out: docs/replay/hiro/hiro_trend_minute.parquet, docs/replay/hiro/hiro_trend_results.csv + printed tables.
"""
from __future__ import annotations

import itertools
import os

import numpy as np
import pandas as pd

V = "/Users/dgrissen/Dev/central_trade_data/spotgamma/hiro/sp500_basket/v1"
SPX = os.path.expanduser("~/Dev/central_trade_data/thetadata/spx_index_1m_ohlc")
DAYS = ["2026-08-12", "2026-08-13", "2026-08-14", "2026-08-17", "2026-08-18"]
FIRST, LAST = 575, 900
FILL_PTS = (3.0, 5.0, 7.0)
HORIZONS = (15, 30, 60)


def hiro_lines(day: str) -> pd.DataFrame:
    h = pd.read_csv(f"{V}/date={day}/normalized/hiro_series.csv")
    h["ts"] = pd.to_datetime(h.utc_iso, utc=True).dt.tz_convert("America/New_York")
    h["min"] = h.ts.dt.hour * 60 + h.ts.dt.minute
    h = h[(h["min"] >= 570) & (h["min"] <= 960)]
    out = pd.DataFrame({"min": range(570, 961)})
    for grp, g in h.groupby("series_group"):
        m = g.groupby("min").agg(dT=("delta_total", "sum"), dC=("delta_call", "sum"), dP=("delta_put", "sum"))
        m = m.reindex(range(570, 961), fill_value=0.0) / 1e9
        out[f"{grp}_dT"] = m.dT.values; out[f"{grp}_dC"] = m.dC.values; out[f"{grp}_dP"] = m.dP.values
        out[f"{grp}_L"] = m.dT.cumsum().values; out[f"{grp}_Lc"] = m.dC.cumsum().values; out[f"{grp}_Lp"] = m.dP.cumsum().values
    return out


def spx_day(day: str) -> pd.DataFrame:
    return pd.read_parquet(f"{SPX}/{day}.parquet").sort_values("min").reset_index(drop=True)


def r2_line(y: np.ndarray) -> float:
    x = np.arange(len(y), dtype=float)
    if y.std() == 0:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1] ** 2)


def features(day: str) -> pd.DataFrame:
    hl = hiro_lines(day); px = spx_day(day)
    df = px.merge(hl, on="min", how="left")
    L = df.all_L.values; Lc = df.all_Lc.values; Lp = df.all_Lp.values; N = df.nextExp_L.values; dT = df.all_dT.values
    cl = df.close.values; hi = df.high.values; lo = df.low.values
    rows = []
    # TREND-LOCAL extremes (fix 2026-08-19): pullback/bounce measured from the running high/low of CLOSES over the last
    # PULL_W bars, i.e. inside the trend window — not from the session extreme (the original session-high geometry
    # selected bounces inside down days and biased the UP branch downward; see doc §5.7).
    PULL_W = 30
    cs = pd.Series(cl)
    loc_hi = cs.rolling(PULL_W, min_periods=5).max().values; loc_lo = cs.rolling(PULL_W, min_periods=5).min().values
    run_hi = np.maximum.accumulate(hi); run_lo = np.minimum.accumulate(lo)
    for i in range(len(df)):
        t = int(df["min"][i])
        r = dict(min=t, px=cl[i], pull_from_hi=loc_hi[i] - cl[i], bounce_from_lo=cl[i] - loc_lo[i],
                 pull_from_session_hi=run_hi[i] - cl[i], bounce_from_session_lo=cl[i] - run_lo[i])
        for W in (15, 30, 45, 60):
            if i - W < 0:
                for k_ in ("dL", "cons", "r2", "ddn", "dLc", "dLp", "dN", "dpx", "pcons", "pr2"):
                    r[f"{k_}{W}"] = np.nan
                continue
            seg = L[i - W:i + 1]; dL = seg[-1] - seg[0]
            sgn = np.sign(dL) if dL != 0 else 0.0
            d = dT[i - W + 1:i + 1]
            r[f"dL{W}"] = dL
            r[f"cons{W}"] = float(np.mean(np.sign(d) == sgn)) if sgn != 0 else 0.0
            r[f"r2{W}"] = r2_line(seg)
            # turn-over: drawdown of L from its running extreme (in the trend direction) within the window, as share of |dL|
            if sgn > 0:
                dd = (np.maximum.accumulate(seg) - seg)[-1]
            elif sgn < 0:
                dd = (seg - np.minimum.accumulate(seg))[-1]
            else:
                dd = 0.0
            r[f"ddn{W}"] = dd / abs(dL) if dL != 0 else np.nan
            r[f"dLc{W}"] = Lc[i] - Lc[i - W]; r[f"dLp{W}"] = Lp[i] - Lp[i - W]; r[f"dN{W}"] = N[i] - N[i - W]
            pseg = cl[i - W:i + 1]; r[f"dpx{W}"] = pseg[-1] - pseg[0]
            pd_ = np.diff(pseg); psg = np.sign(r[f"dpx{W}"])
            r[f"pcons{W}"] = float(np.mean(np.sign(pd_) == psg)) if psg != 0 else 0.0
            r[f"pr2{W}"] = r2_line(pseg)
        for s in (3, 5, 8, 13, 21, 34):
            e = pd.Series(L).ewm(span=s, adjust=False).mean().values
            for k in (3, 5, 10):
                r[f"slope_s{s}_k{k}"] = (e[i] - e[i - k]) / k if i - k >= 0 else np.nan
        # outcomes: fixed-point fills up/down within horizons; adverse before fill
        for pts in FILL_PTS:
            for H in HORIZONS:
                h_, l_ = hi[i + 1:i + 1 + H], lo[i + 1:i + 1 + H]
                iu = int(np.argmax(h_ >= cl[i] + pts)) if (h_ >= cl[i] + pts).any() else -1
                idn = int(np.argmax(l_ <= cl[i] - pts)) if (l_ <= cl[i] - pts).any() else -1
                r[f"up{int(pts)}_{H}"] = iu >= 0; r[f"dn{int(pts)}_{H}"] = idn >= 0
                if H == 60:
                    r[f"ttf_up{int(pts)}"] = iu + 1 if iu >= 0 else np.nan; r[f"ttf_dn{int(pts)}"] = idn + 1 if idn >= 0 else np.nan
                    su = l_[:iu] if iu >= 0 else l_; sd = h_[:idn] if idn >= 0 else h_
                    r[f"advS{int(pts)}"] = max(0.0, cl[i] - su.min()) if len(su) else 0.0   # adverse for a carried short (needs up)
                    r[f"advL{int(pts)}"] = max(0.0, sd.max() - cl[i]) if len(sd) else 0.0   # adverse for a carried long (needs down)
        rows.append(r)
    out = pd.DataFrame(rows); out["day"] = day
    return out


def trend_state(df: pd.DataFrame, W: int, cons: float, r2: float, ddn: float, mag: float, cp_agree: bool, next_agree: bool, px_confirm: bool) -> np.ndarray:
    dL = df[f"dL{W}"]; up = (dL > mag) & (df[f"cons{W}"] >= cons) & (df[f"r2{W}"] >= r2) & (df[f"ddn{W}"] <= ddn)
    dn = (dL < -mag) & (df[f"cons{W}"] >= cons) & (df[f"r2{W}"] >= r2) & (df[f"ddn{W}"] <= ddn)
    if cp_agree:
        up &= (df[f"dLc{W}"] > 0) & (df[f"dLp{W}"] > 0); dn &= (df[f"dLc{W}"] < 0) & (df[f"dLp{W}"] < 0)
    if next_agree:
        up &= df[f"dN{W}"] > 0; dn &= df[f"dN{W}"] < 0
    if px_confirm:
        up &= df[f"dpx{W}"] > 0; dn &= df[f"dpx{W}"] < 0
    return np.where(up, "UP", np.where(dn, "DOWN", "NONE"))


def price_trend_state(df: pd.DataFrame, W: int, cons: float, r2: float, mag_pts: float) -> np.ndarray:
    d = df[f"dpx{W}"]
    up = (d > mag_pts) & (df[f"pcons{W}"] >= cons) & (df[f"pr2{W}"] >= r2)
    dn = (d < -mag_pts) & (df[f"pcons{W}"] >= cons) & (df[f"pr2{W}"] >= r2)
    return np.where(up, "UP", np.where(dn, "DOWN", "NONE"))


def evaluate(df: pd.DataFrame, st: np.ndarray, p: float, pts: float, H: int) -> dict:
    """Entries: TREND_UP with pullback ≥ p (sell-first, needs up fill); TREND_DOWN with bounce ≥ p (long-first, needs down)."""
    d = df.assign(st=st)
    up_e = d[(d.st == "UP") & (d.pull_from_hi >= p)]
    dn_e = d[(d.st == "DOWN") & (d.bounce_from_lo >= p)]
    k = int(pts)
    res = dict(n_up=len(up_e), n_dn=len(dn_e), days_up=up_e.day.nunique(), days_dn=dn_e.day.nunique())
    res["fill_up"] = up_e[f"up{k}_{H}"].mean() if len(up_e) else np.nan
    res["fill_dn"] = dn_e[f"dn{k}_{H}"].mean() if len(dn_e) else np.nan
    res["advS15_up"] = (up_e[f"advS{k}"] > 15).mean() if len(up_e) else np.nan
    res["advL15_dn"] = (dn_e[f"advL{k}"] > 15).mean() if len(dn_e) else np.nan
    res["ttf_up"] = up_e[f"ttf_up{k}"].median() if len(up_e) else np.nan
    res["ttf_dn"] = dn_e[f"ttf_dn{k}"].median() if len(dn_e) else np.nan
    # clock-matched baselines
    for lab, e, col, adv in (("up", up_e, f"up{k}_{H}", f"advS{k}"), ("dn", dn_e, f"dn{k}_{H}", f"advL{k}")):
        if len(e):
            w = e["min"].value_counts(normalize=True)
            b = d[d["min"].isin(w.index)]
            wt = b["min"].map(w) / b.groupby("min")["min"].transform("size")
            res[f"base_fill_{lab}"] = float(np.average(b[col].astype(float), weights=wt))
            res[f"base_adv15_{lab}"] = float(np.average((b[adv] > 15).astype(float), weights=wt))
        else:
            res[f"base_fill_{lab}"] = np.nan; res[f"base_adv15_{lab}"] = np.nan
    return res


def main() -> None:
    df = pd.concat([features(d) for d in DAYS], ignore_index=True)
    df = df[(df["min"] >= FIRST) & (df["min"] <= LAST)].reset_index(drop=True)
    df.to_parquet("docs/replay/hiro/hiro_trend_minute.parquet")
    print("minutes", len(df), "days", df.day.nunique())
    pd.set_option("display.width", 250)

    # --- pre-registered primary cell ---
    P = dict(W=30, cons=0.7, r2=0.8, ddn=0.25, mag=0.5, cp_agree=True, next_agree=True, px_confirm=True)
    st = trend_state(df, **P)
    print("\nPRIMARY CELL", P, "| state counts:", pd.Series(st).value_counts().to_dict())
    for pts in FILL_PTS:
        for H in HORIZONS:
            r = evaluate(df, st, p=3.0, pts=pts, H=H)
            print(f"  fill +{pts:g} pts in {H} min | UP(sell-first, pullback≥3): n={r['n_up']} days={r['days_up']} fill={r['fill_up']:.3f} base={r['base_fill_up']:.3f} adv>15={r['advS15_up']:.3f} base={r['base_adv15_up']:.3f} ttf={r['ttf_up']}"
                  f" || DOWN(long-first, bounce≥3): n={r['n_dn']} days={r['days_dn']} fill={r['fill_dn']:.3f} base={r['base_fill_dn']:.3f} adv>15={r['advL15_dn']:.3f} base={r['base_adv15_dn']:.3f} ttf={r['ttf_dn']}")
    # price-only control at the same cell geometry
    pst = price_trend_state(df, W=30, cons=0.6, r2=0.8, mag_pts=5.0)
    r = evaluate(df, pst, p=3.0, pts=5.0, H=30)
    print("\nPRICE-ONLY TREND CONTROL (W30, cons≥0.6, R²≥0.8, |Δpx|>5): ", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()})
    # HIRO trend, price NOT confirming
    st_nc = trend_state(df, **{**P, "px_confirm": False})
    st_div = np.where((st_nc != "NONE") & (st == "NONE"), st_nc, "NONE")
    r = evaluate(df, st_div, p=3.0, pts=5.0, H=30)
    print("HIRO TREND with price NOT confirming:", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()})
    # call-only UP vs call&put UP
    st_callonly = trend_state(df, **{**P, "cp_agree": False})
    st_co = np.where((st_callonly == "UP") & (df.dLp30 <= 0), "UP", "NONE")
    r = evaluate(df, st_co, p=3.0, pts=5.0, H=30)
    print("UP with CALL line only (put line not rising):", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()})

    # --- sweep ---
    rows = []
    grid = itertools.product((15, 30, 45, 60), (0.6, 0.7, 0.8), (0.7, 0.85), (0.25, 0.5), (0.5, 1.0, 2.0), (False, True), (False, True), (False, True), (3.0, 5.0, 8.0))
    for W, cons, r2, ddn, mag, cp, nx, pc, p in grid:
        stx = trend_state(df, W, cons, r2, ddn, mag, cp, nx, pc)
        r = evaluate(df, stx, p=p, pts=5.0, H=30)
        rows.append(dict(W=W, cons=cons, r2=r2, ddn=ddn, mag=mag, cp=cp, nx=nx, pc=pc, p=p, **r))
    res = pd.DataFrame(rows); res.to_csv("docs/replay/hiro/hiro_trend_results.csv", index=False)
    res["lift_up"] = res.fill_up - res.base_fill_up; res["lift_dn"] = res.fill_dn - res.base_fill_dn
    ok = res[(res.n_up >= 30) & (res.days_up >= 3)]
    print("\nSWEEP (fill +5 in 30 min) — top UP cells by lift with n≥30, ≥3 days:")
    print(ok.sort_values("lift_up", ascending=False).head(12)[["W", "cons", "r2", "ddn", "mag", "cp", "nx", "pc", "p", "n_up", "days_up", "fill_up", "base_fill_up", "lift_up", "advS15_up", "base_adv15_up"]].round(3).to_string(index=False))
    okd = res[(res.n_dn >= 30) & (res.days_dn >= 3)]
    print("\nSWEEP — top DOWN cells by lift:")
    print(okd.sort_values("lift_dn", ascending=False).head(12)[["W", "cons", "r2", "ddn", "mag", "cp", "nx", "pc", "p", "n_dn", "days_dn", "fill_dn", "base_fill_dn", "lift_dn", "advL15_dn", "base_adv15_dn"]].round(3).to_string(index=False))
    print("\nSWEEP distribution of lift_up (cells with n≥30): ", ok.lift_up.describe().round(3).to_dict())
    print("SWEEP distribution of lift_dn (cells with n≥30): ", okd.lift_dn.describe().round(3).to_dict())
    # EMA slope sweep as a standalone state (sign + magnitude above median), fill +5 in 30, pullback≥3
    print("\nEMA-slope-only states (|slope| > 70th pct), fill +5 in 30 min, pullback≥3 / bounce≥3:")
    for s in (3, 5, 8, 13, 21, 34):
        for k in (3, 5, 10):
            col = f"slope_s{s}_k{k}"; thr = df[col].abs().quantile(0.7)
            stx = np.where(df[col] > thr, "UP", np.where(df[col] < -thr, "DOWN", "NONE"))
            r = evaluate(df, stx, p=3.0, pts=5.0, H=30)
            print(f"  span {s:2d} k {k:2d}: UP n={r['n_up']:4d} fill={r['fill_up']:.3f} base={r['base_fill_up']:.3f} adv>15={r['advS15_up']:.3f} | DOWN n={r['n_dn']:4d} fill={r['fill_dn']:.3f} base={r['base_fill_dn']:.3f} adv>15={r['advL15_dn']:.3f}")


if __name__ == "__main__":
    main()
