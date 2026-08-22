"""Backtest runner (task 6): ReplayFeed sessions through the identical rule
module used live — one code path. Dates lacking required sources are refused
and listed (R13.1), never silently skipped."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from .config import Config
from .eventlog import EventLog
from .feeds import FeedError, ReplayFeed
from .models import SessionRow, TierPolicy
from .session import Session, build_range60_history


def available_spx_days(cfg: Config, d_from: str, d_to: str) -> list[str]:
    spx_dir = cfg.path_of("spx_dir")
    days = sorted(p.stem for p in Path(spx_dir).glob("????-??-??.parquet"))
    return [d for d in days if d_from <= d <= d_to]


def run_backtest(cfg: Config, tier: TierPolicy, days: list[str], log: EventLog,
                 mode: str = "backtest") -> list[SessionRow]:
    """Runs sessions in date order with a causal pooled range60 history:
    full tier seeds from stored HIRO-era sessions before the first day;
    price tier accumulates over the run's own days (documented interpretation
    of R3.3 for pre-HIRO-era dates)."""
    feed = ReplayFeed(cfg, days, tier=tier.name)      # refuses+lists missing (R13.1)
    era_start = str(cfg.get("data", "hiro_era_start"))
    hist: list[float] = []
    if tier.name == "full" and days:
        prior = [d for d in available_spx_days(cfg, era_start, max(era_start, days[0]))
                 if d < days[0]]
        hist = build_range60_history(cfg, tier, prior)
    out: list[SessionRow] = []
    for day in sorted(days):
        s = Session(cfg, tier, day, mode, log, range60_history=list(hist))
        out.append(s.run_replay(feed))
        hist.extend(s.features.r60_today)             # causal accumulation across days
    return out
