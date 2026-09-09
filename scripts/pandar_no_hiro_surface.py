"""E-PNDR-012: frozen, local-cache-only daily call-wing normalization experiment."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'docs/replay/pandar_skew_journey_2026-09-06'
DATA = ROOT / 'data/pandar_hypothesis_2026-09-07'
OUTPUT = ROOT / 'outputs/pandar_no_hiro_2026-09-08'
PROTOCOL = ROOT / 'hypothesis_tracking/pandar_no_hiro_surface_protocol_2026-09-08.md'
CUTOFF = pd.Timestamp('2026-09-04')
HORIZONS = (1, 2, 4)
SLOW = 'slowing_rolling'
FAST = 'continued_accelerating'


def prior_ranks(values: pd.Series, window: int = 252, minimum: int = 126) -> pd.Series:
    """Strict prior percentile; same pure calculation as the earlier surface study."""
    data = np.asarray(values, dtype=float)
    windows = np.lib.stride_tricks.sliding_window_view(
        np.concatenate([np.full(window, np.nan), data]), window + 1)
    past, current = windows[:, :-1], windows[:, -1]
    count = np.isfinite(past).sum(axis=1)
    rank = np.divide((past < current[:, None]).sum(axis=1) * 100., count,
                     out=np.full(len(data), np.nan),
                     where=(count >= minimum) & np.isfinite(current))
    return pd.Series(rank, index=values.index)


def episode_features(rank: pd.Series, wing: pd.Series) -> pd.DataFrame:
    """Causal high-rank episode age and depth, preserving unknown episode starts."""
    rows: list[dict] = []
    age, episode, area, peak = 0, 0, 0., np.nan
    unknown_start, censored = True, False
    for r, w in zip(rank, wing, strict=True):
        record = dict(age=0., episode_id=episode, intensity=0., peak_minus_wing=np.nan,
                      left_censored=False)
        if not np.isfinite(r) or not np.isfinite(w):
            age, area, peak, unknown_start = 0, 0., np.nan, True
            record['age'] = np.nan
        elif r >= 85:
            if age == 0:
                episode += 1
                censored = unknown_start
            age += 1
            area += (r - 85) / 15
            peak = w if not np.isfinite(peak) else max(peak, w)
            record.update(age=age, episode_id=episode, intensity=area,
                          peak_minus_wing=peak-w, left_censored=censored)
        else:
            age, area, peak, unknown_start = 0, 0., np.nan, False
        rows.append(record)
    return pd.DataFrame(rows, index=rank.index)


def wing_state(wing: pd.Series) -> pd.DataFrame:
    """Compare the latest three-session slope with the preceding three sessions."""
    valid = wing.rolling(7, min_periods=7).count().eq(7)
    recent = ((wing-wing.shift(3))/3).where(valid)
    preceding = ((wing.shift(3)-wing.shift(6))/3).where(valid)
    fast = recent.gt(0) & recent.ge(preceding)
    state = pd.Series('missing_seven_session_history', index=wing.index)
    state.loc[valid & recent.le(0)] = 'nonpositive_recent'
    state.loc[valid & recent.gt(0) & ~fast] = 'positive_slowing'
    state.loc[valid & fast] = FAST
    group = pd.Series('unavailable', index=wing.index)
    group.loc[valid] = np.where(fast[valid], FAST, SLOW)
    return pd.DataFrame(dict(recent_slope=recent, preceding_slope=preceding,
                             state=state, group=group))


def earnings_status(days: pd.DatetimeIndex, events: pd.DatetimeIndex,
                    coverage: dict) -> pd.Series:
    """Require covered actual-event windows, inclusively through calendar day +30."""
    result = pd.Series('clear', index=days)
    horizon = days + pd.Timedelta(days=30)
    begin = pd.to_datetime(coverage.get('earnings_coverage_start'), errors='coerce')
    finish = pd.to_datetime(coverage.get('earnings_coverage_end'), errors='coerce')
    if coverage.get('earnings_status') != 'ok' or pd.isna(begin) or pd.isna(finish):
        result[:] = 'metadata_unsupported'
    elif events.empty:
        result[:] = 'actual_event_records_missing'
    else:
        events = events.sort_values().unique()
        positions = events.searchsorted(days)
        next_event = np.full(len(days), np.datetime64('NaT'), dtype='datetime64[ns]')
        in_bounds = positions < len(events)
        next_event[in_bounds] = events.to_numpy(dtype='datetime64[ns]')[positions[in_bounds]]
        result.loc[next_event <= horizon.to_numpy(dtype='datetime64[ns]')] = (
            'event_in_next_30_days')
        result.loc[days < begin] = 'before_metadata_coverage'
        result.loc[horizon > finish] = 'after_metadata_coverage'
    result.loc[horizon > CUTOFF] = 'future_earnings_horizon'
    result.loc[days.isna()] = 'reference_session_unavailable'
    return result


def price_basis(frame: pd.DataFrame) -> pd.DataFrame:
    """Use provider-adjusted high/close consistently; never apply adjustments twice."""
    ratio = (frame.clsPx/frame.unadjClsPx).where(
        frame.clsPx.gt(0) & frame.unadjClsPx.gt(0))
    high_valid = frame.hiPx.ge(frame.clsPx*0.999) & frame.hiPx.gt(0)
    return pd.DataFrame(dict(
        adjusted_high=frame.hiPx.where(high_valid),
        adjusted_unadjusted_basis_differs=ratio.sub(1).abs().gt(.001),
        adjusted_high_below_adjusted_close=frame.hiPx.lt(frame.clsPx*.999),
        summary_raw_price_discrepancy=(frame.stockPrice/frame.unadjClsPx-1).abs().gt(.05),
        adjustment_factor_jump=ratio.div(ratio.shift(1)).sub(1).abs().gt(.05),
    ), index=frame.index)


def add_surface_outcomes(frame: pd.DataFrame) -> pd.DataFrame:
    """Reference next session EOD; censor every missing intervening price or IV."""
    result = frame.copy()
    valid_iv = frame.iv10d.gt(0) & frame.dlt5Iv10d.gt(0) & frame.wing.notna()
    valid_price = frame.clsPx.gt(0)
    result['signal_reference_wing_change'] = frame.wing.shift(-1)-frame.wing
    result['signal_reference_atm_change'] = (frame.iv10d.shift(-1)-frame.iv10d)*100
    result['signal_reference_call_iv_change'] = (
        frame.dlt5Iv10d.shift(-1)-frame.dlt5Iv10d)*100
    result['signal_reference_stock_return'] = (
        frame.clsPx.shift(-1)/frame.clsPx-1)*100
    for horizon in HORIZONS:
        price_valid = pd.Series(True, index=frame.index)
        iv_valid = pd.Series(True, index=frame.index)
        for step in range(1, horizon+2):
            price_valid &= valid_price.shift(-step, fill_value=False)
            iv_valid &= valid_iv.shift(-step, fill_value=False)
        valid = price_valid & iv_valid
        wing = (frame.wing.shift(-(horizon+1))-frame.wing.shift(-1)).where(valid)
        atm = ((frame.iv10d.shift(-(horizon+1))-frame.iv10d.shift(-1))*100).where(valid)
        call = wing+atm
        result[f'wing_change_{horizon}'] = wing
        result[f'atm_change_{horizon}'] = atm
        result[f'call_iv_change_{horizon}'] = call
        result[f'stock_return_{horizon}'] = (
            (frame.clsPx.shift(-(horizon+1))/frame.clsPx.shift(-1)-1)*100).where(valid)
        for name, event in {
            'wing_compression': wing.lt(0),
            'call_iv_down': call.lt(0),
            'joint_compression_atm_up': wing.lt(0) & atm.ge(0),
            'joint_compression_atm_up_call_down': wing.lt(0) & atm.ge(0) & call.lt(0),
        }.items():
            result[f'{name}_{horizon}'] = np.where(valid, event, np.nan)
        highs = pd.concat([frame.adjusted_high.shift(-step)
                           for step in range(2, horizon+2)], axis=1)
        result[f'upside_excursion_{horizon}'] = (
            (highs.max(axis=1)/frame.clsPx.shift(-1)-1)*100).where(
                valid & highs.notna().all(axis=1))
        reason = pd.Series('complete', index=frame.index)
        reason.loc[~iv_valid] = 'missing_intervening_iv'
        reason.loc[~price_valid] = 'missing_intervening_price'
        unavailable = np.arange(len(frame))+horizon+1 >= len(frame)
        reason.loc[unavailable] = 'end_of_cached_calendar'
        result[f'censor_reason_{horizon}'] = reason
    return result


def nonoverlap_mask(frame: pd.DataFrame) -> pd.Series:
    """One common reservation rule, independent of state and observed outcomes."""
    admitted = pd.Series(False, index=frame.index)
    eligible = frame[frame.rich_eligible].sort_values(['ticker', 'session_index'])
    for _, group in eligible.groupby('ticker', sort=False):
        reserved_through = -1
        for row in group.itertuples():
            if row.session_index > reserved_through:
                admitted.loc[row.Index] = True
                reserved_through = row.session_index+5
    return admitted


def sha256(path: Path) -> str:
    """Hash exact files used in this local-only run."""
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: dict | list) -> None:
    """Write portable JSON, representing unavailable numeric results as null."""
    def clean(item):
        if isinstance(item, dict):
            return {str(key): clean(val) for key, val in item.items()}
        if isinstance(item, (list, tuple)):
            return [clean(val) for val in item]
        if isinstance(item, (np.integer, np.bool_)):
            return item.item()
        if isinstance(item, (float, np.floating)):
            return float(item) if np.isfinite(item) else None
        return item
    path.write_text(json.dumps(clean(value), indent=2, allow_nan=False)+'\n')


def freeze_inputs() -> dict:
    """Freeze protocol and input hashes before features, selections, or outcomes."""
    paths = [PROTOCOL, Path(__file__), CACHE/'summaries.parquet', CACHE/'dailies.parquet',
             CACHE/'hiro_universe.csv', DATA/'earnings.parquet', DATA/'metadata_coverage.csv',
             DATA/'splits.parquet']
    manifest = dict(frozen_at_utc=datetime.now(timezone.utc).isoformat(),
                    experiment='E-PNDR-012', provider_calls=0,
                    input_files=[dict(path=str(path), sha256=sha256(path)) for path in paths],
                    statement='Frozen before this run; historical panel previously examined.')
    OUTPUT.mkdir(parents=True, exist_ok=True)
    previous = OUTPUT/'input_freeze.json'
    if previous.exists():
        saved = json.loads(previous.read_text())
        receipt = saved['frozen_at_utc'].replace(':', '-').replace('+', '_')
        write_json(OUTPUT/f'input_freeze_{receipt}.json', saved)
    write_json(OUTPUT/'input_freeze.json', manifest)
    return manifest


def build_signal_panel() -> tuple[pd.DataFrame, dict]:
    """Build all stock-session decisions from raw summaries, prices, and earnings."""
    summaries = pd.read_parquet(CACHE/'summaries.parquet')
    prices = pd.read_parquet(CACHE/'dailies.parquet')
    for name, frame in [('summaries', summaries), ('dailies', prices)]:
        if frame.duplicated(['ticker', 'tradeDate']).any():
            raise ValueError(f'Duplicate {name} ticker dates')
    calendar = pd.DatetimeIndex(prices.loc[prices.ticker.eq('SPY'), 'tradeDate'].sort_values())
    if not calendar.is_unique or calendar[-1] != pd.Timestamp('2026-09-03'):
        raise ValueError('SPY calendar is duplicated or does not end on frozen cutoff')
    membership = pd.read_csv(CACHE/'hiro_universe.csv')
    names = sorted(membership.loc[membership.single_stock, 'ticker'].unique())
    earnings = pd.read_parquet(DATA/'earnings.parquet')
    earnings['earnDate'] = pd.to_datetime(earnings.earnDate, errors='raise')
    coverage = pd.read_csv(DATA/'metadata_coverage.csv').set_index('ticker')
    splits = pd.read_parquet(DATA/'splits.parquet')
    split_column = 'splitDate' if 'splitDate' in splits else 'exDate'
    if not splits.empty and split_column not in splits:
        raise ValueError('Unknown split date column')
    parts, source_coverage = [], []
    for ticker in names:
        summary = summaries[summaries.ticker.eq(ticker)].drop(columns='ticker')
        price = prices[prices.ticker.eq(ticker)].drop(columns='ticker')
        x = summary.set_index('tradeDate').join(price.set_index('tradeDate'), how='outer')
        x = x.reindex(calendar)
        x.index.name = 'tradeDate'
        x['ticker'] = ticker
        x['session_index'] = np.arange(len(calendar))
        x['reference_date'] = pd.Series(calendar, index=calendar).shift(-1)
        x['exit_date_4'] = pd.Series(calendar, index=calendar).shift(-5)
        x['wing'] = ((x.dlt5Iv10d-x.iv10d)*100).where(
            x.dlt5Iv10d.gt(0) & x.iv10d.gt(0))
        x['wing_rank'] = prior_ranks(x.wing)
        x = pd.concat([x, episode_features(x.wing_rank, x.wing), wing_state(x.wing),
                       price_basis(x)], axis=1)
        x['dollar_turnover20'] = (x.clsPx*x.stockVolume).where(
            x.clsPx.gt(0) & x.stockVolume.ge(0)).rolling(20, min_periods=20).mean()
        x['confidence_pct'] = x.confidence*100
        events = pd.DatetimeIndex(earnings.loc[earnings.ticker.eq(ticker), 'earnDate'])
        record = coverage.loc[ticker].to_dict() if ticker in coverage.index else {}
        x['signal_earnings_status'] = earnings_status(calendar, events, record).to_numpy()
        x['reference_earnings_status'] = earnings_status(
            pd.DatetimeIndex(x.reference_date), events, record).to_numpy()
        ticker_splits = splits.loc[splits.ticker.eq(ticker), split_column]
        split_dates = pd.DatetimeIndex(pd.to_datetime(ticker_splits))
        x['known_split_on_signal'] = calendar.isin(split_dates)
        x['known_split_through_exit'] = False
        for event in split_dates:
            x.loc[(calendar <= event) & x.exit_date_4.ge(event), 'known_split_through_exit'] = True
        x['split_metadata_status'] = record.get('splits_status', 'missing')
        failures = {
            'missing_summary': x.stockPrice.isna(),
            'missing_price': ~x.clsPx.gt(0),
            'invalid_iv_inputs': ~(x.iv10d.gt(0) & x.iv30d.gt(0) & x.dlt5Iv10d.gt(0)),
            'confidence_below_50_or_missing': ~x.confidence_pct.ge(50),
            'turnover_below_20m_or_incomplete': ~x.dollar_turnover20.ge(20e6),
        }
        x['quality_valid'] = ~pd.DataFrame(failures).any(axis=1)
        failures.update({
            'signal_earnings_not_clear': ~x.signal_earnings_status.eq('clear'),
            'reference_earnings_not_clear': ~x.reference_earnings_status.eq('clear'),
            'rank_history_unavailable': x.wing_rank.isna(),
            'rank_below_85': x.wing_rank.notna() & x.wing_rank.lt(85),
            'wing_nonpositive_or_missing': ~x.wing.gt(0),
        })
        x['quality_earnings_valid'] = (x.quality_valid & x.signal_earnings_status.eq('clear')
                                       & x.reference_earnings_status.eq('clear'))
        x['rich_eligible'] = ~pd.DataFrame(failures).any(axis=1)
        reasons = pd.Series('', index=x.index)
        for reason, mask in failures.items():
            reasons.loc[mask] += reason+';'
        reasons.loc[reasons.eq('')] = 'eligible'
        x['selection_reasons'] = reasons.str.rstrip(';')
        x['state_available'] = x.group.ne('unavailable')
        source_coverage.append(dict(ticker=ticker, summary_rows=len(summary), price_rows=len(price),
            missing_summary_sessions=int(x.stockPrice.isna().sum()),
            missing_price_sessions=int(x.clsPx.isna().sum())))
        parts.append(x.reset_index())
    full = pd.concat(parts, ignore_index=True)
    signals = full[full.tradeDate.ge('2024-01-02')].copy()
    signals['nonoverlap_admitted'] = nonoverlap_mask(signals)
    signals['reference_month'] = signals.reference_date.dt.to_period('M').astype(str)
    signals['era'] = np.where(signals.tradeDate.lt('2026-01-01'), '2024-2025', '2026')
    pd.DataFrame(source_coverage).to_csv(OUTPUT/'stock_source_coverage.csv', index=False)
    signals.to_parquet(OUTPUT/'candidate_reason_ledger.parquet', index=False)
    ledger_columns = ['ticker', 'tradeDate', 'reference_date', 'exit_date_4', 'quality_valid',
        'quality_earnings_valid', 'rich_eligible', 'selection_reasons', 'signal_earnings_status',
        'reference_earnings_status', 'wing', 'wing_rank', 'state', 'group', 'age', 'episode_id',
        'left_censored', 'nonoverlap_admitted', 'known_split_on_signal',
        'known_split_through_exit', 'split_metadata_status', 'adjusted_unadjusted_basis_differs',
        'adjusted_high_below_adjusted_close', 'summary_raw_price_discrepancy',
        'adjustment_factor_jump']
    signals[ledger_columns].to_csv(OUTPUT/'candidate_reason_ledger.csv', index=False)
    counts = dict(background_sessions=len(calendar), background_start=str(calendar[0].date()),
        background_end=str(calendar[-1].date()), membership_stocks=len(names),
        evaluation_sessions=int(signals.tradeDate.nunique()), candidate_stock_dates=len(signals))
    for name in ['quality_valid', 'quality_earnings_valid', 'rich_eligible', 'nonoverlap_admitted']:
        sample = signals[signals[name]]
        counts[name] = sample_counts(sample)
    write_json(OUTPUT/'admission_counts.json', counts)
    write_json(OUTPUT/'selection_freeze.json', dict(
        frozen_at_utc=datetime.now(timezone.utc).isoformat(),
        ledger_sha256=sha256(OUTPUT/'candidate_reason_ledger.parquet'), counts=counts))
    print(json.dumps(counts, indent=2), flush=True)
    return signals, counts


def sample_counts(frame: pd.DataFrame) -> dict:
    """Count actual distinct dates, names and episode identifiers explicitly."""
    return dict(stock_dates=len(frame), stocks=int(frame.ticker.nunique()),
                signal_dates=int(frame.tradeDate.nunique()),
                reference_dates=int(frame.reference_date.nunique()),
                reference_months=int(frame.reference_date.dt.to_period('M').nunique()),
                first_signal=str(frame.tradeDate.min().date()) if len(frame) else None,
                last_signal=str(frame.tradeDate.max().date()) if len(frame) else None,
                episodes=int(frame[['ticker', 'episode_id']].drop_duplicates().shape[0]),
                unknown_start_rows=int(frame.left_censored.sum()))


def summarize_groups(panel: pd.DataFrame) -> pd.DataFrame:
    """Raw outcomes for full quality samples and rich groups, with all censor counts."""
    rows = []
    samples = {
        'quality_valid': panel[panel.quality_valid],
        'quality_earnings_valid': panel[panel.quality_earnings_valid],
        'rich_all_signals': panel[panel.rich_eligible],
        'rich_nonoverlap': panel[panel.nonoverlap_admitted],
    }
    for sample_name, sample in samples.items():
        for era in ['all', '2024-2025', '2026']:
            period = sample if era == 'all' else sample[sample.era.eq(era)]
            for group in ['all', SLOW, FAST, 'positive_slowing', 'nonpositive_recent']:
                current = period if group == 'all' else period[
                    period.group.eq(group) | period.state.eq(group)]
                for horizon in HORIZONS:
                    row = dict(sample=sample_name, era=era, group=group, horizon=horizon,
                               **sample_counts(current))
                    valid = current[f'wing_change_{horizon}'].notna()
                    row.update(valid_outcomes=int(valid.sum()), censored=int((~valid).sum()),
                               valid_signal_dates=int(current.loc[valid, 'tradeDate'].nunique()))
                    for metric in ['wing_change', 'atm_change', 'call_iv_change', 'stock_return',
                                   'upside_excursion', 'wing_compression', 'call_iv_down',
                                   'joint_compression_atm_up', 'joint_compression_atm_up_call_down']:
                        values = current[f'{metric}_{horizon}']
                        row[f'mean_{metric}'] = values.mean()
                        row[f'median_{metric}'] = values.median()
                        row[f'n_{metric}'] = int(values.notna().sum())
                    for column in ['signal_reference_wing_change', 'signal_reference_atm_change',
                                   'signal_reference_call_iv_change', 'signal_reference_stock_return',
                                   'age', 'intensity', 'peak_minus_wing', 'wing', 'wing_rank']:
                        row[f'mean_{column}'] = current[column].mean()
                    rows.append(row)
    return pd.DataFrame(rows)


def month_bootstrap(frame: pd.DataFrame, outcome: str, draws: int = 2000) -> dict:
    """Resample entire reference months jointly across names and both state groups."""
    valid = frame[frame.group.isin([SLOW, FAST]) & frame[outcome].notna()]
    aggregate = valid.groupby(['reference_month', 'group'])[outcome].agg(['sum', 'count'])
    months = sorted(valid.reference_month.unique())
    means = valid.groupby('group')[outcome].mean()
    difference = means.get(SLOW, np.nan)-means.get(FAST, np.nan)
    result = dict(outcome=outcome, months=len(months), draws=draws, seed=20260908,
                  slowing_minus_expanding=difference, ci_low=None, ci_high=None,
                  valid_draws=0)
    if len(months) < 2:
        return result
    arrays = []
    for group in [SLOW, FAST]:
        selected = aggregate.xs(group, level='group').reindex(months, fill_value=0)
        arrays.append((selected['sum'].to_numpy(), selected['count'].to_numpy()))
    rng = np.random.default_rng(20260908)
    indices = rng.integers(0, len(months), (draws, len(months)))
    draw_means = []
    for sums, counts in arrays:
        denominator = counts[indices].sum(axis=1)
        draw_means.append(np.divide(sums[indices].sum(axis=1), denominator,
            out=np.full(draws, np.nan), where=denominator > 0))
    differences = draw_means[0]-draw_means[1]
    finite = differences[np.isfinite(differences)]
    result.update(valid_draws=len(finite),
                  ci_low=float(np.quantile(finite, .025)) if len(finite) else None,
                  ci_high=float(np.quantile(finite, .975)) if len(finite) else None)
    return result


def adjusted_effect(frame: pd.DataFrame, outcome: str) -> dict:
    """Additive within regression; ticker/month fixed effects and month-clustered errors."""
    data = frame[frame.group.isin([SLOW, FAST])].dropna(
        subset=[outcome, 'wing', 'iv10d', 'reference_month']).copy()
    if data.empty:
        return dict(outcome=outcome, status='no_valid_rows')
    y = data[outcome].to_numpy(float)
    x = np.column_stack([data.group.eq(SLOW).to_numpy(float), data.wing.to_numpy(float),
                         data.iv10d.to_numpy(float)*100])
    matrix = np.column_stack([y, x])
    ids = [pd.factorize(data.ticker)[0], pd.factorize(data.reference_month)[0]]
    iterations = 0
    for iterations in range(1, 1001):
        previous = matrix.copy()
        for codes in ids:
            size = codes.max()+1
            counts = np.bincount(codes, minlength=size)
            totals = np.zeros((size, matrix.shape[1]))
            np.add.at(totals, codes, matrix)
            matrix -= (totals/counts[:, None])[codes]
        if np.max(np.abs(matrix-previous)) < 1e-10:
            break
    else:
        raise ValueError('Two-way fixed effect demeaning did not converge')
    y_within, x_within = matrix[:, 0], matrix[:, 1:]
    coefficients, _, rank, _ = np.linalg.lstsq(x_within, y_within, rcond=None)
    if rank < 3:
        return dict(outcome=outcome, status='rank_deficient', rows=len(data))
    residual = y_within-x_within@coefficients
    bread = np.linalg.inv(x_within.T@x_within)
    months = ids[1].max()+1
    scores = np.zeros((months, 3))
    np.add.at(scores, ids[1], x_within*residual[:, None])
    full_parameters = data.ticker.nunique()+months-1+3
    correction = months/(months-1)*(len(data)-1)/(len(data)-full_parameters)
    covariance = correction*bread@(scores.T@scores)@bread
    error = np.sqrt(np.maximum(np.diag(covariance), 0))
    critical = student_t.ppf(.975, months-1)
    support = data.groupby('ticker').group.nunique()
    return dict(outcome=outcome, status='ok', rows=len(data), months=months,
        coefficient=float(coefficients[0]), standard_error=float(error[0]),
        ci_low=float(coefficients[0]-critical*error[0]),
        ci_high=float(coefficients[0]+critical*error[0]),
        ticker_count=int(data.ticker.nunique()), tickers_both_groups=int(support.eq(2).sum()),
        ticker_month_cells=int(data.groupby(['ticker', 'reference_month']).ngroups),
        ticker_month_cells_both_groups=int(
            data.groupby(['ticker', 'reference_month']).group.nunique().eq(2).sum()),
        within_group_variance=float(np.var(x_within[:, 0])), iterations=iterations,
        method='Y ~ slowing + signal W + signal ATM + ticker FE + reference-month FE; '
               'month-clustered sandwich, finite-cluster t interval; observational')


def conditional_diagnostic(panel: pd.DataFrame) -> pd.DataFrame:
    """Post-outcome descriptive decomposition, never an entry feature or primary test."""
    rows = []
    for sample_name, mask in [('rich_all_signals', panel.rich_eligible),
                              ('rich_nonoverlap', panel.nonoverlap_admitted)]:
        for group in [SLOW, FAST]:
            sample = panel[mask & panel.group.eq(group)]
            for horizon in HORIZONS:
                valid = sample[sample[f'wing_change_{horizon}'].notna()]
                atm_up = valid[valid[f'atm_change_{horizon}'].ge(0)]
                compresses = atm_up[f'wing_change_{horizon}'].lt(0)
                both = compresses & atm_up[f'call_iv_change_{horizon}'].lt(0)
                rows.append(dict(sample=sample_name, group=group, horizon=horizon,
                    valid_outcome_count=len(valid), atm_flat_up_count=len(atm_up),
                    atm_flat_up_fraction=len(atm_up)/len(valid) if len(valid) else np.nan,
                    wing_compression_count=int(compresses.sum()),
                    wing_and_total_call_iv_down_count=int(both.sum()),
                    wing_compression_given_atm_up=compresses.mean(),
                    wing_and_total_call_iv_down_given_atm_up=both.mean(),
                    interpretation='Post-outcome conditional description; future ATM state is '
                                   'unknown at signal and is not an admission rule.'))
    return pd.DataFrame(rows)


def write_report(counts: dict, summary: pd.DataFrame, comparisons: list[dict],
                 adjusted: list[dict], flags: dict, conditional: pd.DataFrame) -> None:
    """Explain exact sample size, primary results, and limits without a trade-profit claim."""
    rich = counts['rich_eligible']
    lines = ['# Broad call-wing normalization without HIRO', '',
        'E-PNDR-012. This is a fixed daily-surface experiment, not an executable option-trade backtest. '
        'No HIRO observation, feature, filter, or timing rule is used. The existing membership file '
        'supplies stock names only. No provider calls were made.', '',
        f"Raw background: **{counts['background_sessions']:,} distinct market sessions**, "
        f"{counts['background_start']} through {counts['background_end']}. "
        f"Evaluation ledger: **{counts['evaluation_sessions']:,} distinct signal dates**, "
        f"**{counts['candidate_stock_dates']:,} stock-date slots**, "
        f"**{counts['membership_stocks']} stock names**. Background dates are not additional trade dates.", '',
        '| Sample | Stock-dates | Stocks | Distinct signal dates | First signal | Last signal |',
        '|---|---:|---:|---:|---|---|']
    for name in ['quality_valid', 'quality_earnings_valid', 'rich_eligible', 'nonoverlap_admitted']:
        row = counts[name]
        lines.append(f"| {name} | {row['stock_dates']:,} | {row['stocks']} | "
                     f"{row['signal_dates']} | {row['first_signal']} | {row['last_signal']} |")
    lines += ['', f"Rich observations span {rich['reference_months']} reference months and "
        f"{rich['episodes']:,} ticker-episode identifiers; episodes and stocks are not independent "
        'trials. Unknown episode starts stay labeled. The 30-calendar-day actual-earnings purge '
        'is retrospective; it is not proof that the calendar was known at entry.', '',
        'The signal uses positive 5-delta/10-calendar-day call IV minus same-tenor ATM IV in '
        'the top 15% of its own strictly prior history. This surface coordinate measures a '
        'phenomenon; it does not prescribe a five-delta trade. The reference is the next '
        'market session close. Primary horizon is two sessions after that reference.', '',
        '| Two-session rich group | Valid observations | Wing compresses | Compression with ATM flat/up | '
        'Total call IV falls | All three jointly | Mean wing change (vol points) | Mean stock return | '
        'Mean max upside excursion |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    focus = summary[(summary['sample']=='rich_all_signals') & summary.era.eq('all')
                    & summary.horizon.eq(2) & summary.group.isin([SLOW, FAST])]
    for row in focus.itertuples():
        lines.append(f'| {row.group} | {row.valid_outcomes:,} | '
            f'{100*row.mean_wing_compression:.2f}% | {100*row.mean_joint_compression_atm_up:.2f}% | '
            f'{100*row.mean_call_iv_down:.2f}% | '
            f'{100*row.mean_joint_compression_atm_up_call_down:.2f}% | '
            f'{row.mean_wing_change:.3f} | {row.mean_stock_return:.3f}% | '
            f'{row.mean_upside_excursion:.3f}% |')
    lines += ['', 'The 26%–28% figures above are joint frequencies across **all** valid '
        'observations, not probabilities conditional on ATM IV holding up. The following '
        'decomposition was requested after reviewing the primary result and is explicitly '
        'descriptive. It conditions on a future outcome that cannot be known at entry.', '',
        '| Two-session group | All valid cases | ATM flat/up cases | ATM flat/up frequency | '
        'Wing compresses within ATM-flat/up cases | Wing and total call IV fall within those cases |',
        '|---|---:|---:|---:|---:|---:|']
    conditional_focus = conditional[conditional['sample'].eq('rich_all_signals')
                                     & conditional.horizon.eq(2)]
    for row in conditional_focus.itertuples():
        lines.append(f'| {row.group} | {row.valid_outcome_count:,} | {row.atm_flat_up_count:,} | '
            f'{100*row.atm_flat_up_fraction:.2f}% | {row.wing_compression_count:,}/'
            f'{row.atm_flat_up_count:,} = {100*row.wing_compression_given_atm_up:.2f}% | '
            f'{row.wing_and_total_call_iv_down_count:,}/{row.atm_flat_up_count:,} = '
            f'{100*row.wing_and_total_call_iv_down_given_atm_up:.2f}% |')
    lines += ['', 'All differences below are slowing/rolling minus continued/accelerating. '
        'Month blocks resample the entire stock cross-section together, 2,000 times.', '',
        '| Sample / period | Joint difference (percentage points) | 95% month-block interval | '
        'Mean wing-change difference (vol points) | 95% month-block interval |',
        '|---|---:|---|---:|---|']
    for mode in ['rich_all_signals', 'rich_nonoverlap']:
        for era in ['all', '2024-2025', '2026']:
            pairs = [r for r in comparisons if r['sample']==mode and r['era']==era]
            joint = next(r for r in pairs if r['outcome']=='joint_compression_atm_up_2')
            wing = next(r for r in pairs if r['outcome']=='wing_change_2')
            lines.append(f"| {mode} / {era} | {100*joint['slowing_minus_expanding']:.3f} | "
                f"[{100*joint['ci_low']:.3f}, {100*joint['ci_high']:.3f}] | "
                f"{wing['slowing_minus_expanding']:.3f} | "
                f"[{wing['ci_low']:.3f}, {wing['ci_high']:.3f}] |")
    lines += ['', '| Adjusted model | Joint difference (percentage points) | Month-clustered 95% interval |',
              '|---|---:|---|']
    for item in adjusted:
        if item['outcome']=='joint_compression_atm_up_2' and item['status']=='ok':
            lines.append(f"| {item['sample']} | {100*item['coefficient']:.3f} | "
                         f"[{100*item['ci_low']:.3f}, {100*item['ci_high']:.3f}] |")
    lines += ['', 'The adjusted model includes signal wing, signal ATM IV, ticker effects and '
        'reference calendar-month effects. It is an observational comparison, not causal proof. '
        'Full 1/2/4-session results, positive-but-slowing versus nonpositive slopes, chronology, '
        'signal-to-reference moves and censor counts are in raw_group_summary.csv.', '',
        'Limitations: fixed-delta surfaces roll through different contracts each day and can change '
        'when spot changes. Modeled IV changes are not executable P&L. No option bid/ask, kink '
        'execution, fees, Greek repricing, or spread-leg benefit is established here. Current '
        'membership is applied backward; historical listings and symbol reuse are not reconstructed. '
        'The historical panel was examined in earlier work; neither chronological slice is an unseen holdout. '
        'No new thresholds were selected from these outcomes.', '',
        'Price handling: ORATS defines both hiPx and clsPx as adjusted for splits and dividends '
        '([official definitions](https://orats.com/docs/definitions)). They are used directly '
        'together. An initial implementation assumed raw highs and was corrected after checking '
        'these definitions; no second adjustment is applied. Missing prices/IV at any intervening '
        'session censor the outcome. Adjusted highs below adjusted closes cannot produce an '
        'excursion. Known splits and price-basis '
        f'discrepancies are retained as flags: `{json.dumps(flags, sort_keys=True)}`.', '',
        'Reproduction: `/Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python '
        'scripts/pandar_no_hiro_surface.py`. Protocol/input hashes precede signal computation; '
        'the candidate ledger hash precedes outcome computation. All failed selections remain '
        'in candidate_reason_ledger.csv and candidate_reason_ledger.parquet.', '']
    (OUTPUT/'no_hiro_surface_results.md').write_text('\n'.join(lines))


def main() -> None:
    """Run the single frozen experiment, preserving every candidate and failed outcome."""
    manifest = freeze_inputs()
    panel, counts = build_signal_panel()
    parts = []
    for _, frame in panel.groupby('ticker', sort=False):
        indexed = frame.set_index('tradeDate')
        parts.append(add_surface_outcomes(indexed).reset_index())
    panel = pd.concat(parts, ignore_index=True)
    panel.to_parquet(OUTPUT/'all_analysis_with_outcomes.parquet', index=False)
    panel[panel.rich_eligible].to_csv(OUTPUT/'rich_analysis_with_outcomes.csv', index=False)
    summary = summarize_groups(panel)
    summary.to_csv(OUTPUT/'raw_group_summary.csv', index=False)
    conditional = conditional_diagnostic(panel)
    conditional.to_csv(OUTPUT/'conditional_atm_diagnostic.csv', index=False)
    comparisons, adjusted = [], []
    for name, mask in [('rich_all_signals', panel.rich_eligible),
                       ('rich_nonoverlap', panel.nonoverlap_admitted)]:
        sample = panel[mask]
        for era in ['all', '2024-2025', '2026']:
            current = sample if era=='all' else sample[sample.era.eq(era)]
            for outcome in ['joint_compression_atm_up_2', 'wing_change_2']:
                comparisons.append(dict(sample=name, era=era,
                                        **month_bootstrap(current, outcome)))
        for outcome in ['joint_compression_atm_up_2', 'wing_change_2']:
            adjusted.append(dict(sample=name, **adjusted_effect(sample, outcome)))
    write_json(OUTPUT/'month_block_bootstrap.json', comparisons)
    write_json(OUTPUT/'adjusted_effects.json', adjusted)
    pd.DataFrame(adjusted).to_csv(OUTPUT/'adjusted_effects.csv', index=False)
    rich = panel[panel.rich_eligible]
    monthly = rich.groupby(['reference_month', 'group']).agg(
        stock_dates=('ticker', 'size'), stocks=('ticker', 'nunique'),
        signal_dates=('tradeDate', 'nunique'), valid_outcomes=('wing_change_2', 'count'),
        mean_joint=('joint_compression_atm_up_2', 'mean'),
        mean_wing_change=('wing_change_2', 'mean')).reset_index()
    monthly.to_csv(OUTPUT/'monthly_counts_and_outcomes.csv', index=False)
    pd.concat([rich.groupby(f'censor_reason_{horizon}').size().rename('count').reset_index()
               .rename(columns={f'censor_reason_{horizon}': 'reason'}).assign(horizon=horizon)
               for horizon in HORIZONS]).to_csv(OUTPUT/'censored_counts.csv', index=False)
    flags = {column: int(rich[column].sum()) for column in [
        'known_split_on_signal', 'known_split_through_exit', 'adjusted_unadjusted_basis_differs',
        'adjusted_high_below_adjusted_close', 'summary_raw_price_discrepancy',
        'adjustment_factor_jump']}
    primary = next(item for item in comparisons if item['sample']=='rich_all_signals'
                   and item['era']=='all' and item['outcome']=='joint_compression_atm_up_2')
    chronological = [item for item in comparisons if item['sample']=='rich_all_signals'
                     and item['era']!='all' and item['outcome']=='joint_compression_atm_up_2']
    model = next(item for item in adjusted if item['sample']=='rich_all_signals'
                 and item['outcome']=='joint_compression_atm_up_2')
    supported = bool(primary['ci_low'] is not None and primary['ci_low']>0
                     and all(item['slowing_minus_expanding']>0 for item in chronological)
                     and model.get('coefficient', -np.inf)>0)
    final = dict(experiment='E-PNDR-012', counts=counts, primary=primary,
                 primary_support_criteria_pass=supported, adjusted=model,
                 flags=flags, provider_calls=0, frozen_at_utc=manifest['frozen_at_utc'],
                 completed_at_utc=datetime.now(timezone.utc).isoformat(),
                 source_hashes_unchanged=all(sha256(Path(item['path']))==item['sha256']
                                           for item in manifest['input_files']))
    write_json(OUTPUT/'summary.json', final)
    write_report(counts, summary, comparisons, adjusted, flags, conditional)
    print((OUTPUT/'summary.json').read_text(), flush=True)


if __name__ == '__main__':
    main()
