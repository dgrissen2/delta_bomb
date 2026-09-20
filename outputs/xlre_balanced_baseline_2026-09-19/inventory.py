"""Read-only XLRE cache inventory and bounded backfill estimate; no SDK requests."""
from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = Path('/Users/dgrissen/Dev/central_trade_data/thetadata')
CALENDAR_SOURCES = [
    'https://ir.theice.com/press/news-details/2023/NYSE-Group-Announces-2024-2025-and-2026-Holiday-and-Early-Closings-Calendar/default.aspx',
    'https://ir.theice.com/press/news-details/2024/The-New-York-Stock-Exchange-Will-Close-Markets-on-January-9-to-Honor-the-Passing-of-Former-President-Jimmy-Carter-on-National-Day-of-Mourning/default.aspx',
]
HOLIDAYS = set('''2024-01-01 2024-01-15 2024-02-19 2024-03-29 2024-05-27 2024-06-19
2024-07-04 2024-09-02 2024-11-28 2024-12-25
2025-01-01 2025-01-09 2025-01-20 2025-02-17 2025-04-18 2025-05-26 2025-06-19
2025-07-04 2025-09-01 2025-11-27 2025-12-25
2026-01-01 2026-01-19 2026-02-16 2026-04-03 2026-05-25 2026-06-19 2026-07-03
2026-09-07 2026-11-26 2026-12-25'''.split())
EARLY_CLOSE = set('2024-07-03 2024-11-29 2024-12-24 2025-07-03 2025-11-28 2025-12-24 2026-11-27 2026-12-24'.split())
METHODS = ('option_history_greeks_implied_volatility', 'option_history_greeks_first_order')
EXPECTED = dict(symbol='XLRE', interval='1m', strike='*', right='both', start_time='09:30:00',
                end_time='14:29:00', strike_range=30, rate_type='sofr', version='latest')


def sessions(start: str, end: str) -> list[str]:
    if start[:4] < '2024' or end[:4] > '2026':
        raise ValueError('Only verified 2024–2026 calendar supported')
    return [s for s in pd.bdate_range(start, end).strftime('%Y-%m-%d') if s not in HOLIDAYS]


def selected_expiries(day: str, expirations: list[str]) -> list[str]:
    d = date.fromisoformat(day)
    valid = sorted({e for e in expirations if 8 <= (date.fromisoformat(e)-d).days <= 65})
    front = [e for e in valid if (date.fromisoformat(e)-d).days <= 30]
    back = [e for e in valid if (date.fromisoformat(e)-d).days >= 30]
    return sorted({front[-1], back[0]}) if front and back else []


def compatible(params: dict) -> bool:
    return (all(params.get(k) == v for k, v in EXPECTED.items())
            and not (set(params) - set(EXPECTED) - {'date', 'expiration'}))


def checked_path(meta_path: Path, metadata: dict) -> Path:
    path = meta_path.with_suffix('.parquet')
    if hashlib.sha256(path.read_bytes()).hexdigest() != metadata['sha256']:
        raise ValueError(f'Hash mismatch: {path}')
    return path


