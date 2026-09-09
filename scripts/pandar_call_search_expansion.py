"""Search all rich-front-wing stock dates with controlled delta-band comparisons."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os

import numpy as np
import pandas as pd

from pandar_call_exclusions import AUDIT, CallLedger, OratsClient, STRIKE_FIELDS, contract_checks
from pandar_quote_history import OUTPUT
from pandar_richness import interp_inside

EXPANSION = OUTPUT / 'call_search_expansion'
BANDS = [(2, 6), (2, 8), (2, 10), (1, 10), (2, 15)]


def candidates() -> pd.DataFrame:
    """Broaden only discovery: the fixed front-wing rank proxy stays >=85."""
    frame = pd.read_parquet(AUDIT / 'liquid_surface_rows.parquet')
    frame = frame[frame.call_wing_10_pct252.ge(85)].copy()
    frame['original_surface_pass'] = (frame.sell_archetype.eq('grab')
                                       & frame.sell_first_actionable)
    frame['grab_surface_pass'] = frame.sell_archetype.eq('grab')
    failures = []
    for r in frame.itertuples():
        reasons = []
        for failed, reason in [(r.call_kink_pct252 < 70, 'kink rank <70'),
                               (r.rr25_pct252 > 10, 'local RR rank >10'),
                               (r.put_wing_10_pct252 >= 70, 'opposite put-wing rank >=70'),
                               (r.return_5d_pct <= 0, 'five-day return <=0'),
                               (not 30 <= r.ivRank1y <= 70, 'IVR outside 30–70'),
                               (r.drawdown_20d_pct < -5, 'more than 5% below 20-day high'),
                               (r.earnings_near_front_expiry, 'near-front earnings flag')]:
            if failed:
                reasons.append(reason)
        failures.append('; '.join(reasons) or 'passed original surface')
    frame['original_surface_exclusions'] = failures
    frame = frame.sort_values(['tradeDate', 'ticker'])
    EXPANSION.mkdir(parents=True, exist_ok=True)
    frame.to_csv(EXPANSION / 'surface_candidates.csv', index=False)
    return frame


def fetch(frame: pd.DataFrame) -> None:
    """Reuse the 56 prior audited dates; request only the other 357 stock dates."""
    from dotenv import load_dotenv
    load_dotenv('/Users/dgrissen/Dev/gamma_chaser/.env')
    old = pd.read_csv(AUDIT / 'surface_exclusions.csv')
    covered = set(zip(old.tradeDate, old.ticker))
    missing = frame[[(r.tradeDate, r.ticker) not in covered for r in frame.itertuples()]]
    ledger = CallLedger(EXPANSION / 'api_manifest.json', max_calls=50, initial_used=0)
    client = OratsClient(os.environ.get('ORATS_API_KEY', ''), ledger, 100)
    for day, group in missing.groupby('tradeDate', sort=True):
        tickers = sorted(group.ticker.unique())
        for start in range(0, len(tickers), 10):
            batch = tickers[start:start+10]
            path = EXPANSION / 'chains' / day / ('-'.join(batch)+'.json.gz')
            if path.exists():
                continue
            rows = client.get('hist/strikes', {'ticker': ','.join(batch), 'tradeDate': day,
                                             'dte': '1,30', 'delta': '.005,.80',
                                             'fields': ','.join(STRIKE_FIELDS)},
                              timeout=60, max_attempts=1)
            path.parent.mkdir(parents=True, exist_ok=True)
            with gzip.open(path, 'wt') as handle:
                json.dump(rows, handle)
            print(day, len(batch), 'stocks', len(rows), 'chain rows; calls', ledger.used, flush=True)


def analyze(frame: pd.DataFrame) -> None:
    """Keep all failed contracts and independent band/surface comparisons, without P&L selection."""
    rows, chosen_rows, provenance, coverage = [], [], [], []
    for day, group in frame.groupby('tradeDate', sort=True):
        data = []
        for directory in [AUDIT / 'chains' / day, EXPANSION / 'chains' / day]:
            for path in sorted(directory.glob('*.gz')):
                data.append(pd.DataFrame(json.load(gzip.open(path, 'rt'))))
                provenance.append(dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        chain = pd.concat(data, ignore_index=True)
        for r in group.itertuples():
            stock = chain[chain.ticker.eq(r.ticker) & chain.tradeDate.str[:10].eq(day)]
            if stock.empty or stock.duplicated(['expirDate', 'strike']).any():
                raise ValueError(f'Missing/duplicate chain: {day} {r.ticker}')
            event_known = pd.notna(r.wksNextErn) and r.wksNextErn >= 0
            events = set(stock.loc[stock.dte.ge(r.wksNextErn*7), 'expirDate']) if event_known else set()
            checks = contract_checks(stock, events)
            coverage.append(dict(tradeDate=day, ticker=r.ticker, chain_rows=len(stock),
                                 otm_contracts_with_nearer_strike=len(checks),
                                 status='evaluated' if not checks.empty else
                                 'no OTM call with a nearer strike in returned 1–30DTE slice'))
            if checks.empty:
                continue
            for field in ['ticker', 'tradeDate', 'ivRank1y', 'rr25_pct252', 'call_wing_10_pct252',
                          'call_kink_pct252', 'original_surface_pass', 'grab_surface_pass',
                          'original_surface_exclusions', 'earnings_near_front_expiry']:
                checks[field] = getattr(r, field)
            checks['event_estimate_available'] = event_known
            rows.append(checks)
            for low, high in BANDS:
                passing = checks[checks.without_delta_band & checks.delta.between(low/100, high/100)]
                if passing.empty:
                    continue
                chosen = passing.assign(distance=(passing.delta-.04).abs()).sort_values(
                    ['dte', 'distance', 'quote_width', 'strike']).iloc[0].to_dict()
                chosen.update(band=f'{low}–{high}', eligible_contracts=len(passing),
                              front_5_12_contracts=int(passing.dte.le(12).sum()),
                              fallback_13_19_contracts=int(passing.dte.gt(12).sum()))
                raw = stock[stock.expirDate.eq(chosen['expiry']) & stock.strike.eq(chosen['strike'])].iloc[0]
                expiry = stock[stock.expirDate.eq(chosen['expiry'])]
                nearer = expiry[expiry.strike.eq(chosen['nearer_strike'])].iloc[0]
                chosen['nearer_delta'] = nearer.delta
                chosen['nearer_otm_pct'] = (nearer.strike/nearer.stockPrice-1)*100
                chosen['nearer_bid'] = nearer.callBidPrice
                chosen['nearer_oi'] = nearer.callOpenInterest
                atm = expiry.loc[(expiry.delta-.5).abs().idxmin()]
                chosen['atm_iv_pct'] = atm.callMidIv*100
                chosen['bid_iv_pct'] = raw.callBidIv*100
                chosen['otm_in_atm_expected_moves'] = chosen['otm_pct']/(atm.callMidIv*100*np.sqrt(raw.dte/365))
                deferred = stock[stock.dte.between(max(20, raw.dte+1), 30)]
                chosen['deferred_expiry'] = ''
                chosen['front_bid_minus_deferred_mid_points'] = np.nan
                chosen['deferred_event_inside_estimate'] = np.nan
                for expiry_name, tenor in deferred.groupby('expirDate', sort=True):
                    iv = interp_inside(tenor.delta, tenor.callMidIv, raw.delta)
                    if np.isfinite(iv):
                        chosen['deferred_expiry'] = expiry_name
                        chosen['front_bid_minus_deferred_mid_points'] = (raw.callBidIv-iv)*100
                        chosen['deferred_event_inside_estimate'] = expiry_name in events
                        break
                chosen_rows.append(chosen)
    full, selected = pd.concat(rows, ignore_index=True), pd.DataFrame(chosen_rows)
    full.to_csv(EXPANSION / 'every_contract_check.csv', index=False)
    selected.to_csv(EXPANSION / 'selected_by_delta_band.csv', index=False)
    pd.DataFrame(provenance).to_csv(EXPANSION / 'chain_sources.csv', index=False)
    pd.DataFrame(coverage).to_csv(EXPANSION / 'coverage.csv', index=False)
    summaries = []
    for scope in ['original_surface', 'grab_surface', 'rich_front_wing']:
        sample = selected[selected.original_surface_pass] if scope == 'original_surface' else (
            selected[selected.grab_surface_pass] if scope == 'grab_surface' else selected)
        for low, high in BANDS:
            group = sample[sample.band.eq(f'{low}–{high}')]
            summaries.append(dict(scope=scope, band=f'{low}–{high}', ticker_days=len(group),
                                  stocks=group.ticker.nunique(), front_5_12=int(group.dte.le(12).sum()),
                                  fallback_13_19=int(group.dte.gt(12).sum()),
                                  names=','.join(sorted(group.ticker.unique()))))
    summary = pd.DataFrame(summaries)
    summary.to_csv(EXPANSION / 'band_summary.csv', index=False)
    print(summary.to_string(index=False), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch', action='store_true')
    parser.add_argument('--analyze', action='store_true')
    args = parser.parse_args()
    frame = candidates()
    print('Rich-front-wing discovery:', len(frame), 'stock dates;', frame.ticker.nunique(), 'stocks', flush=True)
    if args.fetch:
        fetch(frame)
    if args.analyze:
        analyze(frame)
