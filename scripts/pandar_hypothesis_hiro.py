"""Build causal HIRO call-flow decisions from local archives, without option outcomes.

The economic rule is unchanged from pandar_leg_timing.py. The explicit archive-quality
assumption is a complete observed five-second grid in (t-30 minutes, t], as used by
these normalized captures. Missing slots, duplicates, and invalid observations make
that decision unavailable; no flow or price is filled. Price confirmation uses the
fifteen preceding minute closing observations, matching the original replay.

These are flow triggers, not executable trades: the actual next-minute chain, Greeks,
bid >= $0.20, sizes and other frozen entry gates remain the caller's responsibility.
Historical capture timestamps do not establish real-time feed receipt or latency.
"""

from __future__ import annotations

import argparse
from functools import lru_cache
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ZONE = 'America/New_York'
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / 'outputs/pandar_hypothesis_2026-09-07'
SOURCE_FIELDS = ['series_group', 'utc_iso', 'delta_call', 'delta_put', 'delta_total',
                 'stock_price', 'row_count']


def decision_times(day: str) -> pd.DatetimeIndex:
    """Return the frozen five-minute decision schedule as offset-aware ET timestamps."""
    return pd.date_range(f'{day} 10:00', f'{day} 14:30', freq='5min', tz=ZONE)


def _base_row(ticker: str, day: str, timestamp: pd.Timestamp) -> dict[str, Any]:
    return dict(
        ticker=ticker, session_date=day, event_at=timestamp, info_cutoff=timestamp,
        action_at=timestamp + pd.Timedelta(minutes=1), series_group='all',
        flow_measure='15-minute signed call delta-notional increments',
        units='USD delta notional', expected_prior_samples=180, expected_current_samples=180,
        prior_samples=0, current_samples=0, missing_slots=360, max_gap_seconds=np.nan,
        prior_call_flow=np.nan, current_call_flow=np.nan, stock_price=np.nan,
        prior_price_low=np.nan, source_last_used=pd.NaT, data_status='unavailable',
        reason='', trigger=False,
    )


def _unavailable(ticker: str, day: str, reason: str) -> pd.DataFrame:
    rows = [_base_row(ticker, day, t) for t in decision_times(day)]
    return pd.DataFrame(rows).assign(reason=reason)


