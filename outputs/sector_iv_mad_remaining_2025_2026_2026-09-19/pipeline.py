"""Extend the approved exact MAD calculation without modifying the prior run."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
OLD = OUT.parent/'sector_iv_mad_2025_2026_2026-09-19'
ROOT = Path('/Users/dgrissen/Dev/central_trade_data/thetadata')
DATA = ROOT/'sector_iv_mad_remaining_2025_2026_2026-09-19-v1'
PRIOR_DATA = ROOT/'sector_iv_mad_2025_2026_2026-09-19-v1'
SYMBOLS = ['XLC','XLY','XLP','XLE','XLV','XLI','XLB','XLK']


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


legacy = load_module('sector_mad_previous',OLD/'pipeline.py')
legacy.DATA, legacy.SYMBOLS = DATA, SYMBOLS
# Imported functions retain their original module's globals; only this in-memory
# instance's output namespace and universe change. Frozen source files stay intact.
BALANCED, PILOT, EXPANSION = legacy.BALANCED, legacy.PILOT, legacy.EXPANSION
balanced, magnitude, rules = legacy.balanced, legacy.magnitude, legacy.rules
date_plan, minute_grid = legacy.date_plan, legacy.minute_grid
input_params, summarize_window = legacy.input_params, legacy.summarize_window
digest, checked_read = legacy.digest, legacy.checked_read
write_json, write_frame, emit = legacy.write_json, legacy.write_frame, legacy.emit
sys.modules.setdefault('pipeline',sys.modules[__name__])
exact = load_module('remaining_exact_mad',OLD/'calibrate_exact.py')


def historical_baseline(history: pd.DataFrame, sessions: list[str], day: str,
                        block: int) -> dict:
    prior = magnitude.prior_sessions(sessions,day)
    return exact.baseline(history[history.date.isin(prior) & history.block.eq(block)])


def freeze() -> None:
    """Verify inherited frozen dependencies, then freeze this additive scope."""
    for name in ['protocol_freeze.json','exact_calibration_freeze.json']:
        inherited = json.loads((PRIOR_DATA/name).read_text())
        for path, sha in inherited['inputs'].items():
            if digest(Path(path)) != sha:
                raise ValueError(f'Inherited frozen dependency changed: {path}')
    inputs = [Path(__file__),OUT/'PROTOCOL.md',OUT/'test_remaining.py',
              OLD/'pipeline.py',OLD/'calibrate_exact.py',OLD/'verify_exact.py',
              PRIOR_DATA/'protocol_freeze.json',PRIOR_DATA/'exact_calibration_freeze.json',
              PRIOR_DATA/'manifest.json',PRIOR_DATA/'inventory.json']
    for symbol in ['XLRE','XLF','XLU']:
        inputs += [PRIOR_DATA/'calibration_exact'/symbol/'summary.json',
                   PRIOR_DATA/'calibration_exact'/symbol/'verification_final.json']
    sessions, targets = date_plan()
    write_json(DATA/'protocol_freeze.json',{'symbols':SYMBOLS,'sessions':sessions,
        'target_sessions':targets,'inputs':{str(p):digest(p) for p in inputs},
        'guard_source_sha256':rules.SOURCE_SHA256,'maximum_sdk_attempts':20000,
        'inherited_policy_change':False,'calibration':'exact_integer_date_weights'})
    assert rules.check_guard_boundaries() == 10


def start_cache() -> Any:
    cache = legacy.start_cache()
    cache.cache.limit = 20000
    return cache


def derive_symbol(records: list[dict], symbol: str) -> dict:
    """Reuse the source/window circuit and calculate exact MAD directly."""
    base, calibration = DATA/'derived'/symbol, DATA/'calibration_exact'/symbol
    summaries = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(legacy.derive_day,row) for row in records]
        for i,future in enumerate(as_completed(futures),1):
            summaries.append(future.result())
            if i % 50 == 0 or i == len(futures):
                emit('measure',symbol=symbol,completed=i,total=len(futures))
    sessions,targets = date_plan()
    history = pd.concat([pd.read_parquet(base/'windows'/f'{d}.parquet') for d in sessions],
                        ignore_index=True)
    write_frame(base/'all_windows.parquet',history)
    rows,scored = [],[]
    for i,day in enumerate(targets,1):
        prior = magnitude.prior_sessions(sessions,day)
        previous = history[history.date.isin(prior)]
        current = history[history.date.eq(day)]
        for block in range(5):
            stats = exact.baseline(previous[previous.block.eq(block)])
            rows.append({'symbol':symbol,'date':day,'block':block,
                'block_label':magnitude.block_name(block),'lookback_start':prior[0],
                'lookback_end':prior[-1],
                **{k:v for k,v in stats.items() if k not in ['source_dates','windows_by_date']},
                'source_dates':json.dumps(stats['source_dates']),
                'windows_by_date':json.dumps(stats['windows_by_date'])})
            frame = current[current.block.eq(block)].copy()
            frame['history_days'],frame['historical_median'] = stats['history_days'],stats['median']
            for field in ['mad','scale']:
                frame[field] = stats[field]
            valid = frame.available & (stats['status']=='ok')
            frame['signed_score'] = np.where(valid,-frame.acceleration/stats['scale'],np.nan)
            frame['downward_magnitude'] = frame.signed_score.where(
                valid & frame.b2.lt(-1e-12) & frame.acceleration.lt(-1e-12))
            frame['score_status'] = np.where(~frame.available,'missing_current_window',stats['status'])
            scored.append(frame)
        if i % 100 == 0 or i == len(targets):
            emit('exact_mad',symbol=symbol,completed=i,total=len(targets))
    baselines,scores = pd.DataFrame(rows),pd.concat(scored,ignore_index=True)
    write_frame(calibration/'block_baselines.parquet',baselines)
    write_frame(calibration/'scored_windows.parquet',scores)
    daily = pd.DataFrame(summaries).drop(columns=['input_hashes','output_hashes'])
    daily = daily.sort_values('date').reset_index(drop=True)
    write_frame(base/'daily_coverage.parquet',daily)
    summary = {'symbol':symbol,'sessions':len(sessions),'target_sessions':len(targets),
        'captured_days':int(daily.status.eq('captured').sum()),
        'missing_tenor_days':int(daily.status.eq('missing_tenor_bracket').sum()),
        'target_windows':len(scores),'target_measured':int(scores.available.sum()),
        'target_scored':int(scores.signed_score.notna().sum()),
        'target_downward_scored':int(scores.downward_magnitude.notna().sum()),
        'baseline_blocks':len(baselines),'baseline_status':baselines.status.value_counts().to_dict(),
        'independent_ols_max_error':float(daily.independent_ols_max_error.max()),
        'calibration':'exact_integer_date_weights','source_code_sha256':digest(Path(__file__)),
        'exact_calibration_code_sha256':digest(OLD/'calibrate_exact.py'),
        'output_hashes':{str(p):digest(p) for p in [base/'all_windows.parquet',
            base/'daily_coverage.parquet',calibration/'block_baselines.parquet',
            calibration/'scored_windows.parquet']}}
    write_json(calibration/'summary.json',summary)
    emit('calculated',**{k:v for k,v in summary.items() if k!='output_hashes'})
    return summary


def finish_symbol(records: list[dict], symbol: str) -> None:
    if not (DATA/'calibration_exact'/symbol/'summary.json').exists():
        derive_symbol(records,symbol)
    verifier = load_module('remaining_mad_verifier',OLD/'verify_exact.py')
    verifier.verify_symbol(symbol)
    emit('symbol_verified',symbol=symbol)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase',choices=['all','listings','collect','derive'],default='all')
    parser.add_argument('--symbol',choices=SYMBOLS)
    args = parser.parse_args()
    freeze()
    cache = start_cache() if args.phase != 'derive' else None
    selections = legacy.collect_listings(cache) if args.phase != 'derive' else None
    if args.phase == 'listings':
        return
    completed = []
    with ThreadPoolExecutor(max_workers=1) as calculation:
        for symbol in ([args.symbol] if args.symbol else SYMBOLS):
            for future in completed:
                if future.done():
                    future.result()
            if args.phase in ['all','collect']:
                records = legacy.collect_symbol(cache,selections,symbol)
            else:
                records = json.loads((DATA/f'{symbol}_collection.json').read_text())
            if args.phase in ['all','derive']:
                completed.append(calculation.submit(finish_symbol,records,symbol))
        for future in completed:
            future.result()
    freeze()
    emit('complete',phase_requested=args.phase)


if __name__ == '__main__':
    main()
