"""Bounded exact-call follow-up for the ten Plannotator report examples."""
from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path

import pandas as pd

from pandar_leg_timing import CUTOFF, SESSIONS, action_price, at, quote_at, shift
from pandar_quote_history import quote_path
from pandar_skew_journey_data import OUTPUT

EXAMPLES = [('COIN', '2026-08-20'), ('COIN', '2026-08-21'), ('STX', '2026-08-24'),
            ('NVDA', '2026-08-26'), ('BE', '2026-08-28'), ('MSTR', '2026-08-20'),
            ('SMCI', '2026-08-13'), ('JNJ', '2026-08-24'), ('MRNA', '2026-08-24'),
            ('TSLA', '2026-09-02')]
CENTRAL = Path('/Users/dgrissen/Dev/central_trade_data/orats')


def earnings_gate(day: str, next_earn: str, snapshot_day: str) -> str:
    """Require a same-date known schedule; exclude date zero through day 30 inclusive."""
    event = pd.to_datetime(next_earn, errors='coerce')
    if snapshot_day != day or pd.isna(event) or event < pd.Timestamp(day):
        return 'unknown'
    return 'exclude_earnings_30d' if event <= pd.Timestamp(day)+pd.Timedelta(days=30) else 'clear'


def session_deadline(entry_day: str, expiry: str, sessions: int) -> str:
    """Entry is session one; cap the requested closing date at contract expiry."""
    if sessions not in (4, 5):
        raise ValueError('Only the frozen four/five-session horizons are allowed')
    return min(shift(entry_day, sessions-1), expiry)


def examples() -> pd.DataFrame:
    frame = pd.read_csv(OUTPUT / 'recent_73_calls_with_journey.csv')
    return pd.concat([frame[frame.ticker.eq(t) & frame.tradeDate.eq(d)] for t, d in EXAMPLES])


def contract_path(ticker: str, expiry: str, strike: float) -> Path:
    old = quote_path(ticker, expiry, strike, 'call')
    if old.exists():
        return old
    return OUTPUT / 'review_quotes' / f'{ticker}_{expiry}_{strike:g}_call.parquet'


