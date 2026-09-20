"""Pure rules: causal windows, explicit unknowns and execution counting."""
from __future__ import annotations

import numpy as np
import pandas as pd

EPS = 1e-12


def classify(yes: int, missing: int, threshold: int = 6) -> str:
    """Bound qualifying votes against the full eleven-sector universe."""
    if not (0 <= yes <= 11 and 0 <= missing <= 11 and yes + missing <= 11):
        raise ValueError('Invalid sector counts')
    return 'yes' if yes >= threshold else 'no' if yes + missing < threshold else 'unknown'


def conjunct(left: str, right: str) -> str:
    if 'no' in (left, right):
        return 'no'
    return 'yes' if left == right == 'yes' else 'unknown'


def measure(series: pd.Series, entry: int) -> dict:
    """Use exactly T−35…T−6; the whole window must be finite."""
    values = series.reindex(range(entry-35, entry-5)).to_numpy(dtype=float)
    result = dict(available=False, b1=np.nan, b2=np.nan, acceleration=np.nan,
                  full_slope=np.nan, endpoint_change=np.nan)
    if not np.isfinite(values).all():
        return result
    w = np.arange(15)-7
    b1, b2 = float(w@values[:15]/280), float(w@values[15:]/280)
    wf = np.arange(30)-14.5
    return dict(available=True, b1=b1, b2=b2, acceleration=(b2-b1)/15,
                full_slope=float(wf@values/(wf@wf)), endpoint_change=float(values[-1]-values[0]))


def unique_entries(frame: pd.DataFrame) -> pd.DataFrame:
    """A date/minute is one executable opportunity regardless of recipe labels."""
    keys = ['date','known_min']
    for column in ['outcome','entry_price']:
        if column in frame and (frame.groupby(keys)[column].nunique(dropna=False)>1).any():
            raise ValueError(f'Conflicting duplicate {column}')
    return frame.sort_values(keys,kind='stable').drop_duplicates(keys).copy()


def thin(frame: pd.DataFrame, mode: str) -> pd.DataFrame:
    rows = frame.sort_values(['date','known_min'],kind='stable')
    if mode == 'all':
        return rows
    if mode == 'first':
        return rows.drop_duplicates('date')
    if mode != 'spaced60':
        raise ValueError(mode)
    keep, previous = [], {}
    for row in rows.itertuples():
        if row.known_min >= previous.get(row.date,-1000)+60:
            keep.append(row.Index)
            previous[row.date] = row.known_min
    return rows.loc[keep]

