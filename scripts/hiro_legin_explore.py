"""Exploratory: does SpotGamma HIRO (S&P 500 basket) confirm direction / turns for SPX delta-bomb leg-in?

Sessions: the five available HIRO captures (2026-08-12/13/14/17/18). Price: real SPX 1-min OHLC (thetadata store).
HIRO per-minute features (causal, from 09:35): cumulative since 09:30; rolling sums over 5/15/30 min for total/call/put
and for scopes all / nextExp / retail; EMA(5/20) of the cumulative line and its slope; agreement flags
(call & put rolling same sign; all & nextExp same sign; retail same sign as all). Outcomes on SPX over the next 60 min:
up-touch +X bp, down-touch −X bp, adverse before each (bp, ≥0, touch bar excluded), time to touch.

Caveats: basket (SPX+SPY+/ES+XSP), not cash SPX; mid_signal reconstruction; 5 sessions only → exploratory, no inference.
Run: ~/Dev/virtualenvs/gamma_chaser/bin/python scripts/hiro_legin_explore.py
Out: docs/replay/hiro/hiro_legin_minute.parquet + printed tables.
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd

V = "/Users/dgrissen/Dev/central_trade_data/spotgamma/hiro/sp500_basket/v1"
SPX = os.path.expanduser("~/Dev/central_trade_data/thetadata/spx_index_1m_ohlc")
DAYS = ["2026-08-12", "2026-08-13", "2026-08-14", "2026-08-17", "2026-08-18"]
X_BP = 4.0
N_MIN = 60
FIRST = 575   # 09:35 — no leg before this
LAST = 900    # 15:00 — leave 60 min of outcome window


def hiro_minutes(day: str) -> pd.DataFrame:
    h = pd.read_csv(f"{V}/date={day}/normalized/hiro_series.csv")
    h["ts"] = pd.to_datetime(h.utc_iso, utc=True).dt.tz_convert("America/New_York")
    h["min"] = h.ts.dt.hour * 60 + h.ts.dt.minute
    h = h[(h["min"] >= 570) & (h["min"] <= 960)]
    out = None
    for grp, g in h.groupby("series_group"):
        m = g.groupby("min").agg(dT=("delta_total", "sum"), dC=("delta_call", "sum"), dP=("delta_put", "sum")).reset_index()
        m = m.set_index("min").reindex(range(570, 961), fill_value=0.0).reset_index()
        for k in ("T", "C", "P"):
            s = m[f"d{k}"] / 1e9                      # $B per minute
            m[f"{grp}_cum{k}"] = s.cumsum()
            for w in (5, 15, 30):
                m[f"{grp}_r{w}{k}"] = s.rolling(w, min_periods=w).sum()
            m[f"{grp}_ema5{k}"] = m[f"{grp}_cum{k}"].ewm(span=5, adjust=False).mean()
            m[f"{grp}_ema20{k}"] = m[f"{grp}_cum{k}"].ewm(span=20, adjust=False).mean()
            m[f"{grp}_slope5{k}"] = m[f"{grp}_ema5{k}"].diff(5)
        m = m.drop(columns=["dT", "dC", "dP"])
        out = m if out is None else out.merge(m, on="min")
    return out


def outcomes(day: str) -> pd.DataFrame:
    g = pd.read_parquet(f"{SPX}/{day}.parquet").sort_values("min")
    m, hi, lo, cl = g["min"].values, g.high.values, g.low.values, g.close.values
    rows = []
    for i in range(len(m)):
        t = m[i]
        if t < FIRST or t > LAST:
            continue
        p0 = cl[i]
        up, dn = p0 * (1 + X_BP / 1e4), p0 * (1 - X_BP / 1e4)
        h, l = hi[i + 1:i + 1 + N_MIN], lo[i + 1:i + 1 + N_MIN]
        iu = int(np.argmax(h >= up)) if (h >= up).any() else -1
        idn = int(np.argmax(l <= dn)) if (l <= dn).any() else -1
        seg_u = l[:iu] if iu >= 0 else l
        seg_d = h[:idn] if idn >= 0 else h
        rows.append(dict(min=int(t), px=p0,
                         up=iu >= 0, dn=idn >= 0, ttf_up=(iu + 1) if iu >= 0 else np.nan, ttf_dn=(idn + 1) if idn >= 0 else np.nan,
                         adv_up=max(0.0, (p0 - seg_u.min()) / p0 * 1e4) if len(seg_u) else 0.0,   # adverse for a sell-first leg (needs up)
                         adv_dn=max(0.0, (seg_d.max() - p0) / p0 * 1e4) if len(seg_d) else 0.0,   # adverse for a long-first leg (needs down)
                         ret60=(cl[min(len(cl) - 1, i + N_MIN)] - p0) / p0 * 1e4))
    return pd.DataFrame(rows)


def build() -> pd.DataFrame:
    frames = []
    for d in DAYS:
        f = outcomes(d).merge(hiro_minutes(d), on="min", how="left")
        f["day"] = d
        frames.append(f)
    df = pd.concat(frames, ignore_index=True)
    df.to_parquet("docs/replay/hiro/hiro_legin_minute.parquet")
    return df


def state(df: pd.DataFrame, col: str, thr: float) -> pd.Series:
    # (#2) incomplete windows (NaN) are excluded, not treated as FLAT
    return np.where(df[col].isna(), "NA", np.where(df[col] > thr, "UP", np.where(df[col] < -thr, "DOWN", "FLAT")))


def report(df: pd.DataFrame, label: str, st: pd.Series) -> None:
    d = df.assign(st=st)
    g = d.groupby("st").agg(n=("up", "size"), P_up=("up", "mean"), P_dn=("dn", "mean"),
                            up_in15=("ttf_up", lambda s: (s <= 15).mean()), dn_in15=("ttf_dn", lambda s: (s <= 15).mean()),
                            adv_up20=("adv_up", lambda s: (s > 20).mean()), adv_dn20=("adv_dn", lambda s: (s > 20).mean()),
                            ret60=("ret60", "mean"))
    print(f"\n== {label} ==")
    print(g.round(3).to_string())


def main() -> None:
    df = build()
    print("minutes", len(df), "days", df.day.nunique())
    base = df.agg(P_up=("up", "mean"), P_dn=("dn", "mean"))
    print("BASELINE (these 5 days, 09:35–15:00): P_up %.3f P_dn %.3f adv_up>20 %.3f adv_dn>20 %.3f" % (
        df.up.mean(), df.dn.mean(), (df.adv_up > 20).mean(), (df.adv_dn > 20).mean()))
    for grp in ("all", "nextExp", "retail"):
        for w in (5, 15, 30):
            col = f"{grp}_r{w}T"
            thr = df[col].abs().quantile(0.5)   # "strong" = above the median absolute rolling flow
            report(df, f"{grp} rolling {w}-min TOTAL, |flow| > median ({thr:.2f} $B)", state(df, col, thr))
    # agreement signals (15-min)
    for grp in ("all", "nextExp"):
        c, p = df[f"{grp}_r15C"], df[f"{grp}_r15P"]
        agree = np.where((c > 0) & (p > 0), "UP", np.where((c < 0) & (p < 0), "DOWN", "MIXED"))
        report(df, f"{grp}: call & put 15-min rolling SAME SIGN", pd.Series(agree))
    a, n = df["all_r15T"], df["nextExp_r15T"]
    agree = np.where((a > 0) & (n > 0), "UP", np.where((a < 0) & (n < 0), "DOWN", "MIXED"))
    agree = np.where(a.isna() | n.isna(), "NA", agree)
    report(df, "all & nextExp 15-min TOTAL same sign", pd.Series(agree))
    rt = df["retail_r15T"]   # (#10) retail agreement with all
    ragree = np.where((a > 0) & (rt > 0), "UP", np.where((a < 0) & (rt < 0), "DOWN", "MIXED"))
    ragree = np.where(a.isna() | rt.isna(), "NA", ragree)
    report(df, "all & retail 15-min TOTAL same sign", pd.Series(ragree))
    # strong + agree
    thr_a, thr_n = df.all_r15T.abs().quantile(0.6), df.nextExp_r15T.abs().quantile(0.6)
    strong = np.where((a > thr_a) & (n > thr_n), "UP", np.where((a < -thr_a) & (n < -thr_n), "DOWN", "OTHER"))
    report(df, f"STRONG all & nextExp 15-min same sign (> 60th pct: {thr_a:.2f}/{thr_n:.2f} $B)", pd.Series(strong))
    # EMA slope of cumulative total (all), sign & strength
    col = "all_slope5T"; thr = df[col].abs().quantile(0.5)
    report(df, f"all cumulative TOTAL EMA5 slope (5-min), |slope| > median ({thr:.2f} $B)", state(df, col, thr))
    # EMA5 vs EMA20 cross of the cumulative total line
    cross = np.where(df.all_ema5T > df.all_ema20T, "UP", "DOWN")
    report(df, "all cumulative TOTAL: EMA5 > EMA20", pd.Series(cross))
    # HIRO vs price divergence: price down over last 15 min but HIRO 15-min up (absorption) etc.
    df["px15"] = df.groupby("day").px.diff(15) / df.groupby("day").px.shift(15) * 1e4   # (#9) lagged denominator
    dv = np.where((df.px15 < -4) & (df.all_r15T > 0), "PX_DOWN_HIRO_UP", np.where((df.px15 > 4) & (df.all_r15T < 0), "PX_UP_HIRO_DOWN",
         np.where((df.px15 < -4) & (df.all_r15T < 0), "BOTH_DOWN", np.where((df.px15 > 4) & (df.all_r15T > 0), "BOTH_UP", "OTHER"))))
    report(df, "price 15-min move vs all 15-min HIRO (confirm / diverge)", pd.Series(dv))
    # per-day summary
    print("\nper-day: range, P_up, P_dn, cum HIRO end (all/nextExp/retail $B)")
    for d, g in df.groupby("day"):
        print(d, "range %.0f" % (g.px.max() - g.px.min()), "P_up %.2f P_dn %.2f" % (g.up.mean(), g.dn.mean()),
              "cum all %.2f next %.2f retail %.2f" % (g.all_cumT.iloc[-1], g.nextExp_cumT.iloc[-1], g.retail_cumT.iloc[-1]))


if __name__ == "__main__":
    main()
