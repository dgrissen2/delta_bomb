"""Publish the frozen inventory's eligibility and exact-leg surface audit, without rescanning."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from pandar_quote_history import OUTPUT, SOURCE

CALL = 'sell-first call grab'
PUT = 'buy-first put-tail inventory'
REPORT = OUTPUT / 'pandar_trade_eligibility_and_leg_timing.md'
BEGIN = '<!-- BEGIN ELIGIBILITY AUDIT -->'
END = '<!-- END ELIGIBILITY AUDIT -->'
DATASETS = {
    '2026-08-11_to_2026-08-27_call_scan': SOURCE.parent / 'hiro_daily_2026-08-11_to_2026-08-27',
    '2026-08-24_to_2026-09-02_four_method_scan': SOURCE.parent / 'hiro_daily_four_methods_2026-08-24_to_2026-09-02',
    '2026-09-03_pandar_only_gap_scan': SOURCE / 'gap_2026-09-03',
}


def contract_metrics(chain: pd.DataFrame, ticker: str, day: str, expiry: str,
                     strike: float, side: str) -> dict:
    """Use exact contract identity; convert ORATS call-coordinate delta for put display."""
    selected = chain[chain.ticker.eq(ticker) & chain.tradeDate.str[:10].eq(day)
                     & chain.expirDate.eq(expiry) & chain.strike.eq(strike)]
    if len(selected) != 1:
        raise ValueError(f'Expected exactly one {ticker} {day} {expiry} {strike} {side}')
    row = selected.iloc[0]
    if row.stockPrice <= 0 or not 0 <= row.delta <= 1:
        raise ValueError('Invalid stock price or call-coordinate delta')
    if side not in {'put', 'call'}:
        raise ValueError(f'Invalid option side: {side}')
    sign = 1 if side == 'call' else -1
    return dict(stock_price=row.stockPrice, otm_pct=sign*(strike/row.stockPrice-1)*100,
                orats_call_coordinate_delta=row.delta,
                option_delta=row.delta if side == 'call' else row.delta-1)


def source_hash(path: Path) -> dict:
    """Record immutable input identity without credentials."""
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def enrich() -> pd.DataFrame:
    """Add original surface fields and both confirmed contracts; preserve master rows."""
    master_path = SOURCE / 'pandar_approved_master.csv'
    master = pd.read_csv(master_path)
    master.insert(0, 'inventory_row_id', np.arange(1, len(master)+1))
    provenance = [source_hash(master_path)]
    parts = []
    for dataset, directory in DATASETS.items():
        all_path = directory / 'single_name_call_screen_all.parquet'
        check_path = directory / 'single_name_call_screen_chain_checks.csv'
        provenance += [source_hash(all_path), source_hash(check_path)]
        features = pd.read_parquet(all_path)
        features.tradeDate = pd.to_datetime(features.tradeDate).dt.strftime('%Y-%m-%d')
        rows = master[master.source_dataset.eq(dataset)]
        fields = ['tradeDate', 'ticker'] + [c for c in features if c not in master]
        rows = rows.merge(features[fields], on=['tradeDate', 'ticker'], how='left',
                          validate='many_to_one', indicator=True)
        if not rows._merge.eq('both').all():
            raise ValueError('Unmatched surface feature row')
        rows = rows.drop(columns='_merge')
        checks = pd.read_csv(check_path)
        checks.scenario = checks.scenario.replace({'sell-first': CALL})
        fields = ['tradeDate', 'ticker', 'scenario', 'contract_wing_iv_points',
                  'event_inside_expiry']
        rows = rows.merge(checks[fields], on=['tradeDate', 'ticker', 'scenario'],
                          how='left', validate='one_to_one')
        parts.append(rows)
    master = pd.concat(parts).sort_values('inventory_row_id').reset_index(drop=True)
    contract_cache = OUTPUT / 'data/screen_selected_contracts.csv'
    cache_rows = pd.read_csv(contract_cache) if contract_cache.exists() else pd.DataFrame()
    contracts = []
    for index, row in master[master.chain_confirmed].iterrows():
        side = 'call' if row.scenario == CALL else 'put'
        if not cache_rows.empty:
            chain = cache_rows
        elif side == 'call':
            path = OUTPUT / 'data/richness/mstr_chains' / f'{row.tradeDate}.json.gz'
            chain = pd.DataFrame(json.load(gzip.open(path, 'rt')))
            provenance.append(source_hash(path))
        else:
            root = Path('/private/tmp/delta_bomb_pandar_approved_20260904' if
                        row.tradeDate == '2026-09-03' else
                        '/private/tmp/delta_bomb_single_name_four_method_20260903')
            frames = []
            for kind in ('hist_strikes', 'hist_strikes_put_tail'):
                candidates = [p for p in (root / kind / row.tradeDate).glob('*.json.gz')
                              if row.ticker in p.name.split('.')[0].split('-')]
                if len(candidates) != 1:
                    raise ValueError(f'Missing or ambiguous raw chain: {row.tradeDate} {row.ticker}')
                path = candidates[0]
                frames.append(pd.DataFrame(json.load(gzip.open(path, 'rt'))))
                provenance.append(source_hash(path))
            chain = pd.concat(frames).drop_duplicates()
        for leg in (1, 2):
            strike = row[f'leg{leg}_strike']
            metrics = contract_metrics(chain, row.ticker, row.tradeDate, row.expiry, strike, side)
            if not np.isclose(metrics['stock_price'], row.stockPrice, atol=.0001):
                raise ValueError('Chain and qualification stock prices disagree')
            if leg == 1 and not np.isclose(metrics['orats_call_coordinate_delta'],
                                            row.leg1_delta, atol=1e-8):
                raise ValueError('Recovered first-leg delta disagrees with master')
            for name, value in metrics.items():
                master.loc[index, f'leg{leg}_{name}'] = value
            if cache_rows.empty:
                contracts.append(chain[chain.ticker.eq(row.ticker)
                                       & chain.tradeDate.str[:10].eq(row.tradeDate)
                                       & chain.expirDate.eq(row.expiry) & chain.strike.eq(strike)])
        master.loc[index, 'delta_basis'] = ('ORATS call model delta' if side == 'call'
                                           else 'ORATS call delta minus one; put approximation')
    if cache_rows.empty:
        pd.concat(contracts).drop_duplicates(['ticker', 'tradeDate', 'expirDate', 'strike'])\
            .to_csv(contract_cache, index=False)
        pd.DataFrame(provenance).drop_duplicates('path').to_csv(
            OUTPUT / 'eligibility_sources.csv', index=False)
    audit = pd.read_csv(OUTPUT / 'entry_eligibility_audit.csv')
    master = master.merge(audit, on=['tradeDate', 'ticker', 'scenario'], how='left',
                          validate='one_to_one').sort_values('inventory_row_id')
    richness = pd.read_csv(OUTPUT / 'mstr_matched_strike_richness.csv')
    richness = richness[richness['mode'].eq('delta')]
    fields = ['tradeDate', 'ticker', 'bid_excess_z', 'bid_excess_n', 'bid_excess_percentile']
    master = master.merge(richness[fields], on=['tradeDate', 'ticker'], how='left',
                          validate='many_to_one')
    assert len(master) == 917 and master.chain_confirmed.sum() == 81
    confirmed = master[master.chain_confirmed]
    assert confirmed.leg2_option_delta.notna().all()
    master.to_csv(OUTPUT / 'pandar_eligibility_enriched.csv', index=False)
    confirmed.to_csv(OUTPUT / 'pandar_exact_legs_enriched.csv', index=False)
    return master


def fmt(value: object, precision: int = 1) -> str:
    """Explicit em dash for unavailable values; never interpret missing as zero."""
    return '—' if pd.isna(value) else f'{value:.{precision}f}'


def table(headers: list[str], rows: list[list]) -> str:
    """Produce portable Markdown with escaped cell delimiters."""
    lines = [headers, ['---']*len(headers), *rows]
    return '\n'.join('| ' + ' | '.join(str(v).replace('|', '/') for v in r) + ' |'
                     for r in lines) + '\n'


def reason(row: pd.Series) -> str:
    """Keep observed rejection reasons distinct from outcomes and Pandar attribution."""
    if row.chain_confirmed:
        if pd.notna(row.get('selection_audit')):
            return '**Alternative passes**; original selected call failed'
        return '**Scanner pass**'
    return str(row.failure_reason).replace('_', ' ')


def daily_table(master: pd.DataFrame) -> str:
    """Label attribution in headers and include the early-put backfill."""
    ledger = pd.read_csv(SOURCE / 'pandar_approved_daily_tickers.csv')
    rows = []
    for day, group in ledger.groupby('tradeDate', sort=True):
        call = group[group.scenario.eq(CALL)].iloc[0]
        current_calls = master[master.tradeDate.eq(day) & master.scenario.eq(CALL)]
        call_passes = ', '.join(sorted(current_calls.loc[current_calls.chain_confirmed, 'ticker']))
        put = group[group.scenario.eq(PUT)].iloc[0].copy()
        early = master[master.tradeDate.eq(day) & master.scenario.eq(PUT)]
        if put.signal_data_status == 'not_in_scope' and not early.empty:
            put['signal_data_status'] = 'backfilled'
            put['surface_count'] = len(early)
            put['exact_chain_tickers'] = ','.join(early.loc[early.chain_confirmed, 'ticker'])
        if call.signal_data_status == 'provider_unavailable':
            rows.append([day, 'Unavailable', 'Unavailable', 'Unavailable', 'Unavailable'])
            continue
        put_count = 'Not scanned' if put.signal_data_status == 'not_in_scope' else put.surface_count
        put_tickers = ('Not scanned' if put.signal_data_status == 'not_in_scope' else
                       str(put.exact_chain_tickers).replace(',', ', '))
        rows.append([day, 'None' if pd.isna(call.surface_tickers) else
                     call.surface_tickers.replace(',', ', '),
                     call_passes or 'None',
                     put_count, put_tickers])
    return table(['Signal date (EOD)', 'Call surface candidates (original project screen)',
                  'Call-sale core: exact 2–6Δ passes (Pandar-approved mechanism)',
                  'Put surface count (project screen)',
                  'Put inventory: exact passes (Pandar-approved core)'], rows)


def render_tables(master: pd.DataFrame) -> dict[str, str]:
    """Build compact main-report tables and a complete daily surface appendix."""
    calls = master[master.scenario.eq(CALL)].sort_values(['tradeDate', 'ticker'])
    put_confirmed = master[master.scenario.eq(PUT) & master.chain_confirmed]
    call_rows, call_legs, put_tables, full = [], [], [], []
    for _, r in calls.iterrows():
        call_rows.append([r.tradeDate, r.ticker, fmt(r.ivRank1y), fmt(r.rr25_pct252),
                          fmt(r.callskew_pct252), fmt(r.call_wing_10_pct252),
                          fmt(r.call_kink_pct252), reason(r)])
        if r.chain_confirmed:
            call_legs.append([r.tradeDate, r.ticker, r.expiry, int(r.dte),
                              f'{r.leg1_strike:g} / {r.leg2_strike:g}',
                              f'{fmt(r.leg1_otm_pct)} / {fmt(r.leg2_otm_pct)}',
                              f'{fmt(r.leg1_option_delta*100, 2)} / {fmt(r.leg2_option_delta*100, 2)}',
                              f'${r.leg1_bid:.2f} / ${r.leg1_ask:.2f}',
                              fmt(r.contract_wing_iv_points, 2),
                              str(r.hiro_status).replace('_', ' ')])
    for day, group in put_confirmed.groupby('tradeDate', sort=True):
        rows = []
        for _, r in group.sort_values('ticker').iterrows():
            rows.append([r.ticker, fmt(r.ivRank1y), fmt(r.rr25_pct252), fmt(r.putskew_pct252),
                         r.expiry, int(r.dte), f'{r.leg1_strike:g} / {r.leg2_strike:g}',
                         f'{fmt(r.leg1_otm_pct)} / {fmt(r.leg2_otm_pct)}',
                         f'{fmt(r.leg1_option_delta*100, 3)} / {fmt(r.leg2_option_delta*100, 3)}',
                         f'${r.entry_cash:.2f}'])
        put_tables.append(f'\n**{day} — {len(group)} put-tail scanner passes**\n\n' +
                          table(['Ticker', 'IVR', 'Local RR rank', 'Put-skew rank', 'Expiry',
                                 'DTE', 'Buy / sell strike', '% OTM buy / sell',
                                 'Approx. option Δ buy / sell (×100)', 'Screen debit'], rows))
    for day, group in master.groupby('tradeDate', sort=True):
        full.append(f'\n## {day}\n')
        rows = []
        for _, r in group.sort_values(['scenario', 'ticker']).iterrows():
            rows.append([r.ticker, 'Call grab' if r.scenario == CALL else 'Put inventory',
                         fmt(r.ivRank1y), fmt(r.rr25_pct252), fmt(r.callskew_pct252),
                         fmt(r.putskew_pct252), fmt(r.call_wing_10_pct252),
                         fmt(r.call_kink_pct252), reason(r)])
        full.append(table(['Ticker', 'Project screen', 'IVR', 'Local RR rank', 'Call-skew rank',
                           'Put-skew rank', 'Front call-wing rank', 'Kink rank', 'Exact-chain result'],
                          rows))
    (OUTPUT / 'pandar_all_daily_surface_candidates.md').write_text(
        '# Every daily surface candidate and exact-chain result\n\n'
        f'All {len(master):,} rows including the early-put backfill; thresholds are project '
        'screen rules, not Pandar prescriptions. '
        'A failed selected contract does not establish that every strike or expiry failed. '
        'Ranks use qualification-day EOD data. See the '
        '[main report](pandar_trade_eligibility_and_leg_timing.md) for definitions, original '
        'coverage gaps, Greeks, timing and P&L. Put rows now begin August 11; September 4 '
        'qualification data were unavailable.\n' + '\n'.join(full))
    return dict(daily=daily_table(master), calls=table(
        ['Date', 'Ticker', 'IVR', 'Local RR rank', 'Call-skew rank', 'Front-wing rank',
         'Kink rank', 'Selected-contract result'], call_rows),
        call_legs=table(['Signal date', 'Ticker', 'Expiry', 'DTE', 'Sell / buy strike',
                         '% OTM sell / buy', 'Option Δ sell / buy (×100)',
                         'Short bid / ask', 'Selected mid-IV − ATM (pts)', 'Next-session HIRO'],
                        call_legs), puts='\n'.join(put_tables))


def richness_table() -> str:
    """Include all six call confirmations, not just the two profitable cases."""
    richness = pd.read_csv(OUTPUT / 'mstr_matched_strike_richness.csv')
    rows = []
    for _, r in richness[richness['mode'].eq('delta')].iterrows():
        otm = richness[richness.tradeDate.eq(r.tradeDate) & richness['mode'].eq('log_otm')].iloc[0]
        rows.append([r.tradeDate, f'{r.strike:g}C', fmt(r.target_delta*100, 2),
                     fmt(r.target_otm_pct), int(r.vendor_dte), fmt(r.bid_iv_pct, 2),
                     fmt(r.atm_mid_iv_pct, 2), fmt(r.bid_excess_iv_points, 2),
                     int(r.bid_excess_n), f'**{r.bid_excess_z:+.2f}**',
                     fmt(r.bid_excess_percentile), f'{int(otm.bid_excess_n)}; no z'])
    return table(['Signal date', 'Sell strike', 'Δ (×100)', '% OTM', 'DTE', 'Bid IV %',
                  'ATM mid IV %', 'Tail excess (pts)', 'Valid n / 60', 'Delta/DTE z',
                  'Historical percentile', 'OTM/DTE history'], rows)


def execution_table() -> str:
    """Actual-time provider Greek snapshots for the original dime-target HIRO paths."""
    greeks = pd.read_csv(OUTPUT / 'actual_execution_greeks.csv')
    rows, contexts = [], []
    feature_path = DATASETS['2026-08-11_to_2026-08-27_call_scan'] / 'single_name_call_screen_all.parquet'
    features = pd.read_parquet(feature_path)
    features.tradeDate = pd.to_datetime(features.tradeDate).dt.strftime('%Y-%m-%d')
    for _, r in greeks.iterrows():
        rows.append([r.signal_date, pd.Timestamp(r.timestamp).strftime('%b %d %H:%M'),
                     f'{"Sell" if r.leg == 1 else "Buy"} {r.strike:g}C',
                     f'${r.stock:.2f}', fmt(r.otm_pct, 2), fmt(r.delta*100, 2),
                     fmt(r.implied_vol_pct, 2), f'${r.bid:.2f} / ${r.ask:.2f}'])
        prior = features[features.ticker.eq(r.ticker)
                         & features.tradeDate.lt(str(r.timestamp)[:10])].sort_values('tradeDate')
        if prior.empty:
            raise ValueError('Missing prior EOD surface context for execution')
        prior = prior.iloc[-1]
        contexts.append(dict(signal_date=r.signal_date, timestamp=r.timestamp,
                             leg=r.leg, strike=r.strike, **{k: prior[k] for k in
                             ['tradeDate', 'ivRank1y', 'rr25_pct252', 'callskew_pct252',
                              'call_wing_10_pct252', 'call_kink_pct252']}))
    pd.DataFrame(contexts).to_csv(OUTPUT / 'execution_surface_context.csv', index=False)
    context_rows = [[pd.Timestamp(r['timestamp']).strftime('%b %d %H:%M'),
                     f'{"Sell" if r["leg"] == 1 else "Buy"} {r["strike"]:g}C',
                     r['tradeDate'], *[fmt(r[k], 2) for k in
                     ['ivRank1y', 'rr25_pct252', 'callskew_pct252',
                      'call_wing_10_pct252', 'call_kink_pct252']]] for r in contexts]
    return table(['Signal date', 'Leg time (ET)', 'Contract, Aug 28 expiry', 'Stock', '% OTM',
                  'Option Δ (×100)', 'Theta IV %', 'Bid / ask'], rows) + (
        '\nThe latest available **prior-session EOD ranks** at each leg were:\n\n') + table(
        ['Leg time (ET)', 'Leg', 'Rank observation date', 'IVR', 'Local RR rank',
         'Call-skew rank', 'Front-wing rank', 'Kink rank'], context_rows)


def main() -> None:
    """Replace one generated block while retaining the frozen P&L report verbatim."""
    master = enrich()
    early_path = OUTPUT / 'early_put_backfill/all_chain_checks.csv'
    if early_path.exists():
        early = pd.read_csv(early_path)
        if not early.tradeDate.between('2026-08-11', '2026-08-21').all():
            raise ValueError('Backfill escaped its intended dates')
        if not early.scenario.eq(PUT).all():
            raise ValueError('Backfill includes a different strategy')
        early['inventory_row_id'] = np.arange(len(master)+1, len(master)+len(early)+1)
        for field in ['pandar_approval_scope', 'pandar_direct_portion', 'project_derived_portion']:
            early[field] = master.loc[master.scenario.eq(PUT), field].iloc[0]
        early['delta_basis'] = 'ORATS call delta minus one; put approximation'
        master = pd.concat([master, early], ignore_index=True)
        if master.duplicated(['tradeDate', 'ticker', 'scenario']).any():
            raise ValueError('Backfill overlaps the frozen inventory')
    alternative_path = OUTPUT / 'call_exclusion_audit/recovered_original_rule_contracts.csv'
    if alternative_path.exists():
        alternatives = pd.read_csv(alternative_path)
        extra_fields = [field for field in alternatives if field not in master]
        master = pd.concat([master, pd.DataFrame(index=master.index, columns=extra_fields)],
                           axis=1).copy()
        for row in alternatives.to_dict('records'):
            match = (master.tradeDate.eq(row['tradeDate']) & master.ticker.eq(row['ticker'])
                     & master.scenario.eq(CALL))
            if match.sum() != 1 or master.loc[match, 'chain_confirmed'].any():
                raise ValueError('Alternative must replace exactly one failed original selection')
            for field, value in row.items():
                master.loc[match, field] = value
    master.to_csv(OUTPUT / 'pandar_eligibility_complete_window.csv', index=False)
    master[master.chain_confirmed].to_csv(OUTPUT / 'pandar_exact_legs_complete_window.csv', index=False)
    tables = render_tables(master)
    template = (OUTPUT / 'eligibility_explanation.template.md').read_text()
    new = master[master.source_dataset.eq('early_put_backfill_2026-08-11_to_2026-08-21')]
    replacements = dict(**tables, richness=richness_table(), executions=execution_table(),
                        expanded_call_search=(OUTPUT / 'call_search_expansion/expanded_call_search.md').read_text(),
                        total_rows=f'{len(master):,}', total_exact=str(int(master.chain_confirmed.sum())),
                        put_rows=f'{int(master.scenario.eq(PUT).sum()):,}',
                        put_exact=str(int((master.scenario.eq(PUT) & master.chain_confirmed).sum())),
                        call_exact=str(int((master.scenario.eq(CALL) & master.chain_confirmed).sum())),
                        early_rows=f'{len(new):,}', early_exact=str(int(new.chain_confirmed.sum())))
    for key, value in replacements.items():
        template = template.replace('{{' + key + '}}', value)
    if '{{' in template:
        raise ValueError('Unresolved report template field')
    report = REPORT.read_text()
    block = BEGIN + '\n' + template.strip() + '\n' + END + '\n\n'
    if BEGIN in report:
        start, after = report.split(BEGIN, 1)
        _, tail = after.split(END, 1)
        report = start + block + tail.lstrip('\n')
    else:
        title, rest = report.split('\n', 1)
        report = title + '\n\n' + block + rest.lstrip('\n')
    REPORT.write_text(report)
    print(f'Updated {REPORT}; {len(master)} surface rows, {master.chain_confirmed.sum()} exact rows')


if __name__ == '__main__':
    main()
