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
        g["range60"] = (g.high.rolling(r60w, min_periods=r60w).max()
                        - g.low.rolling(r60w, min_periods=r60w).min())
        # R7.1 fill-touch indicators from the NEXT bar's open, complete horizons only
        o, hi, lo = g.open.values, g.high.values, g.low.values
        n = len(g)
        up = np.full(n, np.nan); dn = np.full(n, np.nan)
        for i in range(n):
            # engine fill window = execution bar .. entry+60 (fill beats clock on
            # the timeout bar) = rows i+1 .. i+1+HORIZON inclusive
            if i + 2 + HORIZON > n:
                continue                       # incomplete horizon -> excluded
            p = o[i + 1]
            up[i] = float((hi[i + 1:i + 2 + HORIZON] >= p + fill).any())
            dn[i] = float((lo[i + 1:i + 2 + HORIZON] <= p - fill).any())
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


# =============================================================================
# v3.0 controls (R11.4/R11.5): limit-fill indicators from the pinned chain
# caches, derived ONCE by controls_build and persisted as a hash-pinned frame.
# (Kept in control.py — control semantics live with controls; chains.py stays
# a data module. Noted in build_notes.)
# =============================================================================
CONTROL_FRAME = Path(__file__).resolve().parents[2] / "docs/replay/hiro/control_frame_v3.parquet"


def _strike_series(cd) -> dict:
    out: dict = {}
    for k, g in cd.frame.groupby("strike"):
        out[float(k)] = {int(r.min): (float(r.bid), float(r.ask)) for r in g.itertuples()}
    return out


def _limit_replay(series: dict, k2: float, L: float, buy: bool, first: int,
                  last: int, gap_limit: int) -> tuple:
    """(indicator, eligible). Skips single invalid minutes; >= gap_limit
    consecutive -> ineligible (INDETERMINATE, excluded)."""
    q = series.get(k2, {})
    gap = 0
    for m in range(first, last + 1):
        ba = q.get(m)
        if ba is None or ba[0] <= 0 or ba[1] < ba[0]:
            gap += 1
            if gap >= gap_limit:
                return 0.0, False
            continue
        gap = 0
        if (ba[1] <= L) if buy else (ba[0] >= L):
            return 1.0, True
    return 0.0, True


def controls_build(cfg: Config, chains=None) -> pd.DataFrame:
    """The one-shot derived control frame (R11.4/R11.5, task 17)."""
    from .chains import ChainStore
    from .instruments import InstrumentSelector
    chains = chains or ChainStore()
    chains.verify_frozen(cfg)
    sel = InstrumentSelector(cfg)
    credit = cfg.num("r1v3_limits", "credit")
    tick = cfg.num("r1v3_limits", "limit_tick")
    first_off = cfg.i("r1v3_limits", "first_eligible_offset")
    gap_limit = cfg.i("r1v3_limits", "quote_gap_invalid_after")
    clock = cfg.i("r5_clock", "clock_minutes")
    from .models import round_limit_against
    spx_side = build_control_frame(cfg, check_hash=False)   # A-candidate flags (R6.1 fields)
    rows = []
    for day in cfg.control_days:
        cd = chains.load(day)
        series = _strike_series(cd)
        max_min = int(cd.frame["min"].max())
        for t in range(WINDOW[0], WINDOW[1] + 1):
            snap = cd.snapshot(t)
            entry_min = t + 1
            horizon_end = entry_min + clock
            if horizon_end > max_min or not len(snap):
                continue
            rec = dict(day=day, min=t)
            for side, buy in (("sell_first", True), ("long_first", False)):
                k1, k2 = sel.pick_from_snapshot(snap, side)
                ind, elig = 0.0, False
                if k1 is not None:
                    q1 = series.get(k1, {}).get(entry_min)
                    q2 = series.get(k2, {}).get(entry_min)
                    if (q1 and q2 and q1[0] > 0 and q1[1] >= q1[0]
                            and q2[0] > 0 and q2[1] >= q2[0]):
                        fill1 = q1[0] if side == "sell_first" else q1[1]
                        raw = fill1 - credit if side == "sell_first" else fill1 + credit
                        L = round_limit_against(raw, "buy" if buy else "sell", tick)
                        ind, elig = _limit_replay(series, k2, L, buy,
                                                  t + first_off, horizon_end, gap_limit)
                rec[f"{side}_fill"] = ind
                rec[f"{side}_eligible"] = elig
            rows.append(rec)
    frame = pd.DataFrame(rows)
    a_flags = spx_side[["day", "min", "range60", "range60_pct", "bounce30", "mid30",
                        "close", "r30"]]
    frame = frame.merge(a_flags, on=["day", "min"], how="left")
    a_min = cfg.num("r6_entries", "a_bounce_min_pts")
    frame["a_candidate"] = (frame.range60.notna() & frame.range60_pct.notna()
                            & (frame.range60 >= frame.range60_pct)
                            & (frame.bounce30 >= a_min) & (frame.close < frame.mid30)
                            & frame.r30.notna() & (frame.r30 >= 0))
    # PLAUSIBILITY BAND (task 17): a base rate ~0% or ~100% is a units/sign
    # bug, not a market fact — STOP before the one-shot rehearsal is spent.
    for side in ("sell_first", "long_first"):
        el = frame[frame[f"{side}_eligible"]]
        base = float(el[f"{side}_fill"].mean()) if len(el) else float("nan")
        if not (0.02 <= base <= 0.98):
            raise ControlDatasetError(
                f"controls_build plausibility FAIL: {side} base fill rate {base:.3f} "
                "is outside (0.02, 0.98) — investigate units/sign before proceeding")
    CONTROL_FRAME.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(CONTROL_FRAME, index=False)
    return frame


def control_frame_hash() -> str:
    return hashlib.sha256(CONTROL_FRAME.read_bytes()).hexdigest()


def load_control_frame(cfg: Config) -> pd.DataFrame:
    pin = str(cfg.get("chains", "control_frame_hash"))
    if not CONTROL_FRAME.exists():
        raise ControlDatasetError("control frame missing — run controls_build (task 17)")
    if pin and control_frame_hash() != pin:
        raise ControlDatasetError("control frame hash != CONFIG pin (R8.2)")
    return pd.read_parquet(CONTROL_FRAME)


def clock_matched_v3(cfg: Config, entry_minutes, frame: pd.DataFrame = None) -> float:
    """R11.4 v3: every eligible minute's SELL-FIRST limit-fill indicator,
    clock-weighted to the test's B entry SIGNAL minutes."""
    df = frame if frame is not None else load_control_frame(cfg)
    base = df[df.sell_first_eligible].rename(columns={"sell_first_fill": "w"})
    return clock_weighted_mean(base, pd.Series(entry_minutes), "w")


def midpoint_matched_v3(cfg: Config, entry_minutes, frame: pd.DataFrame = None) -> float:
    """R11.5 v3: A-candidate minutes' LONG-FIRST limit-fill indicator."""
    df = frame if frame is not None else load_control_frame(cfg)
    base = df[df.long_first_eligible & df.a_candidate].rename(
        columns={"long_first_fill": "w"})
    return clock_weighted_mean(base, pd.Series(entry_minutes), "w")
