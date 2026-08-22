"""Feeds (R2): stored-data loaders and ReplayFeed. LiveFeed lives in live.py (task 7).

The HIRO minute frame is built EXACTLY as the reviewed research pipeline
(hiro_setup_dashboard.load_day): ET minute buckets, per-minute delta sums on the
570..960 grid (fill 0), cumulative sums / 1e9, inner-merged with SPX bars.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

import pandas as pd

from .config import Config
from .models import Bar, SpyBar

GRID_START, GRID_END = 570, 960


class FeedError(Exception):
    pass


def load_hiro_day(hiro_root: Path, day: str) -> pd.DataFrame:
    """Minute frame indexed 570..960 with columns all_L/all_Lc/all_Lp/nextExp_L ($B, cumulative)."""
    f = Path(hiro_root) / f"date={day}" / "normalized" / "hiro_series.csv"
    if not f.exists():
        raise FeedError(f"missing HIRO partition: {f}")
    h = pd.read_csv(f)
    ts = pd.to_datetime(h.utc_iso, utc=True).dt.tz_convert("America/New_York")
    h = h.assign(min=ts.dt.hour * 60 + ts.dt.minute)
    h = h[(h["min"] >= GRID_START) & (h["min"] <= GRID_END)]
    out = pd.DataFrame({"min": range(GRID_START, GRID_END + 1)})
    for grp, g in h.groupby("series_group"):
        mm = (g.groupby("min").agg(dT=("delta_total", "sum"), dC=("delta_call", "sum"),
                                   dP=("delta_put", "sum"))
              .reindex(range(GRID_START, GRID_END + 1), fill_value=0.0) / 1e9)
        out[f"{grp}_L"] = mm.dT.cumsum().values
        out[f"{grp}_Lc"] = mm.dC.cumsum().values
        out[f"{grp}_Lp"] = mm.dP.cumsum().values
    for col in ("all_L", "all_Lc", "all_Lp", "nextExp_L"):
        if col not in out.columns:
            raise FeedError(f"HIRO partition {day} lacks series for {col}")
    return out


def load_spx_day(spx_dir: Path, day: str) -> pd.DataFrame:
    f = Path(spx_dir) / f"{day}.parquet"
    if not f.exists():
        raise FeedError(f"missing SPX 1-min parquet: {f}")
    return pd.read_parquet(f).sort_values("min").reset_index(drop=True)


def load_spy_day(spy_parquet: Path, day: str) -> Optional[pd.DataFrame]:
    p = Path(spy_parquet)
    if not p.exists():
        return None
    df = pd.read_parquet(p, filters=[("date", "==", day)])
    if not len(df):
        return None
    return df.sort_values("min").reset_index(drop=True)


@dataclass
class ReplayTick:
    """One completed 1-min bar plus everything known at its close (causal)."""
    bar: Bar
    spy_bar: Optional[SpyBar]
    hiro: Optional[pd.DataFrame]     # minute frame truncated through bar.min; None => HIRO down


class ReplayFeed:
    """Replays stored sessions bar by bar. Refuses missing required sources (R13.1)."""

    def __init__(self, cfg: Config, days: list[str], tier: str = "full"):
        self.cfg = cfg
        self.days = list(days)
        self.tier = tier
        self.require_hiro = tier == "full"
        missing: list[str] = []
        for d in self.days:
            if not (Path(cfg.path_of("spx_dir")) / f"{d}.parquet").exists():
                missing.append(f"{d} (SPX)")
            if self.require_hiro and not (
                Path(cfg.path_of("hiro_root")) / f"date={d}" / "normalized" / "hiro_series.csv"
            ).exists():
                missing.append(f"{d} (HIRO)")
        if missing:
            raise FeedError(
                "refusing dates lacking required data (R13.1): " + ", ".join(missing))

    def spy_available(self, day: str) -> bool:
        return load_spy_day(self.cfg.path_of("spy_parquet"), day) is not None

    def iter_day(self, day: str) -> Iterator[ReplayTick]:
        spx = load_spx_day(self.cfg.path_of("spx_dir"), day)
        hiro = load_hiro_day(self.cfg.path_of("hiro_root"), day) if self.require_hiro else None
        if hiro is None and not self.require_hiro:
            try:
                hiro = load_hiro_day(self.cfg.path_of("hiro_root"), day)
            except FeedError:
                hiro = None
        spy = load_spy_day(self.cfg.path_of("spy_parquet"), day)
        spy_by_min = {int(r.min): SpyBar(int(r.min), float(r.open), float(r.high),
                                         float(r.low), float(r.close), float(r.volume))
                      for r in spy.itertuples()} if spy is not None else {}
        for r in spx.itertuples():
            m = int(r.min)
            if m < GRID_START or m > GRID_END:
                continue
            bar = Bar(m, float(r.open), float(r.high), float(r.low), float(r.close))
            h = hiro[hiro["min"] <= m] if hiro is not None else None
            yield ReplayTick(bar=bar, spy_bar=spy_by_min.get(m), hiro=h)
