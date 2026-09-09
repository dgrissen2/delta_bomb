"""Protect time ordering, missing-data treatment, episode state and calendar RV."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from pandar_skew_journey import add_outcomes, episode_features, prior_ranks, trailing_variance


def test_rank_uses_only_prior_observations_and_strict_ties():
    x = pd.Series([1., 2., 2., 3., 99.])
    rank = prior_ranks(x, window=3, minimum=2)
    assert np.isnan(rank.iloc[1])
    assert rank.iloc[2] == 50
    assert rank.iloc[3] == 100
    x.iloc[4] = -999
    assert np.allclose(prior_ranks(x, 3, 2).iloc[:4], rank.iloc[:4], equal_nan=True)


def test_episode_age_peak_exit_and_missing_reset():
    rank = pd.Series([84., 86., 90., 88., 86., 84., np.nan, 90.])
    wing = pd.Series([0., 1., 4., 3., 2., 1., np.nan, 5.])
    x = episode_features(rank, wing)
    assert x.age.iloc[:6].tolist() == [0, 1, 2, 3, 4, 0]
    assert x.peak_minus_wing.iloc[4] == 2
    assert x.exit_age.iloc[5] == 4
    assert x.age.iloc[7] == 1 and x.left_censored.iloc[7]
    assert np.isnan(x.age.iloc[6])
    assert np.isclose(x.intensity.iloc[4], (1+5+3+1)/15)


def test_episode_features_do_not_use_future_peak():
    rank = pd.Series([84., 86., 90., 88., 99.])
    wing = pd.Series([0., 1., 4., 3., 999.])
    a = episode_features(rank, wing)
    wing.iloc[-1] = -100
    b = episode_features(rank, wing)
    assert_frame_equal(a.iloc[:-1], b.iloc[:-1])


def test_calendar_variance_uses_trailing_calendar_window():
    dates = pd.bdate_range('2026-01-01', periods=80)
    prices = pd.Series(np.exp(np.arange(80)*.01), index=dates)
    result = trailing_variance(prices, 30)
    assert np.isclose(result.iloc[-1], 252*.01**2)
    prices.iloc[-3] = np.nan
    assert np.isnan(trailing_variance(prices, 30).iloc[-1])
    assert trailing_variance(prices, 60).iloc[:20].isna().all()


def outcome_frame():
    return pd.DataFrame({'clsPx': [100., 200., 180., 160., 150., 155.],
                         'iv10d': [.5, .4, .3, .2, .25, .3],
                         'iv30d': [.5, .4, .3, .2, .25, .3],
                         'wing': [10., 8., 6., 4., 5., 6.]},
                        index=pd.bdate_range('2026-08-03', periods=6))


def test_outcome_starts_next_session_and_censors_unavailable_future():
    x = add_outcomes(outcome_frame())
    assert np.isclose(x.return_2.iloc[0], -20.)
    assert np.isclose(x.iv10_change_2.iloc[0], -20.)
    assert x.joint_down_2.iloc[0] == 1
    assert np.isnan(x.joint_down_2.iloc[-1])
    assert np.isnan(x.return_3.iloc[-1])


def test_missing_intermediate_price_does_not_become_a_complete_outcome():
    x = outcome_frame()
    x.iloc[2, x.columns.get_loc('clsPx')] = np.nan
    out = add_outcomes(x)
    assert np.isnan(out.joint_down_2.iloc[0])
    assert np.isnan(out.return_2.iloc[0])


def test_summary_confidence_fraction_is_normalized_before_liquidity_gate():
    from pandar_skew_journey import features_one
    dates = pd.bdate_range('2025-01-01', periods=200)
    data = pd.DataFrame(index=dates, data={
        'clsPx': np.exp(np.arange(200)*.001)*100, 'stockVolume': 1e6,
        'dlt5Iv10d': .4, 'iv10d': .3, 'iv30d': .3, 'iv60d': .3,
        'exErnDlt25Iv30d': .35, 'exErnIv30d': .3, 'exErnIv10d': .3,
        'confidence': .9})
    result = features_one(data)
    assert result.eligible.iloc[-1]


def test_named_expanding_column_is_used_in_ablation_masks():
    from pandar_skew_journey import masks
    frame = pd.DataFrame(dict(eligible=[True, True], wing_rank=[90., 90.],
        left_censored=[False, False], age=[4, 4], rolling_over=[True, False],
        expanding=[False, True], wing=[5., 6.], premia_available=[True, True],
        both_premia_positive=[True, True], charlie_exhaustion=[True, False],
        iv10_acceleration=[-1., 1.], earnings_premium10=[0., 0.], exit_age=[0, 0]))
    assert masks(frame)['high_expanding'].tolist() == [False, True]
