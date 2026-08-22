"""InstrumentSelector (R1.1-R1.3) — expiry, strikes, sizing. Pure functions.

With no chain feed (all backtests), signals carry the "nearest -0.20Δ put" hint
(R1.2) and strike fields stay None.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from .config import Config


class InstrumentSelector:
    def __init__(self, cfg: Config):
        self.width = cfg.i("r1_instruments", "width_strikes")
        self.dte_target = cfg.i("r1_instruments", "dte_target")
        self.dte_min = cfg.i("r1_instruments", "dte_min")
        self.dte_max = cfg.i("r1_instruments", "dte_max")
        self.delta_target = cfg.num("r1_instruments", "delta_target")
        self.size = cfg.i("r1_instruments", "size_contracts")   # R1.3: 1, paper, always

    def pick_expiry(self, session_date: str, listed: list[str]) -> Optional[str]:
        """Listed expiry nearest dte_target within [dte_min, dte_max]; tie -> shorter."""
        d0 = date.fromisoformat(session_date)
        best: Optional[tuple[int, int, str]] = None
        for e in listed:
            dte = (date.fromisoformat(e) - d0).days
            if self.dte_min <= dte <= self.dte_max:
                key = (abs(dte - self.dte_target), dte)         # tie -> shorter DTE
                if best is None or key < best[:2]:
                    best = (*key, e)
        return best[2] if best else None

    def pick_strike(self, chain: list[dict]) -> Optional[float]:
        """Put closest to delta_target; tie -> lower strike. chain rows: {strike, delta}."""
        best: Optional[tuple[float, float]] = None
        for row in chain:
            d = row.get("delta")
            if d is None:
                continue
            key = (abs(float(d) - self.delta_target), float(row["strike"]))
            if best is None or key < best:
                best = key
        return best[1] if best else None

    def legs(self, side: str, k: float) -> tuple[float, float]:
        """(first leg strike, second leg strike). Width always 5 strike points."""
        if side == "sell_first":
            return k, k + self.width          # sell K, buy K+5
        return k, k - self.width              # buy K, sell K-5

    def hint(self, side: str) -> str:
        """R1.2 no-chain fallback text."""
        verb = "SELL" if side == "sell_first" else "BUY"
        return f"{verb} nearest -0.20Δ put (no chain feed)"
