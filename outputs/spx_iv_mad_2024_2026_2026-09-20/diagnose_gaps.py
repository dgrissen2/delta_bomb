"""Inspect recorded inputs for unavailable windows; no fetching or rule changes."""
import json
from pathlib import Path

import pandas as pd

import spx_mad as p


def main() -> None:
    rows = []
    for metadata in sorted((p.DATA / 'derived' / 'SPXW' / 'metadata').glob('*.json')):
        record = json.loads(metadata.read_text())
        if record['window_slots'] == record['measured_windows']:
            continue
        day = record['date']
        windows = pd.read_parquet(p.DATA / 'derived' / 'SPXW' / 'windows' / f'{day}.parquet')
        missing = windows[~windows.available]
        native = json.loads((p.DATA / 'days' / 'SPXW' / f'{day}.json').read_text())
        inputs = [r for r in native['raw_files']
                  if r['method'] == 'option_history_greeks_implied_volatility']
        frames = [p.legacy.checked_read(r['path'], r['sha256']) for r in inputs]
        frame = pd.concat(frames, ignore_index=True)
        stamp = pd.to_datetime(frame.timestamp).dt.tz_convert('America/New_York')
        frame['minute'] = stamp.dt.hour * 60 + stamp.dt.minute
        samples = []
        for minute in sorted({int(missing.end_min.min()), int(missing.end_min.max())}):
            for expiry, group in frame[frame.minute.eq(minute)].groupby('expiration'):
                lo, hi = float(group.strike.min()), float(group.strike.max())
                spot_lo, spot_hi = float(group.underlying_price.min()), float(group.underlying_price.max())
                samples.append({'minute': minute, 'expiration': str(expiry),
                                'strike_min': lo, 'strike_max': hi,
                                'spot_min': spot_lo, 'spot_max': spot_hi,
                                'spot_outside_downloaded_strikes': spot_hi < lo or spot_lo > hi})
        rows.append({'date': day, 'unavailable_windows': len(missing),
                     'window_reasons': missing.status.value_counts().to_dict(),
                     'sample_scope': 'first and last unavailable endpoint only',
                     'native_samples': samples,
                     'input_hashes': {r['path']: r['sha256'] for r in inputs}})
    p.write_json(p.DATA / 'gap_diagnostics.json', {
        'scope': 'Source inspection, not a trading test or a change to frozen inputs',
        'producer_sha256': p.digest(Path(__file__)), 'dates': rows})
    print(json.dumps(rows, indent=2))


if __name__ == '__main__':
    main()
