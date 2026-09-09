"""Capture exact-minute option delta/IV at the reported MSTR executions."""
from __future__ import annotations

from datetime import date
import hashlib
import json

import pandas as pd

from pandar_quote_history import OUTPUT


def main() -> None:
    from thetadata import ThetaClient
    client = ThetaClient(creds_file='/Users/dgrissen/Dev/ThetaData/creds.txt')
    cases = pd.read_csv(OUTPUT / 'source_dime_target_sensitivity.csv')
    cases = cases.query('method == "hiro_finance" and horizon == 2')
    rows, provenance = [], []
    for row in cases.itertuples():
        for leg in (1, 2):
            stamp = pd.Timestamp(row.entry_time if leg == 1 else row.leg2_time)
            strike = row.leg1_strike if leg == 1 else row.leg2_strike
            path = OUTPUT / 'data' / f'MSTR_greeks_{stamp:%Y%m%d_%H%M}_{strike:g}C.parquet'
            if path.exists():
                frame = pd.read_parquet(path)
            else:
                response = client.option_history_greeks_first_order(
                    symbol='MSTR', expiration=date(2026,8,28), interval='1m',
                    date=stamp.date(), strike=str(strike), right='call',
                    start_time=stamp.strftime('%H:%M:%S'), end_time=stamp.strftime('%H:%M:%S'))
                frame = response.to_pandas()
                frame.to_parquet(path, index=False)
            if len(frame) != 1:
                raise ValueError(f'Expected one exact-minute Greek row: {path.name}')
            quote = frame.iloc[0]
            assert pd.Timestamp(quote.timestamp) == stamp and quote.strike == strike
            rows.append(dict(signal_date=row.tradeDate, leg=leg, timestamp=stamp.isoformat(),
                             ticker='MSTR', expiry='2026-08-28', strike=strike,
                             delta=quote.delta, implied_vol_pct=quote.implied_vol*100,
                             bid=quote.bid, ask=quote.ask, stock=quote.underlying_price,
                             otm_pct=(strike/quote.underlying_price-1)*100,
                             iv_error=quote.iv_error))
            provenance.append(dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    pd.DataFrame(rows).to_csv(OUTPUT / 'actual_execution_greeks.csv', index=False)
    (OUTPUT / 'data/entry_greeks_manifest.json').write_text(json.dumps(provenance, indent=2))
    print(pd.DataFrame(rows).round(4).to_string(index=False))


if __name__ == '__main__':
    main()
