"""Independent reconciliation of clocks, legacy IV measures and reported counts."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

import numpy as np
import pandas as pd

from analyze import MODES, PERIODS, VARIANTS
from features import DESCRIPTORS, POLICIES
from inputs import DATA, ROOT, SCORE, SYMBOLS, base, digest, normalize_selection, selected_dates, write_json
from provenance import checked_execution, check_manifest


def independent_thin(rows: list[dict], mode: str) -> list[dict]:
    result = []
    last = {}
    for row in sorted(rows,key=lambda r:(r['date'],r['known_min'])):
        if mode == 'all' or row['date'] not in last or (mode == 'spaced60' and row['known_min']-last[row['date']]>=60):
            result.append(row)
            last[row['date']] = row['known_min']
    return result


def verify_native() -> dict:
    paths = sorted((DATA/'days').glob('*/*.json'))
    dates = set(selected_dates())
    assert len(paths) == len(dates)*11
    files = {}
    selections = []
    statuses = Counter()
    for path in paths:
        row = json.loads(path.read_text())
        assert row['date'] in dates and row['symbol'] in SYMBOLS
        assert path.stem == row['date'] and path.parent.name == row['symbol']
        statuses[row['status']] += 1
        selection = normalize_selection(row)
        selections.append(selection)
        if selection['listing_path']:
            assert digest(Path(selection['listing_path'])) == selection['listing_sha256']
        for item in row['raw_files']:
            raw = Path(item['path'])
            meta = json.loads(raw.with_suffix('.json').read_text())
            expected = json.loads(json.dumps(base.input_params(row['symbol'],row['date'],item['expiration']),default=str))
            assert meta['params'] == expected and meta['method'] == item['method']
            assert digest(raw) == meta['sha256'] == item['sha256']
            files[str(raw)] = meta['sha256']
    write_json(DATA/'native_input_hashes.json',files)
    write_json(DATA/'normalized_expiry_selections.json',selections)
    return dict(sector_days=len(paths),statuses=dict(statuses),native_files=len(files))


def verify_legacy(features: pd.DataFrame) -> dict:
    path = ROOT/'b06_iv_expansion_150d_2026-09-19-v1/research/sector_event_features.parquet'
    old = pd.read_parquet(path).rename(columns={'parent_min':'known_min'})
    comparisons = []
    max_error = 0.
    for policy in POLICIES[:-1]:
        before = old[old.variant.eq(policy)].drop_duplicates(['date','known_min','symbol'])
        common = before.merge(features,on=['date','known_min','symbol'],validate='one_to_one')
        if len(before) != 11440 or len(common) != len(before):
            raise ValueError(f'Incomplete legacy comparison for {policy}: {len(common)}/{len(before)}')
        assert common.available.eq(common[policy+'_available']).all()
        for a,b in [('first_slope','b1'),('second_slope','b2'),('acceleration','acceleration')]:
            lhs,rhs = common[a].to_numpy(),common[policy+'_'+b].to_numpy()
            np.testing.assert_allclose(lhs,rhs,atol=1e-10,rtol=1e-10,equal_nan=True)
            finite = np.isfinite(lhs)&np.isfinite(rhs)
            if finite.any():
                max_error = max(max_error,float(np.max(abs(lhs[finite]-rhs[finite]))))
        comparisons.append(dict(policy=policy,sector_events=len(common)))
    return dict(comparisons=comparisons,maximum_error=max_error,legacy_input_sha256=digest(path))


def independent_balanced(source: pd.DataFrame, times: list[int]) -> dict:
    """Re-select actual observations without calling the production recovery routine."""
    chosen = {}
    for target in times:
        if target not in source.index:
            return dict(available=False,b1=np.nan,b2=np.nan,acceleration=np.nan)
        strict = source.at[target,'original']
        if np.isfinite(strict) and strict>0:
            chosen[target] = strict
            continue
        near = [t for t in times if abs(t-target)<=2 and (t-570)//60==(target-570)//60
                and t in source.index and np.isfinite(source.at[t,'original']) and source.at[t,'original']>0]
        if near:
            actual = min(near,key=lambda t:(abs(t-target),t))
            chosen[actual] = source.at[actual,'original']
        elif source.at[target,'guard100'] and np.isfinite(source.at[target,'midpoint']) and source.at[target,'midpoint']>0:
            chosen[target] = source.at[target,'midpoint']
        else:
            return dict(available=False,b1=np.nan,b2=np.nan,acceleration=np.nan)
    halves = [[t for t in sorted(chosen) if (t<times[0]+15)==first] for first in [True,False]]
    if any(len(h)<2 for h in halves):
        return dict(available=False,b1=np.nan,b2=np.nan,acceleration=np.nan)
    slopes = [float(np.polyfit(np.array(h)-h[0],[chosen[t] for t in h],1)[0]) for h in halves]
    return dict(available=True,b1=slopes[0],b2=slopes[1],acceleration=(slopes[1]-slopes[0])/15)


def verify_feature_row(row: dict, source: pd.DataFrame) -> dict:
    entry = row['known_min']
    times = list(range(entry-35,entry-5))
    ref = source.reindex(times)
    errors,checked = [],Counter()

    def same(name: str, expected: float) -> None:
        actual = row[name]
        np.testing.assert_allclose(actual,expected,atol=1e-10,rtol=1e-10,equal_nan=True,err_msg=name)
        if np.isfinite(expected):
            errors.append(float(abs(actual-expected)))
        checked[name] += 1

    for policy in POLICIES[:-1]+DESCRIPTORS:
        values = ref[policy].to_numpy(dtype=float)
        available = bool(np.isfinite(values).all())
        assert available == row[policy+'_available']
        expected = {k:np.nan for k in ['b1','b2','acceleration','full_slope','endpoint_change']}
        if available:
            first = np.polyfit(np.arange(15),values[:15],1)[0]
            second = np.polyfit(np.arange(15),values[15:],1)[0]
            expected.update(b1=first,b2=second,acceleration=(second-first)/15,
                            full_slope=np.polyfit(np.arange(30),values,1)[0],
                            endpoint_change=values[-1]-values[0])
        for name,value in expected.items():
            same(policy+'_'+name,value)
    actual = independent_balanced(source,times)
    assert actual['available'] == row['balanced_available']
    for name in ['b1','b2','acceleration']:
        same('balanced_'+name,actual[name])
    spot = ref.spot.to_numpy(dtype=float)
    available = bool(np.isfinite(spot).all() and (spot>0).all())
    assert available == row['price_available']
    for name,i,j in [('price_return_bps',0,29),('price_first_bps',0,14),('price_second_bps',15,29)]:
        same(name,10000*(spot[j]/spot[i]-1) if available else np.nan)
    for desc in DESCRIPTORS:
        for name in ['b2','acceleration']:
            # Derive coefficients by fitting each unit impulse, independently of production constants.
            coeff = []
            for i in range(30):
                y = np.zeros(30)
                y[i] = 1
                first,second = np.polyfit(range(15),y[:15],1)[0],np.polyfit(range(15),y[15:],1)[0]
                coeff.append(second if name=='b2' else (second-first)/15)
            lows,highs = ref[desc+'_low'].to_numpy(),ref[desc+'_high'].to_numpy()
            finite = np.isfinite(lows).all() and np.isfinite(highs).all()
            lower = sum(min(c*lo,c*hi) for c,lo,hi in zip(coeff,lows,highs)) if finite else np.nan
            upper = sum(max(c*lo,c*hi) for c,lo,hi in zip(coeff,lows,highs)) if finite else np.nan
            same(desc+'_'+name+'_low',lower)
            same(desc+'_'+name+'_high',upper)
        breakout = source[desc].reindex(range(entry-5,entry)).to_numpy()
        same(desc+'_breakout_slope',np.polyfit(range(5),breakout,1)[0] if np.isfinite(breakout).all() else np.nan)
    post = source.reindex(range(entry,entry+15))
    p,v = post.spot.to_numpy(),post.original.to_numpy()
    same('post_price_return_bps',10000*(p[-1]/p[0]-1) if np.isfinite(p).all() and (p>0).all() else np.nan)
    same('post_iv_change',v[-1]-v[0] if np.isfinite(v).all() else np.nan)
    return dict(checks=sum(checked.values()),max_error=max(errors,default=0.))


def verify_windows(features: pd.DataFrame) -> dict:
    if len(features) == 0:
        raise ValueError('No feature windows to verify')
    checks = features.sample(n=min(1000,len(features)),random_state=20260919)
    source_cache = {}
    max_error = 0.
    total = 0
    for row in checks.to_dict('records'):
        key = row['date'],row['symbol']
        if key not in source_cache:
            source_cache[key] = pd.read_parquet(DATA/'derived'/key[1]/'minutes'/f'{key[0]}.parquet').set_index('minute')
        source = source_cache[key]
        result = verify_feature_row(row,source)
        total += result['checks']
        max_error = max(max_error,result['max_error'])
    return dict(sampled_sector_events=len(checks),policies=5,descriptors=4,
                scalar_checks=total,independent_max_error=max_error)


def verify_counts(events: pd.DataFrame) -> dict:
    summary = pd.read_csv(DATA/'comparison.csv').set_index(['period','variant','mode','rule','state'])
    registry = pd.read_parquet(DATA/'rule_registry.parquet')
    rules = registry.loc[registry.category.ne('delayed_only'),'rule'].tolist()
    checks = 0
    for period in ['pooled']+PERIODS+['development_10']:
        pool = events[events.cohort.eq('development_10')] if period == 'development_10' else events[events.cohort.ne('development_10')]
        if period in PERIODS:
            pool = pool[pool.half.eq(period)]
        for variant in VARIANTS:
            raw = pool[pool.variant.eq(variant)].to_dict('records')
            groups = [('baseline','all',raw)]
            groups += [(r,s,[x for x in raw if x[r] == s]) for r in rules for s in ['yes','no','unknown']]
            for rule,state,rows in groups:
                for mode in MODES:
                    selected = independent_thin(rows,mode)
                    outcomes = Counter(x['outcome'] for x in selected)
                    actual = summary.loc[period,variant,mode,rule,state]
                    assert len(selected) == actual.n
                    assert outcomes['target_first'] == actual.targets
                    for name in ['neither','adverse_first','ambiguous']:
                        assert outcomes[name] == actual[name]
                    checks += 1
    assert checks == len(summary)
    # Plain unfiltered family outcomes must equal the already verified −10 run.
    previous = pd.read_csv(SCORE/'comparison.csv')
    previous_checks = 0
    for row in previous.itertuples():
        period = 'pooled' if row.cohort == 'combined_non_development' else row.cohort
        if period not in ['pooled']+PERIODS+['development_10']:
            continue
        mode = 'first' if row.sensitivity == 'first_per_day' else row.sensitivity
        actual = summary.loc[period,row.variant,mode,'baseline','all']
        assert actual.n == row.n and actual.targets == row.target_first
        for name in ['neither','adverse_first','ambiguous']:
            assert actual[name] == getattr(row,name)
        previous_checks += 1
    assert previous_checks == 312
    return dict(summary_rows_reconciled=checks,previous_summary_rows_reproduced=previous_checks,
                original_score_sha256=digest(SCORE/'event_outcomes.parquet'))


def verify_unions(events: pd.DataFrame) -> dict:
    summary = pd.read_csv(DATA/'unions.csv')
    primary = events[events.cohort.ne('development_10')]
    thrust = primary[primary.variant.eq('thrust')]
    groups = {'b06':['b06_breakout'],'b09':['b09'],'b10':['b10_breakout'],
              'all_three':['b06_breakout','b09','b10_breakout']}
    checks = 0
    for name,table in summary.groupby('union'):
        family,rule = name.removeprefix('thrust_plus_').split('__')
        added = primary[primary.variant.isin(groups[family])&primary[rule].eq('yes')]
        unique = {}
        for row in pd.concat([thrust,added]).to_dict('records'):
            key = row['date'],row['known_min']
            if key in unique:
                assert unique[key]['outcome'] == row['outcome']
            unique[key] = row
        assert set(zip(thrust.date,thrust.known_min)) <= set(unique)
        for row in table.itertuples():
            values = list(unique.values())
            if row.period != 'pooled':
                values = [v for v in values if v['half'] == row.period]
            values = independent_thin(values,row.mode)
            assert len(values) == row.n
            assert sum(v['outcome']=='target_first' for v in values) == row.targets
            checks += 1
    return dict(union_rows_reconciled=checks)


def main() -> None:
    checked_execution()
    check_manifest(DATA/'analysis_complete.json')
    check_manifest(DATA/'checkpoint_complete.json')
    features = pd.read_parquet(DATA/'sector_features.parquet')
    events = pd.read_parquet(DATA/'joined_events.parquet')
    report = dict(native=verify_native(),legacy=verify_legacy(features),windows=verify_windows(features),
                  counts=verify_counts(events),unions=verify_unions(events))
    assert len(events[events.cohort.ne('development_10')]) == 16016
    report['inputs'] = {str(DATA/p):digest(DATA/p) for p in
        ['execution_freeze.json','analysis_complete.json','checkpoint_complete.json']}
    report['output_hashes'] = json.loads((DATA/'analysis_complete.json').read_text())['output_hashes'] | json.loads((DATA/'checkpoint_complete.json').read_text())['output_hashes']
    write_json(DATA/'independent_verification.json',report)
    print(json.dumps(report,indent=2),flush=True)


if __name__ == '__main__':
    main()
