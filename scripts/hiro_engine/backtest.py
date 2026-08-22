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
    """Runs sessions in date order. The causal pooled range60 history for day D
    is built from ALL stored sessions in [pool_start, D) — independent of which
    dates the run requests (codex review 2026-08-22 finding 6). pool_start =
    hiro_era_start for the full tier (R3.3); the archive start for price tier
    (documented interpretation, build_notes.md)."""
    feed = ReplayFeed(cfg, days, tier=tier.name)      # refuses+lists missing (R13.1)
    era_start = str(cfg.get("data", "hiro_era_start"))
    pool_start = era_start if tier.name == "full" else "0000-00-00"
    stored = available_spx_days(cfg, pool_start, "9999-99-99")
    hist: list[float] = []
    pooled_upto = 0                                    # index into `stored`
    out: list[SessionRow] = []
    for day in sorted(days):
        while pooled_upto < len(stored) and stored[pooled_upto] < day:
            hist.extend(build_range60_history(cfg, tier, [stored[pooled_upto]]))
            pooled_upto += 1
        s = Session(cfg, tier, day, mode, log, range60_history=list(hist))
        out.append(s.run_replay(feed))
    return out
