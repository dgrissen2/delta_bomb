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
                 mode: str = "backtest", chains=None,
                 prereg_override: bool = False) -> list[SessionRow]:
    """Runs sessions in date order. The causal pooled range60 history for day D
    is built from ALL stored sessions in [pool_start, D) — independent of which
    dates the run requests (codex review 2026-08-22 finding 6). pool_start =
    hiro_era_start for the full tier (R3.3); the archive start for price tier
    (documented interpretation, build_notes.md)."""
    if tier.fill_mode == "limit":
        if chains is None:
            from .chains import ChainStore
            chains = ChainStore()
        # 15B INTERLOCK (R9a boundary): a full-tier run over any frozen control
        # session IS a rehearsal — refuse while the formulas pin is empty,
        # unless the test-only override is set.
        if any(d in set(cfg.control_days) for d in days):
            chains.verify_frozen(cfg)                       # R8.2 pin enforced at runtime
        formulas_pin = str(cfg.get("chains", "r9a_formulas_hash"))
        import os
        override_ok = prereg_override and os.environ.get("HIRO_ENGINE_TEST") == "1"
        if not override_ok and formulas_pin == "" and \
                any(d in set(cfg.control_days) for d in days):
            raise RuntimeError(
                "REFUSED: full-tier backtest over frozen control sessions while "
                "r9a_formulas_hash is unpinned would burn the one-shot rehearsal "
                "boundary (R9a). Pin the pre-registration first (task 16).")
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
        s = Session(cfg, tier, day, mode, log, range60_history=list(hist),
                    chains=chains)
        out.append(s.run_replay(feed))
    return out