def main() -> None:
    warmup = sessions('2024-01-01', '2024-12-31')[-60:]
    requested = sessions('2025-01-01', '2026-09-18')
    dates = warmup + requested
    histories, listings, provenance = {}, {}, []
    for method in (*METHODS, 'option_list_contracts'):
        for meta_path in sorted(ROOT.glob(f'*/{method}/*.json')):
            metadata = json.loads(meta_path.read_text())
            params = metadata.get('params', {})
            symbols = params.get('symbol', [])
            if symbols != 'XLRE' and not (isinstance(symbols, list) and 'XLRE' in symbols):
                continue
            day = params.get('date')
            if day not in dates:
                continue
            if method in METHODS:
                if not compatible(params):
                    continue
                path = checked_path(meta_path, metadata)
                key = (day, params['expiration'], method)
                if key in histories and histories[key]['sha256'] != metadata['sha256']:
                    raise ValueError(f'Conflicting raw history: {key}')
                histories[key] = {'path': str(path), 'sha256': metadata['sha256'],
                                  'bytes': path.stat().st_size, 'rows': metadata['rows']}
            else:
                if params.get('max_dte', 0) < 65 or params.get('request_type') != 'quote':
                    continue
                path = checked_path(meta_path, metadata)
                frame = pd.read_parquet(path)
                expirations = sorted(set(pd.to_datetime(frame.loc[frame.symbol.eq('XLRE'), 'expiration'])
                                         .dt.strftime('%Y-%m-%d')))
                selected = selected_expiries(day, expirations)
                if day in listings and listings[day]['selected'] != selected:
                    raise ValueError(f'Conflicting dated selection: {day}')
                listings[day] = {'expirations': expirations, 'selected': selected}
            provenance.append({'date': day, 'method': method, 'path': str(path),
                               'metadata_path': str(meta_path), 'sha256': metadata['sha256']})
    rows = []
    for day in dates:
        listing = listings.get(day)
        selected = listing['selected'] if listing else []
        required = [(day, e, method) for e in selected for method in METHODS]
        have = [histories[k] for k in required if k in histories]
        status = ('listing_missing' if listing is None else 'no_tenor_bracket' if not selected
                  else 'cached_complete' if len(have) == len(required) else 'history_incomplete')
        rows.append({'date': day, 'year': int(day[:4]), 'role': 'warmup' if day in warmup else 'requested',
                     'early_close': day in EARLY_CLOSE, 'measurement_end': '12:59' if day in EARLY_CLOSE else '14:29',
                     'status': status, 'expirations': json.dumps(selected),
                     'required_history_requests': len(required), 'cached_history_requests': len(have),
                     'known_missing_history_requests': len(required)-len(have),
                     'cached_bytes': sum(h['bytes'] for h in have),
                     'cached_rows': sum(h['rows'] for h in have)})
    frame = pd.DataFrame(rows)
    frame.to_csv(OUT / 'coverage_inventory.csv', index=False)
    pd.DataFrame(provenance).to_csv(OUT / 'inventory_source_files.csv', index=False)
    summary = frame.groupby(['year', 'role', 'status']).size().unstack(fill_value=0)
    summary.to_csv(OUT / 'inventory_summary.csv')
    durations = []
    for log in ROOT.glob('*/requests.jsonl'):
        started = {}
        for line in log.read_text().splitlines():
            record = json.loads(line)
            key = (record.get('method'), record.get('key'))
            if record.get('status') == 'started':
                started[key] = record
            elif record.get('status') == 'ok' and key in started:
                beginning = started.pop(key)
                params = beginning.get('params', {})
                if params.get('symbol') != 'XLRE':
                    continue
                if key[0] in METHODS and compatible(params):
                    kind = 'history'
                elif key[0] == 'option_list_contracts':
                    kind = 'listing'
                else:
                    continue
                seconds = (pd.Timestamp(record['at']) - pd.Timestamp(beginning['at'])).total_seconds()
                durations.append({'kind': kind, 'method': key[0], 'seconds': seconds,
                                  'date': params.get('date'), 'namespace': log.parent.name})
    timing = pd.DataFrame(durations)
    timing.to_csv(OUT / 'request_timing_samples.csv', index=False)
    known = int(frame.known_missing_history_requests.sum())
    unknown = int(frame.status.eq('listing_missing').sum())
    complete = frame[frame.status.eq('cached_complete')]
    hist = timing.loc[timing.kind.eq('history'), 'seconds']
    listing_times = timing.loc[timing.kind.eq('listing'), 'seconds']
    estimate = {'as_of': '2026-09-19', 'last_completed_session': '2026-09-18',
        'warmup_start': warmup[0], 'warmup_sessions': len(warmup),
        'sessions_2025': sum(d.startswith('2025') for d in requested),
        'sessions_2026_completed': sum(d.startswith('2026') for d in requested),
        'sessions_2026_future': len(sessions('2026-09-21', '2026-12-31')),
        'total_needed_to_date_including_warmup': len(dates),
        'complete_cached_days': len(complete), 'known_no_tenor_days': int(frame.status.eq('no_tenor_bracket').sum()),
        'missing_listing_days': unknown, 'known_missing_history_requests': known,
        'additional_request_lower_bound': unknown+known,
        'additional_request_upper_bound': 5*unknown+known,
        'complete_day_median_megabytes': float(complete.cached_bytes.median()/1e6),
        'complete_day_mean_megabytes': float(complete.cached_bytes.mean()/1e6),
        'worst_case_new_raw_megabytes_using_mean_day': float(unknown*complete.cached_bytes.mean()/1e6),
        'history_latency_samples': len(hist), 'history_latency_median_seconds': float(hist.median()),
        'history_latency_p90_seconds': float(hist.quantile(.9)),
        'history_latency_max_seconds': float(hist.max()),
        'listing_latency_samples': len(listing_times), 'listing_latency_median_seconds': float(listing_times.median()),
        'listing_latency_p90_seconds': float(listing_times.quantile(.9)),
        'serial_median_seconds_upper_request_count': float((4*unknown+known)*hist.median()+unknown*listing_times.median()),
        'serial_p90_seconds_upper_request_count': float((4*unknown+known)*hist.quantile(.9)+unknown*listing_times.quantile(.9)),
        'calendar_sources': CALENDAR_SOURCES,
        'inventory_code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (OUT / 'inventory_estimate.json').write_text(json.dumps(estimate, indent=2)+'\n')
    print(summary.to_string())
    print(json.dumps(estimate, indent=2))


if __name__ == '__main__':
    main()
