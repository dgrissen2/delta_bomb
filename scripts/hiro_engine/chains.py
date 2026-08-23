"""ChainStore (task 13, spec v3.0 R2.5) — the ONLY module that touches the
option-chain client. Historical: per-session full-chain full-day 1-min
NBBO+greeks cache. Live: minute snapshots (validated by the task-14 spike).

PIN SCOPING (R8.2): CONFIG pins the FROZEN REHEARSAL set only (the 8 control
sessions' manifest sha + SDK version). Live chain data is never a rolling pin.

Expiry convention (frozen, build_notes): candidate expiries are FRIDAYS within
the R1.1 window [20, 40] DTE, nearest 30, tie -> shorter. Fridays are listed
months ahead, so the choice is guaranteed to have existed at signal time
(dailies are listed only ~2 weeks out and would be lookahead).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

from .config import Config
from .models import QuoteSnap, QuoteView

CHAIN_ROOT = Path("~/Dev/central_trade_data/thetadata/spxw_bomb_chains").expanduser()
SYMBOL = "SPXW"
TICK = 0.05                      # exchange minimum; premia here trade on 0.10


class ChainError(Exception):
    pass


def friday_expiry_for(session_date: str, dte_min: int = 20, dte_max: int = 40,
                      dte_target: int = 30) -> dt.date:
    """Frozen convention: nearest FRIDAY to target DTE inside [min, max]; tie -> shorter."""
    d0 = dt.date.fromisoformat(session_date)
    best = None
    for dte in range(dte_min, dte_max + 1):
        cand = d0 + dt.timedelta(days=dte)
        if cand.weekday() == 4:
            key = (abs(dte - dte_target), dte)
            if best is None or key < best[0]:
                best = (key, cand)
    if best is None:
        raise ChainError(f"no Friday expiry within [{dte_min},{dte_max}] DTE of {session_date}")
    return best[1]


def _sdk_pull_day(day: str, expiry: dt.date) -> pd.DataFrame:
    """One full-chain, full-day 1-min greeks pull (puts only — the strategy is puts)."""
    from .live import theta_client, _pull
    import hiro_engine.live as _live
    old = _live.PULL_TIMEOUT_S
    _live.PULL_TIMEOUT_S = 90.0
    try:
        r = _pull(theta_client().option_history_greeks_first_order,
                  symbol=SYMBOL, expiration=expiry, interval="1m",
                  date=dt.date.fromisoformat(day), strike="*", right="put",
                  start_time="09:30:00", end_time="16:00:00")
    finally:
        _live.PULL_TIMEOUT_S = old
    df = r.to_pandas() if hasattr(r, "to_pandas") else pd.DataFrame(r)
    ts = pd.to_datetime(df.timestamp)
    df["min"] = (ts.dt.hour * 60 + ts.dt.minute).astype(int)
    keep = ["min", "strike", "bid", "ask", "delta", "underlying_price"]
    return df[keep].sort_values(["min", "strike"]).reset_index(drop=True)


def sdk_version() -> str:
    import thetadata
    return getattr(thetadata, "__version__", "unknown")


@dataclass(frozen=True)
class ChainDay:
    date: str
    expiry: str
    frame: pd.DataFrame            # min, strike, bid, ask, delta, underlying_price

    def snapshot(self, minute: int) -> pd.DataFrame:
        return self.frame[self.frame["min"] == minute]

    def quote(self, minute: int, strike: float) -> Optional[QuoteSnap]:
        row = self.frame[(self.frame["min"] == minute) & (self.frame.strike == strike)]
        if not len(row):
            return None
        bid, ask = float(row.bid.iloc[0]), float(row.ask.iloc[0])
        return QuoteSnap(strike=strike, bid=bid, ask=ask,
                         valid=(bid > 0 and ask >= bid))          # R10.4 validity


class ChainStore:
    """Historical cache manager. fetch() is idempotent; verify() checks the manifest."""

    def __init__(self, root: Path = CHAIN_ROOT):
        self.root = Path(root)
        self.manifest_path = self.root / "manifest.json"
        self._days: dict[str, ChainDay] = {}

    # -- cache lifecycle ------------------------------------------------------
    def _paths(self, day: str) -> Path:
        return self.root / f"date={day}" / "chain_1m.parquet"

    def fetch(self, day: str) -> ChainDay:
        p = self._paths(day)
        expiry = friday_expiry_for(day)
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            df = _sdk_pull_day(day, expiry)
            if not len(df):
                raise ChainError(f"empty chain pull for {day} {expiry}")
            df.to_parquet(p, index=False)
            self._update_manifest(day, str(expiry), p)
        return self.load(day)

    def _update_manifest(self, day: str, expiry: str, p: Path) -> None:
        m = json.load(open(self.manifest_path)) if self.manifest_path.exists() else {
            "dataset": "spxw_bomb_chains", "symbol": SYMBOL,
            "convention": "Friday expiry nearest 30 DTE in [20,40], tie shorter; puts only; 1-min NBBO+delta",
            "sessions": {}}
        m["sdk_version"] = sdk_version()
        m["sessions"][day] = {
            "expiry": expiry,
            "path": str(p.relative_to(self.root)),
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "rows": int(len(pd.read_parquet(p, columns=["min"]))),
        }
        json.dump(m, open(self.manifest_path, "w"), indent=1, sort_keys=True)

    def load(self, day: str) -> ChainDay:
        if day not in self._days:
            p = self._paths(day)
            if not p.exists():
                raise ChainError(f"chain cache missing for {day} (R13.1): {p}")
            m = json.load(open(self.manifest_path))
            expiry = m["sessions"][day]["expiry"]
            self._days[day] = ChainDay(day, expiry, pd.read_parquet(p))
        return self._days[day]

    def frozen_manifest_hash(self, days: list[str]) -> str:
        """Hash of the FROZEN rehearsal subset of the manifest (pin scope, R8.2)."""
        m = json.load(open(self.manifest_path))
        sub = {d: m["sessions"][d] for d in sorted(days)}
        blob = json.dumps({"sessions": sub, "sdk_version": m["sdk_version"]},
                          sort_keys=True).encode()
        return hashlib.sha256(blob).hexdigest()

    def verify_frozen(self, cfg: Config) -> None:
        pin = str(cfg.get("chains", "frozen_manifest_hash"))
        got = self.frozen_manifest_hash(cfg.control_days)
        if got != pin:
            raise ChainError(f"frozen chain cache changed: {got[:16]}… != pin {pin[:16]}… (R8.2)")
        m = json.load(open(self.manifest_path))
        for d in cfg.control_days:
            p = self.root / m["sessions"][d]["path"]
            if hashlib.sha256(p.read_bytes()).hexdigest() != m["sessions"][d]["sha256"]:
                raise ChainError(f"chain parquet bytes changed for {d}")

    # -- engine-facing views ----------------------------------------------------
    def quote_view(self, day: str, minute: int, k1: Optional[float],
                   k2: Optional[float]) -> QuoteView:
        cd = self.load(day)
        return QuoteView(minute=minute,
                         leg1=cd.quote(minute, k1) if k1 is not None else None,
                         leg2=cd.quote(minute, k2) if k2 is not None else None)

    def signal_snapshot(self, day: str, minute: int) -> pd.DataFrame:
        return self.load(day).snapshot(minute)

    def expiry_of(self, day: str) -> str:
        return self.load(day).expiry


# ---------------------------------------------------------------------------
def real_cache_sanity(cd: ChainDay) -> list[str]:
    """Strategy-blind checks protecting the one-shot rehearsal (task 13)."""
    problems: list[str] = []
    f = cd.frame[(cd.frame.bid > 0)]
    # tick grid
    off = ((f.bid / TICK).round() * TICK - f.bid).abs().max()
    if off > 1e-9:
        problems.append(f"bid off the {TICK} grid by {off}")
    off = ((f.ask / TICK).round() * TICK - f.ask).abs().max()
    if off > 1e-9:
        problems.append(f"ask off the {TICK} grid by {off}")
    # put mid >= intrinsic - 1 tick
    mid = (f.bid + f.ask) / 2
    intrinsic = (f.strike - f.underlying_price).clip(lower=0)
    viol = (mid < intrinsic - TICK - 1e-9).mean()
    if viol > 0.001:
        problems.append(f"put mid < intrinsic on {viol:.2%} of quotes")
    # delta monotonic in strike (puts: more negative at higher strike), per sampled minutes
    for m in f["min"].unique()[::60]:
        snap = f[f["min"] == m].sort_values("strike")
        if len(snap) > 10 and not snap.delta.is_monotonic_decreasing:
            d = snap.delta.diff()
            if (d > 0.005).any():                        # tolerate quote noise
                problems.append(f"delta not monotonic at minute {m}")
                break
    # minute alignment vs SPX grid
    mins = set(cd.frame["min"].unique())
    expected = set(range(570, 961))
    missing = expected - mins
    if len(missing) > 30:
        problems.append(f"{len(missing)} session minutes absent from the chain frame")
    return problems
