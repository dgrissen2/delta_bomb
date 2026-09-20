"""SPX index IV MAD history: isolated SPXW/calendar adapter over frozen calculations."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

import pandas as pd

OUT = Path(__file__).resolve().parent
PREVIOUS = OUT.parent / 'sector_iv_mad_remaining_2025_2026_2026-09-19'
ROOT = Path('/Users/dgrissen/Dev/central_trade_data/thetadata')
DATA = ROOT / 'spx_iv_mad_2024_2026_2026-09-20-v1'
SYMBOLS = ['SPXW']


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# Legacy imports use the name "pipeline". Load those against their original
# adapter first, then bind only this process to the isolated SPX namespace.
sys.modules.pop('pipeline', None)
previous = load_module('spx_inherited_adapter', PREVIOUS / 'pipeline.py')
legacy = previous.legacy
balanced, magnitude, rules, exact = previous.balanced, previous.magnitude, previous.rules, previous.exact
BALANCED, PILOT = previous.BALANCED, previous.PILOT
digest, write_json, write_frame = previous.digest, previous.write_json, previous.write_frame
input_params, summarize_window = previous.input_params, previous.summarize_window
emit = previous.emit


def date_plan() -> tuple[list[str], list[str]]:
    """Sixty 2023 warmup sessions, then every completed 2024–2026 session."""
    holidays = {'2023-11-23', '2023-12-25'}
    warmup = [d for d in pd.bdate_range('2023-10-01', '2023-12-31').strftime('%Y-%m-%d')
              if d not in holidays][-60:]
    targets = legacy.calendar.sessions('2024-01-01', '2026-09-18')
    return warmup + targets, targets


def minute_grid(day: str) -> pd.DatetimeIndex:
    early = day in legacy.calendar.EARLY_CLOSE or day == '2023-11-24'
    return pd.date_range(f'{day} 09:30', periods=210 if early else 300,
                         freq='min', tz='America/New_York')


def historical_baseline(history: pd.DataFrame, sessions: list[str], day: str,
                        block: int) -> dict:
    prior = magnitude.prior_sessions(sessions, day)
    return exact.baseline(history[history.date.isin(prior) & history.block.eq(block)])


for module in [previous, legacy]:
    module.DATA, module.SYMBOLS = DATA, SYMBOLS
    module.date_plan, module.minute_grid = date_plan, minute_grid
sys.modules['pipeline'] = sys.modules[__name__]


def request_pool(*, max_workers: int) -> ThreadPoolExecutor:
    if max_workers != 2:
        raise ValueError('Unexpected inherited request concurrency')
    return ThreadPoolExecutor(max_workers=4)


legacy.ThreadPoolExecutor = request_pool


def freeze() -> None:
    """Preserve every scientific dependency and freeze SPX-specific scope."""
    inherited = ROOT / 'sector_iv_mad_2025_2026_2026-09-19-v1'
    paths: set[Path] = set()
    for name in ['protocol_freeze.json', 'exact_calibration_freeze.json']:
        source = inherited / name
        manifest = json.loads(source.read_text())
        for filename, sha in manifest['inputs'].items():
            path = Path(filename)
            if digest(path) != sha:
                raise ValueError(f'Inherited scientific dependency changed: {path}')
            paths.add(path)
        paths.add(source)
    paths.update([Path(__file__), OUT / 'PROTOCOL.md', OUT / 'test_spx_mad.py',
                  OUT / 'verify.py', PREVIOUS / 'pipeline.py', PREVIOUS / 'provider_recovery.py',
                  PREVIOUS / 'service_resume.py'])
    sessions, targets = date_plan()
    write_json(DATA / 'protocol_freeze.json', {
        'underlying': 'SPX', 'option_roots': SYMBOLS, 'sessions': sessions,
        'target_sessions': targets, 'maximum_sdk_attempts': 12000,
        'request_workers': 4, 'cpu_workers': 2,
        'inputs': {str(path): digest(path) for path in sorted(paths)},
        'measurement_change': False, 'calendar_extension': '2023 warmup / 2024 target start',
        'guard_source_sha256': rules.SOURCE_SHA256})
    assert rules.check_guard_boundaries() == 10


def start_cache() -> Any:
    raw = legacy.start_cache()
    raw.cache.limit = 12000
    gateway = load_module('spx_gateway_policy', PREVIOUS / 'service_resume.py')
    guarded = gateway.GatewayPause(raw, raw.cache.record)
    recovery = load_module('spx_provider_recovery', PREVIOUS / 'provider_recovery.py')
    logs = [json.loads(line) for line in raw.cache.log.read_text().splitlines()] if raw.cache.log.exists() else []
    errors = {row['key']: row['code'] for row in logs if row['status'] == 'error'}
    return recovery.ProviderRecovery(guarded, key_fn=sys.modules['collect'].request_key,
                                     previous_errors=errors)


def probe(cache: Any) -> None:
    """Check real native schemas and measured coverage at fixed date boundaries."""
    sessions, targets = date_plan()
    results = []
    for day in [sessions[0], targets[0], targets[-1]]:
        listing, path = cache.get('option_list_contracts', {
            'request_type': 'quote', 'date': date.fromisoformat(day),
            'symbol': SYMBOLS, 'max_dte': 65})
        expirations = sorted(set(pd.to_datetime(listing.loc[listing.symbol.eq('SPXW'), 'expiration'])
                                 .dt.strftime('%Y-%m-%d')))
        selection = {'date': day, 'symbol': 'SPXW',
                     'expirations': legacy.calendar.selected_expiries(day, expirations),
                     'listed_expirations': expirations, 'listing_path': str(path),
                     'listing_sha256': digest(path)}
        raw = []
        for expiration in selection['expirations']:
            for method in legacy.METHODS:
                frame, native = cache.get(method, input_params('SPXW', day, expiration))
                raw.append({'method': method, 'expiration': expiration, 'path': str(native),
                            'sha256': digest(native), 'rows': len(frame)})
        record = {'date': day, 'symbol': 'SPXW', 'selection': selection, 'raw_files': raw,
                  'status': 'captured' if selection['expirations'] else 'missing_tenor_bracket'}
        write_json(DATA / 'days' / 'SPXW' / f'{day}.json', record)
        result = legacy.derive_day(record)
        results.append(result)
        emit('probe', date=day, strict=result['strict_minutes'], windows=result['measured_windows'])
        if result['measured_windows'] == 0:
            raise ValueError(f'No measurable SPX IV on boundary probe {day}; inspect inputs')
    write_json(DATA / 'boundary_probe.json', results)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=['probe', 'all', 'derive'], default='all')
    args = parser.parse_args()
    freeze()
    if args.phase == 'probe':
        probe(start_cache())
        return
    if args.phase == 'all':
        cache = start_cache()
        selections = legacy.collect_listings(cache)
        records = legacy.collect_symbol(cache, selections, 'SPXW')
    else:
        records = json.loads((DATA / 'SPXW_collection.json').read_text())
    if not (DATA / 'calibration_exact' / 'SPXW' / 'summary.json').exists():
        previous.derive_symbol(records, 'SPXW')
    verifier = load_module('spx_independent_verifier', OUT / 'verify.py')
    verifier.verify_symbol('SPXW')
    freeze()
    emit('complete', symbol='SPXW', underlying='SPX')


if __name__ == '__main__':
    main()
