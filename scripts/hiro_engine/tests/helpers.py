"""Fixture builders for rule/executor/session tests."""
from __future__ import annotations

from hiro_engine.models import Bar, FeatureRow, Vetoes


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
        episode_a=None, episode_b=None, a_conditions=False, b_armed=False,
        b_gates=False, late_state=False, hiro_fresh=True,
        vetoes=Vetoes(), health="OK",
    )
    defaults.update(kw)
    return FeatureRow(**defaults)


def b_fire_row(m: int, episode: int = 1, **kw) -> FeatureRow:
    base = dict(b_armed=True, b_gates=True, episode_b=episode, r15=0.5, weak_side=0.4)
    base.update(kw)
    return mk_row(m, **base)


def a_fire_row(m: int, episode: int = 1, **kw) -> FeatureRow:
    base = dict(a_conditions=True, episode_a=episode, r30=-0.5)
    base.update(kw)
    return mk_row(m, **base)
