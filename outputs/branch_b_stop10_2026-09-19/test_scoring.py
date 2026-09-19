"""Barrier ordering, horizon and unknown intraminute order must survive rescoring."""
import pandas as pd
import pytest

from scoring import score


def prices():
    return pd.DataFrame({'open': 100., 'high': 101., 'low': 99., 'close': 100.},
                        index=range(600, 661))


def test_old_winner_can_stop_before_reaching_target():
    bars = prices()
    bars.loc[610, 'low'] = 90
    bars.loc[615, 'high'] = 105
    assert score(bars, 600, 15)['outcome'] == 'target_first'
    assert score(bars, 600, 10)['outcome'] == 'adverse_first'
    assert score(bars, 600, 10)['first_touch_min'] == 610


def test_posttarget_stop_does_not_change_a_win():
    bars = prices()
    bars.loc[601, 'high'] = 105
    bars.loc[610, 'low'] = 80
    assert score(bars, 600, 10)['outcome'] == 'target_first'


def test_same_bar_double_touch_is_ambiguous():
    bars = prices()
    bars.loc[600, ['high', 'low']] = [105, 90]
    assert score(bars, 600, 10)['outcome'] == 'ambiguous'
    assert score(bars, 600, 15)['outcome'] == 'target_first'


def test_horizon_includes_sixtieth_bar_excludes_sixty_first():
    bars = prices()
    bars.loc[660, 'high'] = 105
    assert score(bars, 600, 10)['outcome'] == 'neither'
    bars.loc[659, 'high'] = 105
    assert score(bars, 600, 10)['outcome'] == 'target_first'


def test_old_timeout_can_become_new_stop():
    bars = prices()
    bars.loc[615, 'low'] = 89
    assert score(bars, 600, 15)['outcome'] == 'neither'
    assert score(bars, 600, 10)['outcome'] == 'adverse_first'


@pytest.mark.parametrize('stop', [0, -10, float('nan'), float('inf'), True])
def test_invalid_stop_rejected(stop):
    with pytest.raises(ValueError):
        score(prices(), 600, stop)


def test_missing_observation_is_not_a_timeout():
    with pytest.raises(ValueError):
        score(prices().drop(index=601), 600, 10)


def test_invalid_ohlc_is_not_scored():
    bars = prices()
    bars.loc[605, 'high'] = 99
    with pytest.raises(ValueError):
        score(bars, 600, 10)
