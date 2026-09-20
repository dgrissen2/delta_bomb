"""Pure, causal rules for the two predeclared B09 MAD grids."""
from __future__ import annotations

import numpy as np
import pandas as pd

EPS = 1e-12
OUTCOMES = ('target_first', 'adverse_first', 'neither', 'ambiguous')


def classify(score: np.ndarray, b2: np.ndarray, threshold: int, breadth: int,
             falling: bool) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return event state and observed yes/unknown counts without imputing gaps."""
    if score.ndim != 2 or b2.shape != score.shape:
        raise ValueError('Scores and slopes require identical event-by-sector shapes')
    if np.isinf(score).any() or np.isinf(b2).any():
        raise ValueError('Infinite measurement')
    if threshold <= 0 or not 1 <= breadth <= score.shape[1]:
        raise ValueError('Invalid positive threshold or sector count')
    finite = np.isfinite(score)
    yes = finite & (score > threshold)
    no = finite & (score <= threshold)
    if falling:
        yes &= np.isfinite(b2) & (b2 < -EPS)
        no |= np.isfinite(b2) & (b2 >= -EPS)
    unknown = ~(yes | no)
    count = yes.sum(axis=1)
    missing = unknown.sum(axis=1)
    state = np.where(count >= breadth, 'yes',
                     np.where(count + missing < breadth, 'no', 'unknown'))
    return state, count, missing


def choose_endpoint(events: pd.DataFrame, scores: pd.DataFrame) -> pd.DataFrame:
    """Exact T−1 join; absent endpoints remain absent and duplicates fail."""
    if scores.duplicated(['date', 'end_min']).any():
        raise ValueError('Duplicate sector endpoint')
    keys = events.copy()
    keys['end_min'] = keys.known_min - 1
    return keys.merge(scores, on=['date', 'end_min'], how='left', validate='many_to_one')


def thin(frame: pd.DataFrame, mode: str) -> pd.DataFrame:
    """Chronological filter-first execution sensitivity, with daily clock reset."""
    rows = frame.sort_values(['date', 'known_min'], kind='stable')
    if mode == 'all':
        return rows
    if mode == 'first':
        return rows.drop_duplicates('date')
    if mode != 'spaced60':
        raise ValueError(mode)
    keep, prior = [], {}
    for row in rows.itertuples():
        if row.known_min >= prior.get(row.date, -10000) + 60:
            keep.append(row.Index)
            prior[row.date] = row.known_min
    return rows.loc[keep]


def describe(frame: pd.DataFrame) -> dict:
    """Keep all four inherited outcomes in the hit-rate denominator."""
    if not frame.outcome.isin(OUTCOMES).all():
        raise ValueError('Unknown price outcome')
    counts = frame.outcome.value_counts()
    n, wins = len(frame), int(counts.get('target_first', 0))
    return dict(n=n, targets=wins, days=int(frame.date.nunique()),
                rate=100 * wins / n if n else np.nan,
                **{key: int(counts.get(key, 0)) for key in OUTCOMES[1:]})
