"""E-PNDR-013: cache-only exact-call economics, with frozen contracts and quote sides."""
from __future__ import annotations

import gzip
import hashlib
import json
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'outputs/pandar_no_hiro_exact_2026-09-08'
SURFACE = ROOT / 'outputs/pandar_no_hiro_2026-09-08'
CACHE = ROOT / 'docs/replay/pandar_skew_journey_2026-09-06'
PROTOCOL = ROOT / 'hypothesis_tracking/pandar_no_hiro_exact_protocol_2026-09-08.md'
INVENTORY = SURFACE / 'exact_chain_cache_inventory.csv'
PRIOR_SIX = {'CRM', 'DIS', 'MRVL', 'ORCL', 'PLTR', 'QCOM'}
NUMERIC = ['strike', 'stockPrice', 'callBidPrice', 'callAskPrice', 'callBidSize',
           'callAskSize', 'callBidIv', 'callMidIv', 'callAskIv', 'delta', 'gamma', 'vega']
HORIZONS = (2, 4)


def sha256(path: Path) -> str:
    """Hash an exact local input without changing it."""
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, obj: dict | list) -> None:
    """Write standard JSON with explicit nulls for unavailable results."""
    def clean(value):
        if isinstance(value, dict):
            return {str(k): clean(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [clean(v) for v in value]
        if isinstance(value, (np.integer, np.bool_)):
            return value.item()
        if isinstance(value, (float, np.floating)):
            return float(value) if np.isfinite(value) else None
        if isinstance(value, (pd.Timestamp, Path)):
            return str(value)
        return value
    path.write_text(json.dumps(clean(obj), indent=2, allow_nan=False)+'\n')


def valid_quote(row: pd.Series, *, entry: bool = True, date: pd.Timestamp | None = None) -> bool:
    """Validate displayed prices/sizes; exits allow a zero bid but require an ask."""
    fields = ['callBidPrice', 'callAskPrice', 'callAskSize']
    if entry:
        fields += ['callBidSize', 'callBidIv', 'callMidIv', 'callAskIv']
    if any(not np.isfinite(row.get(k, np.nan)) for k in fields):
        return False
    if date is not None:
        stamp = pd.to_datetime(row.get('quoteDate'), utc=True, errors='coerce')
        if pd.isna(stamp) or stamp.tz_convert('America/New_York').date() != date.date():
            return False
    return bool(row.callAskPrice >= row.callBidPrice >= 0 and row.callAskPrice > 0
                and row.callAskSize >= 1 and (not entry or (
                    row.callBidPrice > 0 and row.callBidSize >= 1
                    and min(row.callBidIv, row.callMidIv, row.callAskIv) > 0)))


def spot_atm_iv(chain: pd.DataFrame, spot: float,
                date: pd.Timestamp | None = None) -> tuple[float, str]:
    """Interpolate the immediate spot bracket, never skipping an invalid neighbor."""
    x = chain.sort_values('strike')
    if not np.isfinite(spot) or spot <= 0 or x.empty:
        return np.nan, 'spot_atm_missing_spot_or_chain'
    exact = x[x.strike.eq(spot)]
    if len(exact) > 1:
        return np.nan, 'spot_atm_duplicate_exact_strike'
    if len(exact) == 1:
        row = exact.iloc[0]
        return (float(row.callMidIv), 'exact_spot_strike') if valid_quote(row, date=date) else (
            np.nan, 'spot_atm_invalid_exact_strike')
    lo, hi = x[x.strike.lt(spot)].tail(1), x[x.strike.gt(spot)].head(1)
    if lo.empty or hi.empty:
        return np.nan, 'spot_atm_no_bracket'
    lower, upper = lo.iloc[0], hi.iloc[0]
    if x.strike.eq(lower.strike).sum() > 1 or x.strike.eq(upper.strike).sum() > 1:
        return np.nan, 'spot_atm_duplicate_closest_bracket'
    if not valid_quote(lower, date=date) or not valid_quote(upper, date=date):
        return np.nan, 'spot_atm_invalid_closest_bracket'
    weight = (spot-lower.strike)/(upper.strike-lower.strike)
    return float(lower.callMidIv*(1-weight)+upper.callMidIv*weight), 'interpolated_spot'


def candidate_metrics(chain: pd.DataFrame, date: pd.Timestamp,
                      maximum_exit: pd.Timestamp) -> pd.DataFrame:
    """Calculate all dated candidates vectorially, retaining each rejection reason."""
    x = chain.copy().reset_index(drop=True)
    for column in NUMERIC:
        x[column] = pd.to_numeric(x.get(column, np.nan), errors='coerce')
    x['expirDate'] = pd.to_datetime(x.expirDate, errors='coerce').dt.normalize()
    x['dte'] = (x.expirDate-date).dt.days
    x['spot_atm_iv'] = np.nan
    x['atm_status'] = 'outside_search_envelope'
    envelope = (x.strike.gt(x.stockPrice) & x.dte.between(1, 35)
                & x.expirDate.ge(maximum_exit))
    x['provably_outside_envelope'] = (
        (np.isfinite(x.strike) & np.isfinite(x.stockPrice) & x.strike.le(x.stockPrice))
        | (x.dte.notna() & ~x.dte.between(1, 35))
        | (x.expirDate.notna() & x.expirDate.lt(maximum_exit)))
    stamp = pd.to_datetime(x.get('quoteDate', pd.Series(pd.NaT, index=x.index)),
                           utc=True, errors='coerce', format='mixed')
    session = stamp.dt.tz_convert('America/New_York').dt.tz_localize(None).dt.normalize()
    quote_valid = (x.callAskPrice.ge(x.callBidPrice) & x.callBidPrice.gt(0)
                   & x.callBidSize.ge(1) & x.callAskSize.ge(1)
                   & x[['callBidIv', 'callMidIv', 'callAskIv']].gt(0).all(axis=1))
    quote_valid &= np.isfinite(x[['callBidPrice', 'callAskPrice', 'callBidSize',
                                 'callAskSize', 'callBidIv', 'callMidIv', 'callAskIv']]).all(axis=1)
    quote_valid &= session.eq(date)
    x['kink_mid_points'] = np.nan
    x['kink_bid_vs_mid_points'] = np.nan
    x['kink_bid_vs_ask_points'] = np.nan
    x['kink_status'] = 'unsupported_neighbors'
    for _, expiry in x.groupby('expirDate', dropna=False):
        relevant = expiry[envelope.loc[expiry.index]]
        if relevant.empty:
            continue
        for spot, targets in relevant.groupby('stockPrice'):
            atm, status = spot_atm_iv(expiry, spot, date)
            x.loc[targets.index, 'spot_atm_iv'] = atm
            x.loc[targets.index, 'atm_status'] = status
        ordered = expiry.sort_values('strike')
        lower_strike, upper_strike = ordered.strike.shift(1), ordered.strike.shift(-1)
        lower_ok = quote_valid.loc[ordered.index].shift(1, fill_value=False)
        upper_ok = quote_valid.loc[ordered.index].shift(-1, fill_value=False)
        support = (lower_ok & upper_ok & lower_strike.gt(0)
                   & upper_strike.gt(ordered.strike) & lower_strike.lt(ordered.strike))
        weight = np.log(ordered.strike/lower_strike)/np.log(upper_strike/lower_strike)
        mid = ordered.callMidIv.shift(1)*(1-weight)+ordered.callMidIv.shift(-1)*weight
        ask = ordered.callAskIv.shift(1)*(1-weight)+ordered.callAskIv.shift(-1)*weight
        x.loc[ordered.index, 'kink_mid_points'] = (100*(ordered.callMidIv-mid)).where(support)
        x.loc[ordered.index, 'kink_bid_vs_mid_points'] = (100*(ordered.callBidIv-mid)).where(support)
        x.loc[ordered.index, 'kink_bid_vs_ask_points'] = (100*(ordered.callBidIv-ask)).where(support)
        x.loc[ordered.index[support], 'kink_status'] = 'supported'
    masks = {
        'not_otm': ~x.strike.gt(x.stockPrice),
        'outside_1_35_calendar_dte': ~x.dte.between(1, 35),
        'expiry_before_common_deadline': ~x.expirDate.ge(maximum_exit),
        'duplicate_contract_rows': x.duplicated(['expirDate', 'strike'], keep=False),
        'missing_or_nonfinite_fields': ~np.isfinite(x[NUMERIC].to_numpy()).all(axis=1),
        'missing_expiry_identity': x.expirDate.isna(),
        'invalid_displayed_quote_or_iv': ~quote_valid,
        'invalid_greeks_or_spot': ~(x.delta.gt(0) & x.delta.lt(1) & x.gamma.ge(0)
                                   & x.vega.gt(0) & x.stockPrice.gt(0) & x.strike.gt(0)),
        'quote_timestamp_missing_or_wrong_session': session.ne(date),
    }
    reasons = pd.Series('', index=x.index)
    for reason, mask in masks.items():
        reasons.loc[mask] += reason+';'
    unsupported = envelope & x.spot_atm_iv.isna()
    reasons.loc[unsupported] += x.loc[unsupported, 'atm_status']+';'
    x['candidate_valid'] = reasons.eq('') & envelope & x.spot_atm_iv.notna()
    x['candidate_reasons'] = reasons.str.rstrip(';').replace('', 'valid')
    x['wing_points'] = 100*(x.callBidIv-x.spot_atm_iv)
    x['round_trip_cost'] = 100*(x.callAskPrice-x.callBidPrice)+3.30
    x['scenario_gross_uncapped'] = 100*x.vega*.25*x.wing_points.clip(lower=0)
    x['uncapped_recovery_exceeds_ask'] = x.scenario_gross_uncapped.gt(100*x.callAskPrice)
    x['scenario_gross'] = np.minimum(x.scenario_gross_uncapped, 100*x.callAskPrice)
    x['scenario_iv_decline_points'] = .25*x.wing_points.clip(lower=0)
    x['scenario_iv_decline_fraction_of_bid_iv'] = x.scenario_iv_decline_points/(100*x.callBidIv)
    x['scenario_net'] = x.scenario_gross-x.round_trip_cost
    move = .01*x.stockPrice
    x['rally_loss_1pct'] = 100*(x.delta*move+.5*x.gamma*move**2)
    x['economic_ratio'] = x.scenario_net/x.rally_loss_1pct.where(x.rally_loss_1pct.gt(0))
    x['required_iv_decline'] = x.round_trip_cost/(100*x.vega.where(x.vega.gt(0)))
    x['required_wing_fraction'] = x.required_iv_decline/x.wing_points.where(x.wing_points.gt(0))
    x['otm_pct'] = 100*(x.strike/x.stockPrice-1)
    x['displayed_spread'] = x.callAskPrice-x.callBidPrice
    return x


def choose_contract(candidates: pd.DataFrame, selector: str) -> tuple[dict | None, str]:
    """Apply frozen mechanical or economic ordering without reading any future quote."""
    if candidates.empty:
        return None, 'empty_chain'
    valid = candidates[candidates.candidate_valid].copy()
    if valid.empty:
        return None, 'no_valid_candidates'
    if selector == 'mechanical':
        valid['ten_day_distance'] = (valid.dte-10).abs()
        expiry = valid.sort_values(['ten_day_distance', 'expirDate']).expirDate.iloc[0]
        valid = valid[valid.expirDate.eq(expiry)]
        valid['delta_distance'] = (valid.delta-.10).abs()
        row = valid.sort_values(['delta_distance', 'strike'], ascending=[True, False]).iloc[0]
    elif selector == 'economic':
        if valid.scenario_net.max() <= 0:
            return None, 'no_positive_net_scenario'
        row = valid.sort_values(['economic_ratio', 'displayed_spread', 'expirDate', 'strike'],
                                ascending=[False, True, True, False]).iloc[0]
    else:
        raise ValueError(f'Unknown selector {selector}')
    return row.to_dict(), 'selected'


def fixed_contract_entry(selected: dict, chain: pd.DataFrame, date: pd.Timestamp,
                         maximum_exit: pd.Timestamp, selector: str) -> dict:
    """Recheck the exact selected call. Never replace a missing or failed contract."""
    if chain.empty:
        return dict(entry_status='censored', entry_reason='entry_chain_missing')
    expiry_chain = chain[chain.expirDate.astype(str).str[:10].eq(
        str(pd.Timestamp(selected['expirDate']).date()))]
    if expiry_chain.empty:
        return dict(entry_status='censored', entry_reason='fixed_contract_missing')
    x = candidate_metrics(expiry_chain, date, maximum_exit)
    chosen = x[x.expirDate.eq(pd.Timestamp(selected['expirDate']))
               & x.strike.eq(selected['strike'])]
    if len(chosen) != 1:
        return dict(entry_status='censored', entry_reason='fixed_contract_missing')
    row = chosen.iloc[0]
    out = {f'entry_{k}': v for k, v in row.to_dict().items()}
    if not row.candidate_valid:
        unknown = any(s in row.candidate_reasons for s in [
            'missing', 'no_bracket', 'invalid_closest_bracket', 'duplicate_contract'])
        out.update(entry_status='censored' if unknown else 'no_entry',
                   entry_reason=row.candidate_reasons)
    elif selector == 'economic' and row.scenario_net <= 0:
        out.update(entry_status='no_entry', entry_reason='entry_no_positive_net_scenario')
    else:
        out.update(entry_status='admitted', entry_reason='valid_fixed_contract')
    return out


def no_selection_status(candidates: pd.DataFrame, reason: str) -> str:
    """Distinguish an observable failed screen from unavailable selection measurements."""
    if candidates.empty:
        return 'censored'
    if reason == 'no_positive_net_scenario':
        return 'no_entry'
    potential = candidates[~candidates.provably_outside_envelope]
    unknown = potential.candidate_reasons.str.contains(
        'missing|duplicate|spot_atm_no|spot_atm_invalid', regex=True).any()
    return 'censored' if unknown else 'no_entry'


def nonoverlap(frame: pd.DataFrame) -> pd.Series:
    """Reserve the same earliest input-eligible dates through entry plus four sessions."""
    result = pd.Series(False, index=frame.index)
    for _, group in frame[frame.input_eligible].sort_values(
            ['ticker', 'session_index']).groupby('ticker', sort=False):
        reserved = -1
        for row in group.itertuples():
            if row.session_index > reserved:
                result.loc[row.Index] = True
                reserved = row.session_index+5
    return result


def closing_pnl(entry_bid: float, exit_ask: float) -> float:
    """One assumed standard contract, crossing quotes plus two fees and adverse slippage."""
    return 100*(entry_bid-.01-exit_ask-.01)-1.30


def policy_pnl(entry_status: str, observed_pnl: float) -> float:
    """Only known no-entry is zero; missing entries/exits are not hypothetical winners."""
    if entry_status == 'no_entry':
        return 0.
    return observed_pnl if entry_status == 'admitted' else np.nan


@lru_cache(maxsize=32)
def read_file(path: str) -> pd.DataFrame:
    """Read existing JSON, gzip JSON, or parquet without provider access."""
    file = Path(path)
    if file.suffix == '.parquet':
        return pd.read_parquet(file)
    opener = gzip.open if file.suffix == '.gz' else open
    with opener(file, 'rt') as handle:
        data = json.load(handle)
    if isinstance(data, dict):
        data = data.get('data', data.get('rows', data))
    if not isinstance(data, list):
        raise ValueError(f'Unsupported historical chain envelope: {path}')
    return pd.DataFrame(data)


def read_chain(source: dict | None, ticker: str, date: pd.Timestamp) -> pd.DataFrame:
    """Filter the actual requested identity; never substitute a different date or name."""
    if source is None:
        return pd.DataFrame()
    raw = read_file(source['path'])
    if not {'ticker', 'tradeDate', 'expirDate', 'strike'}.issubset(raw.columns):
        return pd.DataFrame()
    dates = raw.tradeDate.astype(str).str[:10]
    result = raw[raw.ticker.eq(ticker) & dates.eq(str(date.date()))].copy()
    for column in NUMERIC:
        result[column] = pd.to_numeric(result.get(column, np.nan), errors='coerce')
    return result.reset_index(drop=True)


def resolve_sources(inventory: pd.DataFrame) -> pd.DataFrame:
    """Resolve duplicate copies only by the fixed provenance ordering."""
    x = inventory.copy()
    x['central_priority'] = x.source.ne('central_strikes').astype(int)
    x['full_priority'] = (~x.full_diagnostic_fields).astype(int)
    x = x.sort_values(['ticker', 'date', 'central_priority', 'full_priority', 'path'])
    counts = x.groupby(['ticker', 'date']).size().rename('source_copy_count')
    selected = x.drop_duplicates(['ticker', 'date']).merge(counts, on=['ticker', 'date'])
    return selected.drop(columns=['central_priority', 'full_priority'])


def prepare_population(sources: pd.DataFrame) -> tuple[pd.DataFrame, pd.DatetimeIndex, dict]:
    """Use projected signal features, not surface outcomes, and retain all unavailable days."""
    columns = ['ticker', 'tradeDate', 'reference_date', 'session_index', 'quality_valid',
               'quality_earnings_valid', 'signal_earnings_status', 'reference_earnings_status',
               'wing', 'wing_rank', 'age', 'state', 'group', 'known_split_through_exit',
               'split_metadata_status', 'reference_month', 'era']
    frame = pd.read_parquet(SURFACE/'candidate_reason_ledger.parquet', columns=columns)
    prices = pd.read_parquet(CACHE/'dailies.parquet')
    calendar = pd.DatetimeIndex(prices.loc[prices.ticker.eq('SPY'), 'tradeDate'].sort_values())
    lookup = {(r.ticker, str(r.date)): r._asdict() for r in sources.itertuples(index=False)}
    frame['signal_chain_full'] = [bool(lookup.get((r.ticker, str(r.tradeDate.date())), {})
                                      .get('full_diagnostic_fields', False))
                                  for r in frame.itertuples()]
    frame['entry_chain_full'] = [bool(lookup.get((r.ticker, str(r.reference_date.date())), {})
                                     .get('full_diagnostic_fields', False))
                                 if pd.notna(r.reference_date) else False
                                 for r in frame.itertuples()]
    frame['input_eligible'] = (frame.quality_earnings_valid & frame.signal_chain_full
                                & frame.entry_chain_full)
    frame['population_reason'] = ''
    for reason, mask in {
        'signal_daily_quality_failed': ~frame.quality_valid,
        'signal_earnings_not_clear': frame.signal_earnings_status.ne('clear'),
        'entry_earnings_not_clear': frame.reference_earnings_status.ne('clear'),
        'signal_full_chain_unavailable': ~frame.signal_chain_full,
        'entry_full_chain_unavailable': ~frame.entry_chain_full,
    }.items():
        frame.loc[mask, 'population_reason'] += reason+';'
    frame.loc[frame.input_eligible, 'population_reason'] = 'eligible'
    frame['common_nonoverlap'] = nonoverlap(frame)
    frame['outside_prior_six'] = ~frame.ticker.isin(PRIOR_SIX)
    return frame, calendar, lookup


def source_conflict_audit(sources: pd.DataFrame, inventory: pd.DataFrame,
                          keys: set[tuple[str, str]]) -> pd.DataFrame:
    """Flag actual shared-quote differences without changing deterministic source choice."""
    results = []
    candidates = sources[sources.source_copy_count.gt(1)]
    for row in candidates.itertuples():
        if (row.ticker, row.date) not in keys:
            continue
        chosen = read_chain(row._asdict(), row.ticker, pd.Timestamp(row.date))
        others = inventory[inventory.ticker.eq(row.ticker) & inventory.date.eq(row.date)
                           & inventory.path.ne(row.path)]
        for other in others.itertuples():
            alternate = read_chain(other._asdict(), row.ticker, pd.Timestamp(row.date))
            fields = ['callBidPrice', 'callAskPrice', 'stockPrice', 'callBidIv', 'delta']
            if chosen.empty or alternate.empty:
                shared, conflicts = 0, 0
            else:
                a, b = chosen.copy(), alternate.copy()
                for x in [a, b]:
                    x['expirDate'] = x.expirDate.astype(str).str[:10]
                    x.drop_duplicates(['expirDate', 'strike'], inplace=True)
                merged = a[['expirDate', 'strike']+fields].merge(
                    b[['expirDate', 'strike']+fields], on=['expirDate', 'strike'],
                    suffixes=('_chosen', '_other'))
                shared = len(merged)
                different = np.zeros(shared, dtype=bool)
                for field in fields:
                    left, right = merged[field+'_chosen'], merged[field+'_other']
                    comparable = left.notna() & right.notna()
                    different |= comparable & ~np.isclose(left, right, rtol=1e-7, atol=1e-8)
                conflicts = int(different.sum())
            results.append(dict(ticker=row.ticker, date=row.date, chosen_path=row.path,
                                alternate_path=other.path, shared_contracts=shared,
                                conflicting_contracts=conflicts,
                                different_coverage=len(chosen) != len(alternate)))
    return pd.DataFrame(results)


def build_selections(population: pd.DataFrame, calendar: pd.DatetimeIndex,
                     lookup: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Select all contracts and entry decisions before computing any outcome P&L."""
    candidates, decisions = [], []
    eligible = population[population.input_eligible]
    for number, signal in enumerate(eligible.itertuples(), 1):
        ticker, date, reference = signal.ticker, signal.tradeDate, signal.reference_date
        exit_date = calendar[signal.session_index+5] if signal.session_index+5 < len(calendar) else pd.NaT
        source = lookup.get((ticker, str(date.date())))
        raw = read_chain(source, ticker, date)
        measured = candidate_metrics(raw, date, exit_date) if not raw.empty else pd.DataFrame()
        if not measured.empty:
            measured['signal_date'] = date
            measured['source_path'] = source['path']
            candidates.append(measured)
        for selector in ['mechanical', 'economic']:
            selected, reason = choose_contract(measured, selector)
            record = dict(ticker=ticker, signal_date=date, entry_date=reference,
                          exit_date_4=exit_date, selector=selector,
                          common_nonoverlap=signal.common_nonoverlap,
                          outside_prior_six=signal.outside_prior_six,
                          reference_month=signal.reference_month, era=signal.era,
                          session_index=signal.session_index, signal_wing=signal.wing,
                          signal_wing_rank=signal.wing_rank, signal_state=signal.state,
                          signal_age=signal.age, selection_reason=reason,
                          known_split_through_exit=signal.known_split_through_exit,
                          signal_source_path=source['path'] if source else '')
            if selected is None:
                record.update(entry_status=no_selection_status(measured, reason),
                              entry_reason=reason)
            else:
                record.update({f'signal_{k}': v for k, v in selected.items()})
                entry_source = lookup.get((ticker, str(reference.date())))
                entry_chain = read_chain(entry_source, ticker, reference)
                record['entry_source_path'] = entry_source['path'] if entry_source else ''
                record.update(fixed_contract_entry(selected, entry_chain, reference,
                                                   exit_date, selector))
            decisions.append(record)
        if number % 100 == 0:
            print(f'Selected {number}/{len(eligible)} input-eligible ticker-dates', flush=True)
    return pd.concat(candidates, ignore_index=True) if candidates else pd.DataFrame(), pd.DataFrame(decisions)


def quote_for_contract(chain: pd.DataFrame, expiry: pd.Timestamp, strike: float,
                        date: pd.Timestamp) -> tuple[pd.Series | None, str]:
    """Locate an exact dated exit quote without requiring irrelevant entry Greeks."""
    if chain.empty:
        return None, 'chain_unavailable'
    x = chain[chain.expirDate.astype(str).str[:10].eq(str(expiry.date()))
              & chain.strike.eq(strike)]
    if len(x) != 1:
        return None, 'fixed_contract_absent_or_duplicated'
    row = x.iloc[0]
    quote_date = pd.to_datetime(row.get('quoteDate'), utc=True, errors='coerce')
    if pd.isna(quote_date) or quote_date.tz_convert('America/New_York').date() != date.date():
        return None, 'quote_timestamp_missing_or_wrong_session'
    if not valid_quote(row, entry=False):
        return None, 'nonexecutable_exit_quote'
    if not np.isfinite(row.stockPrice) or row.stockPrice <= 0:
        return None, 'underlying_price_missing'
    return row, 'observed'


def replay(decisions: pd.DataFrame, calendar: pd.DatetimeIndex, lookup: dict) -> pd.DataFrame:
    """Compute both predeclared exits, preserving absent exact contracts as censored."""
    prices = pd.read_parquet(CACHE/'dailies.parquet').set_index(['ticker', 'tradeDate'])
    rows = []
    for trade in decisions.to_dict('records'):
        for horizon in HORIZONS:
            row = trade.copy()
            row.update(horizon=horizon, trade_pnl=np.nan, policy_pnl=np.nan,
                       exit_status='not_entered', worst_eod_cover_pnl=np.nan,
                       observed_worst_eod_cover_pnl=np.nan, complete_adverse_coverage=False,
                       underlying_high_excursion_pct=np.nan)
            if trade['entry_status'] == 'no_entry':
                row['policy_pnl'] = 0.
                rows.append(row)
                continue
            if trade['entry_status'] != 'admitted':
                row['exit_status'] = 'entry_censored'
                rows.append(row)
                continue
            expiry = pd.Timestamp(trade['signal_expirDate'])
            entry_position = int(trade['session_index'])+1
            exit_position = entry_position+horizon
            if exit_position >= len(calendar):
                row['exit_status'] = 'calendar_deadline_unavailable'
                rows.append(row)
                continue
            exit_date = calendar[exit_position]
            row['actual_exit_date'] = exit_date
            observed, missing, quote_records = [], [], []
            for position in range(entry_position, exit_position+1):
                date = calendar[position]
                source = lookup.get((trade['ticker'], str(date.date())))
                chain = read_chain(source, trade['ticker'], date)
                quote, reason = quote_for_contract(chain, expiry, trade['signal_strike'], date)
                if quote is None:
                    missing.append(f'{date.date()}:{reason}')
                else:
                    mark = closing_pnl(trade['entry_callBidPrice'], quote.callAskPrice)
                    observed.append(mark)
                    quote_records.append(dict(date=str(date.date()), quote_date=str(quote.quoteDate),
                                              bid=float(quote.callBidPrice), ask=float(quote.callAskPrice),
                                              ask_size=float(quote.callAskSize),
                                              stock=float(quote.stockPrice),
                                              source_path=source['path'], mark_pnl=float(mark)))
                    if position == exit_position:
                        expiry_chain = chain[chain.expirDate.astype(str).str[:10].eq(
                            str(expiry.date()))]
                        exit_atm, atm_status = spot_atm_iv(expiry_chain, quote.stockPrice, date)
                        row.update(trade_pnl=mark, policy_pnl=mark, exit_status='priced',
                                   exit_ask=quote.callAskPrice, exit_bid=quote.callBidPrice,
                                   exit_ask_size=quote.callAskSize, exit_quote_date=quote.quoteDate,
                                   exit_stock=quote.stockPrice, exit_source_path=source['path'],
                                   exit_callBidIv=quote.callBidIv, exit_callMidIv=quote.callMidIv,
                                   exit_callAskIv=quote.callAskIv, exit_spot_atm_iv=exit_atm,
                                   exit_atm_status=atm_status)
                        if quote.callMidIv > 0 and np.isfinite(exit_atm):
                            row['fixed_strike_mid_wing_change_points'] = 100*(
                                quote.callMidIv-exit_atm-trade['entry_callMidIv']
                                + trade['entry_spot_atm_iv'])
                            row['atm_change_points'] = 100*(exit_atm-trade['entry_spot_atm_iv'])
                            row['fixed_strike_mid_iv_change_points'] = 100*(
                                quote.callMidIv-trade['entry_callMidIv'])
            if row['exit_status'] != 'priced':
                row['exit_status'] = 'exit_censored'
            row['missing_intermediate_or_exit'] = ';'.join(missing)
            row['observed_eod_quote_count'] = len(observed)
            row['expected_eod_quote_count'] = horizon+1
            row['complete_adverse_coverage'] = not missing
            row['observed_worst_eod_cover_pnl'] = min(observed) if observed else np.nan
            row['worst_eod_cover_pnl'] = min(observed) if observed and not missing else np.nan
            row['quote_observations'] = json.dumps(quote_records)
            # hiPx is already adjusted in ORATS. Convert the entry snapshot to that basis.
            entry_key = (trade['ticker'], trade['entry_date'])
            if entry_key in prices.index and not trade['known_split_through_exit']:
                entry_daily = prices.loc[entry_key]
                factor = entry_daily.clsPx/entry_daily.unadjClsPx
                entry_adjusted = trade['entry_stockPrice']*factor
                highs = []
                for date in calendar[entry_position+1:exit_position+1]:
                    key = (trade['ticker'], date)
                    value = np.nan
                    if key in prices.index:
                        daily = prices.loc[key]
                        if daily.hiPx >= daily.clsPx*.999:
                            value = daily.hiPx
                    highs.append(value)
                if (np.isfinite(factor) and factor > 0 and np.isfinite(entry_adjusted)
                        and entry_adjusted > 0 and all(np.isfinite(highs))
                        and all(h > 0 for h in highs)):
                    row['underlying_high_excursion_pct'] = 100*(max(highs)/entry_adjusted-1)
            if trade['known_split_through_exit']:
                row.update(trade_pnl=np.nan, policy_pnl=np.nan,
                           exit_status='corporate_action_identity_unverified',
                           worst_eod_cover_pnl=np.nan, complete_adverse_coverage=False)
            rows.append(row)
    return pd.DataFrame(rows)


def block_bootstrap(paired: pd.DataFrame) -> dict:
    """Resample reference months jointly across names and selectors, 2,000 fixed draws."""
    valid = paired[paired.paired_observed]
    aggregate = valid.groupby('reference_month').difference.agg(['sum', 'count'])
    result = dict(draws=2000, seed=20260908, paired_cases=len(valid),
                  month_blocks=len(aggregate), mean_difference=valid.difference.mean(),
                  median_difference=valid.difference.median(), ci95=None)
    if len(aggregate) >= 2:
        rng = np.random.default_rng(20260908)
        indexes = rng.integers(0, len(aggregate), size=(2000, len(aggregate)))
        samples = aggregate['sum'].to_numpy()[indexes].sum(axis=1)/(
            aggregate['count'].to_numpy()[indexes].sum(axis=1))
        result['ci95'] = np.quantile(samples, [.025, .975]).tolist()
    return result


def summarize(trades: pd.DataFrame, population: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    """Report policy and trade-conditioned economics on transparent common coverage."""
    index = ['ticker', 'signal_date', 'entry_date', 'reference_month', 'era',
             'common_nonoverlap', 'outside_prior_six', 'horizon']
    paired = trades.pivot(index=index, columns='selector', values='policy_pnl').reset_index()
    paired['paired_observed'] = paired[['economic', 'mechanical']].notna().all(axis=1)
    paired['difference'] = (paired.economic-paired.mechanical).where(paired.paired_observed)
    statuses = trades.pivot(index=index, columns='selector', values='entry_status').reset_index()
    statuses['both_entered'] = statuses.economic.eq('admitted') & statuses.mechanical.eq('admitted')
    paired = paired.merge(statuses[index+['both_entered']], on=index, validate='one_to_one')
    risks = trades.pivot(index=index, columns='selector', values='worst_eod_cover_pnl').reset_index()
    risks['both_complete_worst_cover_difference'] = (risks.economic-risks.mechanical).where(
        risks[['economic', 'mechanical']].notna().all(axis=1))
    paired = paired.merge(risks[index+['both_complete_worst_cover_difference']],
                          on=index, validate='one_to_one')
    comparisons, counts, diagnostics = [], [], []
    for label, sample in {
        'all_signals': paired,
        'common_nonoverlap': paired[paired.common_nonoverlap],
        'common_nonoverlap_excluding_prior_six': paired[
            paired.common_nonoverlap & paired.outside_prior_six],
        'common_nonoverlap_both_entered_priced': paired[
            paired.common_nonoverlap & paired.both_entered & paired.paired_observed],
    }.items():
        for era in ['all', '2024-2025', '2026']:
            period = sample if era == 'all' else sample[sample.era.eq(era)]
            for horizon in HORIZONS:
                subset = period[period.horizon.eq(horizon)]
                comparisons.append(dict(sample=label, era=era, horizon=horizon,
                    population_cases=len(subset), **block_bootstrap(subset),
                    both_complete_risk_cases=int(subset.both_complete_worst_cover_difference.notna().sum()),
                    mean_worst_cover_difference=subset.both_complete_worst_cover_difference.mean()))
    for label, sample in {'all_signals': trades,
                          'common_nonoverlap': trades[trades.common_nonoverlap]}.items():
        for (selector, horizon), group in sample.groupby(['selector', 'horizon']):
            admitted = group[group.entry_status.eq('admitted')]
            priced = admitted[admitted.exit_status.eq('priced')]
            counts.append(dict(sample=label, selector=selector, horizon=horizon,
                policy_cases=len(group), admitted=len(admitted),
                known_no_entry=int(group.entry_status.eq('no_entry').sum()),
                entry_censored=int(group.entry_status.eq('censored').sum()),
                priced_trades=len(priced), unpriced_admitted=len(admitted)-len(priced),
                trade_mean_pnl=priced.trade_pnl.mean(), trade_median_pnl=priced.trade_pnl.median(),
                trade_sum_pnl=priced.trade_pnl.sum(), trade_win_rate=priced.trade_pnl.gt(0).mean(),
                mean_policy_pnl=group.policy_pnl.mean(),
                mean_entry_delta=admitted.entry_delta.mean() if len(admitted) else np.nan,
                median_entry_otm_pct=admitted.entry_otm_pct.median() if len(admitted) else np.nan,
                median_entry_dte=admitted.entry_dte.median() if len(admitted) else np.nan,
                complete_adverse_cases=int(admitted.complete_adverse_coverage.sum()),
                total_entry_local_1pct_rally_loss=admitted.entry_rally_loss_1pct.sum(),
                median_entry_local_1pct_rally_loss=admitted.entry_rally_loss_1pct.median(),
                complete_worst_eod_cover_pnl_sum=admitted.worst_eod_cover_pnl.sum(min_count=1),
                minimum_observed_trade_pnl=priced.trade_pnl.min()))
    selected = population[population.input_eligible]
    nonover = selected[selected.common_nonoverlap]
    for selector, group in trades[trades.horizon.eq(4)].groupby('selector'):
        for stage in ['signal', 'entry']:
            for metric in ['scenario_iv_decline_points', 'scenario_iv_decline_fraction_of_bid_iv',
                           'rally_loss_1pct', 'economic_ratio', 'required_wing_fraction']:
                column = f'{stage}_{metric}'
                values = pd.to_numeric(group.get(column, pd.Series(dtype=float)), errors='coerce')
                if stage == 'entry':
                    values = values[group.entry_status.eq('admitted')]
                diagnostics.append(dict(selector=selector, stage=stage, metric=metric,
                    count=int(values.notna().sum()), minimum=values.min(),
                    median=values.median(), p95=values.quantile(.95), p99=values.quantile(.99),
                    maximum=values.max()))
            ceiling_column = f'{stage}_uncapped_recovery_exceeds_ask'
            if ceiling_column in group:
                ceiling = group[ceiling_column].eq(True)
                if stage == 'entry':
                    ceiling &= group.entry_status.eq('admitted')
                diagnostics.append(dict(selector=selector, stage=stage,
                    metric='uncapped_recovery_exceeds_ask', count=int(ceiling.sum())))
    pd.DataFrame(diagnostics).to_csv(OUTPUT/'selected_diagnostics.csv', index=False)
    summary = dict(experiment='E-PNDR-013', provider_calls=0,
        full_population_stock_dates=len(population), full_population_stocks=int(population.ticker.nunique()),
        full_population_signal_dates=int(population.tradeDate.nunique()),
        input_eligible_stock_dates=len(selected), input_eligible_stocks=int(selected.ticker.nunique()),
        input_eligible_signal_dates=int(selected.tradeDate.nunique()),
        input_eligible_first_signal=str(selected.tradeDate.min().date()),
        input_eligible_last_signal=str(selected.tradeDate.max().date()),
        common_nonoverlap_cases=len(nonover), common_nonoverlap_stocks=int(nonover.ticker.nunique()),
        common_nonoverlap_signal_dates=int(nonover.tradeDate.nunique()),
        counts=counts, comparisons=comparisons, selected_diagnostics=diagnostics,
        limitations=['Cache-selected exploratory dates, not random population coverage.',
                     'No 60-date matched delta and forward richness qualification.',
                     'Spot-ATM proxy; model Greek ranking and 25% normalization scenario.',
                     'Vendor daily snapshot quotes, not fills or complete intraday exposure.',
                     'Standard 100-share deliverables assumed; identity not independently certified.',
                     'Actual-event earnings exclusion, not archived as-known schedules.',
                     'No HIRO fields, captures, or availability requirements.'])
    return summary, paired


def report(summary: dict) -> None:
    """Write a readable result with explicit dates, denominators, and interpretation."""
    lines = ['# Preliminary exact-call economics without HIRO', '',
        f"The cache supplies **{summary['input_eligible_stock_dates']:,} eligible stock-dates**, "
        f"across **{summary['input_eligible_signal_dates']} signal dates** and "
        f"**{summary['input_eligible_stocks']} stocks**, from "
        f"{summary['input_eligible_first_signal']} through {summary['input_eligible_last_signal']}. "
        f"The common nonoverlap sample has **{summary['common_nonoverlap_cases']} cases** across "
        f"{summary['common_nonoverlap_signal_dates']} dates and {summary['common_nonoverlap_stocks']} stocks.", '',
        'Signals use existing stock names and daily quality with the authorized 30-day actual-earnings '
        'exclusion. No HIRO observations, features or coverage gates are used. Dates are selected by '
        'signal and next-session input availability, never by later outcome availability.', '',
        'The economic selector compares the net modeled benefit of removing 25% of the current '
        'call-minus-spot-ATM IV with local dollar loss from a 1% rally. Gross recovery is capped '
        'at the entire ask value so the projected buyback ask cannot become negative; uncapped '
        'values and violations are retained. This is a testable scenario '
        'ranking, not an expected-return forecast. The control chooses nearest ten-day expiry and '
        'nearest ten-delta call. Exact strikes remain fixed at entry, with no replacement after failure.', '',
        '## Common nonoverlap results', '',
        '| Policy | Sessions after entry | Admitted | Priced | Known no-entry | Entry censored | '
        'Mean priced trade | Median priced trade | Win rate |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for row in summary['counts']:
        if row['sample'] != 'common_nonoverlap':
            continue
        lines.append(f"| {row['selector']} | {row['horizon']} | {row['admitted']} | "
            f"{row['priced_trades']} | {row['known_no_entry']} | {row['entry_censored']} | "
            f"${row['trade_mean_pnl']:.2f} | ${row['trade_median_pnl']:.2f} | "
            f"{row['trade_win_rate']:.1%} |")
    lines += ['', 'Per assumed standard 100-share contract, using actual entry bid minus one cent and '
              'exit ask plus one cent, with $0.65 per action. These are daily vendor snapshots '
              '(actual timestamps retained), not closing-auction fills.', '',
              '## Paired policy comparison', '',
              '| Sample / period | Horizon | Paired cases | Month blocks | Economic minus control, '
              'mean per case | 95% month-block interval |',
              '| --- | ---: | ---: | ---: | ---: | --- |']
    for row in summary['comparisons']:
        if row['horizon'] != 4:
            continue
        interval = row['ci95']
        text = f"${interval[0]:.2f} to ${interval[1]:.2f}" if interval else 'Unavailable'
        lines.append(f"| {row['sample']} / {row['era']} | 4 | {row['paired_cases']} | "
                     f"{row['month_blocks']} | ${row['mean_difference']:.2f} | {text} |")
    lines += ['', 'Known no-entry decisions count as zero policy P&L. Unknown entries and exits remain '
              'censored. Paired comparisons require both policy outcomes; trade-only averages answer '
              'a different question. Common reservations persist even when either policy fails.', '',
              '## Interpretation and limitations', '',
              'This does not certify Pandar-approved trades or demonstrate an optimal delta/expiry. '
              'The candidate search has no narrow delta or percentage-OTM band. Many cached daily '
              'chains truncate contracts below five DTE; a selected contract disappearing before '
              'expiry is censored, never replaced or marked at zero.', '',
              'Call-wing depth, local strike residuals, required IV contraction, actual entry '
              'delta/distance/DTE, runner-up candidates, and quote timestamps are retained. '
              'No long call is automatically purchased. Greek sensitivity is local and cannot bound '
              'naked-call upside loss. Historical deliverables and full comparable-surface richness '
              'remain unverified.', '',
              'Worst EOD ask-to-cover loss is complete only when every intervening exact quote '
              'exists. A separate observed partial worst mark is not represented as complete risk. '
              'Underlying highs use the provider’s already-adjusted daily high and the entry '
              'snapshot converted to the same price basis; entry-day pre-trade highs are excluded.', '',
              'Artifacts: `population_ledger.csv`, `candidates.parquet`, `frozen_selections.csv`, '
              '`policy_trades.csv`, `paired_policy_results.csv`, `failure_ledger.csv`, '
              '`source_conflicts.csv`, `summary.json`, `bootstrap.json`, and the input/selection '
              'hash manifests. Reproduce with the project Python runtime running '
              '`scripts/pandar_no_hiro_exact.py`. Zero provider calls.']
    (OUTPUT/'exact_chain_results.md').write_text('\n'.join(lines)+'\n')


def main() -> None:
    """Freeze local inputs, select causally, then replay and preserve every disposition."""
    OUTPUT.mkdir(parents=True, exist_ok=True)
    inventory = pd.read_csv(INVENTORY)
    sources = resolve_sources(inventory)
    sources.to_csv(OUTPUT/'selected_sources.csv', index=False)
    population, calendar, lookup = prepare_population(sources)
    population.to_csv(OUTPUT/'population_ledger.csv', index=False)
    input_paths = [PROTOCOL, Path(__file__), INVENTORY,
                   SURFACE/'candidate_reason_ledger.parquet', CACHE/'dailies.parquet']
    source_paths = sorted(set(sources.loc[sources.date.ge('2024-01-02'), 'path']))
    frozen = dict(experiment='E-PNDR-013', frozen_at_utc=datetime.now(timezone.utc).isoformat(),
                  provider_calls=0,
                  inputs=[dict(path=str(p), sha256=sha256(p)) for p in input_paths],
                  chain_files=[dict(path=p, sha256=sha256(Path(p))) for p in source_paths])
    write_json(OUTPUT/'input_freeze.json', frozen)
    eligible = population[population.input_eligible]
    print(f'Frozen {len(source_paths)} files; {len(eligible)} eligible ticker-dates, '
          f'{eligible.ticker.nunique()} stocks, {eligible.tradeDate.nunique()} dates', flush=True)
    candidates, decisions = build_selections(population, calendar, lookup)
    candidates.to_parquet(OUTPUT/'candidates.parquet', index=False)
    decisions.to_csv(OUTPUT/'frozen_selections.csv', index=False)
    write_json(OUTPUT/'selection_freeze.json', dict(
        frozen_at_utc=datetime.now(timezone.utc).isoformat(),
        candidates_sha256=sha256(OUTPUT/'candidates.parquet'),
        selections_sha256=sha256(OUTPUT/'frozen_selections.csv'),
        statement='Saved all exact contracts and entry decisions before outcome replay.'))
    keys = {(r.ticker, str(calendar[position].date())) for r in eligible.itertuples()
            for position in range(r.session_index, min(r.session_index+6, len(calendar)))}
    source_conflict_audit(sources, inventory, keys).to_csv(OUTPUT/'source_conflicts.csv', index=False)
    trades = replay(decisions, calendar, lookup)
    trades.to_csv(OUTPUT/'policy_trades.csv', index=False)
    trades[(trades.entry_status.ne('admitted')) | trades.exit_status.ne('priced')].to_csv(
        OUTPUT/'failure_ledger.csv', index=False)
    summary, paired = summarize(trades, population)
    paired.to_csv(OUTPUT/'paired_policy_results.csv', index=False)
    write_json(OUTPUT/'summary.json', summary)
    write_json(OUTPUT/'bootstrap.json', summary['comparisons'])
    report(summary)
    print(json.dumps({k: v for k, v in summary.items() if k not in ['counts', 'comparisons',
                                                                  'selected_diagnostics',
                                                                  'limitations']}, indent=2), flush=True)


if __name__ == '__main__':
    main()
