"""Small causal admission and scoring helpers for the frozen Branch B rerun."""
from __future__ import annotations

from numbers import Integral, Real

import numpy as np
import pandas as pd


def checked_window(raw: pd.DataFrame, start: int, end: int) -> pd.DataFrame:
    """Require a complete ordered native window with valid OHLC bounds."""
    if any(isinstance(x, bool) or not isinstance(x, Integral) for x in [start,end]):
        raise ValueError('Window endpoints must be integer minute labels')
    frame = raw.loc[start:end]
    if frame.index.tolist() != list(range(start,end+1)):
        raise ValueError('Missing, duplicate or unordered minute observations')
    values = frame[['open','high','low','close']]
    if not np.isfinite(values.to_numpy(dtype=float)).all() or not (values > 0).all().all():
        raise ValueError('Nonfinite or nonpositive OHLC')
    if not (frame.high.ge(values[['open','close']].max(axis=1))
            & frame.low.le(values[['open','close']].min(axis=1))).all():
        raise ValueError('Invalid OHLC bounds')
    return frame


def vt_flags(raw: pd.DataFrame, minute: int, vt: float) -> dict[str, bool]:
    """Classify admission from observed past lows and the entry open only."""
    if isinstance(vt, (bool,np.bool_)) or not isinstance(vt, Real) or not np.isfinite(vt) or vt <= 0:
        raise ValueError('VT must be finite positive numeric data')
    past = checked_window(raw,570,minute-1)
    if minute not in raw.index or not np.isfinite(raw.loc[minute,'open']):
        raise ValueError('Missing observed entry open')
    above = bool(raw.loc[minute,'open'] > vt)
    return {'entry_above':above,'always_above':bool(above and past.low.min() > vt)}


def score(raw: pd.DataFrame, minute: int) -> dict[str, object]:
    """Score first +5/-15 touch over sixty native minute intervals."""
    window = checked_window(raw,minute,minute+59)
    price = float(window.open.iloc[0])
    up = window.index[window.high.ge(price+5-1e-8)].tolist()
    down = window.index[window.low.le(price-15+1e-8)].tolist()
    a, b = (up[0] if up else 9999), (down[0] if down else 9999)
    if min(a,b) == 9999:
        outcome, touch = 'neither', None
    else:
        outcome = 'ambiguous' if a == b else 'target_first' if a < b else 'adverse_first'
        touch = min(a,b)
    return {'outcome':outcome,'first_touch_min':touch,'entry_price':price,
            'horizon_minutes':60,'endpoint_change':float(window.close.iloc[-1]-price)}


def distinct_entries(events: pd.DataFrame) -> pd.DataFrame:
    """Keep one opportunity per family variant, date and entry minute."""
    return events.sort_values(['date','variant','known_min','event_id']).drop_duplicates(
        ['date','variant','known_min']).reset_index(drop=True)


def thin_entries(events: pd.DataFrame, gap: int) -> pd.DataFrame:
    """Use first eligible entry then an outcome-independent fixed spacing."""
    if isinstance(gap, bool) or not isinstance(gap, Integral) or gap < 1:
        raise ValueError('Spacing must be positive integer minutes')
    frame = distinct_entries(events)
    keep = []
    for _, group in frame.groupby(['date','variant'], sort=False):
        last = None
        for row in group.itertuples():
            if last is None or row.known_min >= last+gap:
                keep.append(row.Index)
                last = row.known_min
    return frame.loc[keep].reset_index(drop=True)
