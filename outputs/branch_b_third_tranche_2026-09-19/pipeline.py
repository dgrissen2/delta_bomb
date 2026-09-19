"""Outcome-blind calendar audit and unchanged Branch B replay for the third tranche."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from datetime import date, datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd

from provenance import assign_cohort, publication_timing

OUT = Path(__file__).resolve().parent
PRIOR = OUT.parent/'branch_b_150d_rerun_2026-09-19'
ROOT = Path('/Users/dgrissen/Dev/central_trade_data/thetadata')
DATA = ROOT/'branch_b_third_tranche_2026-09-19-v1'
OLD_DATA = ROOT/'branch_b_150d_rerun_2026-09-19-v2'
EXPANSION = ROOT/'b06_iv_expansion_150d_2026-09-19-v1'
sys.path.insert(0, str(PRIOR))
import run as replay  # noqa: E402
import analyze as analysis  # noqa: E402
from rerun_core import distinct_entries, score, vt_flags  # noqa: E402


def load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


sampler = load('third_sampler', OUT.parent/'b06_sector_surface_50d_2026-09-13/sample_days.py')
calendar = load('third_calendar', OUT.parent/'xlre_balanced_baseline_2026-09-19/inventory.py')


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    with path.open('x') as file:
        json.dump(value, file, indent=2, allow_nan=False, default=str)
        file.write('\n')


def emit(phase: str, **values: Any) -> None:
    print(json.dumps({'phase': phase, **values}, default=str), flush=True)


def note_evidence(day: str, csv_vt: float | None) -> tuple[dict, list[dict]]:
    notes = []
    for path in sorted(sampler.DEFAULT_NOTES.glob(f'{day}_*/article.md')):
        old = sampler.inspect_note(path, day)
        timing = publication_timing(path.read_text(), day)
        notes.append({'path': str(path), 'sha256': digest(path),
                      'old_preopen': old['preopen'], 'old_issue': old['publication_parse_error'],
                      'vt_values': old['spx_vol_triggers'], 'vt_extracts': old['table_extracts'],
                      **timing})
    values = {v for n in notes if n['preopen'] for v in n['vt_values']}
    legacy = {v for n in notes if n['old_preopen'] for v in n['vt_values']}
    vt = csv_vt
    kind = 'corrected_csv_plus_note'
    if csv_vt is None and len(values) == 1:
        vt, kind = next(iter(values)), 'same_date_preopen_note_only'
    if vt is None or not np.isfinite(vt) or vt <= 0:
        status = 'missing_or_invalid_vt'
    elif values == {vt}:
        status = 'matching_preopen_note'
    elif values:
        status = 'conflicting_preopen_vt'
    else:
        status = 'missing_matching_preopen_note'
    return {'vol_trigger': vt, 'vt_source_kind': kind, 'vt_provenance_status': status,
            'legacy_note_match': csv_vt is not None and legacy == {csv_vt},
            'publication_format_recovered': status == 'matching_preopen_note' and legacy != {vt},
            'note_time_discrepancy': any(n['preopen'] and n['time_labels_differ'] for n in notes)}, notes


def price_source(day: str, prior: dict) -> tuple[dict, list[dict]]:
    paths = []
    if day in prior and isinstance(prior[day].get('source_path'), str) and prior[day]['source_path']:
        paths.append(Path(prior[day]['source_path']))
    paths += [sampler.DEFAULT_ORIGINAL/f'{day}.parquet', sampler.DEFAULT_NEW/f'{day}.parquet',
              EXPANSION/'spx_normalized'/f'{day}.parquet', DATA/'spx_normalized'/f'{day}.parquet']
    attempts = []
    for path in dict.fromkeys(paths):
        if not path.exists():
            continue
        info = sampler.inspect_spx(pd.read_parquet(path), day)
        info.update(source_path=str(path), source_sha256=digest(path))
        attempts.append(info)
        if info['complete']:
            return info, attempts
    return (attempts[-1] if attempts else {'status': 'missing_spx', 'complete': False,
            'spot_open': None, 'rth_rows': 0, 'source_path': '', 'source_sha256': ''}), attempts


def audit_population() -> tuple[pd.DataFrame, dict]:
    """Enumerate every calendar date; neither signals nor outcomes are consulted."""
    levels = pd.read_csv(sampler.DEFAULT_VT).set_index('Date')['Vol Trigger']
    if not levels.index.is_unique:
        raise ValueError('Duplicate dated VT rows')
    old = pd.read_csv(OLD_DATA/'selected_days.csv')
    sources = pd.read_csv(EXPANSION/'research/population_ledger.csv').set_index('date').to_dict('index')
    sources.update(old.set_index('date').to_dict('index'))
    original = set(old[old.cohort.eq('original_50')].date)
    added = set(old[old.cohort.eq('additional_100')].date)
    development = set(json.loads((OLD_DATA/'dashboard_reproduction_inputs/manifest.json').read_text())['selected_dates'])
    rows, evidence = [], []
    for day in calendar.sessions('2025-01-01', '2026-09-18'):
        csv_vt = float(levels[day]) if day in levels else None
        note, notes = note_evidence(day, csv_vt)
        source, attempts = price_source(day, sources)
        vt, opening = note['vol_trigger'], source.get('spot_open')
        above = vt is not None and np.isfinite(vt) and opening is not None and opening > vt
        reasons = []
        if note['vt_provenance_status'] != 'matching_preopen_note':
            reasons.append(note['vt_provenance_status'])
        if not source['complete']:
            reasons.append(source['status'])
        if opening is not None and vt is not None and not above:
            reasons.append('open_not_above_vt')
        cohort = assign_cohort(day, original, added, development)
        rows.append({'date': day, 'cohort': cohort, 'csv_vol_trigger': csv_vt, **note,
                     'spot_open': opening, 'above_vt_at_open': bool(above),
                     'complete_spx': source['complete'], 'rth_rows': source['rth_rows'],
                     'source_path': source['source_path'], 'source_sha256': source['source_sha256'],
                     'early_close': day in calendar.EARLY_CLOSE,
                     'eligible': not reasons, 'exclusion_reasons': '|'.join(reasons)})
        evidence.append({'date': day, 'notes': notes, 'price_attempts': attempts})
    return pd.DataFrame(rows), {'sessions': evidence, 'window_end': '2026-09-18'}


def audit() -> None:
    if DATA.exists():
        raise FileExistsError(DATA)
    ledger, evidence = audit_population()
    DATA.mkdir()
    ledger.to_csv(DATA/'population_before_coverage.csv', index=False)
    write_json(DATA/'provenance_before_coverage.json', evidence)
    needed = ledger[~ledger.complete_spx & ledger.vt_provenance_status.eq('matching_preopen_note') &
                    ~ledger.early_close].date.tolist()
    write_json(DATA/'coverage_plan.json', {'dates': needed, 'source_policy': 'existing native sources first',
                                         'maximum_requests': len(needed)*2})
    write_json(DATA/'protocol_freeze.json', {'at': datetime.now(timezone.utc).isoformat(),
        'before_outcomes': True, 'hashes': {str(p): digest(p) for p in
            [OUT/'PROTOCOL.md', OUT/'provenance.py', OUT/'pipeline.py', Path(sampler.__file__),
             Path(calendar.__file__), sampler.DEFAULT_VT]}})
    emit('audit', sessions=len(ledger), eligible=ledger[ledger.eligible].cohort.value_counts().to_dict(),
         needed=needed, exclusions=ledger[~ledger.eligible].exclusion_reasons.value_counts().to_dict())


def coverage() -> None:
    """Fetch only essential missing price coverage with the existing SDK collector."""
    verify('protocol_freeze.json')
    plan = json.loads((DATA/'coverage_plan.json').read_text())
    if (DATA/'coverage_complete.json').exists():
        raise FileExistsError('Coverage already audited')
    records = []
    if plan['dates']:
        collect = load('collect', OUT.parent/'b06_iv_expansion_150d_2026-09-19/collect.py')
        collect.DATA = DATA
        renewable = load('third_transport', OUT.parent/'b06_iv_expansion_150d_2026-09-19/resume_collect.py')
        cache = renewable.RenewableSDKCache(collect.authenticate())
        for day in plan['dates']:
            try:
                raw, source = cache.get('index_history_ohlc', collect.normalizer.request_params(date.fromisoformat(day)))
                frame, info = collect.normalizer.normalize_native(raw, date.fromisoformat(day))
                target = DATA/'spx_normalized'/f'{day}.parquet'
                target.parent.mkdir(exist_ok=True)
                if target.exists():
                    raise FileExistsError(target)
                frame.to_parquet(target, index=False)
                records.append({'date': day, 'source': str(source), 'source_sha256': digest(source),
                                'normalized': str(target), 'sha256': digest(target), 'status': 'ok', **info})
            except (RuntimeError, ValueError) as error:
                records.append({'date': day, 'status': 'error', 'error': str(error)})
            emit('coverage', **records[-1])
    ledger, evidence = audit_population()
    ledger.to_csv(DATA/'population.csv', index=False)
    write_json(DATA/'vt_note_provenance.json', evidence)
    write_json(DATA/'coverage_complete.json', {'records': records, 'universe_dates': len(ledger)})
    selected = ledger[ledger.eligible].sort_values('date').reset_index(drop=True)
    original = pd.read_csv(OLD_DATA/'selected_days.csv')
    if not set(original.date).issubset(set(selected.date)):
        raise ValueError('Earlier150 lost under expanded provenance audit')
    selected.to_csv(DATA/'selected_days.csv', index=False)
    emit('population_frozen', qualifying=len(selected), cohorts=selected.cohort.value_counts().to_dict(),
         third_by_year=selected[selected.cohort.eq('third_tranche')].date.str[:4].value_counts().to_dict())


def verify(manifest: str) -> None:
    for path, wanted in json.loads((DATA/manifest).read_text())['hashes'].items():
        if digest(Path(path)) != wanted:
            raise ValueError(f'Frozen input changed: {path}')


def prepare() -> None:
    verify('protocol_freeze.json')
    if (DATA/'input_freeze.json').exists():
        raise FileExistsError('Inputs already frozen')
    selected = pd.read_csv(DATA/'selected_days.csv')
    old = pd.read_csv(OLD_DATA/'history_ledger.csv')
    sources = {r.date: {'date': r.date, 'path': r.path, 'sha256': r.sha256,
                       'included_in_warmup': bool(r.included_5m),
                       'included_in_rsi_warmup': bool(r.included_1m)} for r in old.itertuples()}
    population = pd.read_csv(DATA/'population.csv')
    for r in population[population.source_path.notna() & population.source_path.ne('')].itertuples():
        if r.date not in sources or r.date > '2026-09-08':
            sources[r.date] = {'date': r.date, 'path': r.source_path, 'sha256': r.source_sha256}
    for r in selected.itertuples():
        if r.date in sources and sources[r.date]['path'] != r.source_path:
            raise ValueError('Selected source differs from preserved warmup source')
    five, minute, history = replay.history(list(sources.values()))
    five[five.date.isin(selected.date)].to_parquet(DATA/'five_features.parquet', index=False)
    minute[minute.date.isin(selected.date)].to_parquet(DATA/'minute_features.parquet', index=False)
    pd.DataFrame(history).to_csv(DATA/'history_ledger.csv', index=False)
    # Use old outcome-free diagnostic cuts without refitting the extension.
    with (DATA/'diagnostic_bins.json').open('x') as file:
        file.write((OLD_DATA/'diagnostic_bins.json').read_text())
    paths = [OUT/'PROTOCOL.md', OUT/'provenance.py', Path(__file__), Path(replay.__file__),
             Path(analysis.__file__), PRIOR/'rerun_core.py', sampler.DEFAULT_VT,
             DATA/'population.csv', DATA/'selected_days.csv', DATA/'vt_note_provenance.json',
             DATA/'five_features.parquet', DATA/'minute_features.parquet', DATA/'diagnostic_bins.json']
    paths += list((PRIOR/'frozen_rules').glob('*.py'))
    hashes = {str(p): digest(p) for p in paths}
    hashes.update({r['path']: r['sha256'] for r in history})
    provenance = json.loads((DATA/'vt_note_provenance.json').read_text())
    hashes.update({n['path']: n['sha256'] for s in provenance['sessions'] for n in s['notes']})
    write_json(DATA/'input_freeze.json', {'at': datetime.now(timezone.utc).isoformat(),
                                         'before_outcomes': True, 'hashes': hashes})
    emit('prepared', sources=len(history), qualifying_dates=len(selected))


def generate() -> None:
    verify('input_freeze.json')
    if (DATA/'events_before_outcomes.parquet').exists():
        raise FileExistsError('Events already frozen')
    selected = pd.read_csv(DATA/'selected_days.csv').set_index('date')
    five, minute = [pd.read_parquet(DATA/f'{kind}_features.parquet') for kind in ['five', 'minute']]
    raw_days = {d: g.set_index('min') for d, g in minute.groupby('date')}
    contexts = {d: g.set_index('min5') for d, g in five.groupby('date')}
    events, setups = [], []
    with ProcessPoolExecutor(max_workers=2) as pool:
        for number, (emitted, episodes) in enumerate(pool.map(replay.evaluate,
                replay.jobs(five, minute, selected.index.tolist())), start=1):
            setups.extend(episodes)
            for event in emitted:
                d, m = event['date'], int(event['known_min'])
                raw, vt = raw_days[d], float(selected.loc[d, 'vol_trigger'])
                price = float(raw.loc[m, 'open'])
                context = contexts[d].loc[:m-5].iloc[-1]
                opening = raw.loc[570:min(m-1, 604)]
                event.update(vt_flags(raw, m, vt))
                event.update(vol_trigger=vt, entry_price=price, cohort=selected.loc[d, 'cohort'],
                    vt_room=price-vt, atr_at_entry=float(context.t_atr), target_in_atr=5/float(context.t_atr),
                    opening_range_observed=float(opening.high.max()-opening.low.min()),
                    opening35_complete=m >= 605, entry_hour=m//60,
                    last100_max_calendar_gap_days=float(context.last100_max_calendar_gap_days))
                events.append(event)
            if number % 25 == 0:
                emit('events', dates=number, raw_rows=len(events))
    frame = pd.DataFrame(events)
    if not frame.event_id.is_unique:
        raise ValueError('Duplicate setup identity')
    prior = pd.read_parquet(OLD_DATA/'events_before_outcomes.parquet')
    same = frame[frame.date.isin(prior.date)]
    columns = ['event_id', 'variant', 'date', 'known_min', 'entry_price', 'always_above', 'entry_above']
    pd.testing.assert_frame_equal(same[columns].sort_values('event_id').reset_index(drop=True),
                                 prior[columns].sort_values('event_id').reset_index(drop=True), check_dtype=False)
    # Truncate real source history before noon; no later bars may change an earlier signal.
    third = selected[selected.cohort.eq('third_tranche')].index.tolist()
    checks = list(dict.fromkeys([third[0], third[len(third)//2], third[-1]]))
    for day in checks:
        f, r = five[five.date.eq(day)], minute[minute.date.eq(day)]
        full = replay.evaluate((day, f, r))[0]
        truncated = replay.evaluate((day, f[f.min5.lt(720)], r[r['min'].lt(720)]))[0]
        if replay.event_signature([e for e in full if e['known_min'] <= 720]) != replay.event_signature(truncated):
            raise ValueError('Temporal-prefix invariance failed')
    frame.to_parquet(DATA/'events_before_outcomes.parquet', index=False)
    pd.DataFrame(setups).to_parquet(DATA/'setup_ledger.parquet', index=False)
    write_json(DATA/'event_freeze.json', {'before_outcomes': True,
        'at': datetime.now(timezone.utc).isoformat(), 'prior_raw_reproduced': len(same),
        'prior_distinct_reproduced': len(distinct_entries(same)), 'prefix_dates': checks,
        'hashes': {str(p): digest(p) for p in [DATA/'events_before_outcomes.parquet', DATA/'setup_ledger.parquet']}})
    emit('events_frozen', raw=len(frame), prior_reproduced=len(same))


def outcomes() -> None:
    verify('input_freeze.json')
    verify('event_freeze.json')
    if (DATA/'event_outcomes.parquet').exists():
        raise FileExistsError('Outcomes already scored')
    frame = pd.read_parquet(DATA/'events_before_outcomes.parquet')
    minute = pd.read_parquet(DATA/'minute_features.parquet')
    raw = {d: f.set_index('min') for d, f in minute.groupby('date')}
    scored = {(d, m): score(raw[d], int(m)) for d, m in
              frame[['date', 'known_min']].drop_duplicates().itertuples(index=False, name=None)}
    results = pd.DataFrame([r | scored[(r['date'], r['known_min'])] for r in frame.to_dict('records')])
    old = pd.read_parquet(OLD_DATA/'event_outcomes.parquet').set_index('event_id')
    if not results.set_index('event_id').loc[old.index, 'outcome'].eq(old.outcome).all():
        raise ValueError('Prior outcomes differ')
    results.to_parquet(DATA/'event_outcomes.parquet', index=False)
    distinct_entries(results).to_csv(DATA/'distinct_event_outcomes.csv', index=False)
    emit('scored', raw=len(results), distinct=len(distinct_entries(results)))


def cohort(frame: pd.DataFrame, name: str) -> pd.DataFrame:
    if name == 'all_qualifying':
        return frame
    if name == 'combined_150':
        return frame[frame.cohort.isin(['original_50', 'additional_100'])]
    if name == 'combined_non_development':
        return frame[~frame.cohort.eq('development_10')]
    if name.startswith('third_20'):
        return frame[frame.cohort.eq('third_tranche') & frame.date.str.startswith(name[-4:])]
    if name.startswith('added_20'):
        return frame[frame.cohort.eq('additional_100') & frame.date.str.startswith(name[-4:])]
    return frame[frame.cohort.eq(name)]


def configure_analysis() -> None:
    replay.DATA = analysis.DATA = DATA
    analysis.cohort = cohort
    names = ['original_50', 'additional_100', 'third_tranche', 'third_2025', 'third_2026',
             'combined_150', 'combined_non_development', 'development_10', 'all_qualifying']
    selected = pd.read_csv(DATA/'selected_days.csv')
    analysis.COHORTS = [n for n in names if len(cohort(selected, n))]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['audit', 'coverage', 'prepare', 'freeze', 'generate', 'outcomes', 'analyze'])
    stage = parser.parse_args().stage
    if stage in ['freeze', 'analyze']:
        configure_analysis()
        {'freeze': analysis.freeze, 'analyze': analysis.analyze}[stage]()
    else:
        globals()[stage]()
