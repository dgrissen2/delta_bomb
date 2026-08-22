"""Four persona-designed HIRO experiments (Brent/Charlie joint shortlist, 2026-08-21) on the 8-session lab table.

All features causal (expanding thresholds shifted one bar); episodes deduped (15-min refire); entries at the NEXT
bar's open; outcomes +/-3/+/-5 pts with complete horizons; controls per design (clock-matched or state-matched).
Spot proxy. Run: ~/Dev/virtualenvs/gamma_chaser/bin/python scripts/hiro_experiments.py
Out: docs/replay/hiro/hiro_experiments_results.csv + per-experiment episode CSVs + printed tables.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

LAB = "docs/replay/hiro/hiro_lab_minute.parquet"
REFIRE = 15
FIRST, LAST = 575, 900          # complete 60-min horizons


def exq(s: pd.Series, q: float, minp: int = 300) -> pd.Series:
    """Causal expanding quantile over the pooled chronological series, shifted one bar."""
    return s.expanding(min_periods=minp).quantile(q).shift(1)


def epis(mask: pd.Series, df: pd.DataFrame) -> pd.Index:
    """First minute of each episode: qualifying minutes deduped by day with a REFIRE-minute gap."""
    idx = []
    last_day, last_min = None, -999
    for i in df.index[mask]:
        d, m = df.day[i], df["min"][i]
        if d != last_day or m - last_min >= REFIRE:
            idx.append(i)
        last_day, last_min = d, m
    return pd.Index(idx)


def outcome_row(df: pd.DataFrame, idx: pd.Index, side: str) -> pd.DataFrame:
    cols = ("u3_60", "u5_60", "ttf_u3", "ttf_u5", "advS") if side == "sell" else ("d3_60", "d5_60", "ttf_d3", "ttf_d5", "advL")
    e = df.loc[idx, ["day", "min", "pe"] + list(cols)].copy()
    e.columns = ["day", "min", "pe", "f3", "f5", "t3", "t5", "adv"]
    return e.dropna(subset=["f3"])


def cm_base(df: pd.DataFrame, e: pd.DataFrame, side: str) -> dict:
    from hiro_engine.control import clock_weighted_mean   # single home of the weighting (DRY)
    col3, col5, adv = ("u3_60", "u5_60", "advS") if side == "sell" else ("d3_60", "d5_60", "advL")
    b = df[df[col3].notna()].assign(_adv10=lambda x: (x[adv] > 10).astype(float))
    return dict(b3=clock_weighted_mean(b, e["min"], col3), b5=clock_weighted_mean(b, e["min"], col5),
                badv=clock_weighted_mean(b, e["min"], "_adv10"))


def report(name: str, df: pd.DataFrame, e: pd.DataFrame, side: str) -> dict:
    if len(e) == 0:
        print(f"{name}: no episodes"); return dict(name=name, n=0)
    base = cm_base(df, e, side)
    r = dict(name=name, side=side, n=len(e), days=e.day.nunique(),
             f3=e.f3.mean(), f5=e.f5.mean(), b3=base["b3"], b5=base["b5"],
             t3_med=e.t3.median(), f3_15=float((e.t3 <= 15).mean()),
             adv10=float((e.adv > 10).mean()), badv=base["badv"])
    print(f"{name:44s} n={r['n']:3d} d={r['days']} | ±3 {r['f3']:.2f} vs {r['b3']:.2f} | ±5 {r['f5']:.2f} vs {r['b5']:.2f} | "
          f"≤15m {r['f3_15']:.2f} | med t3 {r['t3_med']:.0f} | adv>10 {r['adv10']:.2f} vs {r['badv']:.2f}")
    return r


def main() -> None:
    df = pd.read_parquet(LAB).sort_values(["day", "min"]).reset_index(drop=True)
    df = df[(df["min"] >= FIRST)].reset_index(drop=True)
    ok = (df["min"] <= LAST)
    pw = {"2026-08-12": 7400, "2026-08-13": 7500, "2026-08-14": 7500, "2026-08-17": 7500, "2026-08-18": 7500}
    df["pwall"] = df.day.map(pw)
    pd.set_option("display.width", 240)
    results = []

    # ---- E1: put absorption near VT/Put Wall ------------------------------------------------------------------
    put_shock = df.r5p <= exq(df.r5p, 0.10)                       # extreme 5-min put buying (put line falling hard)
    near_level = (abs(df.close - df.vt) <= 15) | (abs(df.close - df.pwall) <= 15)
    no_new_low = df.low > df.groupby("day").low.transform(lambda s: s.rolling(30, min_periods=30).min()).shift(3)
    shocked = put_shock.groupby(df.day).transform(lambda s: s.rolling(10, min_periods=1).max()).astype(bool)   # a put shock within the last 10 min
    give = df.dn_dd >= 0.25 * df.dn_run.clip(lower=0.1)                 # down-run giving back ≥ 25%
    reclaim = df.close > df.groupby("day").close.transform(lambda s: (s.rolling(5).max() + s.rolling(5).min()) / 2)
    m1 = ok & shocked & near_level & no_new_low & give & reclaim
    e1 = outcome_row(df, epis(m1, df), "sell"); e1.to_csv("docs/replay/hiro/exp1_put_absorption.csv", index=False)
    results.append(report("E1 put absorption @ VT/PW (sell-first)", df, e1, "sell"))
    c1 = ok & shocked & near_level & ~(give & reclaim & no_new_low)      # control: same shock/level, no absorption signature
    e1c = outcome_row(df, epis(c1, df), "sell")
    results.append(report("E1-CONTROL shock @ level, no absorption", df, e1c, "sell"))

    # ---- E2: de-gross bounce failure (long-first) --------------------------------------------------------------
    hi_rng = df.rng60 >= exq(df.rng60, 0.75)
    m2 = (ok & hi_rng & (df.r30 < 0) & (df.bounce30 >= 3)
          & (df.r15c > 0) & (df.r15p < 0)                                # call relief masking put deterioration
          & (df.close < df.groupby("day").close.transform(lambda s: (s.rolling(30, min_periods=30).min() + s.rolling(30, min_periods=30).max()) / 2)))
    e2 = outcome_row(df, epis(m2, df), "long"); e2.to_csv("docs/replay/hiro/exp2_degross_bounce.csv", index=False)
    results.append(report("E2 de-gross bounce failure (long-first)", df, e2, "long"))
    below_mid = df.close < df.groupby("day").close.transform(lambda s: (s.rolling(30, min_periods=30).min() + s.rolling(30, min_periods=30).max()) / 2)
    c2 = ok & hi_rng & (df.r30 < 0) & (df.bounce30 >= 3) & below_mid & ~((df.r15c > 0) & (df.r15p < 0))
    results.append(report("E2-CONTROL bounce, no C/P divergence", df, outcome_row(df, epis(c2, df), "long"), "long"))

    # ---- E3: retail divergence fade ---------------------------------------------------------------------------
    zr = (df.r15r - df.r15r.expanding(300).mean().shift(1)) / df.r15r.expanding(300).std().shift(1)
    za = (df.r15 - df.r15.expanding(300).mean().shift(1)) / df.r15.expanding(300).std().shift(1)
    stall = df.ret5.abs() < 1.0
    cap = ok & (zr <= -1.5) & ((za - zr) >= 1.5) & (df.ret15 < 0) & stall     # retail capitulation, basket refuses
    chase = ok & (zr >= 1.5) & ((zr - za) >= 1.5) & (df.ret15 > 0) & stall    # retail chase, basket refuses
    e3a = outcome_row(df, epis(cap, df), "sell"); e3b = outcome_row(df, epis(chase, df), "long")
    e3a.to_csv("docs/replay/hiro/exp3_retail_cap.csv", index=False); e3b.to_csv("docs/replay/hiro/exp3_retail_chase.csv", index=False)
    results.append(report("E3a retail capitulation → sell-first", df, e3a, "sell"))
    results.append(report("E3b retail chase → long-first", df, e3b, "long"))
    c3 = ok & (zr <= -1.5) & ((za - zr) < 1.5) & (df.ret15 < 0) & stall       # equally extreme retail, basket agrees
    results.append(report("E3-CONTROL capitulation, basket agrees", df, outcome_row(df, epis(c3, df), "sell"), "sell"))

    # ---- E4: post-shock dealer vacuum -------------------------------------------------------------------------
    new_low = df.low <= df.groupby("day").low.transform(lambda s: s.rolling(30, min_periods=30).min())
    fell3 = df.ret15 <= -3
    shock_recent = (new_low & fell3).groupby(df.day).transform(lambda s: s.rolling(10, min_periods=1).max()).astype(bool)
    r3c = df.groupby("day").Lc.diff(3); r3p = df.groupby("day").Lp.diff(3)
    flat = (r3c.abs() <= exq(r3c.abs(), 0.25)) & (r3p.abs() <= exq(r3p.abs(), 0.25))
    no_ext = df.low >= df.groupby("day").low.transform(lambda s: s.rolling(3).min()).shift(1)
    m4 = ok & shock_recent & flat & no_ext
    e4 = outcome_row(df, epis(m4, df), "sell"); e4.to_csv("docs/replay/hiro/exp4_vacuum.csv", index=False)
    results.append(report("E4 post-shock vacuum (sell-first)", df, e4, "sell"))
    c4 = ok & shock_recent & ~flat & no_ext
    results.append(report("E4-CONTROL shock, flow still active", df, outcome_row(df, epis(c4, df), "sell"), "sell"))

    pd.DataFrame([r for r in results if r.get("n", 0) >= 0]).to_csv("docs/replay/hiro/hiro_experiments_results.csv", index=False)


if __name__ == "__main__":
    main()
