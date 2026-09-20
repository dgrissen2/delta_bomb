"""Day influence on the unchanged, unspaced B09 sector-F4-or-SPX cohort."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

SOURCE = Path('/Users/dgrissen/Dev/central_trade_data/thetadata/mad_transfer_spx_2026-09-20-v1')
DEST = SOURCE.parent / 'b09_or_day_influence_2026-09-20-v1'
OUTCOMES = ['target_first', 'adverse_first', 'neither', 'ambiguous']


def sha(path: Path) -> str:
    """Return the file digest used for immutable source verification."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def daily_counts(events: pd.DataFrame, dates: list[str]) -> pd.DataFrame:
    """Count all outcomes, preserving eligible dates without entries."""
    if len(set(dates)) != len(dates):
        raise ValueError('Duplicate research dates')
    if not set(events.date).issubset(dates):
        raise ValueError('Entry date outside research calendar')
    if not set(events.outcome).issubset(OUTCOMES):
        raise ValueError('Unrecognized outcome')
    table = pd.crosstab(events.date, events.outcome).reindex(
        index=dates, columns=OUTCOMES, fill_value=0
    ).astype(int)
    table.index.name = 'date'
    table['n'] = table[OUTCOMES].sum(axis=1)
    table['rate'] = 100 * table.target_first / table.n.replace(0, np.nan)
    return table.reset_index()


def leave_one_out(daily: pd.DataFrame) -> pd.DataFrame:
    """Subtract one entire date; an empty remaining sample is unestimable."""
    result = daily.copy()
    for field in ['n', *OUTCOMES]:
        result[f'remaining_{field}'] = daily[field].sum() - daily[field]
    result['remaining_rate'] = (
        100 * result.remaining_target_first / result.remaining_n.replace(0, np.nan)
    )
    total_n = int(daily.n.sum())
    full_rate = 100 * daily.target_first.sum() / total_n if total_n else np.nan
    result['delta_pp'] = result.remaining_rate - full_rate
    result['remaining_active_days'] = int(daily.n.gt(0).sum()) - daily.n.gt(0).astype(int)
    return result


def summarize(period: str, daily: pd.DataFrame, loo: pd.DataFrame) -> dict:
    """Describe fixed concentration cutoffs and both meanings of best day."""
    n, wins = int(daily.n.sum()), int(daily.target_first.sum())
    ranked = daily.sort_values(['target_first', 'date'], ascending=[False, True])
    best = ranked.iloc[0]
    best_removed = loo.loc[loo.date.eq(best.date)].iloc[0]
    minimum = loo.sort_values(['remaining_rate', 'date']).iloc[0]
    maximum = loo.sort_values(['remaining_rate', 'date'], ascending=[False, True]).iloc[0]
    row = {
        'period': period, 'research_days': len(daily), 'active_days': int(daily.n.gt(0).sum()),
        'winning_days': int(daily.target_first.gt(0).sum()), 'n': n, 'wins': wins,
        'rate': 100 * wins / n, 'parent_n': int(daily.parent_n.sum()),
        'parent_wins': int(daily.parent_target_first.sum()),
        'parent_rate': 100 * daily.parent_target_first.sum() / daily.parent_n.sum(),
        'best_winner_day': best.date, 'best_day_n': int(best.n),
        'best_day_wins': int(best.target_first),
        'best_winner_day_ties': '|'.join(ranked.loc[
            ranked.target_first.eq(best.target_first), 'date']),
        'without_best_n': int(best_removed.remaining_n),
        'without_best_wins': int(best_removed.remaining_target_first),
        'without_best_rate': best_removed.remaining_rate,
        'loo_min_rate': minimum.remaining_rate, 'loo_min_date': minimum.date,
        'loo_max_rate': maximum.remaining_rate, 'loo_max_date': maximum.date,
        'loo_min_uplift_pp': float(loo.remaining_uplift_pp.min()),
        'loo_max_uplift_pp': float(loo.remaining_uplift_pp.max()),
        'largest_signal_day_share_pct': 100 * daily.n.max() / n,
    }
    for k in [1, 3, 5]:
        row[f'top{k}_wins'] = int(ranked.head(k).target_first.sum())
        row[f'top{k}_win_share_pct'] = 100 * row[f'top{k}_wins'] / wins
    return row


def verify_rows(loo: pd.DataFrame, selected: pd.DataFrame, parent: pd.DataFrame) -> int:
    """Independently filter original records for every period/date/cohort."""
    checked = 0
    for row in loo.itertuples(index=False):
        for label, events in [('or', selected), ('parent', parent)]:
            kept = events.loc[events.date.ne(row.date)]
            if row.period != 'pooled':
                kept = kept.loc[kept.half.eq(row.period)]
            prefix = 'remaining_' if label == 'or' else 'remaining_parent_'
            assert len(kept) == getattr(row, prefix + 'n')
            for outcome in OUTCOMES:
                assert int(kept.outcome.eq(outcome).sum()) == getattr(row, prefix + outcome)
            expected_rate = 100 * kept.outcome.eq('target_first').mean()
            assert np.isclose(expected_rate, getattr(row, prefix + 'rate'), equal_nan=True)
            checked += 1
    return checked


