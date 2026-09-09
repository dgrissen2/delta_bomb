"""Protect inclusive earnings gates and deterministic pre-outcome population selection."""
from pathlib import Path
import sys

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from pandar_hypothesis_population import (
    PopulationConfig,
    freeze_population,
    read_signal_features,
)


def inputs() -> dict:
    """Small real-calendar June fixture with metadata independent of event max date."""
    sessions = pd.to_datetime([
        '2026-06-11', '2026-06-12', '2026-06-15', '2026-06-16',
        '2026-06-17', '2026-06-18', '2026-06-22', '2026-06-23',
        '2026-06-24', '2026-06-25', '2026-06-26', '2026-06-29',
    ])
    return dict(
        features=pd.DataFrame([
            dict(ticker='AAA', tradeDate='2026-06-11', eligible=True, wing=2.,
                 wing_rank=90., episode_id=1),
            dict(ticker='AAA', tradeDate='2026-06-12', eligible=True, wing=2.,
                 wing_rank=91., episode_id=1),
            dict(ticker='AAA', tradeDate='2026-06-18', eligible=True, wing=2.,
                 wing_rank=92., episode_id=1),
        ]),
        membership=pd.DataFrame([dict(ticker='AAA', single_stock=True)]),
        hiro=pd.DataFrame([
            dict(ticker='AAA', session_date=d.strftime('%Y-%m-%d'),
                 source_path=f'/archive/{d:%Y-%m-%d}.csv') for d in sessions
        ]),
        earnings=pd.DataFrame([dict(ticker='AAA', earnDate='2026-07-30')]),
        splits=pd.DataFrame(columns=['ticker', 'splitDate']),
        coverage=pd.DataFrame([dict(
            ticker='AAA', earnings_status='ok', earnings_coverage_start='2024-01-01',
            earnings_coverage_end='2026-09-04', splits_status='ok',
            splits_coverage_start='1900-01-01', splits_coverage_end='2026-09-04',
        )]),
        sessions=sessions,
        config=PopulationConfig(),
    )


def test_inclusive_day_30_and_entry_recheck() -> None:
    args = inputs()
    args['features'] = args['features'].iloc[:1]
    args['earnings'].loc[0, 'earnDate'] = '2026-07-11'
    row = freeze_population(**args).iloc[0]
    assert row.signal_earnings_status == 'event_in_next_30_days'
    assert not row.selected
    args['earnings'].loc[0, 'earnDate'] = '2026-07-12'
    row = freeze_population(**args).iloc[0]
    assert row.signal_earnings_status == 'clear'
    assert row.entry_earnings_status == 'event_in_next_30_days'
    assert not row.selected


def test_signal_day_event_excluded_even_when_entry_is_after_event() -> None:
    args = inputs()
    args['features'] = args['features'].iloc[:1]
    args['earnings'].loc[0, 'earnDate'] = '2026-06-11'
    row = freeze_population(**args).iloc[0]
    assert row.signal_earnings_status == 'event_in_next_30_days'
    assert row.entry_earnings_status == 'clear'
    assert not row.selected


def test_failed_earlier_row_does_not_consume_episode_or_holding_window() -> None:
    args = inputs()
    args['earnings'].loc[0, 'earnDate'] = '2026-06-11'
    ledger = freeze_population(**args)
    assert ledger.selected.tolist() == [False, True, False]
    assert ledger.iloc[2].selection_status == 'holding_window_overlap'
    assert ledger.iloc[1].holding_deadline == '2026-06-22'


def test_five_session_nonoverlap_uses_exchange_sessions_and_is_order_invariant() -> None:
    args = inputs()
    expected = freeze_population(**args)
    assert expected.selected.tolist() == [True, False, True]
    assert expected.iloc[0].holding_deadline == '2026-06-18'
    args['features'] = args['features'].iloc[::-1]
    actual = freeze_population(**args)
    pd.testing.assert_frame_equal(expected, actual)


