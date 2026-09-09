"""Fill the inherited August 11–21 put-screen omission using the frozen project rules."""
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

sys.path.insert(0, str(SOURCE.parents[2] / 'scripts'))
from single_name_call_screen import (
    CallLedger, OratsClient, STRIKE_FIELDS, rowwise_prior_percentile,
    select_put_tail_inventory_spread,
)

BACKFILL = OUTPUT / 'early_put_backfill'
SUMMARY_CACHE = Path('/private/tmp/delta_bomb_single_name_four_method_20260903')
ORIGINAL_FEATURES = SOURCE.parent / 'hiro_daily_2026-08-11_to_2026-08-27/single_name_call_screen_all.parquet'


def surface_candidates() -> pd.DataFrame:
    """Reuse original daily universe/ranks and add causal put-skew ranks from cached history."""
    destination = BACKFILL / 'surface_candidates.csv'
    if destination.exists():
        return pd.read_csv(destination)
    daily = json.load(gzip.open(SUMMARY_CACHE / 'hist_dailies/SPY_full_history.json.gz', 'rt'))
    dates = sorted({str(r['tradeDate'])[:10] for r in daily})
    dates = dates[dates.index('2026-08-11')-252:dates.index('2026-08-27')+1]
    wanted = set(dates)
    history = []
    hashes = []
    for path in sorted((SUMMARY_CACHE / 'hist_summaries_full').glob('*.gz')):
        raw = json.load(gzip.open(path, 'rt'))
        frame = pd.DataFrame([{k: r.get(k) for k in
                               ['ticker', 'tradeDate', 'exErnDlt75Iv30d', 'exErnIv30d']}
                              for r in raw if str(r.get('tradeDate', ''))[:10] in wanted])
        frame.tradeDate = frame.tradeDate.str[:10]
        frame['putskew'] = frame.exErnDlt75Iv30d*100-frame.exErnIv30d*100
        history.append(frame[['ticker', 'tradeDate', 'putskew']])
        hashes.append(dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    history = pd.concat(history).drop_duplicates(['tradeDate', 'ticker'])
    pivot = history.pivot(index='tradeDate', columns='ticker', values='putskew').reindex(dates)
    ranks = []
    for day in dates:
        if day < '2026-08-11':
            continue
        rank = rowwise_prior_percentile(pivot, day).rename('putskew_pct252').reset_index()
        rank['tradeDate'] = day
        ranks.append(rank)
    features = pd.read_parquet(ORIGINAL_FEATURES)
    features.tradeDate = pd.to_datetime(features.tradeDate).dt.strftime('%Y-%m-%d')
    features = features.merge(pd.concat(ranks), on=['tradeDate', 'ticker'], how='left',
                              validate='one_to_one').merge(history, on=['tradeDate', 'ticker'],
                                                          how='left', validate='one_to_one')
    # Real-data regression: the recomputed overlapping dates must match the existing put scan.
    existing = pd.read_parquet(SOURCE.parent /
                              'hiro_daily_four_methods_2026-08-24_to_2026-09-02/single_name_call_screen_all.parquet')
    existing.tradeDate = pd.to_datetime(existing.tradeDate).dt.strftime('%Y-%m-%d')
    overlap = features.merge(existing[['tradeDate', 'ticker', 'putskew_pct252']],
                             on=['tradeDate', 'ticker'], suffixes=('_new', '_old'))
    if len(overlap) == 0 or not np.allclose(overlap.putskew_pct252_new,
                                           overlap.putskew_pct252_old, equal_nan=True):
        raise ValueError('Put-skew ranks do not reproduce the frozen overlap')
    rows = features[features.tradeDate.le('2026-08-21') & features.liquid_final
                    & features.ivRank1y.le(35) & features.rr25_pct252.le(50)
                    & features.putskew_pct252.le(25)].copy()
    rows['scenario'] = 'buy-first put-tail inventory'
    rows['ranking_score'] = (15+(35-rows.ivRank1y).clip(lower=0)
                             +(50-rows.rr25_pct252).clip(lower=0)/5
                             +(25-rows.putskew_pct252).clip(lower=0)/5)
    rows = rows.sort_values(['tradeDate', 'ticker'])
    BACKFILL.mkdir(parents=True, exist_ok=True)
    rows.to_csv(destination, index=False)
    features.to_parquet(BACKFILL / 'all_surface_features.parquet', index=False)
    hashes.append(dict(path=str(ORIGINAL_FEATURES),
                       sha256=hashlib.sha256(ORIGINAL_FEATURES.read_bytes()).hexdigest()))
    pd.DataFrame(hashes).to_csv(BACKFILL / 'surface_sources.csv', index=False)
    print(f'Reproduced put-skew ranks on {len(overlap)} overlapping ticker/dates', flush=True)
    return rows


def fetch_chains(candidates: pd.DataFrame) -> None:
    """One combined-delta request per ten tickers covers both original put-chain passes."""
    from dotenv import load_dotenv
    load_dotenv('/Users/dgrissen/Dev/gamma_chaser/.env')
    # This annotation adds a new nine-session scan. Keep its 90-request allowance
    # separate from the immutable prior-run ledger (414 recorded requests).
    ledger = CallLedger(BACKFILL / 'api_manifest.json', max_calls=90, initial_used=0)
    client = OratsClient(os.environ.get('ORATS_API_KEY', ''), ledger, 100)
    jobs = []
    for day, group in candidates.groupby('tradeDate', sort=True):
        tickers = sorted(group.ticker.unique())
        for i in range(0, len(tickers), 10):
            batch = tickers[i:i+10]
            path = BACKFILL / 'chains' / day / ('-'.join(batch)+'.json.gz')
            if not path.exists():
                jobs.append((day, batch, path))
    if ledger.used+len(jobs) > ledger.max_calls:
        raise ValueError(f'Backfill needs {len(jobs)} calls; only {ledger.max_calls-ledger.used} remain')
    for index, (day, batch, path) in enumerate(jobs, 1):
        rows = client.get('hist/strikes', {'ticker': ','.join(batch), 'tradeDate': day,
                                         'dte': '14,75', 'delta': '.005,.99999',
                                         'fields': ','.join(STRIKE_FIELDS)},
                          timeout=60, max_attempts=1)
        path.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(path, 'wt') as handle:
            json.dump(rows, handle)
        print(f'{index}/{len(jobs)} {day} {len(batch)} tickers, {len(rows)} rows; '
              f'backfill calls {ledger.used}/90', flush=True)


def confirm(candidates: pd.DataFrame) -> None:
    """Apply the existing exact selector and retain every failure and raw leg coordinate."""
    results, provenance = [], []
    for day, group in candidates.groupby('tradeDate', sort=True):
        frames = []
        for path in sorted((BACKFILL / 'chains' / day).glob('*.gz')):
            frames.append(pd.DataFrame(json.load(gzip.open(path, 'rt'))))
            provenance.append(dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        chain = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        for _, row in group.iterrows():
            if chain.empty or row.ticker not in set(chain.ticker):
                raise ValueError(f'Missing chain coverage {day} {row.ticker}')
            subset = chain[chain.ticker.eq(row.ticker) & chain.tradeDate.str[:10].eq(day)]
            if subset.duplicated(['ticker', 'tradeDate', 'expirDate', 'strike']).any():
                raise ValueError('Duplicate chain identity')
            # Earnings are retained as estimated metadata and are not a put-selection veto.
            event_expiries = set(subset.loc[subset.dte.ge(row.wksNextErn*7), 'expirDate'])\
                if pd.notna(row.wksNextErn) and row.wksNextErn >= 0 else set()
            contract = select_put_tail_inventory_spread(subset, event_expiries)
            result = {**row.to_dict(), **contract, 'source_dataset': 'early_put_backfill_2026-08-11_to_2026-08-21',
                      'earnings_basis': 'signal-day weeks-to-earnings estimate; not a selection veto',
                      'replay_status': 'new qualification; not in original frozen P&L cohort'}
            for leg in (1, 2):
                if pd.isna(contract.get(f'leg{leg}_strike')):
                    continue
                selected = subset[subset.expirDate.eq(contract['expiry'])
                                  & subset.strike.eq(contract[f'leg{leg}_strike'])]
                if len(selected) != 1:
                    raise ValueError('Ambiguous selected backfill leg')
                item = selected.iloc[0]
                result[f'leg{leg}_otm_pct'] = (1-item.strike/item.stockPrice)*100
                result[f'leg{leg}_orats_call_coordinate_delta'] = item.delta
                result[f'leg{leg}_option_delta'] = item.delta-1
            results.append(result)
    frame = pd.DataFrame(results).sort_values(['tradeDate', 'ticker'])
    frame.to_csv(BACKFILL / 'all_chain_checks.csv', index=False)
    frame[frame.chain_confirmed].to_csv(BACKFILL / 'exact_confirmations.csv', index=False)
    pd.DataFrame(provenance).to_csv(BACKFILL / 'chain_sources.csv', index=False)
    print(frame.groupby('tradeDate').agg(surface=('ticker', 'size'),
                                         exact=('chain_confirmed', 'sum')).to_string(), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch-chains', action='store_true')
    parser.add_argument('--confirm', action='store_true')
    args = parser.parse_args()
    candidates = surface_candidates()
    print(candidates.groupby('tradeDate').size().to_string(), flush=True)
    print('Combined chain calls:', sum((len(g)+9)//10 for _, g in candidates.groupby('tradeDate')), flush=True)
    if args.fetch_chains:
        fetch_chains(candidates)
    if args.confirm:
        confirm(candidates)
