from math import lcm
import numpy as np
import pandas as pd
import pytest
from calibrate_exact import exact_median


def test_3600_equal_weights_select_lower_middle_regression():
    values=np.arange(3600,dtype=float)
    dates=pd.Series(np.repeat(np.arange(60),60))
    assert exact_median(values,dates) == 1799


def test_more_rows_do_not_give_one_date_more_weight():
    assert exact_median(np.r_[0.,np.full(100,100.)],pd.Series(['a']+['b']*100)) == 0
    assert exact_median(np.r_[np.zeros(77),np.full(100,100.)],pd.Series(['a']*77+['b']*100)) == 0


def test_unequal_counts_have_exact_date_weights():
    assert exact_median(np.array([0,10,20,30,40,50]),pd.Series(['a','a','b','b','b','c'])) == 30


def test_large_denominator_uses_arbitrary_precision():
    counts=[13,17,19,23,29,31,37,41,43,47,53,59]
    assert lcm(*counts)*len(counts) > np.iinfo(np.int64).max
    values=np.concatenate([np.full(n,0. if i<6 else 100.) for i,n in enumerate(counts)])
    dates=pd.Series(np.concatenate([np.full(n,i) for i,n in enumerate(counts)]))
    assert exact_median(values,dates) == 0


def test_nonfinite_input_rejected():
    with pytest.raises(ValueError):
        exact_median(np.array([0.,np.nan]),pd.Series(['a','b']))
