"""Independently check native prices, admission, population and final accounting."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline import DATA, OLD_DATA, digest, verify


def population_subset(frame: pd.DataFrame, group: str) -> pd.DataFrame:
    if len(group) == 7 and group[4:6] == '_H':
        halves = frame.date.str[:4] + '_H' + frame.date.str[5:7].astype(int).map(lambda m: '1' if m <= 6 else '2')
        return frame[halves.eq(group) & frame.cohort.ne('development_10')]
    if group == 'prior_239':
        return frame[frame.cohort.isin(['original_50', 'additional_100', 'third_tranche'])]
    if group == 'all_qualifying':
        return frame
    if group == 'combined_150':
        return frame[frame.cohort.isin(['original_50', 'additional_100'])]
    if group == 'combined_non_development':
        return frame[frame.cohort.ne('development_10')]
    if group.startswith('third_20'):
        return frame[frame.cohort.eq('third_tranche') & frame.date.str[:4].eq(group[-4:])]
    return frame[frame.cohort.eq(group)]


def main() -> None:
    destination = DATA/'independent_verification.json'
    if destination.exists():
        raise FileExistsError(destination)
    for manifest in ['protocol_freeze.json', 'input_freeze.json', 'analysis_freeze.json',
                     'event_freeze.json', 'analysis_complete.json']:
        verify(manifest)
    days = pd.read_csv(DATA/'selected_days.csv', float_precision='round_trip')
    population = pd.read_csv(DATA/'population.csv')
    prior = pd.read_csv(OLD_DATA/'selected_days.csv')
    assert population.date.nunique() == len(population) == 681
    assert set(days.date) == set(population[population.eligible].date)
    assert set(prior.date) == set(days[days.date.ge('2025-01-01')].date)
    assert not set(days[days.cohort.eq('new_2024')].date) & set(prior.date)
    assert not set(days[days.cohort.eq('third_tranche')].date) & set(days[days.cohort.eq('development_10')].date)
    half_dates = [set(population_subset(days, f'{y}_H{h}').date)
                  for y in (2024, 2025, 2026) for h in (1, 2)]
    assert len(set().union(*half_dates)) == sum(map(len, half_dates)) == len(days)-10
    assert set().union(*half_dates) == set(days[days.cohort.ne('development_10')].date)
    raw = pd.read_parquet(DATA/'event_outcomes.parquet')
    events = raw.sort_values('event_id').drop_duplicates(['variant', 'date', 'known_min'])
    native_checked = 0
    for day in days.itertuples():
        assert digest(Path(day.source_path)) == day.source_sha256
        prices = pd.read_parquet(day.source_path).set_index('min')
        assert prices.loc[570:959].index.tolist() == list(range(570, 960))
        assert prices.loc[570, 'open'] > day.vol_trigger
        assert day.vt_provenance_status == 'matching_preopen_note'
        for event in events[events.date.eq(day.date)].itertuples():
            start = int(event.known_min)
            opening = prices.loc[start, 'open']
            assert opening == event.entry_price
            assert (opening > day.vol_trigger) == event.entry_above
            strict = (opening > day.vol_trigger and
                      bool((prices.loc[570:start-1, 'low'] > day.vol_trigger).all()))
            assert strict == event.always_above
            outcome = 'neither'
            for bar in prices.loc[start:start+59].itertuples():
                up, down = bar.high >= opening+5-1e-8, bar.low <= opening-15+1e-8
                if up or down:
                    outcome = 'ambiguous' if up and down else 'target_first' if up else 'adverse_first'
                    assert event.first_touch_min == bar.Index
                    break
            assert outcome == event.outcome
            native_checked += 1
    summary = pd.read_csv(DATA/'comparison.csv')
    for record in summary.itertuples():
        eligible = events if record.gate == 'opening_only' else events[events[record.gate]]
        group = population_subset(eligible, record.cohort)
        group = group[group.variant.eq(record.variant)].sort_values(['date', 'known_min'])
        if record.sensitivity == 'first_per_day':
            group = group.drop_duplicates('date')
        elif record.sensitivity == 'spaced60':
            keep, previous = [], {}
            for event in group.itertuples():
                if event.date not in previous or event.known_min-previous[event.date] >= 60:
                    keep.append(event.Index)
                    previous[event.date] = event.known_min
            group = group.loc[keep]
        assert len(group) == record.n
        assert group.date.nunique() == record.active_dates
        counts = Counter(group.outcome)
        for outcome in ['target_first', 'adverse_first', 'neither', 'ambiguous']:
            assert counts[outcome] == getattr(record, outcome)
        if len(group):
            assert np.isclose(record.hit_pct, 100*counts['target_first']/len(group))
        controls = {(e.date, e.known_min//60): e.outcome == 'target_first'
                    for e in eligible[eligible.variant.eq('b01')].itertuples()}
        differences = [(e.outcome == 'target_first')-controls[(e.date, e.known_min//60)]
                       for e in group.itertuples() if (e.date, e.known_min//60) in controls]
        assert len(differences) == record.matched_n
        if differences:
            assert np.isclose(np.mean(differences)*100, record.control_difference_pp)
    # Compare historical summaries, without assuming warmup additions are inert.
    original = pd.read_csv(OLD_DATA/'comparison.csv')
    shared = ['original_50', 'additional_100', 'combined_150', 'third_tranche', 'development_10']
    keys = ['gate', 'sensitivity', 'cohort', 'variant']
    columns = keys+['n', 'target_first', 'adverse_first', 'neither', 'ambiguous', 'hit_pct']
    a = summary[summary.cohort.isin(shared)][columns].sort_values(keys).reset_index(drop=True)
    b = original[original.cohort.isin(shared)][columns].sort_values(keys).reset_index(drop=True)
    differences = a.merge(b, on=keys, suffixes=('_new', '_previous'), validate='one_to_one')
    changed = np.zeros(len(differences), dtype=bool)
    for col in columns[len(keys):]:
        changed |= ~np.isclose(differences[col+'_new'], differences[col+'_previous'], equal_nan=True)
    differences[changed].to_csv(DATA/'prior_summary_changes.csv', index=False)
    identity = json.loads((DATA/'prior_event_comparison.json').read_text())
    if identity['exactly_reproduced']:
        pd.testing.assert_frame_equal(a, b)
    result = {'calendar_sessions': len(population), 'eligible_dates': len(days),
              'cohort_dates': days.cohort.value_counts().to_dict(),
              'native_opportunities_checked': native_checked,
              'raw_setup_rows': len(raw), 'strict_distinct_opportunities': int(events.always_above.sum()),
              'summary_rows_reconciled': len(summary), 'prior_summary_rows_compared': len(a),
              'prior_summary_rows_changed': int(changed.sum()),
              'prior_identities_exact': identity['exactly_reproduced'],
              'six_research_periods_partition_dates': True,
              'all_frozen_hashes_verified': True, 'verifier_sha256': digest(Path(__file__))}
    with destination.open('x') as file:
        json.dump(result, file, indent=2)
        file.write('\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
