"""Measure prior-only call richness at matched delta/OTM and DTE for MSTR confirmations."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np
import pandas as pd

from pandar_quote_history import OUTPUT, SOURCE

CACHE = OUTPUT / 'data/richness'
SCAN_REPO = SOURCE.parents[2]
OLD_CACHE = Path('/private/tmp/delta_bomb_single_name_four_method_20260903')


def prior_stats(history: pd.DataFrame, day: str, current: float, lookback: int = 60,
                minimum: int = 40) -> dict:
    """Prior sessions only; sample standard deviation and empirical percentile, no p-value."""
    if history.date.duplicated().any():
        raise ValueError('duplicate sessions in richness history')
    prior = history[history.date < day].sort_values('date').tail(lookback)
    values = pd.to_numeric(prior.value, errors='coerce').dropna()
    n = len(values)
    mean, std = values.mean(), values.std(ddof=1)
    median = values.median()
    mad = (values - median).abs().median()
    valid = n >= minimum and np.isfinite(current)
    return dict(n=n, mean=mean, std=std, z=(current-mean)/std
                if valid and std > 1e-12 else np.nan,
                percentile=float((values < current).mean()*100) if valid else np.nan,
                robust_z=(current-median)/(1.4826*mad) if valid and mad > 1e-12 else np.nan,
                first=prior.date.min(), last=prior.date.max())


def interp_inside(x: object, y: object, target: float) -> float:
    """Linear interpolation inside observed support only; repeated coordinates use median."""
    f = pd.DataFrame({'x': x, 'y': y}).replace([np.inf, -np.inf], np.nan).dropna()
    f = f.groupby('x', as_index=False).y.median().sort_values('x')
    if f.empty or target < f.x.min()-1e-10 or target > f.x.max()+1e-10:
        return np.nan
    return float(np.interp(target, f.x, f.y))


def tenor_iv(dte: object, iv: object, target: float) -> float:
    """Interpolate total variance across expirations at fixed coordinate; no extrapolation."""
    dte, iv = np.asarray(dte, dtype=float), np.asarray(iv, dtype=float)
    if target <= 0:
        return np.nan
    variance = interp_inside(dte, iv**2*dte, target)
    return float(np.sqrt(variance/target)) if variance >= 0 else np.nan


def fetch() -> None:
    """Add only MSTR daily short-tenor chains within the existing 500-call cap."""
    sys.path.insert(0, str(SCAN_REPO / 'scripts'))
    from single_name_call_screen import CallLedger, OratsClient, STRIKE_FIELDS
    from dotenv import load_dotenv
    load_dotenv('/Users/dgrissen/Dev/gamma_chaser/.env')
    ledger = CallLedger(CACHE / 'manifest.json', max_calls=500, initial_used=337)
    client = OratsClient(os.environ.get('ORATS_API_KEY', ''), ledger, 100)
    daily = json.load(gzip.open(OLD_CACHE / 'hist_dailies/SPY_full_history.json.gz', 'rt'))
    dates = sorted({str(r['tradeDate'])[:10] for r in daily if r.get('tradeDate')})
    start_index = dates.index('2026-08-19')
    dates = sorted(set([d for d in dates[max(0, start_index-65):] if d <= '2026-09-03']
                       + ['2026-09-03']))
    for i, day in enumerate(dates, 1):
        path = CACHE / 'mstr_chains' / f'{day}.json.gz'
        if path.exists():
            continue
        rows = client.get('hist/strikes', {'ticker': 'MSTR', 'tradeDate': day,
                                         'dte': '1,30', 'delta': '.005,.80',
                                         'fields': ','.join(STRIKE_FIELDS)},
                          timeout=40, max_attempts=1)
        path.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(path, 'wt') as handle:
            json.dump(rows, handle)
        print(i, '/', len(dates), day, 'rows', len(rows), 'calls', ledger.used, flush=True)


def surface_at(frame: pd.DataFrame, coordinate: float, target_dte: float,
               mode: str) -> dict:
    """Return matched bid/mid IV and ATM IV for one historical session."""
    rows = []
    for _, expiry in frame.groupby('expirDate'):
        valid = expiry[(expiry.callBidPrice > 0) & (expiry.callAskPrice >= expiry.callBidPrice)
                       & (expiry.callBidIv > 0) & (expiry.callMidIv > 0)]
        if valid.empty:
            continue
        x = valid.delta if mode == 'delta' else np.log(valid.strike / valid.stockPrice)
        atm = interp_inside(valid.delta, valid.callMidIv, .5)
        bid = interp_inside(x, valid.callBidIv, coordinate)
        mid = interp_inside(x, valid.callMidIv, coordinate)
        rows.append(dict(dte=float(valid.dte.iloc[0]), bid=bid, mid=mid, atm=atm))
    if not rows:
        return dict(bid=np.nan, mid=np.nan, atm=np.nan)
    values = pd.DataFrame(rows)
    return {field: tenor_iv(values.dte, values[field], target_dte) for field in ('bid', 'mid', 'atm')}


def analyze() -> None:
    """Compare selected strike IV with prior 60-session surfaces at fixed DTE and coordinate."""
    chains = {}
    provenance = []
    for path in sorted((CACHE / 'mstr_chains').glob('*.gz')):
        frame = pd.DataFrame(json.load(gzip.open(path, 'rt')))
        if frame.empty:
            continue
        day = path.name[:10]
        assert frame.ticker.eq('MSTR').all() and frame.tradeDate.str[:10].eq(day).all()
        chains[day] = frame
        provenance.append(dict(path=str(path), day=day, rows=len(frame),
                               sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    source = pd.read_csv(SOURCE / 'pandar_approved_exact_confirmations.csv')
    confirmed = source[source.scenario.eq('sell-first call grab')]
    outcomes, history_rows = [], []
    for row in confirmed.itertuples():
        current = chains.get(row.tradeDate)
        if current is None:
            continue
        pair = current[current.expirDate.eq(row.expiry)]
        selected = pair[pair.strike.eq(row.leg1_strike)]
        if len(selected) != 1:
            raise ValueError(f'Missing exact selected MSTR strike on {row.tradeDate}')
        chosen = selected.iloc[0]
        atm = interp_inside(pair.delta, pair.callMidIv, .5)
        prior_days = sorted(d for d in chains if d < row.tradeDate)[-60:]
        for mode in ('delta', 'log_otm'):
            coordinate = float(chosen.delta) if mode == 'delta' else float(np.log(chosen.strike/chosen.stockPrice))
            matched = []
            for day in prior_days:
                point = surface_at(chains[day], coordinate, float(chosen.dte), mode)
                matched.append(dict(date=day, **point,
                                    bid_excess=(point['bid']-point['atm'])*100,
                                    mid_excess=(point['mid']-point['atm'])*100))
                history_rows.append(dict(signal_date=row.tradeDate, mode=mode,
                                         target_coordinate=coordinate, target_dte=chosen.dte,
                                         **matched[-1]))
            history = pd.DataFrame(matched)
            result = dict(tradeDate=row.tradeDate, ticker=row.ticker, expiry=row.expiry,
                          strike=row.leg1_strike, mode=mode, target_delta=chosen.delta,
                          target_otm_pct=(chosen.strike/chosen.stockPrice-1)*100,
                          vendor_dte=chosen.dte, bid=chosen.callBidPrice, ask=chosen.callAskPrice,
                          bid_iv_pct=chosen.callBidIv*100, mid_iv_pct=chosen.callMidIv*100,
                          atm_mid_iv_pct=atm*100,
                          bid_excess_iv_points=(chosen.callBidIv-atm)*100,
                          mid_excess_iv_points=(chosen.callMidIv-atm)*100)
            for metric, value in [('bid_excess', result['bid_excess_iv_points']),
                                  ('mid_excess', result['mid_excess_iv_points']),
                                  ('bid', chosen.callBidIv)]:
                stats = prior_stats(history[['date', metric]].rename(columns={metric: 'value'}),
                                    row.tradeDate, value)
                result.update({f'{metric}_{k}': v for k, v in stats.items()})
            outcomes.append(result)
    pd.DataFrame(outcomes).to_csv(OUTPUT / 'mstr_matched_strike_richness.csv', index=False)
    pd.DataFrame(history_rows).to_csv(OUTPUT / 'mstr_matched_strike_history.csv', index=False)
    pd.DataFrame(provenance).to_csv(OUTPUT / 'richness_sources.csv', index=False)
    print(pd.DataFrame(outcomes)[['tradeDate','strike','mode','target_delta','target_otm_pct',
                                 'bid_excess_iv_points','bid_excess_n','bid_excess_z',
                                 'bid_excess_percentile','mid_excess_z']].round(3).to_string(index=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch', action='store_true')
    args = parser.parse_args()
    if args.fetch:
        fetch()
    analyze()