def session_decisions(source: pd.DataFrame, ticker: str, day: str) -> pd.DataFrame:
    """Evaluate one session using only observations at or before each decision cutoff.

    Args:
        source: Normalized capture, possibly containing multiple dates and flow scopes.
        ticker: Underlying symbol from the frozen coverage ledger.
        day: Exchange session date in New York, in ISO date format.

    Returns:
        All 55 scheduled decisions, including unavailable decisions and their reasons.
    """
    missing = sorted(set(SOURCE_FIELDS) - set(source.columns))
    if missing:
        return _unavailable(ticker, day, 'schema_missing:' + ','.join(missing))
    frame = source.loc[source.series_group.eq('all'), SOURCE_FIELDS].copy()
    if frame.empty:
        return _unavailable(ticker, day, 'all_trades_unavailable')
    timestamps = pd.to_datetime(frame.utc_iso, utc=True, errors='coerce')
    if timestamps.isna().any():
        return _unavailable(ticker, day, 'invalid_source_timestamp')
    frame.index = pd.DatetimeIndex(timestamps).tz_convert(ZONE)
    frame = frame.loc[
        (frame.index >= pd.Timestamp(f'{day} 09:30', tz=ZONE))
        & (frame.index <= pd.Timestamp(f'{day} 16:00', tz=ZONE))
    ].sort_index()
    if frame.empty:
        return _unavailable(ticker, day, 'session_rth_unavailable')
    numeric = ['delta_call', 'delta_put', 'delta_total', 'stock_price', 'row_count']
    frame[numeric] = frame[numeric].apply(pd.to_numeric, errors='coerce')
    rows = []
    for timestamp in decision_times(day):
        row = _base_row(ticker, day, timestamp)
        start = timestamp - pd.Timedelta(minutes=30)
        midpoint = timestamp - pd.Timedelta(minutes=15)
        window = frame.loc[(frame.index > start) & (frame.index <= timestamp)]
        expected = pd.date_range(start + pd.Timedelta(seconds=5), timestamp, freq='5s')
        unique_times = window.index.unique()
        row['prior_samples'] = int((window.index <= midpoint).sum())
        row['current_samples'] = int((window.index > midpoint).sum())
        row['missing_slots'] = len(expected.difference(unique_times))
        boundaries = pd.DatetimeIndex([start, *unique_times, timestamp]).sort_values()
        row['max_gap_seconds'] = float(boundaries.to_series().diff().dt.total_seconds().max())
        row['source_last_used'] = window.index.max() if not window.empty else pd.NaT
        reasons = []
        if row['missing_slots']:
            reasons.append('missing_5s_slots')
        if window.index.duplicated().any():
            reasons.append('duplicate_timestamps')
        if len(unique_times.difference(expected)):
            reasons.append('off_grid_timestamps')
        if (not np.isfinite(window[numeric].to_numpy()).all()
                or window.stock_price.le(0).any() or window.row_count.le(0).any()):
            reasons.append('invalid_flow_or_price')
        if not np.isclose(window.delta_total, window.delta_call + window.delta_put,
                          rtol=1e-5, atol=.01, equal_nan=False).all():
            reasons.append('flow_identity_mismatch')
        if reasons:
            row['reason'] = '|'.join(reasons)
        else:
            previous_prices = pd.date_range(midpoint, timestamp - pd.Timedelta(minutes=1),
                                            freq='min')
            row['prior_call_flow'] = float(window.loc[window.index <= midpoint, 'delta_call'].sum())
            row['current_call_flow'] = float(window.loc[window.index > midpoint, 'delta_call'].sum())
            row['stock_price'] = float(window.loc[timestamp, 'stock_price'])
            row['prior_price_low'] = float(window.loc[previous_prices, 'stock_price'].min())
            row['data_status'] = 'available'
            row['trigger'] = bool(row['current_call_flow'] < 0 < row['prior_call_flow']
                                  and row['stock_price'] < row['prior_price_low'])
        rows.append(row)
    return pd.DataFrame(rows)


