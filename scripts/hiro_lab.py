"""HIRO lab — one rich, causal, minute-level feature table for the 8 captured sessions, plus episode builders.

Everything downstream (persona-designed experiments) reads this table. All features computable at the close of
minute t; outcomes measured from the NEXT bar's open with complete-horizon flags. Spot proxy.

Run: ~/Dev/virtualenvs/gamma_chaser/bin/python scripts/hiro_lab.py   (writes docs/replay/hiro/hiro_lab_minute.parquet)
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd

V = "/Users/dgrissen/Dev/central_trade_data/spotgamma/hiro/sp500_basket/v1"
SPX = os.path.expanduser("~/Dev/central_trade_data/thetadata/spx_index_1m_ohlc")
SG = "/Users/dgrissen/Dev/core_spotgamma_spx_vix_data/offset_historical_spotgamma_data.csv"
DAYS = ["2026-08-12", "2026-08-13", "2026-08-14", "2026-08-17", "2026-08-18", "2026-08-19", "2026-08-20", "2026-08-21"]
REV = 0.6


def load_day(day: str) -> pd.DataFrame:
    h = pd.read_csv(f"{V}/date={day}/normalized/hiro_series.csv")
    h["ts"] = pd.to_datetime(h.utc_iso, utc=True).dt.tz_convert("America/New_York")
    h["min"] = h.ts.dt.hour * 60 + h.ts.dt.minute
    h = h[(h["min"] >= 570) & (h["min"] <= 960)]
    out = pd.DataFrame({"min": range(570, 961)})
    for grp, g in h.groupby("series_group"):
        mm = g.groupby("min").agg(dT=("delta_total", "sum"), dC=("delta_call", "sum"), dP=("delta_put", "sum")).reindex(range(570, 961), fill_value=0.0) / 1e9
        out[f"{grp}_L"], out[f"{grp}_Lc"], out[f"{grp}_Lp"] = mm.dT.cumsum().values, mm.dC.cumsum().values, mm.dP.cumsum().values
    px = pd.read_parquet(f"{SPX}/{day}.parquet").sort_values("min")
    df = out.merge(px, on="min", how="inner").reset_index(drop=True)
    return df


def runs(L: np.ndarray, sign: int) -> dict:
    """Trough(peak)-anchored runs in direction `sign` (+1 up, −1 down); returns per-row run/dur/extreme drawdown."""
    n = len(L)
    lo = hi = 0
    run = np.zeros(n); dur = np.zeros(n); dd = np.zeros(n); anchor = np.zeros(n, int)
    for i in range(n):
        s = L[i] * sign
        if s < L[lo] * sign:
            lo = hi = i
        if s > L[hi] * sign:
            hi = i
        d = (L[hi] - L[i]) * sign
        if d >= REV:
            lo = hi = i; d = 0.0
        run[i] = (L[i] - L[lo]) * sign; dur[i] = i - lo; dd[i] = d; anchor[i] = lo
    return dict(run=run, dur=dur, dd=dd, anchor=anchor)


def build() -> pd.DataFrame:
    sg = pd.read_csv(SG).set_index("Date")
    frames = []
    for day in DAYS:
        df = load_day(day)
        L, Lc, Lp, N, R = df.all_L.values, df.all_Lc.values, df.all_Lp.values, df.nextExp_L.values, df.retail_L.values
        cl, hi_, lo_, op = df.close.values, df.high.values, df.low.values, df.open.values
        up = runs(L, +1); dn = runs(L, -1)
        d = pd.DataFrame({"day": day, "min": df["min"],
                          "open": op, "high": hi_, "low": lo_, "close": cl,
                          "L": L, "Lc": Lc, "Lp": Lp, "N": N, "R": R})
        for w in (5, 15, 30):
            d[f"r{w}"] = pd.Series(L).diff(w); d[f"r{w}c"] = pd.Series(Lc).diff(w); d[f"r{w}p"] = pd.Series(Lp).diff(w)
            d[f"r{w}n"] = pd.Series(N).diff(w); d[f"r{w}r"] = pd.Series(R).diff(w)
        d["up_run"], d["up_dur"], d["up_dd"] = up["run"], up["dur"], up["dd"]
        d["dn_run"], d["dn_dur"], d["dn_dd"] = dn["run"], dn["dur"], dn["dd"]
        for lab, rr in (("up", up), ("dn", dn)):
            a = rr["anchor"]
            d[f"{lab}_dC"] = Lc - Lc[a]; d[f"{lab}_dP"] = Lp - Lp[a]; d[f"{lab}_dN"] = N - N[a]
            d[f"{lab}_px"] = cl - cl[a]
        cs = pd.Series(cl)
        d["pull30"] = cs.rolling(30, min_periods=30).max() - cs
        d["bounce30"] = cs - cs.rolling(30, min_periods=30).min()
        d["rng60"] = (pd.Series(hi_).rolling(60, min_periods=60).max() - pd.Series(lo_).rolling(60, min_periods=60).min())
        d["ret5"] = cs.diff(5); d["ret15"] = cs.diff(15); d["ret30"] = cs.diff(30)
        d["vt"] = float(sg.loc[day, "Vol Trigger"]) if day in sg.index else np.nan
        d["sgidx"] = float(sg.loc[day, "sg_index"]) if day in sg.index else np.nan
        # outcomes from next bar's open, horizons 30/60, both directions
        n = len(d)
        for name in ("u3_30", "u5_30", "u3_60", "u5_60", "d3_30", "d5_30", "d3_60", "d5_60",
                     "ttf_u3", "ttf_u5", "ttf_d3", "ttf_d5", "advS", "advL", "pe"):
            d[name] = np.nan
        for i in range(n - 1):
            pe = op[i + 1]
            d.at[i, "pe"] = pe
            for H, tag in ((30, "30"), (60, "60")):
                h, l = hi_[i + 1:i + 1 + H], lo_[i + 1:i + 1 + H]
                if len(h) < H:
                    continue
                for pts in (3, 5):
                    iu = int(np.argmax(h >= pe + pts)) + 1 if (h >= pe + pts).any() else np.nan
                    idn = int(np.argmax(l <= pe - pts)) + 1 if (l <= pe - pts).any() else np.nan
                    d.at[i, f"u{pts}_{tag}"] = float(not np.isnan(iu)); d.at[i, f"d{pts}_{tag}"] = float(not np.isnan(idn))
                    if tag == "60":
                        d.at[i, f"ttf_u{pts}"] = iu; d.at[i, f"ttf_d{pts}"] = idn
                        if pts == 3:
                            su = l[:int(iu) - 1] if not np.isnan(iu) else l
                            sd = h[:int(idn) - 1] if not np.isnan(idn) else h
                            d.at[i, "advS"] = max(0.0, pe - su.min()) if len(su) else 0.0
                            d.at[i, "advL"] = max(0.0, sd.max() - pe) if len(sd) else 0.0
        frames.append(d)
    out = pd.concat(frames, ignore_index=True)
    out.to_parquet("docs/replay/hiro/hiro_lab_minute.parquet")
    return out


if __name__ == "__main__":
    df = build()
    print(len(df), "minutes,", df.day.nunique(), "days → docs/replay/hiro/hiro_lab_minute.parquet")
