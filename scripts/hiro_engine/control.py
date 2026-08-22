"""Frozen matched controls (R11.4 / R11.5) — deterministic functions computed at
scorecard time over the frozen control dataset (8 research sessions pinned by
path + data hash in CONFIG). The clock-matched weighting math is the SINGLE HOME
of the research logic from hiro_uptrend_confirm.clock_matched / 
hiro_experiments.cm_base (those scripts import `clock_weighted_mean` from here).
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from .config import Config
from .feeds import FeedError, load_hiro_day, load_spx_day

HORIZON = 60
WINDOW = (600, 870)              # R11.4 candidate minutes 10:00-14:30


class ControlDatasetError(Exception):
    pass


def control_data_hash(cfg: Config) -> str:
    """sha256 over the frozen sessions' HIRO CSVs + SPX parquets (name+bytes)."""
    h = hashlib.sha256()
    for d in cfg.control_days:
        for p in (Path(cfg.path_of("hiro_root")) / f"date={d}" / "normalized" / "hiro_series.csv",
                  Path(cfg.path_of("spx_dir")) / f"{d}.parquet"):
            h.update(p.name.encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def verify_control_dataset(cfg: Config) -> None:
    got = control_data_hash(cfg)
    if got != cfg.control_data_hash:
        raise ControlDatasetError(
            f"frozen control dataset changed: hash {got[:16]}… != CONFIG pin "
            f"{cfg.control_data_hash[:16]}… (R8.2) — controls are invalid")


def clock_weighted_mean(base: pd.DataFrame, entry_minutes: pd.Series, col: str) -> float:
    """Weight candidate minutes to match the entries' clock-minute distribution
    (ported verbatim from the reviewed research weighting)."""
    w = pd.Series(entry_minutes).value_counts(normalize=True)
    b = base[base["min"].isin(w.index) & base[col].notna()]
    if not len(b):
        return float("nan")
    wt = b["min"].map(w) / b.groupby("min")["min"].transform("size")
    return float(np.average(b[col].astype(float), weights=wt))


def build_control_frame(cfg: Config, check_hash: bool = True,
                        days: list[str] | None = None) -> pd.DataFrame:
    """Pooled per-minute frame with fill-touch indicators and the R6.1 candidate
    fields (causal, pooled range60_pct). Default: the frozen control sessions
    (hash-checked). `days` overrides for R13.3 own-dataset controls."""
    if days is None:
        if check_hash:
            verify_control_dataset(cfg)
        days = cfg.control_days
    fill = cfg.num("r1_instruments", "fill_touch_pts")
    roll = cfg.i("r3_derived", "roll_window")
    r60w = cfg.i("r3_derived", "range60_window")
    frames = []
    for day in days:
        spx = load_spx_day(cfg.path_of("spx_dir"), day)
        try:
            hiro = load_hiro_day(cfg.path_of("hiro_root"), day)
            g = hiro.merge(spx, on="min", how="inner").reset_index(drop=True)
        except FeedError:
            g = spx.copy()                        # price-tier own-dataset controls
            g["r30"] = float("nan")
        g = g.reset_index(drop=True)
        g["day"] = day
        if "all_L" in g.columns:
            g["r30"] = g.all_L.diff(30)
        elif "r30" not in g.columns:
            g["r30"] = float("nan")
        c = g.close
        g["bounce30"] = c - c.rolling(roll, min_periods=roll).min()
        g["mid30"] = (c.rolling(roll, min_periods=roll).max()
                      + c.rolling(roll, min_periods=roll).min()) / 2
        g["range60"] = (c.rolling(r60w, min_periods=r60w).max()
                        - c.rolling(r60w, min_periods=r60w).min()).shift(1)
        # R7.1 fill-touch indicators from the NEXT bar's open, complete horizons only
        o, hi, lo = g.open.values, g.high.values, g.low.values
        n = len(g)
        up = np.full(n, np.nan); dn = np.full(n, np.nan)
        for i in range(n):
            if i + 1 + HORIZON > n:
                continue                       # incomplete horizon -> excluded
            p = o[i + 1]
            up[i] = float((hi[i + 1:i + 1 + HORIZON] >= p + fill).any())
            dn[i] = float((lo[i + 1:i + 1 + HORIZON] <= p - fill).any())
        g["touch_up"], g["touch_dn"] = up, dn
        frames.append(g)
    df = pd.concat(frames).reset_index(drop=True)
    # causal pooled expanding percentile, shifted one bar (research exq form)
    pct = cfg.num("r3_derived", "range60_pctile")
    minp = cfg.i("r3_derived", "range60_min_obs")
    df["range60_pct"] = df.range60.expanding(min_periods=minp).quantile(pct).shift(1)
    return df


def clock_matched(cfg: Config, entry_minutes, frame: pd.DataFrame | None = None) -> float:
    """R11.4 — Branch B control: every frozen-dataset minute 10:00-14:30 with a
    complete horizon, weighted to the entries' clock distribution; weighted mean
    of the sell-first fill-touch indicator."""
    df = frame if frame is not None else build_control_frame(cfg)
    base = df[(df["min"] >= WINDOW[0]) & (df["min"] <= WINDOW[1])]
    return clock_weighted_mean(base, pd.Series(entry_minutes), "touch_up")


def midpoint_matched(cfg: Config, entry_minutes, frame: pd.DataFrame | None = None) -> float:
    """R11.5 — Branch A control: candidate minutes satisfy R6.1 (i),(iii),(iv)
    but FAIL (ii) (r30 >= 0); same weighting; long-first fill-touch indicator."""
    df = frame if frame is not None else build_control_frame(cfg)
    a_min = cfg.num("r6_entries", "a_bounce_min_pts")
    cand = df[(df["min"] >= WINDOW[0]) & (df["min"] <= WINDOW[1])
              & df.range60.notna() & df.range60_pct.notna()
              & (df.range60 >= df.range60_pct)
              & (df.bounce30 >= a_min) & (df.close < df.mid30)
              & df.r30.notna() & (df.r30 >= 0)]
    return clock_weighted_mean(cand, pd.Series(entry_minutes), "touch_dn")
