"""Freeze outcome-free MAD memberships, then join unchanged B09 price outcomes."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from logic import choose_endpoint, classify, describe, thin

OUT = Path(__file__).resolve().parent
ROOT = Path('/Users/dgrissen/Dev/central_trade_data/thetadata')
DATA = ROOT / 'b09_mad_grid_2026-09-19-v1'
REGISTRY = OUT.parent / 'sector_iv_mad_remaining_2025_2026_2026-09-19/all_sector_sources.json'
SCORE = ROOT / 'branch_b_stop10_2026-09-19-v1/event_outcomes.parquet'
DAYS = ROOT / 'branch_b_2024_halfyear_2026-09-19-v1/selected_days.csv'
COMPLETE = ['2025_H1', '2025_H2', '2026_H1']
PERIODS = ['pooled', 'completed'] + COMPLETE + ['2026_H2']
MODES = ['all', 'first', 'spaced60']
SYMBOLS = sorted(['XLC', 'XLY', 'XLP', 'XLE', 'XLF', 'XLV', 'XLI', 'XLB', 'XLRE', 'XLK', 'XLU'])


def digest(path: Path) -> str:
    """Hash a file without loading it all into memory."""
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def save_json(path: Path, value: dict) -> None:
    """Write strict JSON for provenance and verification receipts."""
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def period_rows(frame: pd.DataFrame, period: str) -> pd.DataFrame:
    """Select declared periods; the incomplete half never enters stability ranking."""
    if period == 'pooled':
        return frame
    return frame[frame.half.isin(COMPLETE)] if period == 'completed' else frame[frame.half.eq(period)]


def prepare() -> None:
    """Verify source provenance and freeze grid classifications without outcome fields."""
    if DATA.exists():
        raise FileExistsError(f'Refusing to overwrite prepared data: {DATA}')
    sources = json.loads(REGISTRY.read_text())
    if sorted(s['symbol'] for s in sources) != SYMBOLS:
        raise ValueError('Sector universe changed')
    hashes = {str(REGISTRY): digest(REGISTRY), str(DAYS): digest(DAYS)}
    for source in sources:
        for path, expected in source['files'].items():
            if digest(Path(path)) != expected:
                raise ValueError(f'Changed MAD source: {path}')
            hashes[path] = expected
    expected = json.loads((SCORE.parent / 'score_verification.json').read_text())['hashes'][str(SCORE)]
    if digest(SCORE) != expected:
        raise ValueError('Price outcomes changed')
    hashes[str(SCORE)] = expected
    keys = ['date', 'variant', 'known_min', 'signal_min', 'always_above', 'cohort', 'event_id']
    events = pd.read_parquet(SCORE, columns=keys)
    events = events[events.variant.eq('b09') & events.always_above
                    & events.cohort.ne('development_10') & events.date.ge('2025-01-01')
                    & events.date.le('2026-09-18')]
    events = events.sort_values(['date', 'known_min', 'event_id']).drop_duplicates(['date', 'known_min'])
    events = events.reset_index(drop=True)
    events['entry_id'] = events.date + '|' + events.known_min.astype(str)
    events['half'] = events.date.str[:4] + '_H' + np.where(events.date.str[5:7].astype(int) <= 6, '1', '2')
    if len(events) != 3141 or events.date.nunique() != 178:
        raise ValueError('Frozen parent counts changed')
    days = pd.read_csv(DAYS)
    days = days[days.cohort.ne('development_10') & days.date.ge('2025-01-01')
                & days.date.le('2026-09-18')]
    if not set(events.date) <= set(days.date) or days.date.duplicated().any():
        raise ValueError('Invalid selected-date join')
    frames, coverage = [], []
    for source in sources:
        scores = pd.read_parquet(next(p for p in source['files'] if p.endswith('/scored_windows.parquet')))
        bases = pd.read_parquet(next(p for p in source['files'] if p.endswith('/block_baselines.parquet')))
        if len(bases) != 2145 or not bases.status.eq('ok').all() or not bases.lookback_end.lt(bases.date).all():
            raise ValueError('Baseline availability or temporal boundary failed')
        for base in bases.itertuples():
            history = json.loads(base.source_dates)
            if len(history) != base.history_days or not all(base.lookback_start <= d <= base.lookback_end < base.date for d in history):
                raise ValueError('Historical scale used an invalid date')
        valid = scores.signed_score.notna()
        np.testing.assert_allclose(scores.loc[valid, 'signed_score'],
                                   -scores.loc[valid, 'acceleration'] / scores.loc[valid, 'scale'])
        joined = choose_endpoint(events[['entry_id', 'date', 'known_min', 'half']], scores)
        joined['symbol'] = source['symbol']
        for row in joined[joined.signed_score.notna()].itertuples():
            minutes = json.loads(row.source_minutes)
            if (row.start_min != row.end_min - 29 or row.end_min != row.known_min - 1
                    or len(set(minutes)) != len(minutes)
                    or not all(row.start_min <= m <= row.end_min for m in minutes)):
                raise ValueError('Current source timestamp is outside causal window or duplicated')
            if not np.isfinite([row.b1, row.b2, row.scale]).all() or row.scale <= 0:
                raise ValueError('Invalid usable slope/scale')
        frames.append(joined)
        coverage.append(dict(symbol=source['symbol'],available=int(joined.signed_score.notna().sum()),
                             parent_n=len(events)))
    sectors = pd.concat(frames, ignore_index=True)
    score = sectors.pivot(index='entry_id', columns='symbol', values='signed_score').reindex(index=events.entry_id, columns=SYMBOLS).to_numpy()
    slopes = sectors.pivot(index='entry_id', columns='symbol', values='b2').reindex(index=events.entry_id, columns=SYMBOLS).to_numpy()
    grid = []
    for family in ['signed', 'falling']:
        for threshold in [1, 2, 3, 4]:
            for breadth in range(4, 10):
                state, yes, missing = classify(score, slopes, threshold, breadth, family == 'falling')
                block = events[['entry_id', 'date', 'known_min', 'half']].copy()
                block['family'], block['threshold'], block['breadth'] = family, threshold, breadth
                block['rule'] = f'{family}_m{threshold}_b{breadth}'
                block['state'], block['qualifying_sectors'], block['unknown_sectors'] = state, yes, missing
                grid.append(block)
    DATA.mkdir(parents=True)
    events.to_parquet(DATA / 'event_keys.parquet', index=False)
    days.to_csv(DATA / 'research_dates.csv', index=False)
    sectors.to_parquet(DATA / 'sector_at_entry.parquet', index=False)
    pd.concat(grid, ignore_index=True).to_parquet(DATA / 'memberships.parquet', index=False)
    pd.DataFrame(coverage).to_csv(DATA / 'coverage.csv', index=False)
    generated = ['event_keys.parquet', 'research_dates.csv', 'sector_at_entry.parquet',
                 'memberships.parquet', 'coverage.csv']
    freeze = dict(stage='outcome_free_memberships', input_hashes=hashes,
                  code_hashes={str(p): digest(p) for p in sorted(OUT.glob('*.py'))},
                  protocol_sha256=digest(OUT / 'PROTOCOL.md'),
                  output_hashes={str(DATA / p): digest(DATA / p) for p in generated},
                  rule_count=48, parent_n=len(events), active_dates=int(events.date.nunique()),
                  research_dates=int(days.date.nunique()), outcome_columns_loaded=False)
    save_json(DATA / 'freeze.json', freeze)
    print(json.dumps({k: v for k, v in freeze.items() if not k.endswith('hashes')}), flush=True)


def check_freeze() -> dict:
    """Reject changes to any source, membership, protocol or analysis implementation."""
    freeze = json.loads((DATA / 'freeze.json').read_text())
    checks = freeze['input_hashes'] | freeze['output_hashes'] | freeze['code_hashes']
    checks[str(OUT / 'PROTOCOL.md')] = freeze['protocol_sha256']
    for path, expected in checks.items():
        if digest(Path(path)) != expected:
            raise ValueError(f'Frozen input changed: {path}')
    return freeze


def summaries(events: pd.DataFrame, memberships: pd.DataFrame) -> pd.DataFrame:
    """Enumerate every state and execution policy, preserving unknown disclosures."""
    rows = []
    for period in PERIODS:
        parent = period_rows(events, period)
        for mode in MODES:
            base = thin(parent, mode)
            stats = describe(base)
            rows.append(dict(period=period, mode=mode, rule='baseline', family='baseline',
                             threshold=0, breadth=0, state='all', **stats))
            baseline_winners = set(base.loc[base.outcome.eq('target_first'), 'entry_id'])
            for rule, group in memberships.groupby('rule', sort=True):
                states = period_rows(group, period).set_index('entry_id').state
                aligned = parent.entry_id.map(states)
                if aligned.isna().any():
                    raise ValueError('Missing entry membership')
                for state in ['yes', 'no', 'unknown', 'measurable']:
                    selected = thin(parent[aligned.ne('unknown') if state == 'measurable' else aligned.eq(state)], mode)
                    result = describe(selected)
                    wins = set(selected.loc[selected.outcome.eq('target_first'), 'entry_id'])
                    rows.append(dict(period=period, mode=mode, rule=rule,
                        family=group.family.iloc[0], threshold=int(group.threshold.iloc[0]),
                        breadth=int(group.breadth.iloc[0]), state=state, **result,
                        parent_n=stats['n'], parent_targets=stats['targets'],
                        uplift_pp=result['rate'] - stats['rate'],
                        target_overlap=len(wins & baseline_winners),
                        parent_winners_not_retained=len(baseline_winners - wins)))
    return pd.DataFrame(rows)


def stability(table: pd.DataFrame) -> pd.DataFrame:
    """Rank high N among positive-in-each-half candidates; expose the full frontier."""
    records = []
    yes = table[table.state.eq('yes')]
    for (mode, rule), group in yes.groupby(['mode', 'rule']):
        complete = group[group.period.isin(COMPLETE)]
        pooled, total = group[group.period.eq('pooled')].iloc[0], group[group.period.eq('completed')].iloc[0]
        all_halves = len(complete) == 3 and complete.n.gt(0).all()
        row = dict(mode=mode, rule=rule, family=pooled.family, threshold=int(pooled.threshold),
                   breadth=int(pooled.breadth), n=int(pooled.n), targets=int(pooled.targets),
                   days=int(pooled.days), rate=pooled.rate, completed_n=int(total.n),
                   completed_rate=total.rate, worst_rate=complete.rate.min() if all_halves else np.nan,
                   worst_uplift=complete.uplift_pp.min() if all_halves else np.nan,
                   half_rate_sd=complete.rate.std(ddof=0) if all_halves else np.nan,
                   min_half_n=int(complete.n.min()), min_half_days=int(complete.days.min()),
                   positive_all_halves=bool(all_halves and complete.uplift_pp.gt(0).all()))
        records.append(row)
    result = pd.DataFrame(records)
    result['pareto'] = False
    result['high_n_stable_rank'] = pd.Series(index=result.index, dtype='Int64')
    for mode in MODES:
        scope = result[result['mode'].eq(mode)]
        for idx, row in scope.iterrows():
            if pd.isna(row.worst_rate):
                continue
            dominates = (scope.completed_n.ge(row.completed_n) & scope.worst_rate.ge(row.worst_rate)
                         & scope.worst_uplift.ge(row.worst_uplift)
                         & (scope.completed_n.gt(row.completed_n) | scope.worst_rate.gt(row.worst_rate)
                            | scope.worst_uplift.gt(row.worst_uplift)))
            result.loc[idx, 'pareto'] = not dominates.any()
        ranked = scope[scope.positive_all_halves].sort_values(
            ['completed_n', 'worst_rate', 'rule'], ascending=[False, False, True])
        result.loc[ranked.index, 'high_n_stable_rank'] = range(1, len(ranked) + 1)
    return result


def uncertainty(events: pd.DataFrame, memberships: pd.DataFrame) -> pd.DataFrame:
    """Whole-date resampling with shared draws; intervals are descriptive, unadjusted."""
    dates = pd.read_csv(DATA / 'research_dates.csv').date.tolist()
    weights = np.random.default_rng(20260919).multinomial(
        len(dates), np.full(len(dates), 1 / len(dates)), size=5000)

    def draws(frame: pd.DataFrame) -> np.ndarray:
        daily = frame.assign(hit=frame.outcome.eq('target_first').astype(int)).groupby('date').agg(
            n=('hit', 'size'), wins=('hit', 'sum')).reindex(dates, fill_value=0)
        n, wins = weights @ daily.n.to_numpy(), weights @ daily.wins.to_numpy()
        return np.divide(100 * wins, n, out=np.full(len(n), np.nan), where=n > 0)

    def interval(values: np.ndarray, frame: pd.DataFrame) -> tuple[float, float]:
        valid = values[np.isfinite(values)]
        if frame.date.nunique() < 2 or frame.outcome.eq('target_first').nunique() < 2 or not len(valid):
            return np.nan, np.nan
        return tuple(float(x) for x in np.quantile(valid, [.025, .975]))

    records = []
    for mode in MODES:
        base = thin(events, mode)
        base_draws = draws(base)
        for rule, group in memberships.groupby('rule'):
            states = events.entry_id.map(group.set_index('entry_id').state)
            selected = thin(events[states.eq('yes')], mode)
            measured = thin(events[states.ne('unknown')], mode)
            values, measured_values = draws(selected), draws(measured)
            low, high = interval(values, selected)
            delta_low, delta_high = interval(values - base_draws, selected)
            mlow, mhigh = interval(values - measured_values, selected)
            records.append(dict(mode=mode, rule=rule, low=low, high=high,
                uplift_low=delta_low, uplift_high=delta_high,
                measurable_uplift_low=mlow, measurable_uplift_high=mhigh,
                finite_draws=int(np.isfinite(values).sum()), draws=5000,
                adjustment='none; exploratory across 48 cells'))
    return pd.DataFrame(records)


def paired_families(events: pd.DataFrame, memberships: pd.DataFrame) -> pd.DataFrame:
    """Show what requiring falling IV removes at the exact same threshold/breadth."""
    wide = memberships.pivot(index='entry_id', columns='rule', values='state').reindex(events.entry_id)
    rows = []
    for threshold in [1, 2, 3, 4]:
        for breadth in range(4, 10):
            signed = wide[f'signed_m{threshold}_b{breadth}'].eq('yes').to_numpy()
            falling = wide[f'falling_m{threshold}_b{breadth}'].eq('yes').to_numpy()
            if (falling & ~signed).any():
                raise ValueError('Falling qualifiers must be a subset of signed qualifiers')
            for period in PERIODS:
                for name, mask in [('falling_qualifiers', falling),
                                   ('signed_yes_falling_no', signed & wide[f'falling_m{threshold}_b{breadth}'].eq('no').to_numpy()),
                                   ('signed_yes_falling_unknown', signed & wide[f'falling_m{threshold}_b{breadth}'].eq('unknown').to_numpy())]:
                    rows.append(dict(threshold=threshold, breadth=breadth, period=period,
                                     group=name, **describe(period_rows(events[mask], period))))
    return pd.DataFrame(rows)


def analyze() -> None:
    """Attach verified outcomes only after memberships and code have been frozen."""
    check_freeze()
    if (DATA / 'analysis_receipt.json').exists():
        raise FileExistsError('Completed analysis already exists')
    events = pd.read_parquet(DATA / 'event_keys.parquet')
    cols = ['date', 'variant', 'known_min', 'outcome', 'entry_price', 'first_touch_min']
    outcomes = pd.read_parquet(SCORE, columns=cols)
    outcomes = outcomes[outcomes.variant.eq('b09')]
    for field in ['outcome', 'entry_price', 'first_touch_min']:
        if outcomes.groupby(['date', 'known_min'])[field].nunique(dropna=False).gt(1).any():
            raise ValueError(f'Conflicting duplicate outcome: {field}')
    outcomes = outcomes.drop_duplicates(['date', 'known_min']).drop(columns='variant')
    events = events.merge(outcomes, on=['date', 'known_min'], validate='one_to_one', how='left')
    if events.outcome.isna().any():
        raise ValueError('Missing price outcome')
    memberships = pd.read_parquet(DATA / 'memberships.parquet')
    table = summaries(events, memberships)
    table.to_csv(DATA / 'summary.csv', index=False)
    stability(table).to_csv(DATA / 'stability.csv', index=False)
    paired_families(events, memberships).to_csv(DATA / 'paired_families.csv', index=False)
    events.to_parquet(DATA / 'events_with_outcomes.parquet', index=False)
    print('Summaries and stability complete; computing whole-date intervals.', flush=True)
    uncertainty(events, memberships).to_csv(DATA / 'uncertainty.csv', index=False)
    files = ['summary.csv', 'stability.csv', 'paired_families.csv', 'events_with_outcomes.parquet',
             'uncertainty.csv']
    save_json(DATA / 'analysis_receipt.json', dict(freeze_sha256=digest(DATA / 'freeze.json'),
        outputs={str(DATA / p): digest(DATA / p) for p in files},
        review_status='NOT RUN: separate reviewer prohibited in this side conversation'))
    print(table[table.rule.eq('baseline') & table['mode'].eq('all')].to_string(index=False), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['prepare', 'analyze'])
    command = parser.parse_args().stage
    prepare() if command == 'prepare' else analyze()
