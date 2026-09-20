"""Separate scalar replay of grid membership and every published summary count."""
from __future__ import annotations

from collections import Counter
import json
import math

import numpy as np
import pandas as pd

from run import COMPLETE, DATA, ROOT, check_freeze, digest, save_json


def scalar_vote(score: float, slope: float, threshold: int, falling: bool) -> str:
    """Three-valued conjunction implemented independently of vectorized rules."""
    magnitude = None if not math.isfinite(score) else score > threshold
    direction = True if not falling else None if not math.isfinite(slope) else slope < -1e-12
    if magnitude is False or direction is False:
        return 'no'
    if magnitude is True and direction is True:
        return 'yes'
    return 'unknown'


def independent_thin(frame: pd.DataFrame, mode: str) -> pd.DataFrame:
    """Separate chronological replay; ignores outcomes entirely."""
    indices, last = [], {}
    for row in frame.sort_values(['date', 'known_min']).itertuples():
        if mode == 'all' or row.date not in last or (mode == 'spaced60' and row.known_min - last[row.date] >= 60):
            indices.append(row.Index)
            last[row.date] = row.known_min
    return frame.loc[indices]


def main() -> None:
    """Fail on any provenance, membership, count, nesting or inherited baseline mismatch."""
    check_freeze()
    receipt = json.loads((DATA / 'analysis_receipt.json').read_text())
    for path, sha in receipt['outputs'].items():
        if digest(__import__('pathlib').Path(path)) != sha:
            raise ValueError(f'Changed output: {path}')
    sectors = pd.read_parquet(DATA / 'sector_at_entry.parquet')
    membership = pd.read_parquet(DATA / 'memberships.parquet')
    events = pd.read_parquet(DATA / 'events_with_outcomes.parquet')
    table = pd.read_csv(DATA / 'summary.csv')
    scalar = {}
    for (family, threshold), group in membership.groupby(['family', 'threshold']):
        counts = {}
        for entry_id, observations in sectors.groupby('entry_id', sort=False):
            votes = Counter(scalar_vote(float(r.signed_score), float(r.b2), int(threshold), family == 'falling')
                            for r in observations.itertuples())
            counts[entry_id] = votes['yes'], votes['unknown']
        for row in group.itertuples():
            yes, unknown = counts[row.entry_id]
            answer = 'yes' if yes >= row.breadth else 'no' if yes + unknown < row.breadth else 'unknown'
            if (answer, yes, unknown) != (row.state, row.qualifying_sectors, row.unknown_sectors):
                raise ValueError('Scalar classification disagrees')
            scalar[row.entry_id, row.rule] = answer
    wide = membership.pivot(index='entry_id', columns='rule', values='state')
    for family in ['signed', 'falling']:
        for k in [1, 2, 3, 4]:
            for b in range(4, 10):
                yes = wide[f'{family}_m{k}_b{b}'].eq('yes')
                if k < 4 and (wide[f'{family}_m{k+1}_b{b}'].eq('yes') & ~yes).any():
                    raise ValueError('Threshold nesting failed')
                if b < 9 and (wide[f'{family}_m{k}_b{b+1}'].eq('yes') & ~yes).any():
                    raise ValueError('Breadth nesting failed')
                if family == 'falling' and (yes & ~wide[f'signed_m{k}_b{b}'].eq('yes')).any():
                    raise ValueError('Falling subset failed')
    for row in table.itertuples():
        pool = events if row.period == 'pooled' else events[events.half.isin(COMPLETE)] if row.period == 'completed' else events[events.half.eq(row.period)]
        if row.rule != 'baseline':
            states = pool.entry_id.map(wide[row.rule])
            pool = pool[states.ne('unknown') if row.state == 'measurable' else states.eq(row.state)]
        selected = independent_thin(pool, row.mode)
        counts = Counter(selected.outcome)
        actual = (len(selected), counts['target_first'], counts['adverse_first'],
                  counts['neither'], counts['ambiguous'], selected.date.nunique())
        expected = (row.n, row.targets, row.adverse_first, row.neither, row.ambiguous, row.days)
        if actual != expected:
            raise ValueError(f'Summary differs: {row.rule}/{row.period}/{row.mode}/{row.state}')
        rate = 100 * counts['target_first'] / len(selected) if len(selected) else np.nan
        np.testing.assert_allclose(rate, row.rate, rtol=0, atol=1e-10, equal_nan=True)
    inherited = pd.read_csv(ROOT / 'branch_b_iv_full_2024_2026_2026-09-19-v1/comparison.csv')
    inherited = inherited[inherited.variant.eq('b09') & inherited.rule.eq('baseline')
                          & inherited.period.isin(COMPLETE + ['2026_H2'])]
    checks = 0
    for row in inherited.itertuples():
        actual = table[table.rule.eq('baseline') & table.period.eq(row.period) & table['mode'].eq(row.mode)].iloc[0]
        if (actual.n, actual.targets, actual.days) != (row.n, row.targets, row.days):
            raise ValueError('Inherited B09 parent not reproduced')
        checks += 1
    result = dict(input_hashes_unchanged=True, scalar_memberships_replayed=len(scalar),
                  summary_rows_replayed=len(table), inherited_half_mode_baselines=checks,
                  threshold_breadth_and_falling_nesting=True,
                  parent_entries=len(events), parent_active_dates=int(events.date.nunique()),
                  review='local separate-implementation checks; NOT independent Claude review')
    save_json(DATA / 'verification.json', result)
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
