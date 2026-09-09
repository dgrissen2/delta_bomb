"""Collect consistent daily surfaces and adjusted prices for the frozen HIRO stock set."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from pandar_call_exclusions import CallLedger, OratsClient, is_single_stock_ticker
from pandar_quote_history import SOURCE

OUTPUT = Path(__file__).resolve().parents[1] / 'docs/replay/pandar_skew_journey_2026-09-06'
START, END = '2023-01-01', '2026-09-03'
FIELDS = {
    'summaries': ['ticker', 'tradeDate', 'stockPrice', 'confidence', 'mwAdj30',
        'iv10d', 'iv30d', 'iv60d', 'exErnIv10d', 'exErnIv30d', 'exErnIv60d',
        'dlt5Iv10d', 'dlt5Iv30d', 'dlt25Iv30d', 'dlt75Iv30d',
        'exErnDlt25Iv30d', 'exErnDlt75Iv30d', 'rSlp30', 'rDrv30'],
    'dailies': ['ticker', 'tradeDate', 'clsPx', 'open', 'hiPx', 'loPx', 'stockVolume',
                'unadjClsPx'],
}


def universe() -> list[str]:
    """Freeze current membership; do not claim historical point-in-time HIRO membership."""
    source = SOURCE / 'hiro_tickers_2026-09-03.csv'
    frame = pd.read_csv(source).rename(columns={'Ticker': 'ticker'})
    frame['single_stock'] = frame.ticker.map(is_single_stock_ticker)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUTPUT / 'hiro_universe.csv', index=False)
    metadata = dict(path=str(source), sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    membership_asof='2026-09-03', history_start=START, history_end=END,
                    membership_limitation='current frozen universe applied backwards; survivorship/selection bias')
    (OUTPUT / 'universe_source.json').write_text(json.dumps(metadata, indent=2)+'\n')
    return sorted(set(frame.loc[frame.single_stock, 'ticker']) | {'SPY'})


def fetch(limit: int | None = None) -> None:
    """Use a separate 80-attempt research ledger; never alter previous call allowances."""
    names = universe()
    load_dotenv('/Users/dgrissen/Dev/gamma_chaser/.env')
    ledger = CallLedger(OUTPUT / 'api_manifest.json', max_calls=80, initial_used=0)
    client = OratsClient(os.environ.get('ORATS_API_KEY', ''), ledger, 10)
    batches = [names[i:i+10] for i in range(0, len(names), 10)]
    if limit is not None:
        batches = batches[:limit]
    print('Universe including SPY calendar:', len(names), 'names;', len(batches), 'batches', flush=True)
    for batch in batches:
        for endpoint, fields in FIELDS.items():
            path = OUTPUT / 'raw' / endpoint / ('-'.join(batch)+'.json.gz')
            if path.exists():
                continue
            rows = client.get('hist/'+endpoint,
                {'ticker': ','.join(batch), 'fields': ','.join(fields)}, timeout=60, max_attempts=1)
            retained = [r for r in rows if START <= str(r['tradeDate'])[:10] <= END]
            path.parent.mkdir(parents=True, exist_ok=True)
            with gzip.open(path, 'wt') as handle:
                json.dump(retained, handle, separators=(',', ':'))
            print(endpoint, batch[0], batch[-1], len(retained), 'rows; calls', ledger.used, flush=True)
    provenance = []
    for endpoint in FIELDS:
        parts = []
        for path in sorted((OUTPUT / 'raw' / endpoint).glob('*.gz')):
            parts.append(pd.DataFrame(json.load(gzip.open(path, 'rt'))))
            provenance.append(dict(endpoint=endpoint, path=str(path),
                                   sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        if parts:
            frame = pd.concat(parts, ignore_index=True)
            frame.tradeDate = pd.to_datetime(frame.tradeDate.str[:10])
            if frame.duplicated(['ticker', 'tradeDate']).any():
                raise ValueError(f'Duplicate {endpoint} rows')
            frame.to_parquet(OUTPUT / f'{endpoint}.parquet', index=False)
    pd.DataFrame(provenance).to_csv(OUTPUT / 'data_sources.csv', index=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch', action='store_true')
    parser.add_argument('--limit', type=int)
    args = parser.parse_args()
    if args.fetch:
        fetch(args.limit)
    else:
        print('Stocks plus SPY calendar:', len(universe()))