def test_unknown_metadata_and_missing_hiro_are_preserved() -> None:
    args = inputs()
    args['coverage'].loc[0, 'earnings_status'] = 'missing'
    args['hiro'] = args['hiro'].iloc[:0]
    ledger = freeze_population(**args)
    assert len(ledger) == 3
    assert not ledger.selected.any()
    assert ledger.signal_earnings_status.eq('metadata_unsupported').all()
    assert ledger.failure_reasons.str.contains('entry_hiro_missing').all()


def test_first_known_event_bounds_metadata_support() -> None:
    args = inputs()
    args['coverage'].loc[0, 'earnings_coverage_start'] = '2026-07-30'
    ledger = freeze_population(**args)
    assert ledger.signal_earnings_status.eq('before_metadata_coverage').all()
    assert not ledger.selected.any()


def test_split_in_holding_window_is_retained_but_not_selected() -> None:
    args = inputs()
    args['splits'] = pd.DataFrame([dict(ticker='AAA', splitDate='2026-06-18')])
    ledger = freeze_population(**args)
    assert ledger.iloc[0].split_status == 'split_in_contract_window'
    assert not ledger.iloc[0].selected


def test_entry_earnings_horizon_must_be_complete_by_cutoff() -> None:
    args = inputs()
    args['features'] = pd.DataFrame([dict(
        ticker='AAA', tradeDate='2026-08-05', eligible=True, wing=2.,
        wing_rank=90., episode_id=4,
    )])
    args['sessions'] = pd.to_datetime([
        '2026-08-05', '2026-08-06', '2026-08-07', '2026-08-10',
        '2026-08-11', '2026-08-12',
    ])
    row = freeze_population(**args).iloc[0]
    assert row.signal_earnings_status == 'clear'
    assert row.entry_earnings_status == 'future_earnings_horizon'
    assert not row.selected


def test_all_dates_and_failed_rank_rows_are_kept() -> None:
    args = inputs()
    args['features'].loc[0, 'wing_rank'] = 84.99
    args['features'].loc[1, 'eligible'] = False
    args['features'].loc[2, 'tradeDate'] = '2026-08-20'
    ledger = freeze_population(**args)
    assert len(ledger) == 3
    assert not ledger.selected.any()
    assert 'rank_below_85' in ledger.iloc[0].failure_reasons
    assert 'surface_ineligible' in ledger.iloc[1].failure_reasons
    assert 'signal_outside_research_bounds' in ledger.iloc[2].failure_reasons


def test_csv_reader_drops_outcomes_before_population_construction(tmp_path: Path) -> None:
    file = tmp_path / 'signals.csv'
    args = inputs()
    f = args['features'].assign(return_2=123., joint_down_2=True)
    f.to_csv(file, index=False)
    read = read_signal_features(file)
    assert 'return_2' not in read
    assert 'joint_down_2' not in read
    assert set(args['features']).issubset(read)


def test_duplicate_inputs_fail_instead_of_multiplying_candidates() -> None:
    args = inputs()
    args['coverage'] = pd.concat([args['coverage'], args['coverage']])
    with pytest.raises(ValueError, match='coverage.*duplicate'):
        freeze_population(**args)


def test_high_percentile_with_negative_or_zero_absolute_wing_is_excluded() -> None:
    args = inputs()
    args['features']['wing'] = [-1., 0., 2.]
    ledger = freeze_population(**args)
    assert ledger.selected.tolist() == [False, False, True]
    assert ledger.iloc[:2].failure_reasons.str.contains('negative_or_zero_call_wing').all()


def test_supported_coverage_without_any_actual_event_rows_fails_closed() -> None:
    args = inputs()
    args['earnings'] = args['earnings'].iloc[:0]
    ledger = freeze_population(**args)
    assert ledger.signal_earnings_status.eq('actual_event_records_missing').all()
    assert not ledger.selected.any()


def test_provider_placeholder_is_rejected_before_population_publication() -> None:
    args = inputs()
    args['earnings'].loc[0, 'earnDate'] = '0000-00-00'
    with pytest.raises(ValueError):
        freeze_population(**args)
