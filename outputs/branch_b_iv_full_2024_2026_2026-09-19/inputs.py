"""Immutable native collection for this isolated full-population experiment."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

import pandas as pd

if not __debug__:
    raise RuntimeError('Research integrity checks require Python without -O or PYTHONOPTIMIZE')

OUT = Path(__file__).resolve().parent
ROOT = Path('/Users/dgrissen/Dev/central_trade_data/thetadata')
DATA = ROOT/'branch_b_iv_full_2024_2026_2026-09-19-v1'
PRICE = ROOT/'branch_b_2024_halfyear_2026-09-19-v1'
SCORE = ROOT/'branch_b_stop10_2026-09-19-v1'
SYMBOLS = ['XLC','XLY','XLP','XLE','XLF','XLV','XLI','XLB','XLRE','XLK','XLU']


def load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


base = load('full_iv_base',OUT.parent/'sector_iv_mad_2025_2026_2026-09-19/pipeline.py')
base.DATA, base.SYMBOLS = DATA, SYMBOLS
digest, write_json, write_frame = base.digest, base.write_json, base.write_frame
calendar, surface, rules, balanced = base.calendar, base.surface, base.rules, base.balanced
calendar.EARLY_CLOSE.add('2023-11-24')
METHODS = base.METHODS


def all_dates() -> list[str]:
    warmup = [d for d in pd.bdate_range('2023-10-01','2023-12-31').strftime('%Y-%m-%d')
              if d not in ['2023-11-23','2023-12-25']][-60:]
    return warmup+calendar.sessions('2024-01-01','2026-09-18')


def selected_dates() -> list[str]:
    return sorted(pd.read_csv(PRICE/'selected_days.csv').date)


def freeze() -> None:
    paths = [OUT/'PROTOCOL.md',OUT/'SCOPE_CLARIFICATION.md',Path(__file__),OUT/'core.py',OUT/'test_core.py',
             PRICE/'selected_days.csv',SCORE/'event_outcomes.parquet',
             OUT.parent/'b06_sector_surface_50d_2026-09-13/surface.py',
             OUT.parent/'b06_iv_expansion_150d_2026-09-19/iv_rules.py',
             OUT.parent/'xlre_balanced_baseline_2026-09-19/balanced.py',
             OUT.parent/'sector_iv_mad_2025_2026_2026-09-19/calibrate_exact.py']
    write_json(DATA/'protocol_freeze_v4.json',dict(inputs={str(p):digest(p) for p in paths},
        selected_dates=selected_dates(), history_dates=all_dates(), symbols=SYMBOLS,
        maximum_sdk_attempts=25000, primary_dates=411, development_dates=10))
    assert rules.check_guard_boundaries() == 10


def prior_records() -> dict:
    """Prefer completed dated manifests; defer raw-file hash checks to consumption."""
    result = {}
    for namespace in ['sector_iv_mad_2025_2026_2026-09-19-v1',
                      'sector_iv_mad_remaining_2025_2026_2026-09-19-v1']:
        for path in sorted((ROOT/namespace/'days').glob('*/*.json')):
            row = json.loads(path.read_text())
            key = row['date'],row['symbol']
            if key in result and result[key]['raw_files'] != row['raw_files']:
                raise ValueError(f'Conflicting dated record: {key}')
            row['reused_manifest'] = str(path)
            row['reused_manifest_sha256'] = digest(path)
            result[key] = row
    return result


def normalize_selection(record: dict) -> dict:
    """Interpret both inherited schemas without changing any original dated record."""
    selection = record.get('selection',record.get('listing',{}))
    selected = record['selected'] if 'selected' in record else selection['expirations']
    listed = selection.get('listed_expirations',selection.get('expirations'))
    if selection.get('listing_path'):
        listing_path = Path(selection['listing_path'])
        if digest(listing_path) != selection['listing_sha256']:
            raise ValueError('Changed native expiry listing')
        native = pd.read_parquet(listing_path)
        listed = sorted(set(pd.to_datetime(native.loc[native.symbol.eq(record['symbol']),
                                                       'expiration']).dt.strftime('%Y-%m-%d')))
    if listed is None or selected != calendar.selected_expiries(record['date'],listed):
        raise ValueError('Listed expiries do not reproduce selected bracket')
    return dict(date=record['date'],symbol=record['symbol'],selected_expirations=selected,
                listed_expirations=listed,listing_path=selection.get('listing_path'),
                listing_sha256=selection.get('listing_sha256'))


def collect_one(cache: Any, selection: dict) -> dict:
    day, symbol = selection['date'],selection['symbol']
    path = DATA/'days'/symbol/f'{day}.json'
    if path.exists():
        return json.loads(path.read_text())
    files = []
    for expiry in selection['selected']:
        params = base.input_params(symbol,day,expiry)
        for method in METHODS:
            frame, raw = cache.get(method,params)
            files.append(dict(method=method,expiration=expiry,path=str(raw),
                              sha256=digest(raw),rows=len(frame)))
    record = dict(date=day,symbol=symbol,selected=selection['selected'],raw_files=files,
                  status='captured' if selection['selected'] else 'missing_tenor_bracket',
                  listing=selection)
    write_json(path,record)
    return record


def collect(phase: str) -> None:
    """Four bounded SDK workers; stop queue on provider failure without faking missing data."""
    freeze()
    dates = selected_dates() if phase == 'research' else all_dates()
    old = prior_records()
    pending = []
    for day in dates:
        for symbol in SYMBOLS:
            path = DATA/'days'/symbol/f'{day}.json'
            if path.exists():
                continue
            if (day,symbol) in old:
                write_json(path,old[day,symbol])
            else:
                pending.append((day,symbol))
    print(json.dumps(dict(phase='plan',scope=phase,dates=len(dates),pending=len(pending))),flush=True)
    if not pending:
        return
    listings = base.cached_listings(dates)
    for row in listings.values():
        row['selected'] = row.pop('expirations')
    cache = base.start_cache()
    cache.cache.limit = 25000
    with ThreadPoolExecutor(max_workers=4) as pool:
        for day in dates:
            symbols = [s for d,s in pending if d == day]
            if not symbols:
                continue
            missing = [s for s in symbols if (day,s) not in listings]
            if missing:
                contracts,path = cache.get('option_list_contracts',dict(symbol=missing,
                    date=date.fromisoformat(day),request_type='quote',max_dte=65))
                for symbol in missing:
                    expiries = sorted(set(pd.to_datetime(contracts.loc[contracts.symbol.eq(symbol),
                                                                        'expiration']).dt.strftime('%Y-%m-%d')))
                    listings[day,symbol] = dict(date=day,symbol=symbol,
                        selected=calendar.selected_expiries(day,expiries),listed_expirations=expiries,
                        listing_path=str(path),listing_sha256=digest(path))
            tasks = {pool.submit(collect_one,cache,dict(listings[day,s],date=day,symbol=s)):s for s in symbols}
            for future in as_completed(tasks):
                try:
                    row = future.result()
                    print(json.dumps(dict(phase='collected',date=day,symbol=tasks[future],status=row['status'])),flush=True)
                except Exception:
                    for task in tasks:
                        task.cancel()
                    raise
    write_json(DATA/f'collection_{phase}_complete.json',dict(dates=dates,sector_days=len(dates)*11))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase',choices=['research'])
    collect(parser.parse_args().phase)
