"""Critical causal and accounting checks for the exploratory exact-chain replay."""
import numpy as np
import pandas as pd
import pytest

from scripts.pandar_no_hiro_exact import (
    candidate_metrics,
    choose_contract,
    closing_pnl,
    fixed_contract_entry,
    nonoverlap,
    no_selection_status,
    policy_pnl,
    replay,
    spot_atm_iv,
)


def chain() -> pd.DataFrame:
    return pd.DataFrame([
        dict(ticker='TEST', tradeDate='2026-06-01', expirDate='2026-06-19',
             strike=k, stockPrice=100., callBidPrice=bid, callAskPrice=bid+.10,
             callBidSize=1., callAskSize=1., callBidIv=iv-.01, callMidIv=iv,
             callAskIv=iv+.01, delta=d, gamma=.003, vega=.05,
             quoteDate='2026-06-01T19:46:00Z')
        for k, bid, iv, d in [(95, 6., .40, .7), (105, 2., .42, .3),
                               (110, 1., .60, .1), (115, .70, .65, .05)]
    ])


def test_spot_atm_requires_nearest_valid_bracket_without_extrapolation():
    x = chain()
    assert spot_atm_iv(x, 100.)[0] == pytest.approx(.41)
    assert np.isnan(spot_atm_iv(x, 94.)[0])
    x.loc[x.strike.eq(105), 'callMidIv'] = np.nan
    assert np.isnan(spot_atm_iv(x, 100.)[0])


def test_metrics_cost_units_and_true_calendar_dte():
    x = candidate_metrics(chain(), pd.Timestamp('2026-06-01'),
                          pd.Timestamp('2026-06-08'))
    r = x[x.strike.eq(110)].iloc[0]
    assert r.dte == 18
    assert r.wing_points == pytest.approx(18.)
    assert r.scenario_gross == pytest.approx(22.5)
    assert r.round_trip_cost == pytest.approx(13.3)
    assert r.scenario_net == pytest.approx(9.2)
    assert r.required_iv_decline == pytest.approx(2.66)
    assert r.rally_loss_1pct == pytest.approx(10.15)


def test_selectors_and_ties_are_deterministic():
    x = candidate_metrics(chain(), pd.Timestamp('2026-06-01'),
                          pd.Timestamp('2026-06-08'))
    control, _ = choose_contract(x, 'mechanical')
    economic, _ = choose_contract(x, 'economic')
    assert control['strike'] == 110
    assert economic['strike'] == 115
    shuffled, _ = choose_contract(x.sample(frac=1, random_state=42), 'economic')
    assert shuffled['strike'] == economic['strike']


def test_fixed_contract_entry_never_reselects_after_selected_quote_disappears():
    x = candidate_metrics(chain(), pd.Timestamp('2026-06-01'),
                          pd.Timestamp('2026-06-08'))
    chosen, _ = choose_contract(x, 'economic')
    entry = chain().query('strike != 115').copy()
    entry['tradeDate'] = '2026-06-02'
    entry['quoteDate'] = '2026-06-02T19:46:00Z'
    result = fixed_contract_entry(chosen, entry, pd.Timestamp('2026-06-02'),
                                 pd.Timestamp('2026-06-08'), 'economic')
    assert result['entry_status'] == 'censored'
    assert result['entry_reason'] == 'fixed_contract_missing'


def test_failed_entry_economics_is_known_no_entry_without_substitution():
    x = candidate_metrics(chain(), pd.Timestamp('2026-06-01'),
                          pd.Timestamp('2026-06-08'))
    chosen, _ = choose_contract(x, 'economic')
    entry = chain()
    entry['tradeDate'] = '2026-06-02'
    entry['quoteDate'] = '2026-06-02T19:46:00Z'
    entry.loc[entry.strike.eq(115), ['callBidIv', 'callMidIv', 'callAskIv']] = [.41,.42,.43]
    result = fixed_contract_entry(chosen, entry, pd.Timestamp('2026-06-02'),
                                 pd.Timestamp('2026-06-08'), 'economic')
    assert result['entry_status'] == 'no_entry'
    assert result['entry_reason'] == 'entry_no_positive_net_scenario'


def test_deadline_requires_actual_session_and_reservation_survives_failures():
    x = pd.DataFrame(dict(ticker=['A']*4, session_index=[0,1,5,6],
                          input_eligible=[True]*4))
    assert nonoverlap(x).tolist() == [True,False,False,True]
    candidates = candidate_metrics(chain(), pd.Timestamp('2026-06-01'),
                                   pd.Timestamp('2026-06-22'))
    assert not candidates.candidate_valid.any()


