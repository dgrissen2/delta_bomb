"""Audit why the frozen call screen retained only MSTR, with explicit filter ablations."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

from pandar_quote_history import OUTPUT, SOURCE

sys.path.insert(0, str(SOURCE.parents[2] / 'scripts'))
from single_name_call_screen import (
    CallLedger, OratsClient, STRIKE_FIELDS, contract_record, is_single_stock_ticker,
)

AUDIT = OUTPUT / 'call_exclusion_audit'


def contract_checks(chain: pd.DataFrame, event_expiries: set[str]) -> pd.DataFrame:
    """Enumerate alternatives under the original contract gates, changing one filter at a time."""
    results = []
    for expiry, frame in chain.groupby('expirDate'):
        frame = frame.sort_values('strike')
        atm = frame.loc[(frame.delta-.5).abs().idxmin()]
        for index in range(1, len(frame)):
            row, nearer = frame.iloc[index], frame.iloc[index-1]
            if row.strike <= row.stockPrice:
                continue
            spread = row.callAskPrice-row.callBidPrice
            wing = (row.callMidIv-atm.callMidIv)*100
            quote_ok = (row.callBidPrice >= .20 and row.callAskPrice >= row.callBidPrice
                        and row.callOpenInterest >= 25 and nearer.callAskPrice > 0)
            surface_ok = (np.isfinite(wing) and atm.callMidIv > 0 and wing >= 2
                          and expiry not in event_expiries)
            tenor_ok = 5 <= row.dte <= 19
            delta_ok = .02 <= row.delta <= .06
            width_ok = spread <= .10+1e-9
            common = quote_ok and surface_ok and tenor_ok
            results.append(dict(expiry=expiry, strike=row.strike, dte=row.dte,
                                stock=row.stockPrice, delta=row.delta,
                                otm_pct=(row.strike/row.stockPrice-1)*100,
                                bid=row.callBidPrice, ask=row.callAskPrice, quote_width=spread,
                                width_pct_of_bid=spread/row.callBidPrice*100 if row.callBidPrice > 0 else np.nan,
                                oi=row.callOpenInterest, wing_mid_excess_points=wing,
                                wing_bid_excess_points=(row.callBidIv-atm.callMidIv)*100,
                                nearer_strike=nearer.strike, nearer_ask=nearer.callAskPrice,
                                event_inside_estimate=expiry in event_expiries,
                                all_original_contract_gates=bool(common and delta_ok and width_ok),
                                without_delta_band=bool(common and width_ok),
                                without_absolute_width=bool(common and delta_ok)))
    return pd.DataFrame(results)


def surface_inventory() -> pd.DataFrame:
    """Retain original per-date surface features; do not include ETF rows from the older scan."""
    parts, sources = [], []
    for folder, start, end in [
        ('hiro_daily_2026-08-11_to_2026-08-27', '2026-08-11', '2026-08-27'),
        ('hiro_daily_four_methods_2026-08-24_to_2026-09-02', '2026-08-28', '2026-09-02'),
        ('hiro_daily_pandar_approved_2026-08-11_to_2026-09-04/gap_2026-09-03', '2026-09-03', '2026-09-03'),
    ]:
        path = SOURCE.parent / folder / 'single_name_call_screen_all.parquet'
        f = pd.read_parquet(path)
        f.tradeDate = pd.to_datetime(f.tradeDate).dt.strftime('%Y-%m-%d')
        parts.append(f[f.tradeDate.between(start, end)])
        sources.append(dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    frame = pd.concat(parts)
    frame = frame[frame.liquid_final & frame.ticker.map(is_single_stock_ticker)].copy()
    AUDIT.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(AUDIT / 'liquid_surface_rows.parquet', index=False)
    candidates = frame[frame.sell_archetype.eq('grab')].copy()
    candidates['original_surface_pass'] = candidates.sell_first_actionable
    reasons = []
    for row in candidates.itertuples():
        failures = []
        if not 30 <= row.ivRank1y <= 70:
            failures.append('IVR outside 30–70')
        if row.drawdown_20d_pct < -5:
            failures.append('more than 5% below 20-day high')
        if row.earnings_near_front_expiry:
            failures.append('near-front earnings flag')
        reasons.append('; '.join(failures) or 'Passed original surface')
    candidates['original_surface_reason'] = reasons
    candidates = candidates.sort_values(['tradeDate', 'ticker'])
    candidates.to_csv(AUDIT / 'surface_exclusions.csv', index=False)
    pd.DataFrame(sources).to_csv(AUDIT / 'surface_sources.csv', index=False)
    return candidates


def fetch(candidates: pd.DataFrame) -> None:
    """Bound exact-chain collection to the 56 one-sided surface signals, using 17 batches."""
    from dotenv import load_dotenv
    load_dotenv('/Users/dgrissen/Dev/gamma_chaser/.env')
    ledger = CallLedger(AUDIT / 'api_manifest.json', max_calls=20, initial_used=0)
    client = OratsClient(os.environ.get('ORATS_API_KEY', ''), ledger, 100)
    for day, group in candidates.groupby('tradeDate', sort=True):
        tickers = sorted(group.ticker.unique())
        for start in range(0, len(tickers), 10):
            batch = tickers[start:start+10]
            path = AUDIT / 'chains' / day / ('-'.join(batch)+'.json.gz')
            if path.exists():
                continue
            rows = client.get('hist/strikes', {'ticker': ','.join(batch), 'tradeDate': day,
                                             'dte': '1,30', 'delta': '.005,.80',
                                             'fields': ','.join(STRIKE_FIELDS)},
                              timeout=60, max_attempts=1)
            path.parent.mkdir(parents=True, exist_ok=True)
            with gzip.open(path, 'wt') as handle:
                json.dump(rows, handle)
            print(day, ','.join(batch), len(rows), 'rows; calls', ledger.used, flush=True)


def analyze(candidates: pd.DataFrame) -> None:
    """Keep all alternatives and summarize coverage independently of subsequent trade outcomes."""
    originals = pd.read_csv(SOURCE / 'pandar_approved_master.csv')
    originals = originals[originals.scenario.eq('sell-first call grab')]
    results, summaries, provenance, replacements = [], [], [], []
    for day, group in candidates.groupby('tradeDate', sort=True):
        frames = []
        for path in sorted((AUDIT / 'chains' / day).glob('*.gz')):
            frames.append(pd.DataFrame(json.load(gzip.open(path, 'rt'))))
            provenance.append(dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        if not frames:
            raise ValueError(f'Missing chains {day}')
        chain = pd.concat(frames, ignore_index=True)
        for row in group.itertuples():
            subset = chain[chain.ticker.eq(row.ticker) & chain.tradeDate.str[:10].eq(day)]
            if subset.empty or subset.duplicated(['expirDate', 'strike']).any():
                raise ValueError(f'Missing or duplicate chain {day} {row.ticker}')
            # Signal-day event estimates, not later-known realized earnings dates.
            known_event = pd.notna(row.wksNextErn) and row.wksNextErn >= 0
            events = set(subset.loc[subset.dte.ge(row.wksNextErn*7), 'expirDate']) if known_event else set()
            checks = contract_checks(subset, events)
            checks['tradeDate'], checks['ticker'] = day, row.ticker
            checks['original_surface_pass'] = row.original_surface_pass
            checks['ivRank1y'], checks['rr25_pct252'] = row.ivRank1y, row.rr25_pct252
            checks['event_estimate_available'] = known_event
            selected = originals[originals.tradeDate.eq(day) & originals.ticker.eq(row.ticker)]
            checks['original_selected_contract'] = False
            original_pass = False
            if len(selected) == 1:
                selected = selected.iloc[0]
                checks['original_selected_contract'] = (checks.expiry.eq(selected.expiry)
                                                        & checks.strike.eq(selected.leg1_strike))
                original_pass = bool(selected.chain_confirmed)
                if pd.notna(selected.expiry):
                    reproduced = checks[checks.original_selected_contract]
                    if len(reproduced) != 1 or not np.allclose(
                        reproduced.iloc[0][['bid', 'ask', 'delta', 'stock']].astype(float),
                        [selected.leg1_bid, selected.leg1_ask, selected.leg1_delta, selected.stockPrice],
                    ):
                        raise ValueError('New chain does not reproduce frozen selected-contract data')
            checks['original_ticker_chain_pass'] = original_pass
            results.append(checks)
            summary = dict(tradeDate=day, ticker=row.ticker,
                           original_surface_pass=row.original_surface_pass,
                           original_surface_reason=row.original_surface_reason,
                           original_selected_pass=original_pass, ivRank1y=row.ivRank1y,
                           rr25_pct252=row.rr25_pct252,
                           call_wing_10_pct252=row.call_wing_10_pct252,
                           call_kink_pct252=row.call_kink_pct252,
                           event_estimate_available=known_event)
            for mode in ['all_original_contract_gates', 'without_delta_band', 'without_absolute_width']:
                subset = checks[checks[mode]]
                summary[mode+'_count'] = len(subset)
                if not subset.empty:
                    chosen = subset.assign(delta_distance=(subset.delta-.04).abs()).sort_values(
                        ['dte', 'delta_distance', 'quote_width', 'strike']).iloc[0]
                    for field in ['expiry', 'strike', 'delta', 'otm_pct', 'bid', 'ask', 'oi',
                                  'wing_mid_excess_points', 'wing_bid_excess_points']:
                        summary[mode+'_'+field] = chosen[field]
                    if (mode == 'all_original_contract_gates' and row.original_surface_pass
                            and not original_pass):
                        exact_chain = chain[chain.ticker.eq(row.ticker)
                                            & chain.expirDate.eq(chosen.expiry)]
                        wing = exact_chain[exact_chain.strike.eq(chosen.strike)].iloc[0]
                        nearer = exact_chain[exact_chain.strike.eq(chosen.nearer_strike)].iloc[0]
                        record = contract_record(
                            wing, nearer, leg1_action='STO', leg2_action='BTO',
                            entry_cash=chosen.bid, target_leg2_price=max(chosen.bid-.1, .1),
                            contract_wing_iv_points=chosen.wing_mid_excess_points,
                            event_inside_expiry=False, confirmed=True, reasons=[],
                        )
                        record.update(tradeDate=day, ticker=row.ticker,
                                      scenario='sell-first call grab',
                                      selection_audit='alternative passed unchanged contract gates',
                                      frozen_selected_strike=selected.leg1_strike,
                                      frozen_selected_expiry=selected.expiry,
                                      frozen_selected_failure=selected.failure_reason,
                                      hiro_status='alternative contract not yet replayed')
                        for leg, item in [(1, wing), (2, nearer)]:
                            record[f'leg{leg}_option_delta'] = item.delta
                            record[f'leg{leg}_orats_call_coordinate_delta'] = item.delta
                            record[f'leg{leg}_stock_price'] = item.stockPrice
                            record[f'leg{leg}_otm_pct'] = (item.strike/item.stockPrice-1)*100
                        record['delta_basis'] = 'ORATS call model delta'
                        replacements.append(record)
            summaries.append(summary)
    full = pd.concat(results, ignore_index=True)
    summary = pd.DataFrame(summaries)
    full.to_csv(AUDIT / 'every_contract_check.csv', index=False)
    summary.to_csv(AUDIT / 'ticker_day_exclusion_summary.csv', index=False)
    pd.DataFrame(replacements).to_csv(AUDIT / 'recovered_original_rule_contracts.csv', index=False)
    pd.DataFrame(provenance).to_csv(AUDIT / 'chain_sources.csv', index=False)
    for restricted in [True, False]:
        sample = summary[summary.original_surface_pass] if restricted else summary
        print('Original surface only' if restricted else 'Including surface exclusions', len(sample), flush=True)
        for mode in ['all_original_contract_gates', 'without_delta_band', 'without_absolute_width']:
            passes = sample[sample[mode+'_count'].gt(0)]
            print(mode, len(passes), 'ticker/dates;', passes.ticker.nunique(), 'tickers:',
                  ','.join(sorted(passes.ticker.unique())), flush=True)
    print(summary[summary.original_surface_pass & ~summary.original_selected_pass
                  & summary.all_original_contract_gates_count.gt(0)].to_string(index=False), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch', action='store_true')
    parser.add_argument('--analyze', action='store_true')
    args = parser.parse_args()
    candidates = surface_inventory()
    print('One-sided-grab surface:', len(candidates), 'ticker/dates;', candidates.ticker.nunique(),
          'stocks; original surface passes:', candidates.original_surface_pass.sum(), flush=True)
    if args.fetch:
        fetch(candidates)
    if args.analyze:
        analyze(candidates)
