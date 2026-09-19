"""Rescore frozen entries; independently verify native barriers and paired summaries."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

from scoring import score

OUT = Path(__file__).resolve().parent
PRIOR = OUT.parent/'branch_b_2024_halfyear_2026-09-19'
ROOT = Path('/Users/dgrissen/Dev/central_trade_data')
OLD = ROOT/'thetadata/branch_b_2024_halfyear_2026-09-19-v1'
DATA = ROOT/'thetadata/branch_b_stop10_2026-09-19-v1'
sys.path.insert(0, str(PRIOR))
from periods import PERIODS, cohort  # noqa: E402
from rerun_core import distinct_entries, thin_entries  # noqa: E402

VARIANTS = ['b01', 'thrust', 'staircase', 't', 'b05', 'b06_breakout', 'b06_retest',
            'b07', 'b08_price', 'b08_rsi', 'b09', 'b10_breakout', 'b10_retest']
GROUPS = PERIODS+['combined_non_development', 'new_2024', 'prior_239', 'development_10']
OUTCOMES = ['target_first', 'adverse_first', 'neither', 'ambiguous']


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: dict) -> None:
    with path.open('x') as file:
        json.dump(value, file, indent=2, allow_nan=False)
        file.write('\n')


def verify_freeze() -> None:
    for path, wanted in json.loads((DATA/'input_freeze.json').read_text())['hashes'].items():
        if digest(Path(path)) != wanted:
            raise ValueError(f'Frozen input changed: {path}')


def freeze() -> None:
    if DATA.exists():
        raise FileExistsError(DATA)
    old_freeze = json.loads((OLD/'input_freeze.json').read_text())['hashes']
    for path, wanted in old_freeze.items():
        if digest(Path(path)) != wanted:
            raise ValueError(f'Prior frozen input changed: {path}')
    paths = [OUT/'PROTOCOL.md', OUT/'scoring.py', Path(__file__), PRIOR/'periods.py',
             OLD/'event_outcomes.parquet', OLD/'comparison.csv', OLD/'selected_days.csv',
             OLD/'population.csv', OLD/'inventory.json']
    hashes = old_freeze | {str(p): digest(p) for p in paths}
    DATA.mkdir()
    write_json(DATA/'input_freeze.json', {'at': datetime.now(timezone.utc).isoformat(),
        'before_new_outcomes': True, 'target_points': 5, 'adverse_points': 10,
        'previous_adverse_points': 15, 'horizon_minutes': 60,
        'cohorts': GROUPS, 'bootstrap_draws': 10000, 'seed': 20260919, 'hashes': hashes})


def run() -> None:
    verify_freeze()
    if (DATA/'event_outcomes.parquet').exists():
        raise FileExistsError('Rescore already exists')
    days = pd.read_csv(OLD/'selected_days.csv', float_precision='round_trip')
    raw = pd.read_parquet(OLD/'event_outcomes.parquet')
    results = {}
    checks = 0
    for number, day in enumerate(days.itertuples(), start=1):
        path = Path(day.source_path)
        assert digest(path) == day.source_sha256
        prices = pd.read_parquet(path).set_index('min').loc[570:959]
        assert prices.index.tolist() == list(range(570, 960))
        events = raw[raw.date.eq(day.date)]
        for minute, entries in events.groupby('known_min'):
            minute = int(minute)
            pair = {stop: score(prices, minute, stop) for stop in [15, 10]}
            opening = float(prices.loc[minute, 'open'])
            strict = opening > day.vol_trigger and all(
                low > day.vol_trigger for low in prices.loc[570:minute-1, 'low'])
            assert entries.always_above.eq(strict).all()
            assert entries.entry_price.eq(opening).all()
            assert entries.outcome.eq(pair[15]['outcome']).all()
            old_touch = entries.first_touch_min
            assert (old_touch.isna().all() if pair[15]['first_touch_min'] is None
                    else old_touch.eq(pair[15]['first_touch_min']).all())
            assert np.allclose(entries.endpoint_change, pair[15]['endpoint_change'])
            # Separate sequential scan using native values, not scorer masks/helpers.
            for stop in [15, 10]:
                outcome, touch = 'neither', None
                for bar in prices.loc[minute:minute+59].itertuples():
                    upper = bar.high >= opening+5-1e-8
                    lower = bar.low <= opening-stop+1e-8
                    if upper or lower:
                        outcome = ('ambiguous' if upper and lower else
                                   'target_first' if upper else 'adverse_first')
                        touch = bar.Index
                        break
                assert (outcome, touch) == (pair[stop]['outcome'], pair[stop]['first_touch_min'])
            assert pair[10]['outcome'] != 'target_first' or pair[15]['outcome'] == 'target_first'
            results[(day.date, minute)] = pair[10]
            checks += 1
        if number % 100 == 0:
            print(json.dumps({'phase': 'scoring', 'dates': number, 'unique_price_windows': checks}), flush=True)
    renamed = raw.rename(columns={'outcome': 'outcome_15', 'first_touch_min': 'first_touch_min_15'})
    scored = pd.DataFrame([r | results[(r['date'], int(r['known_min']))]
                           for r in renamed.to_dict('records')])
    assert scored.event_id.equals(raw.event_id)
    assert scored.always_above.equals(raw.always_above)
    scored.to_parquet(DATA/'event_outcomes.parquet', index=False)
    distinct = distinct_entries(scored)
    distinct.to_csv(DATA/'distinct_event_outcomes.csv', index=False)
    write_json(DATA/'score_verification.json', {'raw_rows': len(raw), 'distinct_entries': len(distinct),
        'unique_native_windows': checks, 'both_barriers_independently_checked': True,
        'all_previous_15_outcomes_reproduced': True, 'all_strict_vt_flags_verified': True,
        'entry_identities_unchanged': True, 'new_targets_subset_of_previous': True,
        'hashes': {str(DATA/'event_outcomes.parquet'): digest(DATA/'event_outcomes.parquet')}})


def summarize() -> None:
    verify_freeze()
    if (DATA/'comparison.csv').exists():
        raise FileExistsError('Comparison already exists')
    source = DATA/'event_outcomes.parquet'
    assert digest(source) == json.loads((DATA/'score_verification.json').read_text())['hashes'][str(source)]
    all_entries = distinct_entries(pd.read_parquet(source))
    entries = all_entries[all_entries.always_above].copy()
    entries['hit'] = entries.outcome.eq('target_first').astype(int)
    entries['hit_15'] = entries.outcome_15.eq('target_first').astype(int)
    days = pd.read_csv(OLD/'selected_days.csv')
    old_summary = pd.read_csv(OLD/'comparison.csv')
    rows, transitions, daily_rows = [], [], []
    for name in GROUPS:
        dates = cohort(days, name).date.tolist()
        weights = np.random.default_rng(20260919).multinomial(
            len(dates), np.full(len(dates), 1/len(dates)), size=10000)
        group = cohort(entries, name)
        for sensitivity in ['all', 'first_per_day', 'spaced60']:
            if sensitivity == 'all':
                selected = group
            elif sensitivity == 'first_per_day':
                selected = group.sort_values('known_min').drop_duplicates(['date', 'variant'])
            else:
                selected = thin_entries(group, 60)
            for variant in VARIANTS:
                f = selected[selected.variant.eq(variant)]
                old = old_summary[old_summary.gate.eq('always_above') &
                    old_summary.cohort.eq(name) & old_summary.sensitivity.eq(sensitivity) &
                    old_summary.variant.eq(variant)].iloc[0]
                counts, previous = Counter(f.outcome), Counter(f.outcome_15)
                assert len(f) == old.n
                assert all(previous[k] == getattr(old, k) for k in OUTCOMES)
                daily = f.groupby('date').agg(n=('hit', 'size'), target=('hit', 'sum'),
                                              target_15=('hit_15', 'sum')).reindex(dates, fill_value=0)
                totals = weights @ daily[['n', 'target', 'target_15']].to_numpy(dtype=float)
                totals = totals[totals[:, 0] > 0]
                low, high = (np.quantile(totals[:, 1]/totals[:, 0]*100, [.025, .975])
                             if len(totals) else [np.nan, np.nan])
                dl, dh = (np.quantile((totals[:, 1]-totals[:, 2])/totals[:, 0]*100, [.025, .975])
                          if len(totals) else [np.nan, np.nan])
                n = len(f)
                row = {'cohort': name, 'sensitivity': sensitivity, 'variant': variant,
                    'n': n, 'active_dates': f.date.nunique(), 'qualifying_dates': len(dates),
                    **{k: counts[k] for k in OUTCOMES},
                    **{k+'_15': previous[k] for k in OUTCOMES},
                    'hit_pct': counts['target_first']/n*100 if n else np.nan,
                    'hit_pct_15': old.hit_pct,
                    'change_pp': (counts['target_first']-previous['target_first'])/n*100 if n else np.nan,
                    'lost_targets': previous['target_first']-counts['target_first'],
                    'date_ci_low_pct': low, 'date_ci_high_pct': high,
                    'paired_change_ci_low_pp': dl, 'paired_change_ci_high_pp': dh}
                assert sum(counts.values()) == row['n']
                assert row['lost_targets'] >= 0
                rows.append(row)
                if sensitivity == 'all':
                    daily_rows.extend(daily.reset_index().assign(cohort=name, variant=variant).to_dict('records'))
                    for (before, after), g in f.groupby(['outcome_15', 'outcome']):
                        transitions.append({'cohort': name, 'variant': variant,
                                            'outcome_15': before, 'outcome_10': after, 'n': len(g)})
        print(json.dumps({'phase': 'summary', 'cohort': name}), flush=True)
    frame = pd.DataFrame(rows)
    frame.to_csv(DATA/'comparison.csv', index=False)
    pd.DataFrame(transitions).to_csv(DATA/'outcome_transitions.csv', index=False)
    pd.DataFrame(daily_rows).to_csv(DATA/'daily_counts.csv', index=False)
    write_json(DATA/'analysis_verification.json', {'strict_entries_including_development': len(entries),
        'strict_research_entries': len(entries[entries.cohort.ne('development_10')]),
        'summary_rows': len(frame), 'all_original_denominators_and_15_counts_reproduced': True,
        'hashes': {str(p): digest(p) for p in sorted(DATA.glob('*.csv'))}})
    print(frame[frame.cohort.eq('combined_non_development') & frame.sensitivity.eq('all')][
        ['variant', 'n', 'hit_pct_15', 'hit_pct', 'change_pp', 'lost_targets']].to_string(index=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['freeze', 'run', 'summarize'])
    globals()[parser.parse_args().stage]()
