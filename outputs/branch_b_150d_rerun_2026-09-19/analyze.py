"""Predeclared cohort, control and dependence diagnostics for thirteen entry rows."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np
import pandas as pd

from run import DATA, OUT, EXPANSION, VARIANTS, digest, verify_inputs, write_json
from rerun_core import distinct_entries, thin_entries

COHORTS = ['original_50','added_2025','added_2026','additional_100','combined_150']
GATES = ['always_above','entry_above','opening_only']
LABELS = {
    'b01':'B01 · Fixed-time control','thrust':'B02 · Five-minute thrust',
    'staircase':'B03 · Thrust + staircase','t':'B04 · T pullback/break',
    'b05':'B05 · Stall/reclaim','b06_breakout':'B06 · Immediate breakout',
    'b06_retest':'B06 · Breakout/retest','b07':'B07 · Failed breakdown/reclaim',
    'b08_price':'B08 · Band rebound, price','b08_rsi':'B08 · Band rebound + RSI',
    'b09':'B09 · One-minute staircase','b10_breakout':'B10 · Opening-range immediate',
    'b10_retest':'B10 · Opening-range retest'}


def cohort(frame: pd.DataFrame, name: str) -> pd.DataFrame:
    if name == 'combined_150':
        return frame
    if name.startswith('added_'):
        return frame[frame.cohort.eq('additional_100') & frame.date.str.startswith(name[-4:])]
    return frame[frame.cohort.eq(name)]


def rate(values: pd.Series) -> float:
    return float(values.mean()*100) if len(values) else np.nan


def bootstrap(frame: pd.DataFrame, dates: list[str], weights: np.ndarray,
              value: str = 'hit') -> tuple[float,float]:
    """Resample complete dates with zero-event dates included in the draw."""
    daily = frame.groupby('date')[value].agg(['sum','count']).reindex(dates,fill_value=0)
    numerator = weights @ daily['sum'].to_numpy(dtype=float)
    denominator = weights @ daily['count'].to_numpy(dtype=float)
    samples = numerator[denominator>0]/denominator[denominator>0]*100
    if not len(samples):
        return np.nan,np.nan
    return tuple(float(x) for x in np.quantile(samples,[.025,.975]))


def freeze() -> None:
    if (DATA/'event_outcomes.parquet').exists():
        raise ValueError('Analysis definition must be frozen before new outcomes')
    write_json(DATA/'analysis_freeze.json',{'at':datetime.now(timezone.utc).isoformat(),
        'before_outcomes':True,'resamples':10000,'seed':20260919,
        'cohorts':COHORTS,'gates':GATES,'primary_opportunity_unit':'variant/date/known_min',
        'hashes':{str(p):digest(p) for p in [Path(__file__),OUT/'PROTOCOL.md',OUT/'rerun_core.py']}})


def analyze() -> None:
    verify_inputs()
    if (DATA/'comparison.csv').exists():
        raise FileExistsError('Analysis already completed')
    for path,wanted in json.loads((DATA/'analysis_freeze.json').read_text())['hashes'].items():
        if digest(Path(path)) != wanted:
            raise ValueError('Analysis source changed after freeze')
    raw = pd.read_parquet(DATA/'event_outcomes.parquet')
    events = distinct_entries(raw)
    allowed = {'target_first','adverse_first','neither','ambiguous'}
    if not set(events.outcome).issubset(allowed):
        raise ValueError('Unexpected outcome label')
    events['hit'] = events.outcome.eq('target_first').astype(int)
    selected_days = pd.read_csv(DATA/'selected_days.csv')
    rows, daily_rows = [], []
    weights_by_cohort = {}
    for name in COHORTS:
        dates = cohort(selected_days,name).date.tolist()
        weights_by_cohort[name] = np.random.default_rng(20260919).multinomial(
            len(dates),np.full(len(dates),1/len(dates)),size=10000)
    for gate in GATES:
        admitted = events if gate == 'opening_only' else events[events[gate]]
        controls = admitted[admitted.variant.eq('b01')][['date','entry_hour','hit']].rename(
            columns={'hit':'control_hit'})
        for sensitivity in ['all','first_per_day','spaced60']:
            if sensitivity == 'first_per_day':
                candidates = admitted.sort_values('known_min').groupby(
                    ['date','variant'],sort=False).head(1)
            elif sensitivity == 'spaced60':
                candidates = thin_entries(admitted,60)
            else:
                candidates = admitted
            paired = candidates.merge(controls,on=['date','entry_hour'],how='left',validate='many_to_one')
            paired['difference'] = paired.hit-paired.control_hit
            for name in COHORTS:
                dates = cohort(selected_days,name).date.tolist()
                weights = weights_by_cohort[name]
                base = cohort(paired,name)
                for variant in VARIANTS:
                    f = base[base.variant.eq(variant)]
                    matched = f[f.control_hit.notna()]
                    low, high = bootstrap(f,dates,weights)
                    dl, dh = bootstrap(matched,dates,weights,'difference')
                    counts = f.outcome.value_counts()
                    n = len(f)
                    resolved = int(counts.get('target_first',0)+counts.get('adverse_first',0))
                    rows.append({'gate':gate,'sensitivity':sensitivity,'cohort':name,
                        'variant':variant,'label':LABELS[variant],'n':n,'active_dates':f.date.nunique(),
                        'distinct_setups':f.setup_id.nunique(),
                        **{k:int(counts.get(k,0)) for k in allowed},
                        'hit_pct':rate(f.hit),'date_ci_low_pct':low,'date_ci_high_pct':high,
                        'resolved_target_pct':100*counts.get('target_first',0)/resolved if resolved else np.nan,
                        'matched_n':len(matched),'matched_family_pct':rate(matched.hit),
                        'matched_control_pct':rate(matched.control_hit),
                        'control_difference_pp':rate(matched.difference),
                        'control_ci_low_pp':dl,'control_ci_high_pp':dh})
                    if sensitivity == 'all':
                        for date in dates:
                            day = f[f.date.eq(date)]
                            daily_rows.append({'gate':gate,'cohort':name,'variant':variant,'date':date,
                                'n':len(day),'target_first':int(day.hit.sum())})
    summary = pd.DataFrame(rows)
    if not summary['n'].eq(summary[['target_first','adverse_first','neither','ambiguous']].sum(axis=1)).all():
        raise ValueError('Outcome totals do not reconcile')
    strict = summary[summary.gate.eq('always_above')]
    if not strict.matched_n.eq(strict.n).all():
        raise ValueError('Continuous-VT family has missing same-date/hour control')
    summary.to_csv(DATA/'comparison.csv',index=False)
    pd.DataFrame(daily_rows).to_csv(DATA/'daily_counts.csv',index=False)
    diagnostics(events)
    paired_setups(raw)
    write_json(DATA/'analysis_complete.json',{'rows':len(summary),
        'raw_event_rows':len(raw),'distinct_event_rows':len(events),
        'strict_control_matching_complete':True,'outcome_totals_reconcile':True,
        'hashes':{str(p):digest(p) for p in sorted(DATA.glob('*.csv'))}})
    print(summary[summary.gate.eq('always_above') & summary.sensitivity.eq('all') &
                  summary.cohort.eq('additional_100')][['variant','n','active_dates','hit_pct',
                  'matched_control_pct','control_difference_pp','control_ci_low_pp','control_ci_high_pp']].to_string(index=False))


def diagnostics(events: pd.DataFrame) -> None:
    """Write frozen bins, times, warmup gaps, lockouts and existing IV coverage."""
    cuts = json.loads((DATA/'diagnostic_bins.json').read_text())['cuts']
    frame = events[events.always_above].copy()
    mappings = {'opening35_range':'opening_range_observed','atr_known_1005':'atr_at_entry',
                'opening_cushion':'vt_room','opening_cushion_atr':'vt_room_atr'}
    frame['vt_room_atr'] = frame.vt_room/frame.atr_at_entry
    records = []
    for name in COHORTS:
        group = cohort(frame,name)
        for variable, column in mappings.items():
            g = group if variable != 'opening35_range' else group[group.opening35_complete]
            g = g.assign(bucket=np.searchsorted(cuts[variable],g[column].to_numpy(),side='left'))
            for (variant,bucket), f in g.groupby(['variant','bucket']):
                records.append({'cohort':name,'diagnostic':variable,'variant':variant,'bucket':int(bucket),
                    'n':len(f),'target_first':int(f.hit.sum()),'hit_pct':rate(f.hit),
                    'neither_pct':rate(f.outcome.eq('neither'))})
        for (variant,hour),f in group.groupby(['variant','entry_hour']):
            records.append({'cohort':name,'diagnostic':'entry_hour','variant':variant,'bucket':int(hour),
                'n':len(f),'target_first':int(f.hit.sum()),'hit_pct':rate(f.hit),
                'neither_pct':rate(f.outcome.eq('neither'))})
    pd.DataFrame(records).to_csv(DATA/'context_diagnostics.csv',index=False)
    gaps = frame[frame.last100_max_calendar_gap_days.gt(4)]
    gaps[['date','variant','known_min','last100_max_calendar_gap_days']].to_csv(
        DATA/'warmup_gap_events.csv',index=False)
    coverage = pd.read_csv(EXPANSION/'research/event_ledger.csv')
    coverage = coverage[coverage.variant.eq('original')]
    output = []
    for name in ['original_50','added_2025','added_2026']:
        for count,g in cohort(coverage,name).groupby('coverage'):
            output.append({'cohort':name,'observed_sectors':int(count),'n':len(g),
                'yes':int(g.accelerating_state.eq('yes').sum()),
                'no':int(g.accelerating_state.eq('no').sum()),
                'unknown':int(g.accelerating_state.eq('unknown').sum()),
                'qualifying_pct':rate(g.accelerating_state.eq('yes'))})
    pd.DataFrame(output).to_csv(DATA/'existing_iv_coverage_diagnostic.csv',index=False)


def paired_setups(raw: pd.DataFrame) -> None:
    """Show delayed-trigger selection and its missed parent opportunities."""
    rows = []
    for gate in GATES:
        eligible = raw if gate == 'opening_only' else raw[raw[gate]]
        for parent,child in [('b06_breakout','b06_retest'),('b08_price','b08_rsi'),
                             ('b10_breakout','b10_retest')]:
            for name in COHORTS:
                f = cohort(eligible,name)
                a = f[f.variant.eq(parent)]
                b = f[f.variant.eq(child)]
                joined = a.merge(b,on=['date','setup_id'],suffixes=('_parent','_child'),
                                 how='left',validate='one_to_one')
                matched = joined[joined.known_min_child.notna()]
                missing = joined[joined.known_min_child.isna()]
                rows.append({'gate':gate,'cohort':name,'parent':parent,'child':child,
                    'eligible_parents':len(a),'paired_delayed_entries':len(matched),
                    'parents_without_delayed_entry':len(missing),
                    'parent_targets_without_delayed_entry':int(missing.outcome_parent.eq('target_first').sum()),
                    'paired_parent_hit_pct':rate(matched.outcome_parent.eq('target_first')),
                    'paired_child_hit_pct':rate(matched.outcome_child.eq('target_first')),
                    'median_delay_min':float((matched.known_min_child-matched.known_min_parent).median())
                        if len(matched) else np.nan,
                    'parent_target_before_child':int((matched.outcome_parent.eq('target_first') &
                        matched.first_touch_min_parent.lt(matched.known_min_child)).sum())})
    pd.DataFrame(rows).to_csv(DATA/'paired_setup_comparison.csv',index=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage',choices=['freeze','analyze'])
    arguments = parser.parse_args()
    {'freeze':freeze,'analyze':analyze}[arguments.stage]()