@lru_cache(maxsize=64)
def _manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def capture_provenance(path: Path, ticker: str, day: str) -> dict[str, Any]:
    """Retain archive and capture metadata without treating capture time as signal time."""
    result: dict[str, Any] = dict(
        source_path=str(path.resolve()), source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        manifest_path='', manifest_sha256='', captured_at_utc='', capture_status='unknown',
        capture_warning='', capture_metadata_path='', capture_metadata_sha256='',
        capture_time_basis='unknown', receipt_time_verified=False,
    )
    for parent in list(path.parents)[:7]:
        manifest_path = parent / 'manifest.json'
        if not manifest_path.is_file():
            continue
        result['manifest_path'] = str(manifest_path)
        result['manifest_sha256'] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        result['capture_metadata_path'] = str(manifest_path)
        result['capture_metadata_sha256'] = result['manifest_sha256']
        try:
            metadata = _manifest(manifest_path)
        except (json.JSONDecodeError, UnicodeDecodeError):
            result['capture_warning'] = 'unreadable_capture_manifest'
            break
        record = metadata.get('tickers', {}).get(ticker, {})
        item = record.get('sessions', {}).get(day, {})
        result['captured_at_utc'] = record.get('captured_at_utc', metadata.get('created_at_utc', ''))
        if result['captured_at_utc']:
            result['capture_time_basis'] = ('ticker_capture' if record.get('captured_at_utc')
                                            else 'manifest_created_at_utc')
        result['capture_status'] = item.get('status', 'unknown')
        for capture in metadata.get('captures', []):
            recorded_path = Path(capture.get('files', {}).get('series_csv', ''))
            path_matches = (recorded_path == path if recorded_path.is_absolute()
                            else path.parts[-len(recorded_path.parts):] == recorded_path.parts)
            if capture.get('ticker') != ticker or not path_matches:
                continue
            summary = capture.get('summary', {})
            result['captured_at_utc'] = summary.get('capture_utc', '')
            result['capture_time_basis'] = 'capture_summary'
            result['capture_status'] = str(capture.get('ok', 'unknown'))
            result['capture_warning'] = summary.get('error', '')
            break
        break
    if not result['captured_at_utc']:
        summary_path = path.parent.parent / 'summary.csv'
        if summary_path.is_file():
            summaries = pd.read_csv(summary_path, usecols=lambda name: name in
                                    {'ticker', 'capture_utc', 'error'})
            if {'ticker', 'capture_utc'}.issubset(summaries):
                matching = summaries.loc[summaries.ticker.eq(ticker)]
                if len(matching) == 1 and pd.notna(matching.iloc[0].capture_utc):
                    result['captured_at_utc'] = matching.iloc[0].capture_utc
                    result['capture_time_basis'] = 'summary_csv'
                    result['capture_metadata_path'] = str(summary_path)
                    result['capture_metadata_sha256'] = hashlib.sha256(summary_path.read_bytes()).hexdigest()
                    result['capture_status'] = 'summary_only'
                    warning = matching.iloc[0].get('error', '')
                    result['capture_warning'] = warning if pd.notna(warning) else ''
    return result


def build_trigger_table(coverage: pd.DataFrame,
                        requests: pd.DataFrame | None = None) -> pd.DataFrame:
    """Load only the requested archived ticker/sessions and preserve unavailable records."""
    keys = ['ticker', 'session_date']
    if coverage.duplicated(keys).any():
        raise ValueError('coverage has duplicate ticker/session rows; freeze source selection first')
    requested = coverage[keys] if requests is None else requests[keys].drop_duplicates()
    selected = requested.merge(coverage, on=keys, how='left', validate='one_to_one')
    tables = []
    for record in selected.sort_values(keys).to_dict('records'):
        ticker, day = record['ticker'], record['session_date']
        source_path = record.get('source_path', record.get('path'))
        provenance: dict[str, Any] = dict(source_path=source_path, source_sha256='')
        if not isinstance(source_path, str) or not Path(source_path).is_file():
            decisions = _unavailable(ticker, day, 'archive_missing')
        else:
            path = Path(source_path)
            try:
                source = pd.read_csv(path, usecols=lambda name: name in SOURCE_FIELDS)
                decisions = session_decisions(source, ticker, day)
                provenance = capture_provenance(path, ticker, day)
            except (OSError, pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError) as exc:
                decisions = _unavailable(ticker, day, f'archive_read_error:{type(exc).__name__}')
        for name, value in provenance.items():
            decisions[name] = value
        tables.append(decisions)
    return pd.concat(tables, ignore_index=True) if tables else pd.DataFrame()


