"""Fixture builders for rule/executor/session tests."""
from __future__ import annotations

from hiro_engine_v2.models import Bar, FeatureRow, Vetoes


def mk_row(m: int, *, close: float = 100.0, open_: float | None = None,
           high: float | None = None, low: float | None = None, **kw) -> FeatureRow:
    o = open_ if open_ is not None else close
    defaults = dict(
        min=m, bar=Bar(m, o, high if high is not None else close + 0.2,
                       low if low is not None else close - 0.2, close),
        open_0930=100.0,
        L=1.0, Lc=0.6, Lp=0.4, N=0.7, r5=0.1, r15=0.5, r30=0.5, r15n=0.4,
        run=1.0, dur=15.0, rate=4.0 * 0.6, dC=0.6, dP=0.4, dN=0.7, weak_side=0.4,
        share=0.7, drawdown=0.0, run_broke=False,
        pull30=4.0, bounce30=4.0, mid30=101.0, ref_low_bar=m - 20, bh_level=105.0,
        range60=5.0, range60_pct=3.0, warmup=False,
        ema5=100.0, ema9=100.0, ema20=100.0, vwap=100.0, spy_close=100.0,
        vwap_share10=0.9, context_1030=None, context_1300=None,
        episode_a=None, episode_b=None, episode_a_start=None, episode_b_start=None,
        a_conditions=False, b_armed=False,
        b_gates=False, late_state=False, hiro_fresh=True,
        vetoes=Vetoes(), health="OK",
    )
    defaults.update(kw)
    return FeatureRow(**defaults)


def b_fire_row(m: int, episode: int = 1, **kw) -> FeatureRow:
    base = dict(b_armed=True, b_gates=True, episode_b=episode, episode_b_start=m,
                r15=0.5, weak_side=0.4)
    base.update(kw)
    return mk_row(m, **base)


def a_fire_row(m: int, episode: int = 1, **kw) -> FeatureRow:
    base = dict(a_conditions=True, episode_a=episode, episode_a_start=m, r30=-0.5)
    base.update(kw)
    return mk_row(m, **base)


class FakeChains:
    """Test stand-in for ChainStore: static quotes per (minute, strike).
    quotes: {(minute, strike): (bid, ask)}; default None (missing)."""

    def __init__(self, quotes=None, expiry="2026-09-18", snapshot=None):
        self.quotes = quotes or {}
        self._expiry = expiry
        self._snapshot = snapshot          # pandas frame or None

    def _snap(self, minute, strike):
        from hiro_engine_v2.models import QuoteSnap
        if strike is None:
            return None
        q = self.quotes.get((minute, strike))
        if q is None:
            q = self.quotes.get(("*", strike))
        if q is None:
            return None
        bid, ask = q
        return QuoteSnap(strike=strike, bid=bid, ask=ask, valid=(bid > 0 and ask >= bid))

    def quote_view(self, day, minute, k1, k2):
        from hiro_engine_v2.models import QuoteView
        return QuoteView(minute=minute, leg1=self._snap(minute, k1),
                         leg2=self._snap(minute, k2))

    def signal_snapshot(self, day, minute):
        import pandas as pd
        if self._snapshot is not None:
            return self._snapshot
        return pd.DataFrame(columns=["strike", "bid", "ask", "delta"])

    def expiry_of(self, day):
        return self._expiry


def resting_trade(side="sell_first", branch="B", entry_min=700, leg1_fill=40.0,
                  L=None, k1=7500.0, k2=None, **kw):
    """A v3 open trade with a resting limit, for exit-precedence tests."""
    from hiro_engine_v2.models import RestingLimit, SimTrade
    sell = side == "sell_first"
    k2 = k2 if k2 is not None else (k1 + 5 if sell else k1 - 5)
    L = L if L is not None else (leg1_fill - 0.10 if sell else leg1_fill + 0.10)
    lim = RestingLimit(side="buy" if sell else "sell", strike=k2, price=L,
                       placed_min=entry_min, first_eligible_min=entry_min + 1)
    d = dict(id=1, branch=branch, side=side, signal_min=entry_min - 1,
             entry_min=entry_min, s0=100.0, expiry="2026-09-18",
             leg_strikes=f"{k1:.0f}/{k2:.0f}", entry_option_mid=leg1_fill + 0.15,
             resting_limit_ref=L, target=None, bh_level=None,
             entry_L=1.0 if branch == "B" else None, cap_source="chain",
             cap_value=3.5, episode=1, k1=k1, k2=k2, leg1_fill=leg1_fill, limit=lim,
             last_valid_bid=leg1_fill, last_valid_ask=leg1_fill + 0.30,
             last_valid_quote_min=entry_min)
    d.update(kw)
    return SimTrade(**d)


def qv(minute, k1=7500.0, k2=7505.0, leg1=(40.0, 40.3), leg2=(40.2, 40.5)):
    from hiro_engine_v2.models import QuoteSnap, QuoteView
    def snap(k, q):
        if q is None:
            return None
        return QuoteSnap(strike=k, bid=q[0], ask=q[1], valid=(q[0] > 0 and q[1] >= q[0]))
    return QuoteView(minute=minute, leg1=snap(k1, leg1), leg2=snap(k2, leg2))
