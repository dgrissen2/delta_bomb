"""Guard against reversing put moneyness or mixing contracts in the report."""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from pandar_eligibility import contract_metrics


def chain():
    return pd.DataFrame([
        dict(ticker='TEST', tradeDate='2026-08-20', expirDate='2026-09-18',
             strike=70., stockPrice=100., delta=.99),
        dict(ticker='TEST', tradeDate='2026-08-20', expirDate='2026-09-25',
             strike=70., stockPrice=100., delta=.97),
    ])


def test_put_moneyness_and_delta_coordinate():
    result = contract_metrics(chain(), 'TEST', '2026-08-20', '2026-09-18', 70., 'put')
    assert result['otm_pct'] == pytest.approx(30.)
    assert result['option_delta'] == pytest.approx(-.01)
    assert result['orats_call_coordinate_delta'] == .99


def test_call_otm_and_option_delta():
    frame = chain()
    frame.loc[0, ['strike', 'delta']] = [130., .04]
    result = contract_metrics(frame, 'TEST', '2026-08-20', '2026-09-18', 130., 'call')
    assert result['otm_pct'] == pytest.approx(30.)
    assert result['option_delta'] == .04


def test_missing_or_duplicate_contract_is_an_error():
    with pytest.raises(ValueError, match='exactly one'):
        contract_metrics(chain(), 'TEST', '2026-08-21', '2026-09-18', 70., 'put')
    with pytest.raises(ValueError, match='exactly one'):
        contract_metrics(pd.concat([chain(), chain()]), 'TEST', '2026-08-20',
                         '2026-09-18', 70., 'put')
