"""The exclusion audit must test alternatives rather than stop at one failed call."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from pandar_call_exclusions import contract_checks


def fixture_chain():
    return pd.DataFrame([
        dict(expirDate='2026-08-28', dte=8, strike=k, stockPrice=100., delta=delta,
             callBidPrice=bid, callAskPrice=ask, callOpenInterest=100,
             callMidIv=iv, callBidIv=iv-.01)
        for k, delta, bid, ask, iv in [(100., .5, 4., 4.1, .5),
                                       (120., .08, .8, .85, .60),
                                       (125., .04, .10, .15, .65),
                                       (130., .03, .22, .26, .70)]
    ])


def test_another_strike_can_pass_after_nearest_four_delta_fails():
    result = contract_checks(fixture_chain(), set())
    assert not result.set_index('strike').loc[125., 'all_original_contract_gates']
    assert result.set_index('strike').loc[130., 'all_original_contract_gates']


def test_delta_ablation_does_not_relax_quote_gates():
    frame = fixture_chain()
    result = contract_checks(frame, set()).set_index('strike')
    assert not result.loc[120., 'all_original_contract_gates']
    assert result.loc[120., 'without_delta_band']
    frame.loc[frame.strike.eq(120.), 'callAskPrice'] = 1.2
    result = contract_checks(frame, set()).set_index('strike')
    assert not result.loc[120., 'without_delta_band']


def test_event_expiry_and_crossed_quotes_do_not_pass():
    frame = fixture_chain()
    assert not contract_checks(frame, {'2026-08-28'}).all_original_contract_gates.any()
    frame.loc[frame.strike.eq(130.), 'callAskPrice'] = .20
    assert not contract_checks(frame, set()).set_index('strike').loc[130., 'all_original_contract_gates']
