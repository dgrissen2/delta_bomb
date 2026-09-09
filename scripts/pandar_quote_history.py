"""Cache exact-contract minute quotes for the frozen Pandar inventory (research only)."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
import hashlib
import json
from pathlib import Path
import time

import pandas as pd

SOURCE = Path('/Users/dgrissen/Dev/delta_bomb-nvda_call_strat/docs/replay/'
              'hiro_daily_pandar_approved_2026-08-11_to_2026-09-04')
OUTPUT = Path(__file__).resolve().parents[1] / 'docs/replay/pandar_leg_timing_2026-09-05'


def quote_path(ticker: str, expiry: str, strike: float, right: str) -> Path:
    """Return one stable exact-contract history path."""
    return OUTPUT / 'data/quotes' / f'{ticker}_{expiry}_{strike:g}_{right}.parquet'


def contracts() -> list[dict]:
    """Union the two legs across every confirmed ticker/date, preserving first availability."""
    frame = pd.read_csv(SOURCE / 'pandar_approved_exact_confirmations.csv')
    rows = []
    for row in frame.itertuples():
        for strike in (row.leg1_strike, row.leg2_strike):
            rows.append(dict(ticker=row.ticker, expiry=row.expiry, strike=strike,
                             right='put' if row.scenario.startswith('buy-first') else 'call',
                             start=row.tradeDate))
    result = pd.DataFrame(rows).groupby(['ticker', 'expiry', 'strike', 'right'], as_index=False)
    return result.start.min().sort_values(['ticker', 'expiry', 'strike']).to_dict('records')


def fetch_one(client: object, contract: dict) -> dict:
    """Fetch quotes without exposing provider credentials or exception messages."""
    path = quote_path(**{k: contract[k] for k in ('ticker', 'expiry', 'strike', 'right')})
    if path.exists():
        frame = pd.read_parquet(path)
        status = 'cached'
    else:
        end = min(contract['expiry'], '2026-09-04')
        started = time.monotonic()
        try:
            response = client.option_history_quote(
                symbol=contract['ticker'], expiration=date.fromisoformat(contract['expiry']),
                strike=str(contract['strike']), right=contract['right'], interval='1m',
                start_date=date.fromisoformat(contract['start']), end_date=date.fromisoformat(end),
                start_time='09:30:00', end_time='16:00:00')
            frame = response.to_pandas()
        except Exception as error:  # Provider boundary; errors retained in manifest, never zero-filled.
            return dict(**contract, status='error', error_type=type(error).__name__,
                        elapsed=round(time.monotonic() - started, 2))
        if len(frame) == 0:
            return dict(**contract, status='empty', rows=0)
        if not (frame.symbol.eq(contract['ticker']).all()
                and frame.strike.eq(contract['strike']).all()
                and frame.right.str.lower().eq(contract['right']).all()
                and pd.to_datetime(frame.expiration).dt.strftime('%Y-%m-%d')
                .eq(contract['expiry']).all()):
            raise ValueError(f'Contract identity mismatch: {path.name}')
        if frame.timestamp.duplicated().any():
            raise ValueError(f'Duplicate quote timestamps: {path.name}')
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(path, index=False)
        status = 'success'
    return dict(**contract, status=status, rows=len(frame), path=str(path),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                first=str(frame.timestamp.min()), last=str(frame.timestamp.max()))


def main() -> None:
    """Bound downloads to the frozen exact inventory and persist each completed attempt."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workers', type=int, default=2)
    parser.add_argument('--limit', type=int)
    args = parser.parse_args()
    from thetadata import ThetaClient
    client = ThetaClient(creds_file='/Users/dgrissen/Dev/ThetaData/creds.txt')
    tasks = contracts()
    if args.limit:
        tasks = tasks[:args.limit]
    manifest = dict(source='ThetaData option_history_quote, 1m NBBO snapshots; America/New_York',
                    source_inventory=str(SOURCE / 'pandar_approved_exact_confirmations.csv'),
                    created_at=pd.Timestamp.now(tz='UTC').isoformat(), end='2026-09-04',
                    total_contracts=len(tasks), files=[])
    output_path = OUTPUT / 'quote_manifest.json'
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(fetch_one, client, contract) for contract in tasks]
        for index, future in enumerate(as_completed(futures), 1):
            record = future.result()
            manifest['files'].append(record)
            output_path.write_text(json.dumps(manifest, indent=2) + '\n')
            print(index, '/', len(tasks), record['ticker'], record['strike'], record['status'],
                  record.get('rows', 0), flush=True)


if __name__ == '__main__':
    main()
