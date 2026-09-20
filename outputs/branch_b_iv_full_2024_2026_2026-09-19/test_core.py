"""Causal and missing-data boundaries for the full-population IV replay."""
import numpy as np
import pandas as pd
import pytest

from core import classify, conjunct, measure, unique_entries, thin


def test_missing_votes_never_renormalize() -> None:
    assert classify(5, 0, 6) == 'no'
    assert classify(5, 1, 6) == 'unknown'
    assert classify(6, 5, 6) == 'yes'
    assert classify(0, 11, 8) == 'unknown'
    with pytest.raises(ValueError):
        classify(7, 5, 6)


def test_conjunction_uses_known_false() -> None:
    assert conjunct('unknown', 'no') == 'no'
    assert conjunct('yes', 'unknown') == 'unknown'
    assert conjunct('yes', 'yes') == 'yes'


def test_window_is_prebreakout_and_complete() -> None:
    source = pd.Series(30 - np.arange(300)*.01, index=np.arange(570, 870))
    first = measure(source, 605)
    source.loc[600:] = 100000
    assert measure(source, 605) == first
    assert first['b2'] == pytest.approx(-.01)
    assert first['acceleration'] == pytest.approx(0, abs=1e-12)
    assert not measure(source, 604)['available']
    source.loc[570] = np.nan
    assert not measure(source, 605)['available']


def test_union_deduplicates_and_rejects_conflicts() -> None:
    rows = pd.DataFrame({'date':['2024-01-10']*3, 'known_min':[610,610,630],
                         'outcome':['target_first']*3})
    assert len(unique_entries(rows)) == 2
    rows.loc[1,'outcome'] = 'adverse_first'
    with pytest.raises(ValueError):
        unique_entries(rows)


def test_spacing_is_greedy_and_after_filter() -> None:
    rows = pd.DataFrame({'date':['2024-01-10']*4,'known_min':[610,650,669,670]})
    assert thin(rows, 'spaced60').known_min.tolist() == [610,670]
    assert thin(rows.iloc[1:], 'first').known_min.tolist() == [650]


def test_basket_keeps_unknown_and_false_conjuncts_separate() -> None:
    from baskets import count_states, paired_votes
    frame = pd.DataFrame({'date':['2024-01-10']*11,'known_min':[605]*11})
    yes = np.array([True]*5+[False]*6)
    known = np.array([True]*10+[False])
    assert count_states(frame,yes,known,6).iloc[0] == 'unknown'
    price = np.array([1.,-1.,np.nan,np.nan])
    iv = np.array([-.1,np.nan,.1,-.1])
    good,observed = paired_votes(price,iv)
    assert good.tolist() == [True,False,False,False]
    assert observed.tolist() == [True,True,True,False]
