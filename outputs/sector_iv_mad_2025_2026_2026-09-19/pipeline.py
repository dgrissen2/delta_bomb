"""Native three-ETF collection and strictly prior, per-ETF/hour MAD baselines."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = Path('/Users/dgrissen/Dev/central_trade_data/thetadata')
DATA = ROOT / 'sector_iv_mad_2025_2026_2026-09-19-v1'
SYMBOLS = ['XLRE', 'XLF', 'XLU']
BALANCED = OUT.parent / 'xlre_balanced_baseline_2026-09-19'
PILOT = OUT.parent / 'xlre_iv_magnitude_5d_2026-09-19'
EXPANSION = OUT.parent / 'b06_iv_expansion_150d_2026-09-19'
METHODS = ('option_history_greeks_implied_volatility', 'option_history_greeks_first_order')


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


balanced = load_module('approved_balanced', BALANCED / 'balanced.py')
calendar = load_module('approved_calendar', BALANCED / 'inventory.py')
magnitude = load_module('approved_magnitude', PILOT / 'magnitude.py')
surface = load_module('approved_surface', OUT.parent / 'b06_sector_surface_50d_2026-09-13/surface.py')
rules = load_module('approved_rules', EXPANSION / 'iv_rules.py')
digest = balanced.digest


def date_plan() -> tuple[list[str], list[str]]:
    warmup = calendar.sessions('2024-01-01', '2024-12-31')[-60:]
    targets = calendar.sessions('2025-01-01', '2026-09-18')
    return warmup + targets, targets


def minute_grid(day: str) -> pd.DatetimeIndex:
    return pd.date_range(f'{day} 09:30', periods=210 if day in calendar.EARLY_CLOSE else 300,
                         freq='min', tz='America/New_York')


def input_params(symbol: str, day: str, expiration: str) -> dict[str, Any]:
    return {**calendar.EXPECTED, 'symbol': symbol, 'date': date.fromisoformat(day),
            'expiration': date.fromisoformat(expiration)}


def historical_baseline(history: pd.DataFrame, sessions: list[str], day: str, block: int) -> dict:
    return magnitude.robust_baseline(history, magnitude.prior_sessions(sessions, day), block)


def summarize_window(sources: list[dict]) -> dict:
    chosen = sorted({s['source_minute'] for s in sources if s['source_minute'] is not None})
    recovered = sorted({s['source_minute'] for s in sources if s['method'] == 'recovered_exact'})
    shifts = [abs(s['source_minute']-s['target_minute']) for s in sources if s['source_minute'] is not None]
    return {'source_minutes': json.dumps(chosen), 'recovered_source_minutes': json.dumps(recovered),
            'maximum_shift_minutes': max(shifts, default=0)}


def emit(phase: str, **values: Any) -> None:
    print(json.dumps({'phase': phase, **values}, default=str), flush=True)


def write_json(path: Path, value: Any, *, immutable: bool = True) -> None:
    safe = json.loads(json.dumps(value, default=str, allow_nan=False))
    if path.exists() and immutable:
        if json.loads(path.read_text()) != safe:
            raise ValueError(f'Frozen file differs: {path}')
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(path.suffix + '.tmp')
    pending.write_text(json.dumps(safe, indent=2, sort_keys=True)+'\n')
    pending.replace(path)


def write_frame(path: Path, frame: pd.DataFrame) -> None:
    if path.exists():
        pd.testing.assert_frame_equal(pd.read_parquet(path), frame)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.parquet.tmp')
    frame.to_parquet(temporary, index=False)
    temporary.replace(path)


def checked_read(path: str | Path, expected: str) -> pd.DataFrame:
    path = Path(path)
    if digest(path) != expected:
        raise ValueError(f'Source hash differs: {path}')
    return pd.read_parquet(path)


def start_cache() -> Any:
    collect = load_module('collect', EXPANSION / 'collect.py')
    collect.DATA = DATA
    resume = load_module('renewable_mad', EXPANSION / 'resume_collect.py')
    return resume.RenewableSDKCache(collect.authenticate())


def freeze() -> None:
    sessions, targets = date_plan()
    inputs = [Path(__file__), OUT / 'PROTOCOL.md', BALANCED / 'balanced.py',
              BALANCED / 'inventory.py', PILOT / 'magnitude.py', EXPANSION / 'collect.py',
              EXPANSION / 'resume_collect.py', EXPANSION / 'iv_rules.py',
              OUT.parent / 'b06_sector_surface_50d_2026-09-13/surface.py',
              OUT.parent / 'b06_sector_surface_50d_2026-09-13/download.py']
    write_json(DATA / 'protocol_freeze.json', {'symbols': SYMBOLS, 'sessions': sessions,
        'target_sessions': targets, 'inputs': {str(p): digest(p) for p in inputs},
        'guard_source_sha256': rules.SOURCE_SHA256})
    assert rules.check_guard_boundaries() == 10


def cached_listings(sessions: list[str]) -> dict[tuple[str, str], dict]:
    """Reuse only dated quote listings explicitly requested for each symbol."""
    results = {}
    for meta_path in sorted(ROOT.glob('*/option_list_contracts/*.json')):
        meta = json.loads(meta_path.read_text())
        params = meta.get('params', {})
        day = params.get('date')
        symbols = params.get('symbol', [])
        symbols = [symbols] if isinstance(symbols, str) else symbols
        relevant = set(SYMBOLS).intersection(symbols)
        if day not in sessions or not relevant or params.get('request_type') != 'quote' or params.get('max_dte', 0) < 65:
            continue
        path = meta_path.with_suffix('.parquet')
        frame = checked_read(path, meta['sha256'])
        for symbol in relevant:
            expirations = sorted(set(pd.to_datetime(frame.loc[frame.symbol.eq(symbol), 'expiration'])
                                     .dt.strftime('%Y-%m-%d')))
            selected = calendar.selected_expiries(day, expirations)
            key = (day, symbol)
            if key in results and results[key]['expirations'] != selected:
                raise ValueError(f'Dated expiry selections conflict: {key}')
            results[key] = {'date': day, 'symbol': symbol, 'expirations': selected,
                            'listed_expirations': expirations, 'listing_path': str(path),
                            'listing_sha256': meta['sha256']}
    return results


def collect_listings(cache: Any) -> list[dict]:
    plan_path = DATA / 'selections.json'
    if plan_path.exists():
        return json.loads(plan_path.read_text())
    sessions, _ = date_plan()
    known = cached_listings(sessions)
    tasks = [(day, [s for s in SYMBOLS if (day, s) not in known]) for day in sessions]
    tasks = [(day, symbols) for day, symbols in tasks if symbols]
    emit('listing_plan', missing_requests=len(tasks), reused_symbol_dates=len(known))

    def fetch(task: tuple[str, list[str]]) -> list[dict]:
        day, symbols = task
        frame, path = cache.get('option_list_contracts', {'request_type': 'quote',
            'date': date.fromisoformat(day), 'symbol': symbols, 'max_dte': 65})
        if not {'symbol', 'expiration'} <= set(frame.columns):
            raise ValueError(f'Invalid listing schema: {day}')
        rows = []
        for symbol in symbols:
            values = sorted(set(pd.to_datetime(frame.loc[frame.symbol.eq(symbol), 'expiration'])
                                .dt.strftime('%Y-%m-%d')))
            rows.append({'date': day, 'symbol': symbol, 'expirations': calendar.selected_expiries(day, values),
                         'listed_expirations': values, 'listing_path': str(path), 'listing_sha256': digest(path)})
        return rows

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(fetch, task) for task in tasks]
        for i, future in enumerate(as_completed(futures), 1):
            for row in future.result():
                known[(row['date'], row['symbol'])] = row
            if i % 20 == 0 or i == len(futures):
                emit('listings', completed=i, total=len(futures))
    rows = [known[(day, s)] for day in sessions for s in SYMBOLS]
    write_json(plan_path, rows)
    emit('listings_complete', symbol_dates=len(rows),
         missing_tenor={s: sum(r['symbol'] == s and not r['expirations'] for r in rows) for s in SYMBOLS})
    return rows


def collect_symbol(cache: Any, selections: list[dict], symbol: str) -> list[dict]:
    records = []
    rows = [r for r in selections if r['symbol'] == symbol]

    def fetch(row: dict) -> dict:
        day = row['date']
        record_path = DATA / 'days' / symbol / f'{day}.json'
        if record_path.exists():
            result = json.loads(record_path.read_text())
            if result['selection'] != row:
                raise ValueError('Prior selection changed')
            for item in result['raw_files']:
                if digest(Path(item['path'])) != item['sha256']:
                    raise ValueError('Raw input changed')
            return result
        raw = []
        for expiration in row['expirations']:
            for method in METHODS:
                frame, path = cache.get(method, input_params(symbol, day, expiration))
                raw.append({'method': method, 'expiration': expiration, 'path': str(path),
                            'sha256': digest(path), 'rows': len(frame)})
        result = {'date': day, 'symbol': symbol, 'selection': row, 'raw_files': raw,
                  'status': 'captured' if row['expirations'] else 'missing_tenor_bracket'}
        write_json(record_path, result)
        return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(fetch, row) for row in rows]
        for i, future in enumerate(as_completed(futures), 1):
            records.append(future.result())
            if i % 20 == 0 or i == len(futures):
                emit('capture', symbol=symbol, completed=i, total=len(futures), requests=cache.cache.used)
    records.sort(key=lambda r: r['date'])
    write_json(DATA / f'{symbol}_collection.json', records)
    return records


def derive_day(record: dict) -> dict:
    day, symbol = record['date'], record['symbol']
    base = DATA / 'derived' / symbol
    source_path, window_path = base / 'sources' / f'{day}.parquet', base / 'windows' / f'{day}.parquet'
    meta_path = base / 'metadata' / f'{day}.json'
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        for path, expected in meta['output_hashes'].items():
            if digest(Path(path)) != expected:
                raise ValueError(f'Derived data changed: {path}')
        return meta
    grid = minute_grid(day)
    slots = grid.hour.to_numpy()*60 + grid.minute.to_numpy()
    source = pd.DataFrame({'date':day, 'symbol':symbol, 'minute': slots,
                           'strict_iv':np.nan, 'recovered_iv':np.nan, 'guard100':False,
                           'expiry_eligible':record['status'] == 'captured'})
    source['recovery_max_width'] = np.nan
    source['recovery_prior_ok'] = False
    source['recovery_shock'] = False
    raw_rows = 0
    if record['status'] == 'captured':
        raw = {m: [] for m in METHODS}
        for item in record['raw_files']:
            frame = checked_read(item['path'], item['sha256'])
            raw_rows += len(frame)
            raw[item['method']].append(frame)
        iv, greeks = [pd.concat(raw[m], ignore_index=True) for m in METHODS]
        if not iv.symbol.eq(symbol).all() or not greeks.symbol.eq(symbol).all():
            raise ValueError('Wrong ETF in raw history')
        prepared = surface._prepare(iv, greeks)
        if not prepared.session_date.eq(day).all():
            raise ValueError('Wrong date in raw history')
        # Ignore all rows outside the declared equity-session measurement grid.
        prepared = prepared[prepared.timestamp.isin(grid)].copy()
        qualified = rules.add_quality(prepared)
        assert qualified.loc[qualified.mid_valid, 'bid'].gt(0).all()
        assert qualified.loc[qualified.mid_valid, 'underlying_price'].gt(0).all()
        strict, _ = rules.make_surface(qualified, 'valid', grid)
        recovered, _ = rules.make_surface(qualified, 'mid_valid', grid)
        source['strict_iv'] = strict.iv.to_numpy()
        source['recovered_iv'] = recovered.iv.to_numpy()
        source['guard100'] = recovered.guard100.to_numpy(dtype=bool)
        source['recovery_max_width'] = recovered.max_width.to_numpy()
        source['recovery_prior_ok'] = recovered.prior_ok.to_numpy(dtype=bool)
        source['recovery_shock'] = recovered.shock.to_numpy(dtype=bool)
    rows = []
    ols_max = 0.
    for end in slots[29:]:
        row, chosen = balanced.measure_window(slots, source.strict_iv.to_numpy(), source.recovered_iv.to_numpy(),
                                              source.guard100.to_numpy(), end=int(end), radius=2)
        row.update(date=day, symbol=symbol, **summarize_window(chosen))
        if row['available']:
            unique = {s['source_minute']:s['iv'] for s in chosen}
            t = np.array(sorted(unique))
            y = np.array([unique[v] for v in t])
            for mask, name in [(t < end-14, 'b1'), (t >= end-14, 'b2')]:
                independent = np.polyfit(t[mask]-t[mask][0], y[mask], 1)[0]
                ols_max = max(ols_max, abs(independent-row[name]))
        rows.append(row)
    windows = pd.DataFrame(rows)
    assert ols_max < 1e-12
    write_frame(source_path, source)
    write_frame(window_path, windows)
    meta = {'date':day, 'symbol':symbol, 'status':record['status'], 'raw_rows':raw_rows,
            'minute_slots':len(source), 'strict_minutes':int(source.strict_iv.notna().sum()),
            'recovery_guard_minutes':int(source.guard100.sum()),
            'window_slots':len(windows), 'measured_windows':int(windows.available.sum()),
            'independent_ols_max_error':ols_max,
            'input_hashes':{r['path']:r['sha256'] for r in record['raw_files']},
            'output_hashes':{str(p):digest(p) for p in [source_path, window_path]}}
    write_json(meta_path, meta)
    return meta


def derive_symbol(records: list[dict], symbol: str) -> None:
    """Process cached inputs with two workers; perform calibration after all dates."""
    summaries = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(derive_day, row) for row in records]
        for i, future in enumerate(as_completed(futures), 1):
            summaries.append(future.result())
            if i % 20 == 0 or i == len(futures):
                emit('measure', symbol=symbol, completed=i, total=len(futures))
    base = DATA / 'derived' / symbol
    sessions, targets = date_plan()
    all_windows = pd.concat([pd.read_parquet(base / 'windows' / f'{day}.parquet') for day in sessions], ignore_index=True)
    write_frame(base / 'all_windows.parquet', all_windows)
    baseline_rows, scored = [], []
    for i, day in enumerate(targets, 1):
        prior = magnitude.prior_sessions(sessions, day)
        history = all_windows[all_windows.date.isin(prior)]
        today = all_windows[all_windows.date.eq(day)].copy()
        for block in range(5):
            stats = historical_baseline(history, sessions, day, block)
            baseline_rows.append({'symbol':symbol, 'date':day, 'block':block,
                'block_label':magnitude.block_name(block), 'lookback_start':prior[0], 'lookback_end':prior[-1],
                **{k:v for k,v in stats.items() if k not in ['source_dates','windows_by_date']},
                'source_dates':json.dumps(stats['source_dates']), 'windows_by_date':json.dumps(stats['windows_by_date'])})
            frame = today[today.block.eq(block)].copy()
            frame['history_days'] = stats['history_days']
            frame['historical_median'] = stats['median']
            frame['mad'] = stats['mad']
            frame['scale'] = stats['scale']
            valid = frame.available & (stats['status'] == 'ok')
            frame['signed_score'] = np.where(valid, -frame.acceleration/stats['scale'], np.nan)
            frame['downward_magnitude'] = frame.signed_score.where(valid & frame.b2.lt(-1e-12) & frame.acceleration.lt(-1e-12))
            frame['score_status'] = np.where(~frame.available, 'missing_current_window', stats['status'])
            scored.append(frame)
        if i % 50 == 0 or i == len(targets):
            emit('mad', symbol=symbol, completed=i, total=len(targets))
    baselines = pd.DataFrame(baseline_rows)
    scores = pd.concat(scored, ignore_index=True)
    write_frame(base / 'block_baselines.parquet', baselines)
    write_frame(base / 'scored_windows.parquet', scores)
    daily = pd.DataFrame(summaries).drop(columns=['input_hashes','output_hashes']).sort_values('date').reset_index(drop=True)
    write_frame(base / 'daily_coverage.parquet', daily)
    summary = {'symbol':symbol, 'sessions':len(sessions), 'target_sessions':len(targets),
        'captured_days':int(daily.status.eq('captured').sum()),
        'missing_tenor_days':int(daily.status.eq('missing_tenor_bracket').sum()),
        'target_windows':len(scores), 'target_measured':int(scores.available.sum()),
        'target_scored':int(scores.signed_score.notna().sum()),
        'target_downward_scored':int(scores.downward_magnitude.notna().sum()),
        'baseline_blocks':len(baselines), 'baseline_status':baselines.status.value_counts().to_dict(),
        'independent_ols_max_error':float(daily.independent_ols_max_error.max()),
        'output_hashes':{str(p):digest(p) for p in [base/'all_windows.parquet',base/'block_baselines.parquet',
                                                  base/'scored_windows.parquet',base/'daily_coverage.parquet']}}
    write_json(DATA / f'{symbol}_summary.json', summary)
    emit('symbol_complete', **summary)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=['all','listings','collect','derive'], default='all')
    parser.add_argument('--symbol', choices=SYMBOLS)
    args = parser.parse_args()
    freeze()
    cache = start_cache() if args.phase != 'derive' else None
    if args.phase in ('all', 'listings'):
        selections = collect_listings(cache)
    else:
        selections = json.loads((DATA / 'selections.json').read_text())
    if args.phase == 'listings':
        return
    for symbol in ([args.symbol] if args.symbol else SYMBOLS):
        if args.phase in ('all', 'collect'):
            records = collect_symbol(cache, selections, symbol)
        else:
            records = json.loads((DATA / f'{symbol}_collection.json').read_text())
        if args.phase in ('all', 'derive'):
            derive_symbol(records, symbol)
    emit('complete', phase_requested=args.phase)


if __name__ == '__main__':
    main()
