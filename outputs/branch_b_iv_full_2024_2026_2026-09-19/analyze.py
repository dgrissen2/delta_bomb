"""Join frozen IV features to unchanged +5/−10 scores and expose all prespecified cells."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from core import thin, unique_entries
from inputs import DATA, PRICE, SCORE, digest, write_frame, write_json
from provenance import checked_execution, check_manifest, write_csv
from match_features import MATCH_RULES, MATCH_SCOPES

VARIANTS = ['b01','thrust','staircase','t','b05','b06_breakout','b06_retest','b07',
            'b08_price','b08_rsi','b09','b10_breakout','b10_retest']
PERIODS = ['2024_H1','2024_H2','2025_H1','2025_H2','2026_H1','2026_H2']
OUTCOMES = ['target_first','adverse_first','neither','ambiguous']
MODES = ['all','first','spaced60']


def describe(frame: pd.DataFrame) -> dict:
    counts = frame.outcome.value_counts()
    n = len(frame)
    return dict(n=n,targets=int(counts.get('target_first',0)),days=int(frame.date.nunique()),
        rate=100*counts.get('target_first',0)/n if n else np.nan,
        **{x:int(counts.get(x,0)) for x in OUTCOMES[1:]})


def rate_interval(frame: pd.DataFrame, values: np.ndarray) -> dict:
    """Do not imply precise uncertainty from an all-win/all-loss or single-date sample."""
    finite = values[np.isfinite(values)]
    if frame.date.nunique()<2 or frame.hit.nunique()<2 or not len(finite):
        return dict(low=np.nan,high=np.nan,ci_status='insufficient_outcome_or_date_variation')
    return dict(low=float(np.quantile(finite,.025)),high=float(np.quantile(finite,.975)),
                ci_status='whole_date_bootstrap')


def difference_interval(left: pd.DataFrame, right: pd.DataFrame, values: np.ndarray) -> dict:
    if any(f.date.nunique()<2 or f.hit.nunique()<2 for f in [left,right]):
        return dict(low=np.nan,high=np.nan)
    finite = values[np.isfinite(values)]
    return dict(low=float(np.quantile(finite,.025)) if len(finite) else np.nan,
                high=float(np.quantile(finite,.975)) if len(finite) else np.nan)


def load_inputs() -> tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame]:
    for name in ['feature_freeze.json','basket_freeze.json']:
        freeze = json.loads((DATA/name).read_text())
        checks = freeze.get('output_hashes',{}) | freeze.get('inputs',{})
        if name == 'feature_freeze.json':
            checks[str(DATA/'sector_features.parquet')] = freeze['sha256']
            checks.update(freeze['source_hashes'])
            checks[str(Path(__file__).with_name('features.py'))] = freeze['code_sha256']
            # Follow each frozen receipt back to both its derived outputs and native inputs.
            for receipt_path in freeze['source_hashes']:
                if digest(Path(receipt_path)) != freeze['source_hashes'][receipt_path]:
                    raise ValueError(f'Changed derived receipt: {receipt_path}')
                receipt = json.loads(Path(receipt_path).read_text())
                checks.update(receipt['output_hashes'])
                checks.update(receipt['native_hashes'])
                record = DATA/'days'/receipt['symbol']/f"{receipt['date']}.json"
                checks[str(record)] = receipt['record_sha256']
        for path,sha in checks.items():
            if digest(Path(path)) != sha:
                raise ValueError(f'Frozen feature changed: {path}')
    expected = json.loads((SCORE/'score_verification.json').read_text())['hashes']
    assert expected[str(SCORE/'event_outcomes.parquet')] == digest(SCORE/'event_outcomes.parquet')
    events = pd.read_parquet(SCORE/'event_outcomes.parquet')
    events = events.sort_values(['date','variant','known_min','event_id']).drop_duplicates(['date','variant','known_min'])
    events = events[events.always_above].copy()
    states = pd.read_parquet(DATA/'basket_features.parquet')
    events = events.merge(states,on=['date','known_min'],how='left',validate='many_to_one',indicator=True)
    assert events._merge.eq('both').all()
    events = events.drop(columns='_merge')
    events['half'] = events.date.str[:4]+'_H'+np.where(events.date.str[5:7].astype(int)<=6,'1','2')
    events['hit'] = events.outcome.eq('target_first').astype(int)
    days = pd.read_csv(PRICE/'selected_days.csv')
    if days.loc[days.cohort.ne('development_10'),'date'].nunique() != 411:
        raise ValueError('Frozen 411-date research population changed')
    registry = pd.read_parquet(DATA/'rule_registry.parquet')
    assert events.loc[events.cohort.ne('development_10')].shape[0] == 16016
    return events,days,registry


def tables(events: pd.DataFrame, registry: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for period in ['pooled']+PERIODS+['development_10']:
        pool = events[events.cohort.eq('development_10')] if period == 'development_10' else events[events.cohort.ne('development_10')]
        if period in PERIODS:
            pool = pool[pool.half.eq(period)]
        for variant in VARIANTS:
            base = pool[pool.variant.eq(variant)]
            for mode in MODES:
                base_thin = thin(base,mode)
                baseline = describe(base_thin)
                baseline_winners = set(zip(base_thin.loc[base_thin.hit.eq(1),'date'],
                                           base_thin.loc[base_thin.hit.eq(1),'known_min']))
                rows.append(dict(period=period,variant=variant,mode=mode,rule='baseline',state='all',**baseline))
                for rule in registry.loc[registry.category.ne('delayed_only'),'rule']:
                    for state in ['yes','no','unknown']:
                        selected = thin(base[base[rule].eq(state)],mode)
                        stats = describe(selected)
                        retained = len(baseline_winners & set(zip(selected.date,selected.known_min)))
                        rows.append(dict(period=period,variant=variant,mode=mode,rule=rule,state=state,
                            **stats,baseline_n=baseline['n'],baseline_targets=baseline['targets'],
                            entry_retention=stats['n']/baseline['n'] if baseline['n'] else np.nan,
                            retained_baseline_targets=retained,
                            target_retention=retained/baseline['targets'] if baseline['targets'] else np.nan))
        print(json.dumps(dict(phase='tables',period=period,rows=len(rows))),flush=True)
    return pd.DataFrame(rows)


def union_frames(events: pd.DataFrame, registry: pd.DataFrame) -> dict[str,pd.DataFrame]:
    thrust = events[events.variant.eq('thrust')]
    collections = {}
    groups = {'b06':['b06_breakout'],'b09':['b09'],'b10':['b10_breakout'],
              'all_three':['b06_breakout','b09','b10_breakout']}
    for rule in registry.loc[registry.union,'rule']:
        for family,variants in groups.items():
            added = events[events.variant.isin(variants)&events[rule].eq('yes')]
            combined = unique_entries(pd.concat([thrust,added],ignore_index=True))
            collections[f'thrust_plus_{family}__{rule}'] = combined
    return collections


def unions(events: pd.DataFrame, registry: pd.DataFrame) -> tuple[pd.DataFrame,dict]:
    primary = events[events.cohort.ne('development_10')]
    frames = union_frames(primary,registry)
    thrust = unique_entries(primary[primary.variant.eq('thrust')])
    keys = set(zip(thrust.date,thrust.known_min))
    rows = []
    for name,frame in frames.items():
        for period in ['pooled']+PERIODS:
            pool = frame if period == 'pooled' else frame[frame.half.eq(period)]
            baseline = thrust if period == 'pooled' else thrust[thrust.half.eq(period)]
            for mode in MODES:
                selected = thin(pool,mode)
                extra = selected.loc[np.asarray([tuple(k) not in keys for k in
                    zip(selected.date,selected.known_min)],dtype=bool)]
                rows.append(dict(union=name,period=period,mode=mode,**describe(selected),
                    **{'extra_'+k:v for k,v in describe(extra).items()},
                    **{'baseline_'+k:v for k,v in describe(thin(baseline,mode)).items()}))
    return pd.DataFrame(rows),frames


def uncertainty(events: pd.DataFrame, dates: list[str], registry: pd.DataFrame,
                collections: dict) -> pd.DataFrame:
    """Resample complete dates, including dates with zero signals; shared draws for deltas."""
    weights = np.random.default_rng(20260919).multinomial(len(dates),np.ones(len(dates))/len(dates),size=5000)
    cache = {}

    def draws(frame: pd.DataFrame) -> np.ndarray:
        daily = frame.groupby('date').agg(n=('hit','size'),hits=('hit','sum')).reindex(dates,fill_value=0)
        n,hits = weights@daily.n.to_numpy(),weights@daily.hits.to_numpy()
        return np.divide(100*hits,n,out=np.full(len(n),np.nan),where=n>0)

    records = []
    rules = registry.loc[registry.category.isin(['primary','weighted','confirmation','price_control']),'rule'].tolist()
    for variant in VARIANTS:
        base = events[events.variant.eq(variant)]
        for mode in MODES:
            base_thin = thin(base,mode)
            base_draws = draws(base_thin)
            for rule in rules:
                yes = thin(base[base[rule].eq('yes')],mode)
                no = thin(base[base[rule].eq('no')],mode)
                measured = thin(base[base[rule].ne('unknown')],mode)
                dy,dn,dm = draws(yes),draws(no),draws(measured)
                records.append(dict(variant=variant,mode=mode,rule=rule,**rate_interval(yes,dy),
                    **{'delta_no_'+k:v for k,v in difference_interval(yes,no,dy-dn).items()},
                    **{'delta_measured_'+k:v for k,v in difference_interval(yes,measured,dy-dm).items()},
                    **{'delta_all_'+k:v for k,v in difference_interval(yes,base_thin,dy-base_draws).items()}))
                cache[variant,mode,rule] = describe(measured)
    for name,frame in collections.items():
        for mode in MODES:
            selected = thin(frame,mode)
            records.append(dict(variant='union',mode=mode,rule=name,**rate_interval(selected,draws(selected))))
    write_csv(DATA/'measured_baselines.csv',pd.DataFrame([dict(variant=v,mode=m,rule=r,**s) for (v,m,r),s in cache.items()]))
    return pd.DataFrame(records)


def matched(events: pd.DataFrame) -> None:
    freeze = check_manifest(DATA/'match_freeze.json')
    pairs = pd.read_parquet(DATA/'matched_pairs.parquet')
    base = events[events.variant.eq('b06_breakout')].copy()
    base['episode_id'] = base.date+'_'+base.known_min.astype(str)
    scores = base.set_index('episode_id').hit
    rows = []
    for rule in MATCH_RULES:
        for scope in MATCH_SCOPES:
            group = pairs[pairs.rule.eq(rule)&pairs.scope.eq(scope)]
            logged = [g for g in freeze['groups'] if g['rule']==rule and g['scope']==scope]
            if not logged or sum(g['pairs'] for g in logged) != len(group):
                raise ValueError(f'Missing or inconsistent frozen matching group: {rule}/{scope}')
            yes,no = scores.reindex(group.yes_id),scores.reindex(group.no_id)
            assert yes.notna().all() and no.notna().all()
            rows.append(dict(rule=rule,scope=scope,pairs=len(group),yes_targets=int(yes.sum()),
                no_targets=int(no.sum()),yes_rate=100*yes.mean(),no_rate=100*no.mean(),
                unmatched=len(base)-2*len(group),status='matched' if len(group) else 'no_comparable_pairs'))
    write_csv(DATA/'matched_summary.csv',pd.DataFrame(rows))


def contextual_tables(events: pd.DataFrame) -> None:
    rows = []
    b06 = events[events.variant.eq('b06_breakout')&events.cohort.ne('development_10')]
    for name,frame in [('all',b06)]+[(h,b06[b06.half.eq(h)]) for h in PERIODS]:
        for rule in ['original_accelerating_6','original_falling_6','paired_price_iv_6']:
            for (price,iv),group in frame.groupby(['price_only_6',rule]):
                rows.append(dict(period=name,test='price_iv_disagreement',rule=rule,price=price,iv=iv,**describe(group)))
        falling = frame[frame.original_falling_6.eq('yes')]
        for (count,state),group in falling.groupby(['falling_count','original_accelerating_6']):
            rows.append(dict(period=name,test='acceleration_within_falling_count',count=count,state=state,**describe(group)))
        for (count,recruitment,iv),group in frame.groupby(['current_rising_count','recruitment','original_accelerating_6']):
            rows.append(dict(period=name,test='recruitment',count=count,recruitment=recruitment,iv=iv,**describe(group)))
    write_csv(DATA/'contextual_comparisons.csv',pd.DataFrame(rows))
    transitions,cohorts = [],[]
    for (cohort,variant),group in events.groupby(['cohort','variant']):
        cohorts.append(dict(cohort=cohort,variant=variant,rule='baseline',state='all',**describe(group)))
        for policy in ['original','midpoint','guarded_100','guarded_50','balanced']:
            for condition in ['falling','accelerating']:
                rule = f'{policy}_{condition}_6'
                for state,selected in group.groupby(rule):
                    cohorts.append(dict(cohort=cohort,variant=variant,rule=rule,state=state,**describe(selected)))
    for (variant,half),group in events[events.cohort.ne('development_10')].groupby(['variant','half']):
        for condition in ['falling','accelerating']:
            original = f'original_{condition}_6'
            for policy in ['midpoint','guarded_100','guarded_50','balanced']:
                revised = f'{policy}_{condition}_6'
                for (old,new),selected in group.groupby([original,revised]):
                    transitions.append(dict(variant=variant,half=half,condition=condition,
                        policy=policy,original_state=old,revised_state=new,**describe(selected)))
    write_csv(DATA/'policy_transitions.csv',pd.DataFrame(transitions))
    write_csv(DATA/'cohort_comparisons.csv',pd.DataFrame(cohorts))


def main() -> None:
    checked_execution()
    events,days,registry = load_inputs()
    table = tables(events,registry)
    write_csv(DATA/'comparison.csv',table)
    union_table,collections = unions(events,registry)
    write_csv(DATA/'unions.csv',union_table)
    primary = events[events.cohort.ne('development_10')]
    write_csv(DATA/'uncertainty.csv',uncertainty(primary,days.loc[days.cohort.ne('development_10'),'date'].tolist(),registry,collections))
    matched(primary)
    contextual_tables(events)
    write_frame(DATA/'joined_events.parquet',events)
    write_json(DATA/'analysis_complete.json',dict(events=len(events),primary_events=len(primary),
        primary_dates=int(days.loc[days.cohort.ne('development_10'),'date'].nunique()),
        registry_rules=len(registry),table_rows=len(table),union_rows=len(union_table),
        score='+5_before_-10_in_60_native_minutes',bootstrap_draws=5000,seed=20260919,
        inputs={str(p):digest(p) for p in [DATA/'basket_features.parquet',SCORE/'event_outcomes.parquet',DATA/'execution_freeze.json']},
        output_hashes={str(DATA/p):digest(DATA/p) for p in ['comparison.csv','unions.csv','uncertainty.csv',
            'measured_baselines.csv','matched_summary.csv','contextual_comparisons.csv','policy_transitions.csv',
            'cohort_comparisons.csv','joined_events.parquet']}))


if __name__ == '__main__':
    main()
