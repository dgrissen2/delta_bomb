"""Correct only weighted-median arithmetic; preserve all first-pass artifacts."""
from __future__ import annotations

import argparse
import json
from math import lcm
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline import DATA, OUT, SYMBOLS, date_plan, digest, emit, magnitude, write_frame, write_json

EXACT = DATA/'calibration_exact'


def exact_median(values: np.ndarray, dates: pd.Series) -> float:
    """Lower weighted median with exact, equal total mass per contributing date."""
    values = np.asarray(values,dtype=float)
    if len(values) == 0 or len(values) != len(dates) or not np.isfinite(values).all() or dates.isna().any():
        raise ValueError('Aligned finite nonempty values and date labels required')
    counts = dates.value_counts().to_dict()
    denominator = lcm(*(int(n) for n in counts.values()))
    mass = denominator*len(counts)
    dtype = np.int64 if mass <= np.iinfo(np.int64).max else object
    weights_by_date = {d:denominator//int(n) for d,n in counts.items()}
    weights = np.array([weights_by_date[d] for d in dates],dtype=dtype)
    order = np.argsort(values,kind='stable')
    cumulative = np.cumsum(weights[order],dtype=dtype)
    if cumulative[-1] != mass:
        raise ValueError('Date weights do not sum to their exact total')
    position = int(np.searchsorted(cumulative,(mass+1)//2,side='left'))
    return float(values[order[position]])


def baseline(sample: pd.DataFrame) -> dict:
    rows = sample[sample.available & np.isfinite(sample.acceleration)]
    counts = rows.groupby('date').size()
    result = {'history_days':len(counts),'history_windows':len(rows),
              'source_dates':counts.index.tolist(),'windows_by_date':counts.to_dict(),
              'median':np.nan,'mad':np.nan,'scale':np.nan,'status':'insufficient_history'}
    if len(counts) < 10:
        return result
    values = rows.acceleration.to_numpy()
    center = exact_median(values,rows.date)
    mad = exact_median(abs(values-center),rows.date)
    scale = 1.4826*mad
    result.update(median=center,mad=mad,scale=scale,status='ok' if scale > 1e-12 else 'zero_or_tiny_scale')
    return result


def run_symbol(symbol: str) -> dict:
    source = DATA/'derived'/symbol
    target = EXACT/symbol
    old_summary = json.loads((DATA/f'{symbol}_summary.json').read_text())
    for path,sha in old_summary['output_hashes'].items():
        if digest(Path(path)) != sha:
            raise ValueError(f'First-pass output changed: {path}')
    history = pd.read_parquet(source/'all_windows.parquet')
    old_baselines = pd.read_parquet(source/'block_baselines.parquet')
    old_scores = pd.read_parquet(source/'scored_windows.parquet')
    sessions,targets = date_plan()
    rows,scored = [],[]
    for i,day in enumerate(targets,1):
        prior = magnitude.prior_sessions(sessions,day)
        previous = history[history.date.isin(prior)]
        current = history[history.date.eq(day)]
        for block in range(5):
            stats = baseline(previous[previous.block.eq(block)])
            rows.append({'symbol':symbol,'date':day,'block':block,'block_label':magnitude.block_name(block),
                         'lookback_start':prior[0],'lookback_end':prior[-1],
                         **{k:v for k,v in stats.items() if k not in ['source_dates','windows_by_date']},
                         'source_dates':json.dumps(stats['source_dates']),
                         'windows_by_date':json.dumps(stats['windows_by_date'])})
            frame = current[current.block.eq(block)].copy()
            frame['history_days'] = stats['history_days']
            frame['historical_median'] = stats['median']
            frame['mad'] = stats['mad']
            frame['scale'] = stats['scale']
            valid = frame.available & (stats['status']=='ok')
            frame['signed_score'] = np.where(valid,-frame.acceleration/stats['scale'],np.nan)
            frame['downward_magnitude'] = frame.signed_score.where(valid & frame.b2.lt(-1e-12) & frame.acceleration.lt(-1e-12))
            frame['score_status'] = np.where(~frame.available,'missing_current_window',stats['status'])
            scored.append(frame)
        if i % 100 == 0 or i == len(targets):
            emit('exact_mad',symbol=symbol,completed=i,total=len(targets))
    bases = pd.DataFrame(rows)
    scores = pd.concat(scored,ignore_index=True)
    write_frame(target/'block_baselines.parquet',bases)
    write_frame(target/'scored_windows.parquet',scores)
    comparison = bases.merge(old_baselines,on=['symbol','date','block'],suffixes=('_exact','_old'),validate='one_to_one')
    for field in ['median','mad','scale']:
        comparison[field+'_changed'] = ~(comparison[field+'_exact'].eq(comparison[field+'_old']) |
            (comparison[field+'_exact'].isna() & comparison[field+'_old'].isna()))
    comparison['scale_relative_change'] = comparison.scale_exact/comparison.scale_old-1
    comparison.to_csv(target/'numerical_correction.csv',index=False)
    joined = scores.merge(old_scores,on=['date','end_min','symbol'],suffixes=('_exact','_old'),validate='one_to_one')
    np.testing.assert_allclose(joined.acceleration_exact,joined.acceleration_old,rtol=0,atol=0,equal_nan=True)
    changed_scores = (joined.signed_score_exact.notna() & joined.signed_score_old.notna()
                      & joined.signed_score_exact.ne(joined.signed_score_old))
    summary = {k:v for k,v in old_summary.items() if k != 'output_hashes'}
    summary.update(calibration='exact_integer_date_weights',
        target_scored=int(scores.signed_score.notna().sum()),
        target_downward_scored=int(scores.downward_magnitude.notna().sum()),
        baseline_status=bases.status.value_counts().to_dict(),
        median_blocks_corrected=int(comparison.median_changed.sum()),
        mad_blocks_corrected=int(comparison.mad_changed.sum()),
        scale_blocks_corrected=int(comparison.scale_changed.sum()),
        maximum_absolute_relative_scale_change=float(comparison.scale_relative_change.abs().max()),
        current_scores_changed=int(changed_scores.sum()),
        maximum_absolute_score_change=float((joined.signed_score_exact-joined.signed_score_old).abs().max()),
        output_hashes={str(p):digest(p) for p in [target/'block_baselines.parquet',target/'scored_windows.parquet',
                                                source/'all_windows.parquet',source/'daily_coverage.parquet']},
        input_summary_sha256=digest(DATA/f'{symbol}_summary.json'),
        code_sha256=digest(Path(__file__)))
    write_json(target/'summary.json',summary)
    emit('exact_complete',**{k:v for k,v in summary.items() if k!='output_hashes'})
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--symbol',choices=SYMBOLS)
    args = parser.parse_args()
    write_json(DATA/'exact_calibration_freeze.json',{'policy_change':False,
        'correction':'Exact integer CDF masses implement the approved lower weighted median',
        'original_protocol_sha256':digest(DATA/'protocol_freeze.json'),
        'inputs':{str(p):digest(p) for p in [Path(__file__),OUT/'CALIBRATION_NUMERICS.md',OUT/'test_exact_mad.py']}})
    for symbol in ([args.symbol] if args.symbol else SYMBOLS):
        run_symbol(symbol)


if __name__ == '__main__':
    main()
