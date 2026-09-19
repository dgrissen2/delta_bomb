"""Reapply frozen Branch B entry recipes to cached native SPX observations."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
OLD = OUT.parent/'branch_b_above_vt_10d_2026-09-12'
CENTRAL = Path('/Users/dgrissen/Dev/central_trade_data/thetadata')
DATA = CENTRAL/'branch_b_150d_rerun_2026-09-19-v1'
EXPANSION = CENTRAL/'b06_iv_expansion_150d_2026-09-19-v1'
sys.path.insert(0,str(OUT/'frozen_rules'))

from signals import add_features, evaluate_day  # noqa: E402
from t_signals import add_t_features, evaluate_t_day  # noqa: E402
from b05_signals import evaluate_b05_day  # noqa: E402
from b06_signals import evaluate_b06_day  # noqa: E402
from b07_signals import evaluate_b07_day  # noqa: E402
from b08_signals import add_b08_features, add_b08_minute_features, evaluate_b08_day  # noqa: E402
from b09_signals import add_b09_features, evaluate_b09_day  # noqa: E402
from b10_signals import evaluate_b10_day  # noqa: E402
from rerun_core import checked_window, distinct_entries, score, vt_flags  # noqa: E402

VARIANTS = ['b01','thrust','staircase','t','b05','b06_breakout','b06_retest','b07',
            'b08_price','b08_rsi','b09','b10_breakout','b10_retest']


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    """Create a new artifact exclusively; completed evidence is never overwritten."""
    with path.open('x') as file:
        json.dump(value,file,indent=2,allow_nan=False,default=str)
        file.write('\n')


def aggregate(raw: pd.DataFrame, day: str) -> tuple[pd.DataFrame, bool]:
    """Aggregate only observed full five-minute bins, allowing partial warmup days."""
    frame = raw.loc[raw['min'].between(570,959)].copy()
    if frame.empty or not frame['min'].is_monotonic_increasing or frame['min'].duplicated().any():
        raise ValueError('Empty, duplicate or unordered RTH minutes')
    values = frame[['min','open','high','low','close']].to_numpy(dtype=float)
    if not np.isfinite(values).all() or (frame['min'] % 1).any():
        raise ValueError('Nonfinite or fractional minute data')
    if not (frame[['open','high','low','close']] > 0).all().all() or not (
        frame.high.ge(frame[['open','close']].max(axis=1))
        & frame.low.le(frame[['open','close']].min(axis=1))).all():
        raise ValueError('Invalid OHLC bounds')
    frame['min5'] = frame['min']//5*5
    bars = frame.groupby('min5',as_index=False).agg(open=('open','first'),high=('high','max'),
        low=('low','min'),close=('close','last'),count=('min','size'))
    bars = bars[bars['count'].eq(5)].drop(columns='count')
    bars.insert(0,'date',day)
    complete = frame['min'].tolist() == list(range(570,960))
    return bars, complete


def history(sources: list[dict[str, Any]]) -> tuple[pd.DataFrame, pd.DataFrame, list[dict]]:
    """Load declared history sources and apply the inherited warmup conventions."""
    five, minute, ledger = [], [], []
    for item in sorted(sources,key=lambda x:x['date']):
        path = Path(item['path'])
        actual_hash = digest(path)
        if item.get('sha256') and actual_hash != item['sha256']:
            raise ValueError(f'Frozen source changed: {path}')
        record = {'date':item['date'],'path':str(path),'sha256':actual_hash,
                  'bars5':0,'rth_rows':0,'included_5m':False,'included_1m':False,'issue':''}
        raw = pd.read_parquet(path)
        record['rth_rows'] = int(raw['min'].between(570,959).sum())
        try:
            bars, complete = aggregate(raw,item['date'])
            record['bars5'] = len(bars)
            if item.get('included_in_warmup',True):
                five.append(bars)
                record['included_5m'] = True
            if complete and item.get('included_in_rsi_warmup',True):
                minute.append(raw.loc[raw['min'].between(570,959)].assign(date=item['date']))
                record['included_1m'] = True
            if not complete:
                record['issue'] = 'partial_session_complete_5m_bins_only'
        except ValueError as exc:
            record['issue'] = str(exc)
        ledger.append(record)
    if not five or not minute:
        raise ValueError('No usable native warmup history')
    f = add_b09_features(add_b08_features(add_t_features(add_features(
        pd.concat(five,ignore_index=True)))))
    f['calendar_gap_days'] = pd.to_datetime(f.date).diff().dt.days.fillna(0).astype(int)
    f['last100_max_calendar_gap_days'] = f.calendar_gap_days.rolling(100,min_periods=1).max()
    m = add_b08_minute_features(pd.concat(minute,ignore_index=True))
    return f, m, ledger


def evaluate(job: tuple[str,pd.DataFrame,pd.DataFrame]) -> tuple[list[dict], list[dict]]:
    """Run all original entry-only functions without scoring future price paths."""
    day, five, raw = job
    five = five.reset_index(drop=True)
    raw = raw.reset_index(drop=True)
    _, events = evaluate_day(five)
    episodes = []
    for function in [evaluate_t_day,evaluate_b06_day,evaluate_b07_day,
                     evaluate_b08_day,evaluate_b10_day]:
        _, emitted, setups = function(raw,five)
        events.extend(emitted)
        episodes.extend(setups.assign(family=function.__name__).to_dict('records'))
    events.extend(evaluate_b05_day(raw,day)[1])
    events.extend(evaluate_b09_day(raw,five)[1])
    for minute in [600,660,720,780,840]:
        if minute in raw['min'].values:
            events.append({'date':day,'variant':'b01','kind':'fixed_time',
                'known_min':minute,'signal_min':minute,
                'close':float(raw.loc[raw['min'].eq(minute),'open'].iloc[0])})
    for event in events:
        setup = event.get('episode_id',f"{day}_{event['variant']}_{event['known_min']}")
        event['setup_id'] = setup
        event['event_id'] = f"{setup}|{event['variant']}|{event['known_min']}"
    return events, episodes


def jobs(five: pd.DataFrame, minute: pd.DataFrame, dates: list[str]) -> list[tuple]:
    return [(d,five[five.date.eq(d)],minute[minute.date.eq(d)]) for d in dates]


def event_signature(events: list[dict]) -> list[tuple]:
    return sorted((e['date'],e['variant'],int(e['known_min']),e.get('episode_id') or '')
                  for e in events if e['variant'] != 'b01')


def reproduce(five: pd.DataFrame, minute: pd.DataFrame, payload: dict) -> dict:
    """Reproduce the original ten-day identities, including duplicate setup clocks."""
    expected = [e|{'date':d['date']} for d in payload['days'] for e in d['events']]
    actual = []
    with ProcessPoolExecutor(max_workers=2) as pool:
        for events, _ in pool.map(evaluate,jobs(five,minute,[d['date'] for d in payload['days']])):
            actual.extend(events)
    wanted, got = event_signature(expected), event_signature(actual)
    return {'expected_events':len(wanted),'actual_events':len(got),
            'identities_equal':wanted==got,
            'only_expected':sorted(set(wanted)-set(got)),
            'only_actual':sorted(set(got)-set(wanted))}


def prepare() -> None:
    """Prepare indicators and freeze sources after original-population reproduction."""
    if DATA.exists():
        raise FileExistsError(f'Refusing to overwrite prepared study: {DATA}')
    days = pd.read_csv(EXPANSION/'research/combined_days.csv',float_precision='round_trip')
    if len(days) != 150 or not days.date.is_unique:
        raise ValueError('Expected exactly the fixed150 distinct dates')
    manifest = json.loads((OLD/'manifest.json').read_text())
    payload = json.loads((OLD/'chart_data.json').read_text())
    for name, expected in manifest['code_sha256'].items():
        snapshot = OUT/'frozen_rules'/name
        if snapshot.exists() and digest(snapshot) != expected:
            raise ValueError(f'Dashboard source snapshot mismatch: {name}')
    old_five, old_minute, old_ledger = history(manifest['sources'])
    reproduction = reproduce(old_five,old_minute,payload)
    if not reproduction['identities_equal']:
        raise ValueError(f'Original dashboard event reproduction failed: {reproduction}')
    print(json.dumps({'phase':'original_reproduced',**reproduction}),flush=True)
    sources = {r['date']:r for r in manifest['sources']}
    for path in sorted((EXPANSION/'spx_normalized').glob('*.parquet')):
        if path.stem <= max(manifest['selected_dates']) and path.stem not in sources:
            sources[path.stem] = {'date':path.stem,'path':str(path)}
    for row in days.itertuples(index=False):
        sources[row.date] = {'date':row.date,'path':row.source_path,'sha256':row.source_sha256}
    expanded_five, expanded_minute, expanded_ledger = history(list(sources.values()))
    warmup_effect = reproduce(expanded_five,expanded_minute,payload)
    for row in days.itertuples(index=False):
        raw = expanded_minute[expanded_minute.date.eq(row.date)].set_index('min')
        checked_window(raw,570,959)
        if raw.open.iloc[0] <= row.vol_trigger:
            raise ValueError(f'Evaluation day did not open above VT: {row.date}')
    # Causal prefix checks at12:00; nothing after the cutoff may change earlier signals.
    prefix_checks = []
    for day in ['2025-02-06','2025-10-10','2026-01-06','2026-07-31']:
        five = expanded_five[expanded_five.date.eq(day)]
        raw = expanded_minute[expanded_minute.date.eq(day)]
        full = evaluate((day,five,raw))[0]
        prefix = evaluate((day,five[five.min5.lt(720)],raw[raw['min'].lt(720)]))[0]
        wanted = event_signature([e for e in full if e['known_min'] <= 720])
        if wanted != event_signature(prefix):
            raise ValueError(f'Prefix invariance failed: {day}')
        prefix_checks.append(day)
    DATA.mkdir(parents=True)
    days.to_csv(DATA/'selected_days.csv',index=False)
    pd.DataFrame(expanded_ledger).to_csv(DATA/'history_ledger.csv',index=False)
    pd.DataFrame(old_ledger).to_csv(DATA/'original_history_ledger.csv',index=False)
    expanded_five[expanded_five.date.isin(days.date)].to_parquet(DATA/'five_features.parquet',index=False)
    expanded_minute[expanded_minute.date.isin(days.date)].to_parquet(DATA/'minute_features.parquet',index=False)
    write_json(DATA/'reproduction.json',{'original_inventory':reproduction,
        'expanded_inventory_on_original10':warmup_effect,'prefix_checks':prefix_checks})
    contexts = []
    for row in days.itertuples(index=False):
        raw = expanded_minute[expanded_minute.date.eq(row.date)].set_index('min')
        f = expanded_five[expanded_five.date.eq(row.date)].set_index('min5')
        atr = float(f.loc[600,'t_atr'])
        below = raw[raw.low.le(row.vol_trigger)]
        opening = float(raw.loc[570,'open'])
        contexts.append({'date':row.date,'cohort':row.cohort,
            'opening35_range':float(raw.loc[570:604].high.max()-raw.loc[570:604].low.min()),
            'atr_known_1005':atr,'opening_cushion':opening-row.vol_trigger,
            'opening_cushion_atr':(opening-row.vol_trigger)/atr,
            'calendar_gap_before_open':int(f.loc[570,'calendar_gap_days']),
            'first_breach_min_descriptive':int(below.index[0]) if len(below) else None,
            'max_breach_depth_descriptive':float(max(0,row.vol_trigger-raw.low.min()))})
    context_frame = pd.DataFrame(contexts)
    context_frame.to_csv(DATA/'day_context.csv',index=False)
    write_json(DATA/'diagnostic_bins.json',{'method':'Pooled150 day-level terciles, no outcomes',
        'cuts':{c:context_frame[c].quantile([1/3,2/3]).tolist() for c in
                ['opening35_range','atr_known_1005','opening_cushion','opening_cushion_atr']}})
    sources_hashes = {r['path']:r['sha256'] for r in expanded_ledger}
    for path in [OUT/'PROTOCOL.md',OUT/'run.py',OUT/'rerun_core.py',
                 OLD/'manifest.json',OLD/'chart_data.json',EXPANSION/'research/combined_days.csv',
                 *sorted((OUT/'frozen_rules').glob('*.py')),
                 *sorted(DATA.glob('*.parquet')),DATA/'selected_days.csv',
                 DATA/'day_context.csv',DATA/'diagnostic_bins.json',OUT/'PERSONA_DECISIONS.md']:
        sources_hashes[str(path)] = digest(path)
    write_json(DATA/'input_freeze.json',{'at':datetime.now(timezone.utc).isoformat(),
        'before_new_family_outcomes':True,'hashes':sources_hashes})
    print(json.dumps({'phase':'prepared','history_sources':len(expanded_ledger),
        'expanded_history_reproduction':warmup_effect}),flush=True)


def verify_inputs() -> None:
    for name, wanted in json.loads((DATA/'input_freeze.json').read_text())['hashes'].items():
        if digest(Path(name)) != wanted:
            raise ValueError(f'Frozen input changed: {name}')


def generate() -> None:
    """Generate all candidates and causal context before reading their outcomes."""
    verify_inputs()
    if (DATA/'events_before_outcomes.parquet').exists():
        raise FileExistsError('Events already generated')
    days = pd.read_csv(DATA/'selected_days.csv')
    five = pd.read_parquet(DATA/'five_features.parquet')
    minute = pd.read_parquet(DATA/'minute_features.parquet')
    raw_days = {d:g.set_index('min') for d,g in minute.groupby('date')}
    context_days = {d:g.set_index('min5') for d,g in five.groupby('date')}
    lookup = days.set_index('date')
    all_events, all_setups = [], []
    with ProcessPoolExecutor(max_workers=2) as pool:
        for index, (events,setups) in enumerate(pool.map(evaluate,jobs(five,minute,days.date.tolist()))):
            all_setups.extend(setups)
            for event in events:
                day, known = event['date'],int(event['known_min'])
                raw = raw_days[day]
                vt = float(lookup.loc[day,'vol_trigger'])
                flags = vt_flags(raw,known,vt)
                event.update(flags)
                event['vol_trigger'] = vt
                event['entry_price'] = float(raw.loc[known,'open'])
                event['cohort'] = lookup.loc[day,'cohort']
                event['vt_room'] = event['entry_price']-vt
                # Context is the most recent completed five-minute bar at decision time.
                context = context_days[day].loc[:known-5].iloc[-1]
                event['atr_at_entry'] = float(context.t_atr)
                event['target_in_atr'] = 5/event['atr_at_entry']
                available_opening = raw.loc[570:min(known-1,604)]
                event['opening_range_observed'] = float(available_opening.high.max()-available_opening.low.min())
                event['opening35_complete'] = known >= 605
                event['entry_hour'] = known//60
                event['last100_max_calendar_gap_days'] = float(context.last100_max_calendar_gap_days)
                all_events.append(event)
            if (index+1)%25 == 0:
                print(json.dumps({'phase':'events','days':index+1,'rows':len(all_events)}),flush=True)
    events = pd.DataFrame(all_events)
    if not events.event_id.is_unique:
        raise ValueError('Duplicate candidate identity')
    original = pd.read_csv(EXPANSION/'research/b06_parents.csv',float_precision='round_trip')
    actual = events[events.variant.eq('b06_breakout')].set_index('episode_id').loc[original.episode_id]
    if len(actual) != 1040 or len(events[events.variant.eq('b06_breakout')]) != 1040:
        raise ValueError('B06 population changed')
    np.testing.assert_equal(actual.known_min.to_numpy(),original.parent_min.to_numpy())
    np.testing.assert_equal(actual.entry_price.to_numpy(),original.parent_price.to_numpy())
    if actual.always_above.sum() != 762:
        raise ValueError('Strict-VT B06 audit subset changed')
    events.to_parquet(DATA/'events_before_outcomes.parquet',index=False)
    pd.DataFrame(all_setups).to_parquet(DATA/'setup_ledger.parquet',index=False)
    write_json(DATA/'event_freeze.json',{'at':datetime.now(timezone.utc).isoformat(),
        'before_outcomes':True,'rows':len(events),'hashes':{
            str(DATA/'events_before_outcomes.parquet'):digest(DATA/'events_before_outcomes.parquet'),
            str(DATA/'setup_ledger.parquet'):digest(DATA/'setup_ledger.parquet')}})


def outcomes() -> None:
    """Score existing event identities without changing the event population."""
    verify_inputs()
    if (DATA/'event_outcomes.parquet').exists():
        raise FileExistsError('Outcomes already exist')
    for path, expected in json.loads((DATA/'event_freeze.json').read_text())['hashes'].items():
        if digest(Path(path)) != expected:
            raise ValueError('Frozen event artifacts changed')
    minute = pd.read_parquet(DATA/'minute_features.parquet')
    raw_days = {d:g.set_index('min') for d,g in minute.groupby('date')}
    events = pd.read_parquet(DATA/'events_before_outcomes.parquet')
    paths = {(d,int(t)):score(raw_days[d],int(t)) for d,t in
             events[['date','known_min']].drop_duplicates().itertuples(index=False,name=None)}
    results = []
    for event in events.to_dict('records'):
        results.append(event|paths[(event['date'],int(event['known_min']))])
    frame = pd.DataFrame(results)
    saved = pd.read_csv(EXPANSION/'research/event_paths.csv').set_index('episode_id')
    b06 = frame[frame.variant.eq('b06_breakout')].set_index('episode_id')
    if not b06.outcome.eq(saved.loc[b06.index,'outcome']).all():
        raise ValueError('Independent B06 outcome replay differs')
    frame.to_parquet(DATA/'event_outcomes.parquet',index=False)
    distinct_entries(frame).to_csv(DATA/'distinct_event_outcomes.csv',index=False)
    print(json.dumps({'phase':'scored','raw_events':len(frame),
                      'distinct_opportunities':len(distinct_entries(frame))}),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage',choices=['prepare','generate','outcomes'])
    args = parser.parse_args()
    {'prepare':prepare,'generate':generate,'outcomes':outcomes}[args.stage]()
