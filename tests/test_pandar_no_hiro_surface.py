"""Causal safeguards for the broad, clock-referenced call-wing surface experiment."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from pandar_no_hiro_surface import (
    add_surface_outcomes,
    adjusted_effect,
    earnings_status,
    month_bootstrap,
    nonoverlap_mask,
    price_basis,
    prior_ranks,
    wing_state,
)


def test_earnings_exclusion_is_inclusive_and_requires_full_coverage():
    coverage = {'earnings_status': 'ok', 'earnings_coverage_start': '2020-01-01',
                'earnings_coverage_end': '2026-09-04'}
    dates = pd.DatetimeIndex(['2026-06-01', '2026-06-02', '2026-07-02'])
    events = pd.DatetimeIndex(['2026-07-01'])
    assert earnings_status(dates, events, coverage).tolist() == [
        'event_in_next_30_days', 'event_in_next_30_days', 'clear']
    assert earnings_status(pd.DatetimeIndex(['2026-08-06']), events, coverage).iloc[0] == (
        'future_earnings_horizon')
    assert earnings_status(dates, events, {}).eq('metadata_unsupported').all()


def test_signal_and_next_session_earnings_windows_are_separate():
    coverage = {'earnings_status': 'ok', 'earnings_coverage_start': '2020-01-01',
                'earnings_coverage_end': '2026-09-04'}
    events = pd.DatetimeIndex(['2026-07-02'])
    result = earnings_status(pd.DatetimeIndex(['2026-06-01', '2026-06-02']), events, coverage)
    assert result.tolist() == ['clear', 'event_in_next_30_days']


def outcome_frame():
    dates = pd.bdate_range('2026-06-01', periods=7)
    return pd.DataFrame({'clsPx': [100., 200., 190., 180., 175., 170., 165.],
                         'iv10d': [.5, .4, .42, .43, .44, .45, .46],
                         'dlt5Iv10d': [.8, .6, .59, .58, .57, .56, .55],
                         'wing': [30., 20., 17., 15., 13., 11., 9.],
                         'adjusted_high': [101., 201., 205., 195., 190., 185., 180.]},
                        index=dates)


def test_reference_is_next_session_and_call_iv_identity_holds():
    result = add_surface_outcomes(outcome_frame())
    assert np.isclose(result.stock_return_2.iloc[0], -10.)
    assert np.isclose(result.wing_change_2.iloc[0], -5.)
    assert np.isclose(result.atm_change_2.iloc[0], 3.)
    assert np.isclose(result.call_iv_change_2.iloc[0], -2.)
    assert result.joint_compression_atm_up_2.iloc[0] == 1
    assert result.joint_compression_atm_up_call_down_2.iloc[0] == 1
    assert np.isclose(result.upside_excursion_2.iloc[0], 2.5)
    assert np.isnan(result.joint_compression_atm_up_4.iloc[-1])


def test_missing_intervening_session_censors_instead_of_jumping():
    frame = outcome_frame()
    frame.loc[frame.index[2], 'clsPx'] = np.nan
    result = add_surface_outcomes(frame)
    assert np.isnan(result.joint_compression_atm_up_2.iloc[0])
    assert np.isnan(result.wing_change_2.iloc[0])
    assert result.censor_reason_2.iloc[0] == 'missing_intervening_price'
    frame = outcome_frame()
    frame.loc[frame.index[2], 'iv10d'] = np.nan
    assert np.isnan(add_surface_outcomes(frame).wing_change_2.iloc[0])


def test_state_requires_seven_complete_values_and_is_causal():
    values = pd.Series([0., 1., 2., 3., 4., 5., 6., 5.])
    result = wing_state(values)
    assert result.state.iloc[6] == 'continued_accelerating'
    assert result.state.iloc[7] == 'positive_slowing'
    changed = values.copy()
    changed.iloc[-1] = 999.
    assert wing_state(changed).state.iloc[6] == result.state.iloc[6]
    values.iloc[2] = np.nan
    assert wing_state(values).state.iloc[6] == 'missing_seven_session_history'


def test_prior_rank_does_not_include_current_or_future_values():
    values = pd.Series([1., 2., 2., 3., 99.])
    result = prior_ranks(values, window=3, minimum=2)
    assert result.iloc[2] == 50.
    assert result.iloc[3] == 100.
    values.iloc[4] = -999.
    assert prior_ranks(values, 3, 2).iloc[:4].equals(result.iloc[:4])


def test_nonoverlap_reservation_includes_exit_and_ignores_outcome_failure():
    frame = pd.DataFrame({'ticker': ['A']*4+['B'], 'session_index': [1, 5, 6, 7, 2],
                          'rich_eligible': [True]*5, 'fake_outcome': [np.nan]*5})
    # Signal 1 references 2 and exits 6; next allowable signal is 7.
    assert nonoverlap_mask(frame).tolist() == [True, False, False, True, True]


def test_provider_adjusted_high_is_not_adjusted_twice():
    frame = pd.DataFrame({'clsPx': [50., 52.], 'unadjClsPx': [100., 104.],
                          'hiPx': [55., 54.], 'stockPrice': [100., 104.]})
    result = price_basis(frame)
    assert result.adjusted_high.tolist() == [55., 54.]
    assert result.adjusted_unadjusted_basis_differs.all()


def test_month_bootstrap_resamples_both_groups_together():
    frame = pd.DataFrame({'reference_month': ['2024-01']*2+['2024-02']*2,
                          'group': ['slowing_rolling', 'continued_accelerating']*2,
                          'outcome': [.8, .3, .9, .4]})
    result = month_bootstrap(frame, 'outcome')
    assert np.isclose(result['ci_low'], .5)
    assert np.isclose(result['ci_high'], .5)
    assert month_bootstrap(frame.iloc[:2], 'outcome')['ci_low'] is None


def test_adjustment_removes_ticker_month_and_continuous_confounders():
    rng = np.random.default_rng(123)
    rows = []
    for ticker in range(4):
        for month in range(8):
            for repeat in range(3):
                group = (ticker+month+repeat) % 2
                wing, atm = rng.normal(10, 3), rng.uniform(.2, .8)
                rows.append(dict(ticker=str(ticker), reference_month=f'2024-{month+1:02}',
                    group='slowing_rolling' if group else 'continued_accelerating',
                    wing=wing, iv10d=atm, outcome=2*group+.3*wing+.2*atm*100+ticker+month))
    result = adjusted_effect(pd.DataFrame(rows), 'outcome')
    assert np.isclose(result['coefficient'], 2)
    assert result['tickers_both_groups'] == 4
