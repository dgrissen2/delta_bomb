"""Integration tests on synthetic inputs that target genuine failure modes."""
import numpy as np
import pandas as pd

from baskets import build
from features import DESCRIPTORS, POLICIES, sector_features
from inputs import SYMBOLS, balanced


def fixture() -> pd.DataFrame:
    minute = np.arange(570,630)
    values = 30-.01*(minute-570)-.0001*(minute-570)**2
    source = pd.DataFrame(dict(date='2024-01-10',symbol='XLC',minute=minute,
                              spot=100+.01*minute,guard100=True))
    for policy in POLICIES[:-1]:
        source[policy] = values
    for desc in DESCRIPTORS:
        source[desc] = values
        source[desc+'_low'],source[desc+'_high'] = values-1,values+1
    rows = []
    for end in range(599,630):
        row,_ = balanced.measure_window(minute,values,values,np.ones(60,dtype=bool),end=end,radius=2)
        rows.append(row)
    features = sector_features(source,pd.DataFrame(rows),[605])[0]
    return pd.DataFrame([dict(features,symbol=s) for s in SYMBOLS])


def test_majority_and_price_pairing_reproduce_synthetic_signal() -> None:
    states,registry = build(fixture())
    row = states.iloc[0]
    assert row.original_accelerating_6 == row.original_falling_8 == 'yes'
    assert row.paired_price_iv_6 == 'yes'
    assert row.quote_resolved_accelerating_6 == 'no'
    assert row.atm_rising_accelerating_6 == 'no'
    assert not registry.rule.duplicated().any()


def test_weighted_rule_requires_all_weight_mass() -> None:
    frame = fixture()
    weights = pd.DataFrame(dict(date='2024-01-10',symbol=SYMBOLS,equity_weight=np.ones(11)/11))
    states,_ = build(frame,weights)
    assert states.original_weighted_accelerating.iloc[0] == 'yes'
    states,_ = build(frame,weights.iloc[:10])
    assert states.original_weighted_accelerating.iloc[0] == 'unknown'


def test_partial_window_does_not_inherit_finite_half_values() -> None:
    frame = fixture()
    frame.loc[:5,'original_available'] = False
    states,_ = build(frame)
    assert states.original_accelerating_6.iloc[0] == 'unknown'


def test_future_post_measurements_do_not_change_entry_classification() -> None:
    frame = fixture()
    initial,_ = build(frame)
    frame['post_price_return_bps'],frame['post_iv_change'] = -100.,100.
    changed,_ = build(frame)
    assert initial.original_accelerating_6.equals(changed.original_accelerating_6)
    assert initial.paired_price_iv_6.equals(changed.paired_price_iv_6)
    assert initial.post15_paired_6.iloc[0] == 'yes'
    assert changed.post15_paired_6.iloc[0] == 'no'
