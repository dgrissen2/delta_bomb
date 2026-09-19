"""Reconcile the completed replay against native prices without its scoring helpers."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path('/Users/dgrissen/Dev/central_trade_data/thetadata')
DATA = ROOT/'branch_b_150d_rerun_2026-09-19-v2'
FIRST = ROOT/'branch_b_150d_rerun_2026-09-19-v1'


def subset(frame: pd.DataFrame, cohort: str) -> pd.DataFrame:
    if cohort == 'combined_150':
        return frame
    if cohort in ['added_2025', 'added_2026']:
        return frame[frame.cohort.eq('additional_100') &
                     frame.date.str.startswith(cohort[-4:])]
    return frame[frame.cohort.eq(cohort)]


def main() -> None:
    destination = DATA/'independent_verification.json'
    if destination.exists():
        raise FileExistsError(destination)
    days = pd.read_csv(DATA/'selected_days.csv', float_precision='round_trip')
    raw = pd.read_parquet(DATA/'event_outcomes.parquet')
    events = raw.sort_values('event_id').drop_duplicates(['variant', 'date', 'known_min'])
    checked = 0
    for day in days.itertuples():
        native = pd.read_parquet(day.source_path).set_index('min')
        assert hashlib.sha256(Path(day.source_path).read_bytes()).hexdigest() == day.source_sha256
        assert native.loc[570:959].index.tolist() == list(range(570, 960))
        assert native.loc[570, 'open'] > day.vol_trigger
        for row in events[events.date.eq(day.date)].itertuples():
            minute = int(row.known_min)
            entry = native.loc[minute, 'open']
            assert entry == row.entry_price
            assert bool(entry > day.vol_trigger) == row.entry_above
            continuous = entry > day.vol_trigger and bool(
                (native.loc[570:minute-1, 'low'] > day.vol_trigger).all())
            assert continuous == row.always_above
            outcome = 'neither'
            for bar in native.loc[minute:minute+59].itertuples():
                target = bar.high >= entry+5-1e-8
                adverse = bar.low <= entry-15+1e-8
                if target or adverse:
                    outcome = ('ambiguous' if target and adverse else
                               'target_first' if target else 'adverse_first')
                    assert bar.Index == row.first_touch_min
                    break
            assert outcome == row.outcome, (row.event_id, outcome, row.outcome)
            checked += 1
    summaries = pd.read_csv(DATA/'comparison.csv')
    for item in summaries.itertuples():
        eligible = events if item.gate == 'opening_only' else events[events[item.gate]]
        f = subset(eligible, item.cohort)
        f = f[f.variant.eq(item.variant)].sort_values(['date', 'known_min'])
        if item.sensitivity == 'first_per_day':
            f = f.drop_duplicates('date')
        elif item.sensitivity == 'spaced60':
            accepted = []
            last = {}
            for r in f.itertuples():
                if r.date not in last or r.known_min-last[r.date] >= 60:
                    accepted.append(r.Index)
                    last[r.date] = r.known_min
            f = f.loc[accepted]
        assert len(f) == item.n
        assert f.date.nunique() == item.active_dates
        counts = Counter(f.outcome)
        for outcome in ['target_first', 'adverse_first', 'neither', 'ambiguous']:
            assert counts[outcome] == getattr(item, outcome)
        controls = {(r.date, r.known_min//60): r.outcome == 'target_first'
                    for r in eligible[eligible.variant.eq('b01')].itertuples()}
        differences = [(r.outcome == 'target_first')-controls[(r.date, r.known_min//60)]
                       for r in f.itertuples() if (r.date, r.known_min//60) in controls]
        assert len(differences) == item.matched_n
        if differences:
            assert np.isclose(np.mean(differences)*100, item.control_difference_pp)
    for manifest in ['input_freeze.json', 'analysis_freeze.json', 'event_freeze.json',
                     'adapter_freeze.json', 'analysis_complete.json']:
        content = json.loads((DATA/manifest).read_text())
        for path, wanted in content.get('hashes', {}).items():
            assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == wanted, path
    before = pd.read_parquet(FIRST/'events_before_outcomes.parquet')
    left, right = set(before.event_id), set(raw.event_id)
    changes = pd.concat([
        before[~before.event_id.isin(right)].assign(change='v1_only'),
        raw[~raw.event_id.isin(left)].assign(change='v2_only')], ignore_index=True)
    changes = changes[['date', 'variant', 'known_min', 'setup_id', 'event_id', 'change']]
    changes.to_csv(DATA/'warmup_event_identity_changes.csv', index=False)
    old_history = pd.read_csv(FIRST/'history_ledger.csv')
    new_history = pd.read_csv(DATA/'history_ledger.csv')
    new_history[~new_history.date.isin(old_history.date)].to_csv(
        DATA/'warmup_added_sources.csv', index=False)
    changes_summary = changes.groupby(['variant', 'change']).size().unstack(fill_value=0)
    changes_summary.to_csv(DATA/'warmup_change_counts.csv')
    result = {
        'native_days_checked': len(days), 'independent_native_outcomes_and_vt_gates': checked,
        'comparison_rows_reconciled': len(summaries),
        'all_frozen_manifest_hashes_unchanged': True,
        'raw_events': len(raw), 'distinct_opportunities': len(events),
        'strict_raw_events': int(raw.always_above.sum()),
        'strict_distinct_opportunities': int(events.always_above.sum()),
        'v1_unscored_raw_events': len(before), 'v2_raw_events': len(raw),
        'added_history_sources': len(set(new_history.date)-set(old_history.date)),
        'identity_changes': changes_summary.to_dict('index'),
        'verifier_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    with destination.open('x') as file:
        json.dump(result, file, indent=2)
        file.write('\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
