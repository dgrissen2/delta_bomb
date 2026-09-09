"""Causal history and surface-matching invariants for strike richness."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from pandar_richness import prior_stats, interp_inside, tenor_iv


def test_z_score_excludes_current_and_future():
    f = pd.DataFrame({'date': pd.bdate_range('2026-01-01', periods=65).strftime('%Y-%m-%d'),
                      'value': np.arange(65, dtype=float)})
    day = f.date.iloc[60]
    result = prior_stats(f, day, 100, lookback=60, minimum=40)
    f.loc[60:, 'value'] = 1e12
    assert result == prior_stats(f, day, 100, lookback=60, minimum=40)
    assert result['n'] == 60
    assert result['mean'] == pytest.approx(29.5)


def test_insufficient_or_constant_history_has_no_z():
    f = pd.DataFrame({'date': ['2026-01-01', '2026-01-02'], 'value': [2., 2.]})
    assert np.isnan(prior_stats(f, '2026-02-01', 5, minimum=3)['z'])
    assert np.isnan(prior_stats(f, '2026-02-01', 5, minimum=2)['z'])


def test_surface_matching_never_extrapolates():
    assert np.isnan(interp_inside([.03, .05], [1., 2.], .02))
    assert interp_inside([.03, .05], [1., 2.], .04) == pytest.approx(1.5)
    assert np.isnan(tenor_iv([7., 14.], [.2, .4], 5.))


def test_tenor_interpolates_total_variance():
    assert tenor_iv([5., 15.], [.2, .4], 10.) == pytest.approx(np.sqrt(.13))


def test_duplicate_sessions_do_not_inflate_history():
    f = pd.DataFrame({'date': ['2026-01-01', '2026-01-01'], 'value': [2., 2.]})
    with pytest.raises(ValueError, match='duplicate'):
        prior_stats(f, '2026-01-02', 3, minimum=1)
