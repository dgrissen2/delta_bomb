"""Live/backtest parity check (task 19, R12.3 shakedown gate).

Compares a session's live snapshot sidecar (written by the live loop) against
the next-day historical 1-min series for the same strikes/minutes.
PRE-REGISTERED tolerance: 100% fill-decision agreement; booked prices within
1 tick on >= 95% of compared minutes. A FAIL stops the shakedown sequence.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

TICK = 0.10
DECISION_AGREEMENT = 1.00
PRICE_WITHIN_TICK = 0.95


def parity_check(sidecar_df: pd.DataFrame, historical) -> dict:
    """historical: object with .quote(minute, strike) -> QuoteSnap|None
    (a ChainDay or FakeChains-like). Returns the report dict."""
    rows = []
    for r in sidecar_df.itertuples():
        h = historical.quote(int(r.minute), float(r.strike))
        if h is None or not h.valid:
            rows.append(dict(minute=int(r.minute), strike=float(r.strike),
                             compared=False, decision_match=None, within_tick=None))
            continue
        # decision: would the HISTORICAL quote have been marketable vs the limit?
        hist_marketable = None
        if r.limit_price == r.limit_price:                 # not NaN
            hist_marketable = bool(h.ask <= r.limit_price) if r.decision != "sell_side" \
                else bool(h.bid >= r.limit_price)
        d_match = (hist_marketable == bool(r.marketable)) if hist_marketable is not None else True
        within = (abs(h.bid - r.bid) <= TICK + 1e-9 and abs(h.ask - r.ask) <= TICK + 1e-9)
        rows.append(dict(minute=int(r.minute), strike=float(r.strike), compared=True,
                         decision_match=d_match, within_tick=within))
    df = pd.DataFrame(rows)
    comp = df[df.compared]
    n = len(comp)
    dec = float(comp.decision_match.mean()) if n else float("nan")
    tick = float(comp.within_tick.mean()) if n else float("nan")
    ok = n > 0 and dec >= DECISION_AGREEMENT and tick >= PRICE_WITHIN_TICK
    return dict(ok=ok, compared=n, uncompared=int((~df.compared).sum()),
                decision_agreement=dec, price_within_tick=tick, detail=df)


def run_parity_cli(cfg, day: str) -> int:
    from .config import REPO_ROOT
    from .chains import ChainStore
    from .eventlog import QuoteSidecar
    sc_path = REPO_ROOT / f"docs/replay/hiro/live_quotes_{day}.parquet"
    if not sc_path.exists():
        print(f"parity-check: no sidecar for {day} ({sc_path})")
        return 2
    cd = ChainStore().fetch(day)
    rep = parity_check(QuoteSidecar.load(sc_path), cd)
    print(f"parity {day}: compared {rep['compared']} minutes "
          f"({rep['uncompared']} uncomparable) | decision agreement "
          f"{rep['decision_agreement']:.1%} (need 100%) | prices within 1 tick "
          f"{rep['price_within_tick']:.1%} (need >=95%) -> "
          f"{'PASS' if rep['ok'] else 'FAIL — stop the shakedown sequence'}")
    return 0 if rep["ok"] else 1