def fetch() -> None:
    """Reuse cached contracts and make at most one request for each of twenty contracts."""
    from thetadata import ThetaClient
    client = None
    manifest_path = OUTPUT / 'review_quote_manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else \
        dict(cutoff=CUTOFF, request_cap=20, attempts=0, files=[])
    seen = {(r['ticker'], r['expiry'], r['strike']) for r in manifest['files']}
    for row in examples().itertuples():
        for strike in (row.strike, row.nearer_strike):
            if (row.ticker, row.expiry, strike) in seen:
                continue  # Preserve original request counts; do not retry failed downloads.
            path = contract_path(row.ticker, row.expiry, strike)
            record = dict(ticker=row.ticker, expiry=row.expiry, strike=strike, path=str(path))
            if path.exists():
                record['status'] = 'cached'
            else:
                if manifest['attempts'] >= manifest['request_cap']:
                    raise RuntimeError('Frozen ThetaData request cap exhausted')
                if client is None:
                    try:
                        client = ThetaClient(creds_file='/Users/dgrissen/Dev/ThetaData/creds.txt')
                    except Exception as error:
                        raise RuntimeError('ThetaData initialization failed: '
                                           f'{type(error).__name__}') from None
                manifest['attempts'] += 1
                manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')
                try:
                    frame = client.option_history_quote(
                        symbol=row.ticker, expiration=date.fromisoformat(row.expiry),
                        strike=str(strike), right='call', interval='1m',
                        start_date=date.fromisoformat(shift(row.tradeDate, 1)),
                        end_date=date.fromisoformat(min(row.expiry, CUTOFF)),
                        start_time='09:30:00', end_time='16:00:00').to_pandas()
                except Exception as error:  # Provider boundary; never log credential-bearing URLs.
                    record.update(status='error', error_type=type(error).__name__)
                else:
                    if frame.empty:
                        record['status'] = 'empty'
                    else:
                        if not (frame.symbol.eq(row.ticker).all()
                                and frame.strike.eq(strike).all()
                                and frame.right.str.lower().eq('call').all()
                                and pd.to_datetime(frame.expiration).dt.strftime('%Y-%m-%d')
                                .eq(row.expiry).all()) or frame.timestamp.duplicated().any():
                            raise ValueError(f'Contract identity/duplicate mismatch: {path.name}')
                        path.parent.mkdir(parents=True, exist_ok=True)
                        frame.to_parquet(path, index=False)
                        record['status'] = 'fetched'
            if path.exists():
                record['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
                record['rows'] = len(pd.read_parquet(path))
            manifest['files'].append(record)
            manifest_path.write_text(json.dumps(manifest, indent=2)+'\n')
            print(row.ticker, strike, record['status'], record.get('rows', 0), flush=True)


def load_quotes(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_parquet(path)
    frame['timestamp'] = pd.to_datetime(frame.timestamp, utc=True).dt.tz_convert('America/New_York')
    return frame.set_index('timestamp').sort_index()


def replay(row: dict, first: pd.DataFrame, second: pd.DataFrame, horizon: int) -> dict:
    """Separate spread completion, executable closure, conservative marks, and censoring."""
    day = shift(row['tradeDate'], 1)
    opened = at(day, '10:01')
    deadline_day = session_deadline(day, row['expiry'], horizon)
    deadline = at(deadline_day, '15:50')
    result = dict(ticker=row['ticker'], tradeDate=row['tradeDate'], expiry=row['expiry'],
                  short_strike=row['strike'], long_strike=row['nearer_strike'], horizon=horizon,
                  entry_time=opened.isoformat(), deadline=deadline.isoformat(),
                  expiry_shortened=deadline_day < shift(day, horizon-1),
                  elapsed_calendar_days=(deadline.date()-opened.date()).days,
                  paired=False, fully_closed=False)
    if first.empty or second.empty:
        return dict(result, status='missing_contract_history')
    sale = action_price(quote_at(first, opened), 'sell')
    initial_ask = action_price(quote_at(second, opened), 'buy')
    if sale is None or initial_ask is None or sale < .20:
        return dict(result, status='entry_not_admitted', observed_entry_bid=sale,
                    observed_nearer_ask=initial_ask)
    result.update(entry_bid=sale, initial_nearer_ask=initial_ask, threshold=sale-.10)
    observed_end = min(deadline, at(CUTOFF, '15:50'))
    expected = pd.DatetimeIndex([])
    for session in SESSIONS:
        if day <= session <= observed_end.strftime('%Y-%m-%d'):
            expected = expected.append(pd.date_range(at(session, '09:30'), at(session, '15:50'),
                                                    freq='1min'))
    expected = expected[(expected > opened) & (expected <= observed_end)]
    result['expected_post_entry_minutes'] = len(expected)
    result['missing_nearer_rows'] = len(expected.difference(second.index))
    result['invalid_nearer_quotes'] = sum(action_price(quote_at(second, t), 'buy') is None
                                         for t in expected)
    bought = None
    for timestamp in expected:
        ask = action_price(quote_at(second, timestamp), 'buy')
        if ask is not None and ask <= sale-.10+1e-9:
            bought = ask
            result.update(paired=True, leg2_time=timestamp.isoformat(), leg2_ask=ask,
                          construction_cash_after_reserved_fees=100*(sale-ask)-2.60)
            break
    if deadline_day > CUTOFF:
        return dict(result, status='deadline_censored')
    cover = action_price(quote_at(first, deadline), 'buy')
    if cover is None:
        return dict(result, status='exit_unpriced')
    result.update(short_cover_ask=cover, short_only_pnl=100*(sale-cover)-1.30)
    if bought is None:
        return dict(result, status='uncompleted_short_closed', fully_closed=True,
                    pnl_net=result['short_only_pnl'], pnl_extra_1c_slippage=result['short_only_pnl']-2,
                    actions=2)
    long_quote = quote_at(second, deadline)
    long_sale = action_price(long_quote, 'sell')
    status = 'completed_closed'
    if long_sale is None:
        mark = action_price(long_quote, 'sell', marking=True)
        if mark != 0.0:
            return dict(result, status='exit_unpriced')
        long_sale, status = 0., 'completed_zero_bid_long_mark'
    net = 100*(sale-bought+long_sale-cover)-2.60
    return dict(result, status=status, fully_closed=status == 'completed_closed',
                long_exit_bid=long_sale, pnl_net=net, pnl_extra_1c_slippage=net-4,
                actions=4, conversion_vs_short_only=net-result['short_only_pnl'])


def earnings_audit() -> None:
    """Persist source coverage and fail-closed statuses without treating estimates as dates."""
    paths = [CENTRAL / 'earnings/earnings_long.parquet',
             CENTRAL / 'earnings/pit_constituents_earnings_long.parquet',
             CENTRAL / 'stable_rrs_earnings_2026-07-29-v1/normalized/earnings.parquet']
    sources = []
    for path in paths:
        frame = pd.read_parquet(path)
        key = 'tradeDate' if 'tradeDate' in frame else 'earnDate'
        sources.append(dict(path=str(path), rows=len(frame), date_field=key,
                            last_date=str(pd.to_datetime(frame[key]).max()),
                            sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    (OUTPUT / 'review_earnings_sources.json').write_text(json.dumps(sources, indent=2)+'\n')
    calls = pd.read_csv(OUTPUT / 'recent_73_calls_with_journey.csv')
    path = OUTPUT.parent / 'pandar_leg_timing_2026-09-05/call_exclusion_audit/liquid_surface_rows.parquet'
    surface = pd.read_parquet(path)[['ticker', 'tradeDate', 'nextErn', 'wksNextErn']]
    merged = calls[['ticker', 'tradeDate']].merge(surface, on=['ticker', 'tradeDate'],
                                               validate='one_to_one', how='left')
    merged['signal_earnings_gate'] = [earnings_gate(r.tradeDate, r.nextErn, r.tradeDate)
                                      for r in merged.itertuples()]
    merged['estimated_days_to_earnings'] = merged.wksNextErn*7
    merged['entry_earnings_gate'] = 'unknown'
    merged['policy_admitted'] = False  # No fresh dated entry schedules in this reviewed input.
    merged.to_csv(OUTPUT / 'review_earnings_73.csv', index=False)


def analyze() -> None:
    rows = []
    for row in examples().to_dict('records'):
        first = load_quotes(contract_path(row['ticker'], row['expiry'], row['strike']))
        second = load_quotes(contract_path(row['ticker'], row['expiry'], row['nearer_strike']))
        for horizon in (4, 5):
            rows.append(replay(row, first, second, horizon))
    frame = pd.DataFrame(rows)
    frame.to_csv(OUTPUT / 'review_45_session_replay.csv', index=False)
    earnings_audit()
    print(frame[['ticker', 'tradeDate', 'horizon', 'status', 'entry_bid', 'leg2_time',
                 'leg2_ask', 'pnl_net', 'short_only_pnl']].to_string(index=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch', action='store_true')
    args = parser.parse_args()
    if args.fetch:
        fetch()
    else:
        analyze()
