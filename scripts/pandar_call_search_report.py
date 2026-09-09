"""Render all broadened call selections and the controlled delta comparison."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from pandar_call_search_expansion import BANDS, EXPANSION
from pandar_eligibility import fmt, table
from pandar_leg_timing import CUTOFF, at, shift
from pandar_quote_history import OUTPUT, SOURCE


def hiro_coverage(chosen: pd.DataFrame) -> pd.DataFrame:
    """Verify existing All Trades captures; availability does not imply a trade trigger."""
    selected = {}
    tickers = set(chosen.ticker)
    for path in sorted(SOURCE.parent.glob('*/hiro_ticker*/manifest.json')):
        manifest = json.loads(path.read_text())
        for ticker, record in manifest.get('tickers', {}).items():
            if ticker not in tickers:
                continue
            captured = record.get('captured_at_utc', manifest['created_at_utc'])
            for day, item in record.get('sessions', {}).items():
                if item['status'] != 'success' or day > CUTOFF:
                    continue
                file = Path(item['series_csv'])
                key = ticker, day
                if file.exists() and (key not in selected or captured > selected[key][0]):
                    selected[key] = captured, file
    requested = {(r.ticker, shift(r.tradeDate, offset))
                 for r in chosen.itertuples() for offset in range(4)}
    sources, lookup = [], {}
    for (ticker, day), (captured, path) in sorted(selected.items()):
        if (ticker, day) not in requested:
            continue
        frame = pd.read_csv(path)
        frame = frame[frame.series_group.eq('all')].copy()
        frame.index = pd.to_datetime(frame.utc_iso, utc=True).dt.tz_convert('America/New_York')
        frame = frame[(frame.index >= at(day, '09:30')) & (frame.index <= at(day, '16:00'))]
        valid = frame[['delta_total', 'delta_call', 'delta_put', 'stock_price']].notna().all(axis=1)
        if not frame.index.is_unique or not np.allclose(
                frame.loc[valid, 'delta_total'],
                frame.loc[valid, 'delta_call'] + frame.loc[valid, 'delta_put'], atol=.01):
            raise ValueError(f'Invalid HIRO capture: {path}')
        lookup[ticker, day] = int(valid.sum())
        sources.append(dict(ticker=ticker, session_date=day, captured=captured,
            valid_rth_points=int(valid.sum()), first=str(frame.index.min()),
            last=str(frame.index.max()), path=str(path),
            sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    result = chosen.copy()
    for offset, label in enumerate(['signal', 'entry', 'entry_plus1', 'entry_plus2']):
        result[f'hiro_{label}_day'] = [shift(day, offset) for day in result.tradeDate]
        result[f'hiro_{label}_points'] = [lookup.get((r.ticker, shift(r.tradeDate, offset)), 0)
                                         for r in result.itertuples()]
        result[f'hiro_{label}_status'] = np.where(result[f'hiro_{label}_day'].gt(CUTOFF),
            'beyond frozen cutoff', np.where(result[f'hiro_{label}_points'].gt(0),
            'verified existing capture', 'no verified capture in frozen archive'))
    pd.DataFrame(sources).to_csv(EXPANSION / 'hiro_capture_sources.csv', index=False)
    return result


def main() -> None:
    """Publish evidence without conflating broad discovery, history, or replay coverage."""
    selected = pd.read_csv(EXPANSION / 'selected_by_delta_band.csv')
    summary = pd.read_csv(EXPANSION / 'band_summary.csv')
    surface = pd.read_csv(EXPANSION / 'surface_candidates.csv')
    coverage = pd.read_csv(EXPANSION / 'coverage.csv')
    chosen = selected[selected.band.eq('2–10')].copy()
    history = pd.read_csv(OUTPUT / 'mstr_matched_strike_richness.csv')
    history = history[history['mode'].eq('delta')]
    chosen = chosen.merge(history[['tradeDate', 'ticker', 'expiry', 'strike',
                                   'bid_excess_z', 'bid_excess_n']],
                          on=['tradeDate', 'ticker', 'expiry', 'strike'], how='left',
                          validate='one_to_one')
    chosen['both_bid_richness_diagnostics'] = (chosen.wing_bid_excess_points.ge(2)
        & chosen.front_bid_minus_deferred_mid_points.gt(0))
    chosen['history_status'] = np.where(chosen.bid_excess_z.notna(),
        'existing prior-60-session matched-delta/DTE study; interpolated ATM basis',
        'exact strike matched-history z-score not calculated')
    chosen['timing_status'] = np.where(chosen.bid_excess_z.notna(),
        'original MSTR cohort; see frozen replay coverage/results',
        'new selection has not received HIRO/minute-quote replay')
    chosen = hiro_coverage(chosen)
    if chosen.duplicated(['tradeDate', 'ticker']).any() or len(coverage) != len(surface):
        raise ValueError('Expanded research population does not reconcile')
    chosen.to_csv(EXPANSION / 'call_candidates_2_to_10_delta.csv', index=False)
    comparisons = []
    for low, high in BANDS:
        band = f'{low}–{high}'
        records = summary[summary.band.eq(band)].set_index('scope')
        comparisons.append([band, *[
            f'{int(records.loc[scope, "ticker_days"])} / {int(records.loc[scope, "stocks"])}'
            for scope in ['original_surface', 'grab_surface', 'rich_front_wing']],
            f'{int(records.loc["rich_front_wing", "front_5_12"])} / '
            f'{int(records.loc["rich_front_wing", "fallback_13_19"])}'])
    bands = table(['Delta band (×100)', 'Original surface: dates / names',
                   'Grab surface: dates / names', 'Rich-front discovery: dates / names',
                   'Rich-front selections: 5–12 / 13–19 DTE'], comparisons)
    daily_rows = []
    days = set(surface.tradeDate)
    for day in pd.bdate_range('2026-08-11', '2026-09-04').strftime('%Y-%m-%d'):
        if day not in days:
            daily_rows.append([day, 'Unavailable', 'Unavailable', 'Unavailable', 'Unavailable'])
            continue
        group = chosen[chosen.tradeDate.eq(day)]
        daily_rows.append([day, int(surface.tradeDate.eq(day).sum()),
                           ', '.join(group.loc[group.dte.le(12), 'ticker']) or 'None',
                           ', '.join(group.loc[group.dte.gt(12), 'ticker']) or 'None',
                           ', '.join(group.loc[group.both_bid_richness_diagnostics, 'ticker'])
                           or 'None'])
    daily = table(['Signal date (EOD)', 'Rich-front stock-days checked',
                   '2–10Δ quote passes: 5–12 DTE', '2–10Δ quote passes: 13–19 DTE',
                   'Selected calls passing both bid-richness diagnostics'], daily_rows)
    appendix = [
        '# Expanded call discovery: every selected 2–10-delta candidate',
        'This is a broader **project research screen**, not individual Pandar approvals or '
        'a profit table. All ranks and quotes are signal-day EOD observations, available '
        'for prospective use from the next session. The original surface and '
        '2–6-delta cohort remain separately reproducible in the main report.',
        'Ranks in each cell are **IV Rank / local RR rank / front-wing rank / kink rank**. '
        'Local RR uses put IV minus call IV. Richness values are **sold call bid IV minus '
        'same-expiry ATM mid IV / sold call bid IV minus deferred matched-delta mid IV**, '
        'in volatility points. Deferred means the first supported listed expiry at '
        '20–30 vendor DTE; its event estimate is shown. These are current cross-sectional '
        'comparisons, not historical z-scores. The full CSV contains the prospective '
        'nearer long strike, its delta, % OTM and quotes; it does not imply that leg was bought.',
        '[Full contract/rank CSV](call_candidates_2_to_10_delta.csv) · '
        '[Every band](selected_by_delta_band.csv) · [All discovery rows](surface_candidates.csv) · '
        '[All contract checks](every_contract_check.csv) · [Coverage](coverage.csv)',
    ]
    for day, group in chosen.groupby('tradeDate', sort=True):
        rows = []
        for r in group.itertuples():
            contract = (f'{r.expiry} **{r.strike:g}C**; {int(r.dte)} DTE; '
                        f'**{r.delta*100:.2f}Δ**, {r.otm_pct:.2f}% OTM; '
                        f'${r.bid:.2f}/${r.ask:.2f}')
            ranks = ' / '.join(fmt(getattr(r, field), 2) for field in
                ['ivRank1y', 'rr25_pct252', 'call_wing_10_pct252', 'call_kink_pct252'])
            richness = f'{r.wing_bid_excess_points:+.2f} / '
            richness += (f'{r.front_bid_minus_deferred_mid_points:+.2f}'
                         if pd.notna(r.front_bid_minus_deferred_mid_points) else 'unavailable')
            if pd.notna(r.deferred_event_inside_estimate) and r.deferred_event_inside_estimate:
                richness += '; **deferred includes estimated earnings**'
            richness += (f'; history z {r.bid_excess_z:+.2f} (n={int(r.bid_excess_n)})'
                         if pd.notna(r.bid_excess_z) else '; history z unavailable')
            delta_note = '; sold-call delta >6' if r.delta > .06 else ''
            rows.append([r.ticker, contract, ranks, richness,
                         r.original_surface_exclusions + delta_note])
        appendix += [f'## {day}', table(['Ticker', 'Selected short call / bid–ask',
            'Ranks: IVR / RR / front / kink', 'Bid-IV richness: ATM / deferred',
            'Original project exclusions'], rows)]
    (EXPANSION / 'expanded_call_candidate_tables.md').write_text('\n\n'.join(appendix)+'\n')
    content = (EXPANSION / 'expanded_call_search.template.md').read_text()
    content = content.replace('{{bands}}', bands).replace('{{daily}}', daily)
    entry_available = chosen.hiro_entry_points.gt(0)
    rich_available = chosen.both_bid_richness_diagnostics & entry_available
    followthrough = chosen.hiro_entry_plus1_points.gt(0) & chosen.hiro_entry_plus2_points.gt(0)
    hiro_rows = [[r.tradeDate, r.ticker, r.hiro_entry_day,
                  r.hiro_entry_plus1_status, r.hiro_entry_plus2_status]
                 for r in chosen[rich_available].itertuples()]
    hiro = (f'**{int(entry_available.sum())} of 73** selections have verified existing '
            f'All Trades HIRO on the next-session entry day. **{int(rich_available.sum())}** '
            f'also pass both bid-richness diagnostics; **{int((rich_available & followthrough).sum())}** '
            'of those have captures for entry and both following sessions. The table '
            'below lists that 13-row intersection. Capture availability is not a '
            'HIRO trigger, complete minute-quote coverage, or a profitable trade. '
            'The CSV retains signal-day and next-three-session status for all 73; '
            'later dates beyond September 4 are censored, not missing-market claims.\n\n'
            + table(['Signal EOD', 'Ticker', 'Next-session entry: HIRO verified',
                     'Entry +1 session', 'Entry +2 sessions'], hiro_rows)
            + '\n[Verified HIRO capture paths, time coverage and hashes]'
              '(call_search_expansion/hiro_capture_sources.csv).\n')
    content = content.replace('{{hiro}}', hiro)
    if '{{' in content:
        raise ValueError('Unresolved report placeholder')
    (EXPANSION / 'expanded_call_search.md').write_text(content)
    print(f'Published {len(chosen)} candidates; '
          f'{chosen.both_bid_richness_diagnostics.sum()} pass both bid-richness diagnostics')


if __name__ == '__main__':
    main()