def summarize_candidates(candidates: pd.DataFrame, decisions: pd.DataFrame) -> pd.DataFrame:
    """Summarize next-session signal pairs without selecting or excluding any population."""
    if (pd.to_datetime(candidates.entry_date) <= pd.to_datetime(candidates.tradeDate)).any():
        raise ValueError('entry session must be after the EOD signal session')
    if decisions.empty:
        return candidates.assign(hiro_status='unavailable', unavailable_reasons='archive_missing',
                                 scheduled_decisions=0, valid_decisions=0, trigger_count=0)
    decisions = decisions.copy()
    decisions['event_at'] = pd.to_datetime(decisions.event_at, utc=True).dt.tz_convert(ZONE)
    decisions['action_at'] = pd.to_datetime(decisions.action_at, utc=True).dt.tz_convert(ZONE)
    summaries = []
    for (ticker, day), group in decisions.groupby(['ticker', 'session_date'], sort=True):
        available = group.data_status.eq('available')
        triggers = group.loc[available & group.trigger].sort_values('event_at')
        first = triggers.event_at.iloc[0] if len(triggers) else pd.NaT
        earlier_unavailable = int((~available & group.event_at.lt(first)).sum()) if len(triggers) else None
        summaries.append(dict(
            ticker=ticker, entry_date=day, scheduled_decisions=len(group),
            valid_decisions=int(available.sum()), trigger_count=len(triggers),
            first_event_at=first,
            first_action_at=triggers.action_at.iloc[0] if len(triggers) else pd.NaT,
            earlier_unavailable_decisions=earlier_unavailable,
            first_trigger_history_complete=(earlier_unavailable == 0 if len(triggers) else False),
            hiro_status=('available' if available.all() else 'partial' if available.any()
                         else 'unavailable'),
            unavailable_reasons=';'.join(sorted(set(group.loc[~available, 'reason']))),
        ))
    summary = pd.DataFrame(summaries)
    result = candidates.merge(summary, on=['ticker', 'entry_date'], how='left', validate='many_to_one')
    result['hiro_status'] = result.hiro_status.fillna('unavailable')
    result['unavailable_reasons'] = result.unavailable_reasons.fillna('archive_missing')
    return result


def main() -> None:
    """Write pre-August coverage/trigger diagnostics; no providers or outcomes are accessed."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--coverage', type=Path, default=DEFAULT_OUTPUT / 'hiro_archive_coverage.csv')
    parser.add_argument('--candidates', type=Path, default=DEFAULT_OUTPUT / 'data_readiness.json')
    parser.add_argument('--output-prefix', type=Path, default=DEFAULT_OUTPUT / 'hiro_pre_august')
    args = parser.parse_args()
    if args.candidates.suffix == '.json':
        candidates = pd.DataFrame(json.loads(args.candidates.read_text())['high_skew_next_session_pairs'])
    else:
        candidates = pd.read_csv(args.candidates, usecols=['ticker', 'tradeDate', 'entry_date'])
    candidates = candidates.loc[candidates.entry_date.lt('2026-08-01')].copy()
    coverage = pd.read_csv(args.coverage)
    requests = candidates[['ticker', 'entry_date']].rename(columns={'entry_date': 'session_date'})
    decisions = build_trigger_table(coverage, requests)
    summaries = summarize_candidates(candidates, decisions)
    args.output_prefix.parent.mkdir(parents=True, exist_ok=True)
    decisions.to_parquet(str(args.output_prefix) + '_decisions.parquet', index=False)
    summaries.to_csv(str(args.output_prefix) + '_candidates.csv', index=False)
    report = dict(
        signal_candidates=len(summaries), stocks=int(summaries.ticker.nunique()),
        hiro_status_counts=summaries.hiro_status.value_counts().to_dict(),
        candidates_with_trigger=int(summaries.trigger_count.gt(0).sum()),
        total_triggers=int(decisions.trigger.sum()) if not decisions.empty else 0,
        decision_status_counts=decisions.data_status.value_counts().to_dict() if not decisions.empty else {},
        unavailable_reasons=(decisions.loc[decisions.data_status.ne('available'), 'reason']
                             .value_counts().to_dict() if not decisions.empty else {}),
        coverage_sha256=hashlib.sha256(args.coverage.read_bytes()).hexdigest(),
        quality_assumption='Complete observed 5s slots in (t-30min,t]; no filling or substitutions',
        scope='Individual stock All Trades call increments; RTH America/New_York',
        population_admission='Not assessed; missing HIRO does not exclude clock-control eligibility',
        receipt_latency='Historical captures; real-time receipt timestamp/latency not established',
        provider_requests=0, option_outcomes_read=False,
    )
    Path(str(args.output_prefix) + '_summary.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