def test_actual_quote_sides_costs_and_censoring_are_not_zero_returns():
    assert closing_pnl(1., .20) == pytest.approx(76.70)
    assert policy_pnl('no_entry', np.nan) == 0.
    assert np.isnan(policy_pnl('censored', np.nan))
    assert np.isnan(policy_pnl('admitted', np.nan))
    assert policy_pnl('admitted', 76.7) == 76.7


def test_missing_measurements_censor_but_observed_zero_bid_is_known_no_entry():
    x = chain()
    x.loc[x.strike.gt(100), 'delta'] = np.nan
    measured = candidate_metrics(x, pd.Timestamp('2026-06-01'), pd.Timestamp('2026-06-08'))
    assert no_selection_status(measured, 'no_valid_candidates') == 'censored'
    x = chain()
    x.loc[x.strike.gt(105), 'callBidPrice'] = 0
    x.loc[x.strike.eq(105), 'delta'] = 1
    measured = candidate_metrics(x, pd.Timestamp('2026-06-01'), pd.Timestamp('2026-06-08'))
    assert no_selection_status(measured, 'no_valid_candidates') == 'no_entry'


@pytest.mark.parametrize('field', ['stockPrice', 'strike', 'expirDate'])
def test_unknown_search_envelope_is_censored_not_proven_outside(field):
    x = chain().query('strike == 110').copy()
    x[field] = np.nan
    measured = candidate_metrics(x, pd.Timestamp('2026-06-01'), pd.Timestamp('2026-06-08'))
    assert no_selection_status(measured, 'no_valid_candidates') == 'censored'


def test_wrong_session_atm_bracket_and_kink_neighbor_are_unsupported():
    x = chain()
    x.loc[x.strike.eq(95), 'quoteDate'] = '2026-05-29T19:46:00Z'
    measured = candidate_metrics(x, pd.Timestamp('2026-06-01'), pd.Timestamp('2026-06-08'))
    assert not measured.candidate_valid.any()
    x = chain()
    x.loc[x.strike.eq(115), 'quoteDate'] = '2026-05-29T19:46:00Z'
    measured = candidate_metrics(x, pd.Timestamp('2026-06-01'), pd.Timestamp('2026-06-08'))
    row = measured[measured.strike.eq(110)].iloc[0]
    assert row.candidate_valid
    assert row.kink_status == 'unsupported_neighbors'


def test_scenario_recovery_cannot_imply_negative_buyback_ask():
    x = chain()
    x.loc[x.strike.eq(115), ['callBidIv','callMidIv','callAskIv']] = [5.,5.01,5.02]
    measured = candidate_metrics(x, pd.Timestamp('2026-06-01'), pd.Timestamp('2026-06-08'))
    row = measured[measured.strike.eq(115)].iloc[0]
    assert row.scenario_gross <= 100*row.callAskPrice
    assert row.scenario_net <= 100*row.callBidPrice-3.30+1e-10
    assert row.uncapped_recovery_exceeds_ask


def test_replay_preserves_integer_sizes_and_partial_risk_coverage(monkeypatch):
    from scripts import pandar_no_hiro_exact as module
    calendar = pd.DatetimeIndex(pd.to_datetime([
        '2026-06-01','2026-06-02','2026-06-03','2026-06-04','2026-06-05','2026-06-08']))
    dates = pd.DataFrame(dict(ticker=['TEST']*6, tradeDate=calendar,
                             hiPx=[103.]*6, clsPx=[100.]*6, unadjClsPx=[100.]*6))
    monkeypatch.setattr(module.pd, 'read_parquet', lambda _: dates)
    def fake_chain(source, ticker, date):
        if date == pd.Timestamp('2026-06-03'):
            return pd.DataFrame()
        x = chain()
        x['quoteDate'] = str(date.date())+'T19:46:00Z'
        x['callAskSize'] = x.callAskSize.astype(int)
        return x
    monkeypatch.setattr(module, 'read_chain', fake_chain)
    decision = pd.DataFrame([dict(ticker='TEST', selector='mechanical', session_index=0,
        entry_date=calendar[1], signal_expirDate=pd.Timestamp('2026-06-19'),
        signal_strike=110., entry_status='admitted', entry_callBidPrice=1.,
        entry_stockPrice=100., known_split_through_exit=False,
        entry_callMidIv=.60, entry_spot_atm_iv=.41)])
    lookup = {('TEST',str(day.date())): {'path':'fake-source'} for day in calendar}
    result = replay(decision, calendar, lookup)
    assert result.exit_status.eq('priced').all()
    assert all(value == pytest.approx(-13.3) for value in result.policy_pnl)
    assert result.worst_eod_cover_pnl.isna().all()
    assert result.observed_worst_eod_cover_pnl.notna().all()
