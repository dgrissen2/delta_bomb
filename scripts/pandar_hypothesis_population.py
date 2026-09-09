"""Freeze a retrospective HIRO population from features and metadata, without provider calls.

Earnings use actual historical events, as authorized by the user. This is not an
as-known calendar backtest. Previously examined surface history remains exploratory.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / 'docs/replay/pandar_skew_journey_2026-09-06'
OUTPUT = ROOT / 'outputs/pandar_hypothesis_2026-09-07'
DATA = ROOT / 'data/pandar_hypothesis_2026-09-07'
REQUIRED_FEATURES = ('ticker', 'tradeDate', 'eligible', 'wing_rank', 'wing', 'episode_id')
# Explicit projection prevents the existing surface study's outcome columns being read.
FEATURE_COLUMNS = (
    *REQUIRED_FEATURES, 'stockPrice', 'confidence', 'confidence_pct',
    'callskew30', 'callskew30_rank', 'age', 'left_censored', 'intensity',
    'peak_minus_wing', 'exit_age', 'rv30', 'rv60', 'variance_premium30',
    'variance_premium60', 'iv10d', 'iv30d', 'iv60d', 'exErnIv10d',
    'exErnIv30d', 'exErnIv60d', 'dlt5Iv10d', 'dlt5Iv30d',
    'earnings_premium10', 'wing_slope', 'wing_acceleration', 'rolling_over',
    'expanding', 'iv10_slope', 'iv10_acceleration', 'price_acceleration',
    'prior_three_return', 'charlie_exhaustion', 'both_premia_positive',
    'premia_available', 'dollar_turnover20', 'session_index',
)
COVERAGE_COLUMNS = (
    'ticker', 'earnings_status', 'earnings_coverage_start', 'earnings_coverage_end',
    'splits_status', 'splits_coverage_start', 'splits_coverage_end',
)


@dataclass(frozen=True)
class PopulationConfig:
    """Frozen population rules; execution and strike selection remain downstream."""

    signal_start: str = '2024-01-02'
    signal_end: str = '2026-08-05'
    observation_cutoff: str = '2026-09-04'
    earnings_days: int = 30
    rank_minimum: float = 85.
    entry_session_offset: int = 1
    holding_sessions: int = 5

    def __post_init__(self) -> None:
        if pd.Timestamp(self.signal_start) > pd.Timestamp(self.signal_end):
            raise ValueError('signal_start must not follow signal_end')
        if self.earnings_days < 0 or self.entry_session_offset < 1:
            raise ValueError('Invalid earnings window or noncausal entry offset')
        if self.holding_sessions < 1:
            raise ValueError('holding_sessions must be positive')


def require_columns(frame: pd.DataFrame, columns: tuple[str, ...], label: str) -> None:
    """Reject incomplete schemas before producing an apparently valid population."""
    missing = set(columns) - set(frame)
    if missing:
        raise ValueError(f'{label} missing columns: {sorted(missing)}')


def unique_rows(frame: pd.DataFrame, keys: list[str], label: str) -> None:
    """Avoid ambiguous metadata and accidental Cartesian joins."""
    if frame[keys].isna().any().any():
        raise ValueError(f'{label} has null keys: {keys}')
    if frame.duplicated(keys).any():
        raise ValueError(f'{label} contains duplicate keys: {keys}')


def dates(values: pd.Series) -> pd.Series:
    """Normalize date-only metadata without silently accepting invalid dates."""
    parsed = pd.to_datetime(values, errors='raise', utc=True)
    if parsed.isna().any():
        raise ValueError('Null date in required date metadata')
    return parsed.dt.tz_convert(None).dt.normalize()


def true_value(value: object) -> bool:
    """Handle CSV boolean values without treating the string False as truthy."""
    if pd.isna(value):
        return False
    if value in (True, 1, 'True', 'true', '1'):
        return True
    if value in (False, 0, 'False', 'false', '0'):
        return False
    raise ValueError(f'Invalid boolean value: {value!r}')


def read_table(path: Path, columns: tuple[str, ...] | None = None) -> pd.DataFrame:
    """Read local tabular inputs, optionally projecting a strict column allowlist."""
    if path.suffix == '.parquet':
        if columns is None:
            return pd.read_parquet(path)
        import pyarrow.parquet as pq
        available = set(pq.ParquetFile(path).schema.names)
        return pd.read_parquet(path, columns=[c for c in columns if c in available])
    return pd.read_csv(path, usecols=None if columns is None else lambda c: c in columns)


def read_signal_features(path: Path) -> pd.DataFrame:
    """Load only frozen signal features, excluding every outcome column."""
    frame = read_table(path, FEATURE_COLUMNS)
    require_columns(frame, REQUIRED_FEATURES, 'features')
    return frame


def event_lookup(frame: pd.DataFrame, column: str) -> dict[str, pd.DatetimeIndex]:
    """Create sorted, deduplicated actual-event date indexes per ticker."""
    require_columns(frame, ('ticker', column), column)
    if frame.empty:
        return {}
    frame = frame[['ticker', column]].copy()
    frame[column] = dates(frame[column])
    return {
        str(ticker): pd.DatetimeIndex(group[column].drop_duplicates().sort_values())
        for ticker, group in frame.groupby('ticker', sort=True)
    }


def coverage_gate(record: dict, kind: str, start: pd.Timestamp,
                  end: pd.Timestamp) -> str:
    """Require explicit supported coverage, rather than treating missing events as clean."""
    if record.get(f'{kind}_status') != 'ok':
        return 'metadata_unsupported'
    # freeze_population parses each coverage column once, not once per signal row.
    begin = record.get(f'{kind}_coverage_start', pd.NaT)
    finish = record.get(f'{kind}_coverage_end', pd.NaT)
    if pd.isna(begin) or pd.isna(finish):
        return 'metadata_unsupported'
    if start < begin:
        return 'before_metadata_coverage'
    if end > finish:
        return 'after_metadata_coverage'
    return 'clear'


def earnings_gate(day: pd.Timestamp | None, events: pd.DatetimeIndex,
                  coverage: dict, config: PopulationConfig) -> tuple[str, str | None]:
    """Exclude actual earnings inclusively on day through day+30, including entry recheck."""
    if day is None:
        return 'entry_session_unavailable', None
    horizon = day + pd.Timedelta(days=config.earnings_days)
    position = events.searchsorted(day)
    next_event = events[position] if position < len(events) else None
    next_date = next_event.strftime('%Y-%m-%d') if next_event is not None else None
    if horizon > pd.Timestamp(config.observation_cutoff):
        return 'future_earnings_horizon', next_date
    support = coverage_gate(coverage, 'earnings', day, horizon)
    if support != 'clear':
        return support, next_date
    if events.empty:
        return 'actual_event_records_missing', None
    if next_event is not None and next_event <= horizon:
        return 'event_in_next_30_days', next_date
    return 'clear', next_date


def split_gate(signal: pd.Timestamp, deadline: pd.Timestamp | None,
               events: pd.DatetimeIndex, coverage: dict,
               config: PopulationConfig) -> str:
    """Keep unverified split-adjusted deliverables out of exact-contract candidates."""
    if deadline is None:
        return 'holding_deadline_unavailable'
    if deadline > pd.Timestamp(config.observation_cutoff):
        return 'holding_deadline_after_cutoff'
    support = coverage_gate(coverage, 'splits', signal, deadline)
    if support != 'clear':
        return support
    first = events.searchsorted(signal)
    if first < len(events) and events[first] <= deadline:
        return 'split_in_contract_window'
    return 'clear'


def freeze_population(
    features: pd.DataFrame,
    membership: pd.DataFrame,
    hiro: pd.DataFrame,
    earnings: pd.DataFrame,
    splits: pd.DataFrame,
    coverage: pd.DataFrame,
    sessions: pd.DatetimeIndex,
    config: PopulationConfig,
) -> pd.DataFrame:
    """Retain every supplied signal row and select eligible rows with five-session blocking.

    Earlier rejected rows never consume an episode or holding window. HIRO admission
    here proves entry-date archive presence only; minute validity and exact contracts
    must be checked downstream. No price outcomes participate in any decision.
    """
    require_columns(features, REQUIRED_FEATURES, 'features')
    require_columns(membership, ('ticker', 'single_stock'), 'membership')
    require_columns(hiro, ('ticker', 'session_date', 'source_path'), 'hiro')
    require_columns(coverage, COVERAGE_COLUMNS, 'coverage')
    unique_rows(features, ['ticker', 'tradeDate'], 'features')
    unique_rows(membership, ['ticker'], 'membership')
    unique_rows(coverage, ['ticker'], 'coverage')
    unique_rows(hiro, ['ticker', 'session_date'], 'hiro')
    rows = features[[c for c in FEATURE_COLUMNS if c in features]].copy()
    rows['tradeDate'] = dates(rows.tradeDate)
    unique_rows(rows, ['ticker', 'tradeDate'], 'features normalized dates')
    rows = rows.sort_values(['tradeDate', 'ticker']).reset_index(drop=True)
    stock_names = set(membership.loc[membership.single_stock.map(true_value), 'ticker'])
    coverage = coverage.copy()
    for column in COVERAGE_COLUMNS:
        if column.endswith(('_start', '_end')):
            coverage[column] = pd.to_datetime(coverage[column], errors='coerce')
    coverage_by_ticker = coverage.set_index('ticker').to_dict('index')
    hiro = hiro.copy()
    hiro['session_date'] = dates(hiro.session_date).dt.strftime('%Y-%m-%d')
    unique_rows(hiro, ['ticker', 'session_date'], 'hiro normalized dates')
    archive = hiro.set_index(['ticker', 'session_date']).source_path.to_dict()
    earnings_by_ticker = event_lookup(earnings, 'earnDate')
    splits_by_ticker = event_lookup(splits, 'splitDate')
    sessions = pd.DatetimeIndex(pd.to_datetime(sessions, utc=True)).tz_convert(None)
    sessions = sessions.normalize().drop_duplicates().sort_values()
    session_position = {day: position for position, day in enumerate(sessions)}
    empty_dates = pd.DatetimeIndex([])
    last_deadline: dict[str, pd.Timestamp] = {}
    last_selected: dict[str, str] = {}
    result: list[dict] = []
    for row in rows.to_dict('records'):
        signal = row['tradeDate']
        ticker = row['ticker']
        signal_date = signal.strftime('%Y-%m-%d')
        record = coverage_by_ticker.get(ticker, {})
        position = session_position.get(signal)
        entry_position = position + config.entry_session_offset if position is not None else None
        entry = (sessions[entry_position]
                 if entry_position is not None and entry_position < len(sessions) else None)
        holding_dates = ([] if entry_position is None else
                         list(sessions[entry_position:entry_position + config.holding_sessions]))
        deadline = holding_dates[-1] if len(holding_dates) == config.holding_sessions else None
        event_dates = earnings_by_ticker.get(ticker, empty_dates)
        signal_status, signal_next = earnings_gate(signal, event_dates, record, config)
        entry_status, entry_next = earnings_gate(entry, event_dates, record, config)
        split_status = split_gate(signal, deadline, splits_by_ticker.get(ticker, empty_dates),
                                  record, config)
        failures: list[str] = []
        if ticker not in stock_names:
            failures.append('not_current_hiro_stock')
        if not pd.Timestamp(config.signal_start) <= signal <= pd.Timestamp(config.signal_end):
            failures.append('signal_outside_research_bounds')
        if not true_value(row['eligible']):
            failures.append('surface_ineligible')
        rank = pd.to_numeric(row['wing_rank'], errors='coerce')
        if pd.isna(rank) or rank < config.rank_minimum:
            failures.append(f'rank_below_{config.rank_minimum:g}')
        wing = pd.to_numeric(row['wing'], errors='coerce')
        if pd.isna(wing) or wing <= 0:
            failures.append('negative_or_zero_call_wing')
        if entry is None:
            failures.append('entry_session_unavailable')
        if deadline is None:
            failures.append('holding_deadline_unavailable')
        for prefix, status in [('signal_earnings', signal_status),
                               ('entry_earnings', entry_status), ('splits', split_status)]:
            if status != 'clear':
                failures.append(f'{prefix}:{status}')
        entry_date = entry.strftime('%Y-%m-%d') if entry is not None else None
        entry_path = archive.get((ticker, entry_date))
        if not isinstance(entry_path, str) or not entry_path.strip():
            failures.append('entry_hiro_missing')
        base_eligible = not failures
        blocking_signal = None
        selection_status = 'failed_population_filters'
        if base_eligible:
            if ticker in last_deadline and entry <= last_deadline[ticker]:
                failures.append('holding_window_overlap')
                selection_status = 'holding_window_overlap'
                blocking_signal = last_selected[ticker]
            else:
                last_deadline[ticker] = deadline
                last_selected[ticker] = signal_date
                selection_status = 'selected'
        row.update(
            tradeDate=signal_date, signal_id=f'{ticker}:{signal_date}',
            entry_date=entry_date,
            holding_deadline=deadline.strftime('%Y-%m-%d') if deadline is not None else None,
            signal_earnings_status=signal_status, entry_earnings_status=entry_status,
            signal_next_actual_earnings=signal_next, entry_next_actual_earnings=entry_next,
            split_status=split_status, entry_hiro_source_path=entry_path,
            population_eligible_before_nonoverlap=base_eligible,
            selection_status=selection_status, selected=selection_status == 'selected',
            blocking_signal_date=blocking_signal, failure_reasons=';'.join(failures),
            earnings_policy='retrospective_actual_event_exclusion',
            historical_universe_basis='current_hiro_stock_set_applied_backward',
            surface_evaluation_status='previously_examined_exploratory_history',
            hiro_coverage_basis='entry_date_presence_only',
        )
        for number in range(config.holding_sessions):
            day = holding_dates[number] if number < len(holding_dates) else None
            label = day.strftime('%Y-%m-%d') if day is not None else None
            row[f'holding_session_{number + 1}'] = label
            row[f'hiro_source_path_{number + 1}'] = archive.get((ticker, label))
        result.append(row)
    return pd.DataFrame(result)


def file_hash(path: Path) -> str:
    """Hash inputs/outputs without loading or exposing credential material."""
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def main() -> None:
    """Write an auditable population ledger and selected subset from local files."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--features', type=Path, default=RESEARCH / 'high_rank_signal_ledger.csv')
    parser.add_argument('--membership', type=Path, default=RESEARCH / 'hiro_universe.csv')
    parser.add_argument('--hiro', type=Path, default=OUTPUT / 'hiro_archive_coverage.csv')
    parser.add_argument('--earnings', type=Path, default=DATA / 'earnings.parquet')
    parser.add_argument('--splits', type=Path, default=DATA / 'splits.parquet')
    parser.add_argument('--coverage', type=Path, default=DATA / 'metadata_coverage.csv')
    parser.add_argument('--sessions', type=Path,
                        default=RESEARCH / 'daily_features_and_outcomes.parquet')
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    source_paths = {key: getattr(args, key) for key in (
        'features', 'membership', 'hiro', 'earnings', 'splits', 'coverage', 'sessions',
    )}
    input_hashes = {key: {'path': str(path.resolve()), 'sha256': file_hash(path)}
                    for key, path in source_paths.items()}
    config = PopulationConfig()
    population = freeze_population(
        features=read_signal_features(args.features), membership=read_table(args.membership),
        hiro=read_table(args.hiro), earnings=read_table(args.earnings, ('ticker', 'earnDate')),
        splits=read_table(args.splits, ('ticker', 'splitDate')), coverage=read_table(args.coverage),
        sessions=pd.DatetimeIndex(read_table(args.sessions, ('tradeDate',)).tradeDate),
        config=config,
    )
    if population.empty:
        raise ValueError('No input signal rows; refusing to publish an empty population silently')
    for key, path in source_paths.items():
        if file_hash(path) != input_hashes[key]['sha256']:
            raise ValueError(f'Input changed during population freeze: {key}')
    args.output.mkdir(parents=True, exist_ok=True)
    artifacts = {
        'population_ledger.csv': population,
        'selected_population.csv': population[population.selected],
        'future_earnings_horizon.csv': population[
            population.signal_earnings_status.eq('future_earnings_horizon')
            | population.entry_earnings_status.eq('future_earnings_horizon')
        ],
    }
    for name, frame in artifacts.items():
        frame.to_csv(args.output / name, index=False)
    manifest = dict(
        schema_version=1, frozen_at_utc=datetime.now(timezone.utc).isoformat(),
        implementation={'path': str(Path(__file__).resolve()),
                        'sha256': file_hash(Path(__file__))},
        config=asdict(config), inputs=input_hashes,
        outputs={name: {'path': str((args.output / name).resolve()),
                        'sha256': file_hash(args.output / name), 'rows': len(frame)}
                 for name, frame in artifacts.items()},
        selection_counts=population.selection_status.value_counts().to_dict(),
        source_feature_columns=list(read_signal_features(args.features).columns),
        provider_calls=0, outcomes_read=False,
        earnings_policy='retrospective_actual_event_exclusion_user_authorized',
        strict_as_known_schedule_is_not_admission_policy=True,
        nonoverlap='Chronological first eligible signal; block ticker through fifth holding session',
        hiro_gate='Entry-session archive presence only; downstream minute validity required',
        exact_contracts='Not selected; downstream chain, quote, deliverable and execution gates remain',
        universe='Current HIRO stock set applied backward; not historical point-in-time membership',
        evaluation='Previously examined 2024–2026 surface outputs are exploratory',
        calendar='Observed session dates from input surface panel; no business-day shortcut',
    )
    (args.output / 'population_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest['selection_counts'], sort_keys=True))


if __name__ == '__main__':
    main()