def main() -> None:
    """Produce central ledgers and verify against entry-level source records."""
    freeze = json.loads((SOURCE / 'freeze.json').read_text())
    receipt = json.loads((SOURCE / 'analysis_receipt.json').read_text())
    recorded = freeze['output_hashes'] | receipt['outputs']
    sources = {}
    for name in ['research_dates.csv', 'memberships.parquet', 'events_with_outcomes.parquet']:
        path = SOURCE / name
        sources[str(path)] = sha(path)
        if sources[str(path)] != recorded[str(path)]:
            raise ValueError(f'Frozen input changed: {path}')
    dates = pd.read_csv(SOURCE / 'research_dates.csv')
    memberships = pd.read_parquet(SOURCE / 'memberships.parquet')
    events = pd.read_parquet(SOURCE / 'events_with_outcomes.parquet')
    assert len(dates) == 239 and dates.eligible.all()
    assert events.entry_id.is_unique
    parent = events.loc[events.variant.eq('b09')].copy()
    membership = memberships.loc[
        memberships.variant.eq('b09') & memberships.rule.eq('OR_F4_SPX')
    ]
    assert membership.entry_id.is_unique
    assert set(membership.entry_id) == set(parent.entry_id)
    selected = parent.loc[parent.entry_id.isin(
        membership.loc[membership.state.eq('yes'), 'entry_id']
    )].copy()
    assert len(selected) == 318 and selected.outcome.eq('target_first').sum() == 198
    assert len(parent) == 3141 and parent.outcome.eq('target_first').sum() == 1704
    assert parent.always_above.all()
    selected['entry_time_et'] = selected.known_min.map(lambda m: f'{m // 60:02d}:{m % 60:02d}')
    dates['half'] = dates.date.map(lambda d: f'{d[:4]}_H{(int(d[5:7]) - 1) // 6 + 1}')
    assert dict(parent.groupby('date').half.first()) == {
        d: h for d, h in zip(dates.date, dates.half, strict=True) if d in set(parent.date)
    }
    daily = daily_counts(selected, dates.date.tolist())
    daily = daily.merge(dates[['date', 'half']], on='date', validate='one_to_one')
    baseline = daily_counts(parent, dates.date.tolist())
    daily = daily.merge(baseline.rename(columns={c: f'parent_{c}' for c in baseline if c != 'date'}),
                        on='date', validate='one_to_one')
    summaries, ledgers = [], []
    for period in ['pooled', *sorted(dates.half.unique())]:
        part = daily if period == 'pooled' else daily.loc[daily.half.eq(period)]
        loo = leave_one_out(part)
        parent_part = part[['date', *[f'parent_{c}' for c in ['n', *OUTCOMES, 'rate']]]]
        parent_part = parent_part.rename(columns=lambda c: c.removeprefix('parent_'))
        parent_loo = leave_one_out(parent_part)
        for col in parent_loo:
            if col.startswith('remaining_'):
                loo[col.replace('remaining_', 'remaining_parent_', 1)] = parent_loo[col]
        loo['remaining_uplift_pp'] = loo.remaining_rate - loo.remaining_parent_rate
        loo.insert(0, 'period', period)
        summaries.append(summarize(period, part, loo))
        ledgers.append(loo)
    summary = pd.DataFrame(summaries)
    ledger = pd.concat(ledgers, ignore_index=True)
    checked = verify_rows(ledger, selected, parent)
    assert checked == 956
    DEST.mkdir(parents=True, exist_ok=True)
    tables = {'daily_counts.csv': daily, 'leave_one_day_out.csv': ledger,
              'summary.csv': summary, 'selected_entries.csv': selected}
    for name, table in tables.items():
        table.to_csv(DEST / name, index=False)
    script = Path(__file__).resolve()
    record = {
        'scope': 'B09 OR_F4_SPX yes, full cohort, all entries, no spacing',
        'interpretation': 'Post hoc day influence, not confidence intervals or holdout validation',
        'sources': sources,
        'code_protocol_hashes': {str(p): sha(p) for p in [script, script.with_name('PROTOCOL.md'),
                                                        script.with_name('test_analysis.py')]},
        'outputs': {str(DEST / name): sha(DEST / name) for name in tables},
        'verification': {'direct_event_recounts': checked, 'leave_out_rows': len(ledger),
                         'n': len(selected), 'wins': 198, 'research_dates': len(dates)},
    }
    (DEST / 'receipt.json').write_text(json.dumps(record, indent=2) + '\n')
    print(summary.to_string(index=False))
    print(f'Verified {checked} entry-level recounts; saved {DEST}')


if __name__ == '__main__':
    main()
